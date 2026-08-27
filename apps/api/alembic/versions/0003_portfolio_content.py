"""Add managed portfolio content.

Revision ID: 0003_portfolio_content
Revises: 0002_admin_users
"""

from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0003_portfolio_content"
down_revision: Union[str, Sequence[str], None] = "0002_admin_users"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "portfolio_content",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("hero_eyebrow", sa.String(length=120), nullable=False),
        sa.Column("hero_title", sa.String(length=220), nullable=False),
        sa.Column("hero_intro", sa.Text(), nullable=False),
        sa.Column("hero_location", sa.String(length=120), nullable=False),
        sa.Column("hero_experience", sa.String(length=120), nullable=False),
        sa.Column("about_title", sa.String(length=220), nullable=False),
        sa.Column("about_body", sa.Text(), nullable=False),
        sa.Column("github_url", sa.String(length=300), nullable=False),
        sa.Column("studio_title", sa.String(length=220), nullable=False),
        sa.Column("studio_intro", sa.Text(), nullable=False),
        sa.Column("offers", sa.Text(), nullable=False),
        sa.Column("contact_title", sa.String(length=220), nullable=False),
        sa.Column("contact_intro", sa.Text(), nullable=False),
        sa.Column("contact_email", sa.String(length=254), nullable=False),
        sa.Column("skills", sa.Text(), nullable=False),
        sa.Column("projects", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.CheckConstraint("id = 1", name="ck_portfolio_content_singleton"),
    )


def downgrade() -> None:
    op.drop_table("portfolio_content")
