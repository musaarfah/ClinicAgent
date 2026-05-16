"""create locations and handoffs

Revision ID: 0003_locations_handoffs
Revises: 0002_create_agent_session_states
Create Date: 2026-05-16 00:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op


revision: str = "0003_locations_handoffs"
down_revision: str | None = "0002_create_agent_session_states"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "clinic_locations",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("address", sa.String(length=240), nullable=False),
        sa.Column("hours", sa.String(length=120), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "handoff_requests",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("session_id", sa.String(length=64), nullable=False),
        sa.Column("reason", sa.String(length=500), nullable=False),
        sa.Column("status", sa.String(length=40), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_handoff_requests_session_id",
        "handoff_requests",
        ["session_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_handoff_requests_session_id", table_name="handoff_requests")
    op.drop_table("handoff_requests")
    op.drop_table("clinic_locations")
