"""Add Photoshop job tracking fields to service leads.

Revision ID: 0006_lead_job_tracking
Revises: 0005_lead_crm_fields
"""

from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0006_lead_job_tracking"
down_revision: Union[str, Sequence[str], None] = "0005_lead_crm_fields"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("service_leads") as batch_op:
        batch_op.add_column(sa.Column("job_stage", sa.String(length=30), nullable=True))
        batch_op.add_column(sa.Column("quoted_amount", sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column("quote_currency", sa.String(length=10), nullable=True))
        batch_op.add_column(sa.Column("deadline_at", sa.String(length=20), nullable=True))
        batch_op.add_column(sa.Column("file_url", sa.String(length=500), nullable=True))
        batch_op.add_column(sa.Column("delivery_url", sa.String(length=500), nullable=True))
        batch_op.add_column(sa.Column("revision_count", sa.Integer(), nullable=False, server_default="0"))
        batch_op.add_column(sa.Column("paid_at", sa.String(length=20), nullable=True))
        batch_op.create_check_constraint(
            "ck_service_leads_job_stage",
            "job_stage IS NULL OR job_stage IN ('awaiting_files', 'editing', 'review', 'revision', 'delivered', 'paid')",
        )
        batch_op.create_check_constraint(
            "ck_service_leads_quote_nonnegative",
            "quoted_amount IS NULL OR quoted_amount >= 0",
        )
        batch_op.create_check_constraint(
            "ck_service_leads_revision_nonnegative",
            "revision_count >= 0",
        )


def downgrade() -> None:
    with op.batch_alter_table("service_leads") as batch_op:
        batch_op.drop_constraint("ck_service_leads_revision_nonnegative", type_="check")
        batch_op.drop_constraint("ck_service_leads_quote_nonnegative", type_="check")
        batch_op.drop_constraint("ck_service_leads_job_stage", type_="check")
        batch_op.drop_column("paid_at")
        batch_op.drop_column("revision_count")
        batch_op.drop_column("delivery_url")
        batch_op.drop_column("file_url")
        batch_op.drop_column("deadline_at")
        batch_op.drop_column("quote_currency")
        batch_op.drop_column("quoted_amount")
        batch_op.drop_column("job_stage")
