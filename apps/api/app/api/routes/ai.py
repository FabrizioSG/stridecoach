from datetime import UTC, datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.training import TrainingPlan, TrainingWeek, User, Workout
from app.services.ai_service import AIService

router = APIRouter(prefix="/ai", tags=["ai"])


class WorkoutAnalysisResponse(BaseModel):
    analysis: str
    analysisLength: int


@router.post("/workouts/{workout_id}/analysis")
def analyze_workout(
    workout_id: UUID,
    regenerate: bool = Query(False),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> WorkoutAnalysisResponse:
    workout = db.scalar(
        select(Workout)
        .join(Workout.week)
        .join(TrainingWeek.plan)
        .where(Workout.id == workout_id, TrainingPlan.user_id == current_user.id)
    )
    if workout is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workout not found")

    if workout.ai_analysis and not regenerate:
        return WorkoutAnalysisResponse(
            analysis=workout.ai_analysis,
            analysisLength=len(workout.ai_analysis),
        )

    analysis = AIService().analyze_workout(workout)
    workout.ai_analysis = analysis
    workout.ai_analysis_generated_at = datetime.now(UTC)
    db.add(workout)
    db.commit()
    return WorkoutAnalysisResponse(analysis=analysis, analysisLength=len(analysis))
