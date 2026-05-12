from datetime import date
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.training import TrainingPlan, TrainingWeek, User, Workout, WorkoutStatus
from app.schemas.training import DashboardSummary, TrainingPlanRead, WorkoutRead, WorkoutUpdate

router = APIRouter(prefix="/plans", tags=["training plans"])


@router.get("", response_model=list[TrainingPlanRead])
def list_plans(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[TrainingPlan]:
    statement = (
        select(TrainingPlan)
        .where(TrainingPlan.user_id == current_user.id)
        .options(selectinload(TrainingPlan.weeks).selectinload(TrainingWeek.workouts))
        .order_by(TrainingPlan.starts_on.desc())
    )
    return list(db.scalars(statement).all())


@router.get("/active", response_model=TrainingPlanRead)
def get_active_plan(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> TrainingPlan:
    plan = get_active_user_plan(db, current_user)
    if not plan:
        raise HTTPException(status_code=404, detail="No training plan has been imported yet.")
    return plan


@router.delete("/{plan_id}", status_code=204)
def delete_plan(
    plan_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    plan = db.scalar(
        select(TrainingPlan).where(
            TrainingPlan.id == plan_id,
            TrainingPlan.user_id == current_user.id,
        )
    )
    if not plan:
        raise HTTPException(status_code=404, detail="Training plan not found")
    db.delete(plan)
    db.commit()


def get_active_user_plan(db: Session, current_user: User) -> TrainingPlan | None:
    statement = (
        select(TrainingPlan)
        .where(TrainingPlan.user_id == current_user.id)
        .options(selectinload(TrainingPlan.weeks).selectinload(TrainingWeek.workouts))
        .order_by(TrainingPlan.starts_on.desc())
    )
    return db.scalars(statement).first()


@router.get("/dashboard", response_model=DashboardSummary)
def get_dashboard_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    plan = get_active_user_plan(db, current_user)
    if not plan:
        return {
            "weekly_mileage_km": 0,
            "weekly_completed_mileage_km": 0,
            "weekly_planned_mileage_km": 0,
            "upcoming_workout": None,
            "recent_workouts": [],
            "consistency": [],
            "ai_insight": "Import a training plan to unlock coaching insights.",
        }

    workouts = [workout for week in plan.weeks for workout in week.workouts]
    workouts.sort(key=lambda workout: workout.scheduled_date)
    today = date.today()
    upcoming = next((workout for workout in workouts if workout.scheduled_date >= today), None)
    recent = sorted(
        [workout for workout in workouts if workout.status == WorkoutStatus.completed],
        key=lambda workout: workout.scheduled_date,
        reverse=True,
    )[:4]
    current_week_workouts = [
        workout
        for workout in workouts
        if workout.scheduled_date.isocalendar().week == today.isocalendar().week
    ]
    weekly_completed_mileage = sum(
        workout.actual_distance_km or 0
        for workout in current_week_workouts
        if workout.status == WorkoutStatus.completed
    )
    weekly_planned_mileage = sum(
        workout.planned_distance_km or 0 for workout in current_week_workouts
    )

    completed_count = sum(1 for workout in workouts if workout.status == WorkoutStatus.completed)
    planned_count = len(workouts)

    return {
        "weekly_mileage_km": round(weekly_completed_mileage, 1),
        "weekly_completed_mileage_km": round(weekly_completed_mileage, 1),
        "weekly_planned_mileage_km": round(weekly_planned_mileage, 1),
        "upcoming_workout": upcoming,
        "recent_workouts": recent,
        "consistency": build_consistency(plan),
        "ai_insight": build_dashboard_insight(
            upcoming_title=upcoming.title if upcoming else None,
            completed_count=completed_count,
            planned_count=planned_count,
        ),
    }


def build_consistency(plan: TrainingPlan) -> list[dict[str, int | str]]:
    return [
        {
            "week": f"W{week.week_number}",
            "completed": sum(
                1 for workout in week.workouts if workout.status == WorkoutStatus.completed
            ),
            "planned": len(week.workouts),
        }
        for week in plan.weeks
    ]


def build_dashboard_insight(
    upcoming_title: str | None,
    completed_count: int,
    planned_count: int,
) -> str:
    if planned_count == 0:
        return "Import workouts to unlock coaching insights."
    if completed_count == 0:
        if upcoming_title:
            return (
                f"Your plan is loaded. Start with {upcoming_title}, "
                "then sync or link the activity."
            )
        return "Your plan is loaded. Complete or link a workout to start building training history."
    return (
        f"You have completed {completed_count} of {planned_count} planned workouts. "
        "Keep linking activities so your coaching insights reflect the real work."
    )


@router.patch("/workouts/{workout_id}", response_model=WorkoutRead)
def update_workout(
    workout_id: UUID,
    payload: WorkoutUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Workout:
    statement = (
        select(Workout)
        .join(Workout.week)
        .join(TrainingWeek.plan)
        .where(Workout.id == workout_id, TrainingPlan.user_id == current_user.id)
    )
    workout = db.scalar(statement)
    if not workout:
        raise HTTPException(status_code=404, detail="Workout not found")

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(workout, field, value)

    db.add(workout)
    db.commit()
    db.refresh(workout)
    return workout
