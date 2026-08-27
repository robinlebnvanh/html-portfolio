"""Add service lead workflow.

Revision ID: 0004_service_leads
Revises: 0003_portfolio_content
"""

from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0004_service_leads"
down_revision: Union[str, Sequence[str], None] = "0003_portfolio_content"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "service_leads",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("source", sa.String(length=80), nullable=False),
        sa.Column("business_name", sa.String(length=160), nullable=False),
        sa.Column("customer_name", sa.String(length=160), nullable=False),
        sa.Column("email", sa.String(length=254), nullable=False),
        sa.Column("preferred_date", sa.String(length=20), nullable=False),
        sa.Column("package_name", sa.String(length=160), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("status", sa.String(length=30), nullable=False, server_default="new"),
        sa.Column("admin_note", sa.Text()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.CheckConstraint(
            "status IN ('new', 'contacted', 'proposal_sent', 'booked', 'closed')",
            name="ck_service_leads_status",
        ),
    )


def downgrade() -> None:
    op.drop_table("service_leads")
