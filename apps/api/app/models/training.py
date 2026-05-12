import enum
import uuid
from datetime import date, datetime

from sqlalchemy import (
    BigInteger,
    Date,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


class WorkoutStatus(str, enum.Enum):
    planned = "planned"
    completed = "completed"
    missed = "missed"


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    supabase_user_id: Mapped[str | None] = mapped_column(String(255), unique=True, index=True)
    email: Mapped[str | None] = mapped_column(String(255), index=True)
    display_name: Mapped[str | None] = mapped_column(String(255))
    avatar_url: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    training_plans: Mapped[list["TrainingPlan"]] = relationship(back_populates="user")
    strava_connection: Mapped["StravaConnection | None"] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )


class StravaConnection(Base):
    __tablename__ = "strava_connections"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), unique=True, index=True)
    athlete_id: Mapped[int | None] = mapped_column(BigInteger, unique=True, index=True)
    athlete_username: Mapped[str | None] = mapped_column(String(255))
    athlete_firstname: Mapped[str | None] = mapped_column(String(255))
    athlete_lastname: Mapped[str | None] = mapped_column(String(255))
    scope: Mapped[str | None] = mapped_column(String(500))
    access_token: Mapped[str | None] = mapped_column(Text)
    refresh_token: Mapped[str | None] = mapped_column(Text)
    expires_at: Mapped[int | None] = mapped_column(Integer)
    oauth_state: Mapped[str | None] = mapped_column(String(255), unique=True, index=True)
    connected_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    user: Mapped[User] = relationship(back_populates="strava_connection")
    activities: Mapped[list["StravaActivity"]] = relationship(
        back_populates="connection", cascade="all, delete-orphan"
    )


class TrainingPlan(Base):
    __tablename__ = "training_plans"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    title: Mapped[str] = mapped_column(String(200))
    description: Mapped[str | None] = mapped_column(Text)
    goal_race: Mapped[str | None] = mapped_column(String(200))
    starts_on: Mapped[date] = mapped_column(Date)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    user: Mapped[User | None] = relationship(back_populates="training_plans")
    weeks: Mapped[list["TrainingWeek"]] = relationship(
        back_populates="plan", cascade="all, delete-orphan", order_by="TrainingWeek.week_number"
    )


class TrainingWeek(Base):
    __tablename__ = "training_weeks"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    plan_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("training_plans.id"))
    week_number: Mapped[int] = mapped_column(Integer)
    starts_on: Mapped[date] = mapped_column(Date)
    focus: Mapped[str | None] = mapped_column(String(255))

    plan: Mapped[TrainingPlan] = relationship(back_populates="weeks")
    workouts: Mapped[list["Workout"]] = relationship(
        back_populates="week", cascade="all, delete-orphan", order_by="Workout.scheduled_date"
    )


class Workout(Base):
    __tablename__ = "workouts"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    week_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("training_weeks.id"))
    title: Mapped[str] = mapped_column(String(200))
    description: Mapped[str | None] = mapped_column(Text)
    planned_distance_km: Mapped[float | None] = mapped_column(Float)
    planned_duration_min: Mapped[int | None] = mapped_column(Integer)
    planned_pace: Mapped[str | None] = mapped_column(String(50))
    planned_hr_zone: Mapped[str | None] = mapped_column(String(50))
    scheduled_date: Mapped[date] = mapped_column(Date)
    status: Mapped[WorkoutStatus] = mapped_column(
        Enum(WorkoutStatus, name="workout_status"), default=WorkoutStatus.planned
    )
    actual_distance_km: Mapped[float | None] = mapped_column(Float)
    actual_duration_min: Mapped[int | None] = mapped_column(Integer)
    actual_avg_hr: Mapped[int | None] = mapped_column(Integer)
    actual_avg_cadence: Mapped[int | None] = mapped_column(Integer)
    actual_avg_pace: Mapped[str | None] = mapped_column(String(50))
    notes: Mapped[str | None] = mapped_column(Text)
    ai_analysis: Mapped[str | None] = mapped_column(Text)
    ai_analysis_generated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    week: Mapped[TrainingWeek] = relationship(back_populates="workouts")
    strava_activity: Mapped["StravaActivity | None"] = relationship(back_populates="workout")


class StravaActivity(Base):
    __tablename__ = "strava_activities"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    connection_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("strava_connections.id"), index=True
    )
    workout_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("workouts.id"), nullable=True, unique=True, index=True
    )
    strava_activity_id: Mapped[int] = mapped_column(BigInteger, unique=True, index=True)
    name: Mapped[str] = mapped_column(String(255))
    sport_type: Mapped[str | None] = mapped_column(String(100))
    start_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    distance_m: Mapped[float | None] = mapped_column(Float)
    moving_time_sec: Mapped[int | None] = mapped_column(Integer)
    elapsed_time_sec: Mapped[int | None] = mapped_column(Integer)
    average_heartrate: Mapped[float | None] = mapped_column(Float)
    average_cadence: Mapped[float | None] = mapped_column(Float)
    average_speed_mps: Mapped[float | None] = mapped_column(Float)
    raw: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    connection: Mapped[StravaConnection] = relationship(back_populates="activities")
    workout: Mapped[Workout | None] = relationship(back_populates="strava_activity")
