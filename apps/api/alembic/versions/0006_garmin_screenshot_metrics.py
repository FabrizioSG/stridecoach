"""Add Garmin screenshot metrics

Revision ID: 0006_garmin_screenshot_metrics
Revises: 0005_workout_ai_analysis
Create Date: 2026-05-12
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0006_garmin_screenshot_metrics"
down_revision: str | None = "0005_workout_ai_analysis"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("workouts", sa.Column("garmin_screenshot_metrics", sa.Text(), nullable=True))
    op.add_column(
        "workouts",
        sa.Column("garmin_screenshot_imported_at", sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("workouts", "garmin_screenshot_imported_at")
    op.drop_column("workouts", "garmin_screenshot_metrics")
