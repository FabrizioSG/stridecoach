from datetime import date, datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.models.training import WorkoutStatus


def to_camel(value: str) -> str:
    parts = value.split("_")
    return parts[0] + "".join(word.capitalize() for word in parts[1:])


class CamelModel(BaseModel):
    model_config = ConfigDict(from_attributes=True, alias_generator=to_camel, populate_by_name=True)


class WorkoutRead(CamelModel):
    id: UUID
    title: str
    description: str | None
    planned_distance_km: float | None
    planned_duration_min: int | None
    planned_pace: str | None
    planned_hr_zone: str | None
    scheduled_date: date
    status: WorkoutStatus
    actual_distance_km: float | None
    actual_duration_min: int | None
    actual_avg_hr: int | None
    actual_avg_cadence: int | None
    actual_avg_pace: str | None
    notes: str | None
    ai_analysis: str | None
    ai_analysis_generated_at: datetime | None
    garmin_screenshot_metrics: str | None
    garmin_screenshot_imported_at: datetime | None


class GarminScreenshotImportResponse(CamelModel):
    workout: WorkoutRead
    metrics: dict[str, Any]


class WorkoutUpdate(CamelModel):
    status: WorkoutStatus | None = None
    actual_distance_km: float | None = None
    actual_duration_min: int | None = None
    actual_avg_hr: int | None = None
    actual_avg_cadence: int | None = None
    actual_avg_pace: str | None = None
    notes: str | None = None


class TrainingWeekRead(CamelModel):
    id: UUID
    week_number: int
    starts_on: date
    focus: str | None
    workouts: list[WorkoutRead]


class TrainingPlanRead(CamelModel):
    id: UUID
    title: str
    description: str | None
    goal_race: str | None
    starts_on: date
    weeks: list[TrainingWeekRead]


class DashboardSummary(CamelModel):
    weekly_mileage_km: float
    weekly_completed_mileage_km: float
    weekly_planned_mileage_km: float
    upcoming_workout: WorkoutRead | None
    recent_workouts: list[WorkoutRead]
    consistency: list[dict[str, int | str]]
    ai_insight: str
