"""Add CRM fields and lead activities.

Revision ID: 0005_lead_crm_fields
Revises: 0004_service_leads
"""

from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0005_lead_crm_fields"
down_revision: Union[str, Sequence[str], None] = "0004_service_leads"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("service_leads") as batch_op:
        batch_op.add_column(sa.Column("channel", sa.String(length=40), nullable=False, server_default="form"))
        batch_op.add_column(sa.Column("phone", sa.String(length=40), nullable=True))
        batch_op.add_column(sa.Column("follow_up_at", sa.String(length=20), nullable=True))
        batch_op.alter_column("email", existing_type=sa.String(length=254), nullable=True)
        batch_op.alter_column("preferred_date", existing_type=sa.String(length=20), nullable=True)

    op.create_table(
        "service_lead_activities",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("lead_id", sa.Integer(), nullable=False),
        sa.Column("activity_type", sa.String(length=40), nullable=False, server_default="note"),
        sa.Column("note", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.ForeignKeyConstraint(["lead_id"], ["service_leads.id"], ondelete="CASCADE"),
    )


def downgrade() -> None:
    op.drop_table("service_lead_activities")
    with op.batch_alter_table("service_leads") as batch_op:
        batch_op.alter_column("preferred_date", existing_type=sa.String(length=20), nullable=False)
        batch_op.alter_column("email", existing_type=sa.String(length=254), nullable=False)
        batch_op.drop_column("follow_up_at")
        batch_op.drop_column("phone")
        batch_op.drop_column("channel")
