"""Create the PRJ008 relational schema.

The current API continues to initialize SQLite from ``database/schema.sql``
until the repository layer is migrated to SQLAlchemy in a later task.
"""

from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0001_initial_schema"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "stocks",
        sa.Column("ticker", sa.String(length=12), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
    )
    op.create_table(
        "portfolios",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("updated_at", sa.String(), nullable=False),
        sa.Column("note", sa.Text()),
        sa.CheckConstraint("id = 1", name="ck_portfolios_singleton"),
    )
    op.create_table(
        "holdings",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("portfolio_id", sa.Integer(), nullable=False),
        sa.Column("ticker", sa.String(length=12), nullable=False),
        sa.Column("quantity", sa.Integer(), nullable=False),
        sa.Column("avg_cost", sa.Integer(), nullable=False),
        sa.Column("entry_date", sa.String(), nullable=False),
        sa.Column("stop_loss", sa.Integer()),
        sa.Column("status", sa.String(length=40), nullable=False),
        sa.Column("note", sa.Text()),
        sa.ForeignKeyConstraint(["portfolio_id"], ["portfolios.id"]),
        sa.ForeignKeyConstraint(["ticker"], ["stocks.ticker"]),
        sa.CheckConstraint("quantity >= 0", name="ck_holdings_quantity_nonnegative"),
        sa.CheckConstraint("avg_cost >= 0", name="ck_holdings_avg_cost_nonnegative"),
        sa.CheckConstraint("stop_loss IS NULL OR stop_loss >= 0", name="ck_holdings_stop_loss_nonnegative"),
        sa.UniqueConstraint("ticker", name="uq_holdings_ticker"),
    )
    op.create_table(
        "holding_targets",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("holding_id", sa.Integer(), nullable=False),
        sa.Column("target_order", sa.Integer(), nullable=False),
        sa.Column("price", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["holding_id"], ["holdings.id"], ondelete="CASCADE"),
        sa.CheckConstraint("target_order > 0", name="ck_holding_targets_order_positive"),
        sa.CheckConstraint("price >= 0", name="ck_holding_targets_price_nonnegative"),
        sa.UniqueConstraint("holding_id", "target_order", name="uq_holding_targets_order"),
    )
    op.create_table(
        "watchlist_items",
        sa.Column("portfolio_id", sa.Integer(), nullable=False),
        sa.Column("ticker", sa.String(length=12), nullable=False),
        sa.ForeignKeyConstraint(["portfolio_id"], ["portfolios.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["ticker"], ["stocks.ticker"]),
        sa.PrimaryKeyConstraint("portfolio_id", "ticker"),
    )
    op.create_table(
        "journals",
        sa.Column("ticker", sa.String(length=12), primary_key=True),
        sa.Column("buffett", sa.Text()),
        sa.Column("updated_at", sa.String()),
        sa.ForeignKeyConstraint(["ticker"], ["stocks.ticker"]),
    )
    op.create_table(
        "journal_snapshots",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("ticker", sa.String(length=12), nullable=False),
        sa.Column("snapshot_date", sa.String(), nullable=False),
        sa.Column("price", sa.Integer(), nullable=False),
        sa.Column("change_percent", sa.Float()),
        sa.Column("rsi", sa.Float()),
        sa.Column("macd", sa.Text()),
        sa.Column("score", sa.Text()),
        sa.Column("recommendation", sa.Text()),
        sa.Column("note", sa.Text()),
        sa.ForeignKeyConstraint(["ticker"], ["journals.ticker"], ondelete="CASCADE"),
        sa.CheckConstraint("price >= 0", name="ck_journal_snapshots_price_nonnegative"),
        sa.CheckConstraint("rsi IS NULL OR (rsi >= 0 AND rsi <= 100)", name="ck_journal_snapshots_rsi_range"),
        sa.UniqueConstraint("ticker", "snapshot_date", name="uq_journal_snapshots_date"),
    )
    op.create_table(
        "trades",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("ticker", sa.String(length=12), nullable=False),
        sa.Column("trade_date", sa.String(), nullable=False),
        sa.Column("trade_type", sa.String(), nullable=False),
        sa.Column("price", sa.Integer(), nullable=False),
        sa.Column("stop_loss", sa.Integer()),
        sa.Column("pnl", sa.Text()),
        sa.Column("note", sa.Text()),
        sa.ForeignKeyConstraint(["ticker"], ["journals.ticker"], ondelete="CASCADE"),
        sa.CheckConstraint("price >= 0", name="ck_trades_price_nonnegative"),
        sa.CheckConstraint("stop_loss IS NULL OR stop_loss >= 0", name="ck_trades_stop_loss_nonnegative"),
    )
    op.create_table(
        "journal_entry_plans",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("ticker", sa.String(length=12), nullable=False),
        sa.Column("plan_order", sa.Integer(), nullable=False),
        sa.Column("condition", sa.Text(), nullable=False),
        sa.Column("entry_text", sa.Text(), nullable=False),
        sa.Column("stop_loss_action", sa.Text()),
        sa.Column("target_text", sa.Text()),
        sa.ForeignKeyConstraint(["ticker"], ["journals.ticker"], ondelete="CASCADE"),
        sa.CheckConstraint("plan_order > 0", name="ck_journal_entry_plans_order_positive"),
        sa.UniqueConstraint("ticker", "plan_order", name="uq_journal_entry_plans_order"),
    )
    op.create_table(
        "journal_positions",
        sa.Column("ticker", sa.String(length=12), primary_key=True),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("quantity", sa.Integer()),
        sa.Column("avg_cost", sa.Integer()),
        sa.Column("entry_date", sa.String()),
        sa.Column("invested_amount", sa.Integer()),
        sa.ForeignKeyConstraint(["ticker"], ["journals.ticker"], ondelete="CASCADE"),
        sa.CheckConstraint("quantity IS NULL OR quantity >= 0", name="ck_journal_positions_quantity_nonnegative"),
        sa.CheckConstraint("avg_cost IS NULL OR avg_cost >= 0", name="ck_journal_positions_avg_cost_nonnegative"),
        sa.CheckConstraint("invested_amount IS NULL OR invested_amount >= 0", name="ck_journal_positions_invested_nonnegative"),
    )
    op.create_table(
        "journal_theses",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("ticker", sa.String(length=12), nullable=False),
        sa.Column("side", sa.String(), nullable=False),
        sa.Column("item_order", sa.Integer(), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.ForeignKeyConstraint(["ticker"], ["journals.ticker"], ondelete="CASCADE"),
        sa.CheckConstraint("side IN ('bull', 'bear')", name="ck_journal_theses_side"),
        sa.CheckConstraint("item_order > 0", name="ck_journal_theses_order_positive"),
        sa.UniqueConstraint("ticker", "side", "item_order", name="uq_journal_theses_item"),
    )
    op.create_table(
        "blog_posts",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("slug", sa.String(), nullable=False),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("category", sa.String(), nullable=False),
        sa.Column("tags", sa.Text(), nullable=False, server_default="[]"),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("published_at", sa.String()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.CheckConstraint("status IN ('draft', 'published')", name="ck_blog_posts_status"),
        sa.UniqueConstraint("slug", name="uq_blog_posts_slug"),
    )


def downgrade() -> None:
    for table_name in (
        "blog_posts",
        "journal_theses",
        "journal_positions",
        "journal_entry_plans",
        "trades",
        "journal_snapshots",
        "journals",
        "watchlist_items",
        "holding_targets",
        "holdings",
        "portfolios",
        "stocks",
    ):
        op.drop_table(table_name)
