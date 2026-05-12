"""add strava connections

Revision ID: 0002_strava_connections
Revises: 0001_initial
Create Date: 2026-05-12
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0002_strava_connections"
down_revision: str | None = "0001_initial"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "strava_connections",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("athlete_id", sa.Integer(), nullable=True),
        sa.Column("athlete_username", sa.String(length=255), nullable=True),
        sa.Column("athlete_firstname", sa.String(length=255), nullable=True),
        sa.Column("athlete_lastname", sa.String(length=255), nullable=True),
        sa.Column("scope", sa.String(length=500), nullable=True),
        sa.Column("access_token", sa.Text(), nullable=True),
        sa.Column("refresh_token", sa.Text(), nullable=True),
        sa.Column("expires_at", sa.Integer(), nullable=True),
        sa.Column("oauth_state", sa.String(length=255), nullable=True),
        sa.Column("connected_at", sa.DateTime(timezone=True), nullable=True),
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
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_strava_connections_athlete_id"),
        "strava_connections",
        ["athlete_id"],
        unique=True,
    )
    op.create_index(
        op.f("ix_strava_connections_oauth_state"),
        "strava_connections",
        ["oauth_state"],
        unique=True,
    )
    op.create_index(
        op.f("ix_strava_connections_user_id"),
        "strava_connections",
        ["user_id"],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_strava_connections_user_id"), table_name="strava_connections")
    op.drop_index(op.f("ix_strava_connections_oauth_state"), table_name="strava_connections")
    op.drop_index(op.f("ix_strava_connections_athlete_id"), table_name="strava_connections")
    op.drop_table("strava_connections")
