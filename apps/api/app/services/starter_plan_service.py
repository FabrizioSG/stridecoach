from datetime import date, timedelta

from app.models.training import TrainingPlan, TrainingWeek, User, Workout, WorkoutStatus


def build_starter_plan(user: User) -> TrainingPlan:
    start = date.today() - timedelta(days=date.today().weekday())
    plan = TrainingPlan(
        user=user,
        title="Local Demo 10K Base Builder",
        description=(
            "A starter-friendly four week plan focused on consistency, "
            "aerobic base, and gentle speed."
        ),
        goal_race="Community 10K",
        starts_on=start,
    )

    week_definitions = [
        (
            "Foundation rhythm",
            [("Easy Run", 5, "Z2"), ("Strides", 4, "Z2-Z4"), ("Long Run", 8, "Z2")],
        ),
        (
            "Aerobic strength",
            [("Easy Run", 6, "Z2"), ("Tempo Blocks", 7, "Z3"), ("Long Run", 9, "Z2")],
        ),
        (
            "Controlled quality",
            [
                ("Recovery Run", 5, "Z1-Z2"),
                ("Hill Repeats", 6, "Z4"),
                ("Long Run", 10, "Z2"),
            ],
        ),
        (
            "Absorb and sharpen",
            [
                ("Easy Run", 5, "Z2"),
                ("Progression Run", 7, "Z2-Z3"),
                ("Long Run", 8, "Z2"),
            ],
        ),
    ]

    for week_index, (focus, workouts) in enumerate(week_definitions, start=1):
        week = TrainingWeek(
            plan=plan,
            week_number=week_index,
            starts_on=start + timedelta(days=(week_index - 1) * 7),
            focus=focus,
        )
        for workout_index, (title, distance, zone) in enumerate(workouts):
            scheduled = week.starts_on + timedelta(days=[1, 3, 6][workout_index])
            status = WorkoutStatus.completed if scheduled < date.today() else WorkoutStatus.planned
            is_completed = status == WorkoutStatus.completed
            week.workouts.append(
                Workout(
                    title=title,
                    description="Stay relaxed and finish feeling like you could keep going.",
                    planned_distance_km=distance,
                    planned_duration_min=round(distance * 6.2),
                    planned_pace="6:10/km",
                    planned_hr_zone=zone,
                    scheduled_date=scheduled,
                    status=status,
                    actual_distance_km=distance if is_completed else None,
                    actual_duration_min=round(distance * 6.1) if is_completed else None,
                    actual_avg_hr=142 if is_completed else None,
                    actual_avg_cadence=168 if is_completed else None,
                    actual_avg_pace="6:05/km" if is_completed else None,
                    notes="Felt smooth after the first kilometer." if is_completed else None,
                )
            )
        plan.weeks.append(week)

    return plan
