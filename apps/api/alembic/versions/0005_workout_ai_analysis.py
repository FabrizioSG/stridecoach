"""add workout ai analysis fields

Revision ID: 0005_workout_ai_analysis
Revises: 0004_strava_bigint_ids
Create Date: 2026-05-12
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0005_workout_ai_analysis"
down_revision: str | None = "0004_strava_bigint_ids"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("workouts", sa.Column("ai_analysis", sa.Text(), nullable=True))
    op.add_column(
        "workouts",
        sa.Column("ai_analysis_generated_at", sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("workouts", "ai_analysis_generated_at")
    op.drop_column("workouts", "ai_analysis")
