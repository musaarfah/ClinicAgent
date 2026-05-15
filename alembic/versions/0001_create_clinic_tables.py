"""create clinic tables

Revision ID: 0001_create_clinic_tables
Revises:
Create Date: 2026-05-15
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0001_create_clinic_tables"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "patients",
        sa.Column("id", sa.String(length=64), primary_key=True),
        sa.Column("full_name", sa.String(length=200), nullable=False, index=True),
        sa.Column("date_of_birth", sa.Date(), nullable=False),
        sa.Column("phone", sa.String(length=40), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_table(
        "appointment_slots",
        sa.Column("id", sa.String(length=64), primary_key=True),
        sa.Column("provider", sa.String(length=120), nullable=False),
        sa.Column("starts_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("location", sa.String(length=120), nullable=False),
        sa.Column("reason", sa.String(length=120), nullable=False),
        sa.Column("is_available", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_table(
        "appointments",
        sa.Column("id", sa.String(length=64), primary_key=True),
        sa.Column("patient_id", sa.String(length=64), sa.ForeignKey("patients.id"), nullable=False),
        sa.Column("slot_id", sa.String(length=64), sa.ForeignKey("appointment_slots.id"), nullable=False),
        sa.Column("status", sa.String(length=40), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_patients_name_dob", "patients", ["full_name", "date_of_birth"])


def downgrade() -> None:
    op.drop_index("ix_patients_name_dob", table_name="patients")
    op.drop_table("appointments")
    op.drop_table("appointment_slots")
    op.drop_table("patients")
