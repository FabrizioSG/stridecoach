"""add strava activities

Revision ID: 0003_strava_activities
Revises: 0002_strava_connections
Create Date: 2026-05-12
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0003_strava_activities"
down_revision: str | None = "0002_strava_connections"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "strava_activities",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("connection_id", sa.Uuid(), nullable=False),
        sa.Column("workout_id", sa.Uuid(), nullable=True),
        sa.Column("strava_activity_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("sport_type", sa.String(length=100), nullable=True),
        sa.Column("start_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("distance_m", sa.Float(), nullable=True),
        sa.Column("moving_time_sec", sa.Integer(), nullable=True),
        sa.Column("elapsed_time_sec", sa.Integer(), nullable=True),
        sa.Column("average_heartrate", sa.Float(), nullable=True),
        sa.Column("average_cadence", sa.Float(), nullable=True),
        sa.Column("average_speed_mps", sa.Float(), nullable=True),
        sa.Column("raw", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["connection_id"], ["strava_connections.id"]),
        sa.ForeignKeyConstraint(["workout_id"], ["workouts.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_strava_activities_connection_id"),
        "strava_activities",
        ["connection_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_strava_activities_strava_activity_id"),
        "strava_activities",
        ["strava_activity_id"],
        unique=True,
    )
    op.create_index(
        op.f("ix_strava_activities_workout_id"),
        "strava_activities",
        ["workout_id"],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_strava_activities_workout_id"), table_name="strava_activities")
    op.drop_index(
        op.f("ix_strava_activities_strava_activity_id"),
        table_name="strava_activities",
    )
    op.drop_index(
        op.f("ix_strava_activities_connection_id"),
        table_name="strava_activities",
    )
    op.drop_table("strava_activities")
