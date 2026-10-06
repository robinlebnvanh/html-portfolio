"""Add stock analysis review and lesson tables.

Revision ID: 0010_stock_analysis_learning
Revises: 0009_blog_post_images
"""

from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0010_stock_analysis_learning"
down_revision: Union[str, Sequence[str], None] = "0009_blog_post_images"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "stock_analysis_reviews",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("ticker", sa.String(length=12), nullable=False),
        sa.Column("prior_report_path", sa.Text(), nullable=False),
        sa.Column("review_timestamp", sa.Text(), nullable=False),
        sa.Column("evaluation_window", sa.Text()),
        sa.Column("prior_strategy_mode", sa.Text()),
        sa.Column("prior_recommendation", sa.Text()),
        sa.Column("prior_levels", sa.Text()),
        sa.Column("trigger_result", sa.Text()),
        sa.Column("stop_target_order", sa.Text()),
        sa.Column("return_mfe_mae", sa.Text()),
        sa.Column("relative_return", sa.Text()),
        sa.Column("outcome_class", sa.String(length=20), nullable=False),
        sa.Column("process_grade", sa.String(length=20), nullable=False),
        sa.Column("correct_items", sa.Text()),
        sa.Column("gaps", sa.Text()),
        sa.Column("error_tags", sa.Text(), nullable=False, server_default="[]"),
        sa.Column("explanation", sa.Text()),
        sa.Column("ticker_lesson", sa.Text()),
        sa.Column("next_analysis_change", sa.Text()),
        sa.Column("shared_lesson_candidate", sa.Text()),
        sa.Column("payload_json", sa.Text(), nullable=False, server_default="{}"),
        sa.Column("idempotency_key", sa.String(length=160), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.ForeignKeyConstraint(["ticker"], ["stocks.ticker"]),
        sa.CheckConstraint(
            "outcome_class IN ('CORRECT', 'PARTIAL', 'WRONG', 'UNRESOLVED')",
            name="ck_stock_analysis_reviews_outcome",
        ),
        sa.CheckConstraint(
            "process_grade IN ('GOOD', 'MIXED', 'POOR', 'N/A')",
            name="ck_stock_analysis_reviews_process",
        ),
        sa.UniqueConstraint("idempotency_key", name="uq_stock_analysis_reviews_idempotency"),
    )
    op.create_index(
        "ix_stock_analysis_reviews_ticker_created_at",
        "stock_analysis_reviews",
        ["ticker", "created_at"],
    )

    op.create_table(
        "stock_analysis_lessons",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("scope", sa.String(length=20), nullable=False),
        sa.Column("ticker", sa.String(length=12)),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="candidate"),
        sa.Column("severity", sa.String(length=20), nullable=False, server_default="medium"),
        sa.Column("lesson", sa.Text(), nullable=False),
        sa.Column("evidence_count", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("evidence_json", sa.Text(), nullable=False, server_default="[]"),
        sa.Column("idempotency_key", sa.String(length=160), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.ForeignKeyConstraint(["ticker"], ["stocks.ticker"]),
        sa.CheckConstraint("scope IN ('ticker', 'shared')", name="ck_stock_analysis_lessons_scope"),
        sa.CheckConstraint(
            "status IN ('candidate', 'validated', 'rejected')",
            name="ck_stock_analysis_lessons_status",
        ),
        sa.CheckConstraint(
            "severity IN ('low', 'medium', 'high')",
            name="ck_stock_analysis_lessons_severity",
        ),
        sa.CheckConstraint("evidence_count >= 1", name="ck_stock_analysis_lessons_evidence_count"),
        sa.UniqueConstraint("idempotency_key", name="uq_stock_analysis_lessons_idempotency"),
    )
    op.create_index(
        "ix_stock_analysis_lessons_ticker_status",
        "stock_analysis_lessons",
        ["ticker", "status"],
    )


def downgrade() -> None:
    op.drop_index("ix_stock_analysis_lessons_ticker_status", table_name="stock_analysis_lessons")
    op.drop_table("stock_analysis_lessons")
    op.drop_index("ix_stock_analysis_reviews_ticker_created_at", table_name="stock_analysis_reviews")
    op.drop_table("stock_analysis_reviews")
