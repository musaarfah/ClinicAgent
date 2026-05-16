"""create agent session states

Revision ID: 0002_create_agent_session_states
Revises: 0001_create_clinic_tables
Create Date: 2026-05-15 00:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op


revision: str = "0002_create_agent_session_states"
down_revision: str | None = "0001_create_clinic_tables"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "agent_session_states",
        sa.Column("session_id", sa.String(length=64), nullable=False),
        sa.Column("validated_patient_id", sa.String(length=64), nullable=True),
        sa.Column("validated_patient", sa.JSON(), nullable=True),
        sa.Column("last_available_slots", sa.JSON(), nullable=False),
        sa.Column("last_patient_appointments", sa.JSON(), nullable=False),
        sa.Column("last_booked_appointment", sa.JSON(), nullable=True),
        sa.Column("last_cancelled_appointment", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["validated_patient_id"], ["patients.id"]),
        sa.PrimaryKeyConstraint("session_id"),
    )


def downgrade() -> None:
    op.drop_table("agent_session_states")
