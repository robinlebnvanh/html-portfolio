"""SQLAlchemy Core table definitions for the PRJ008 API data model.

These definitions describe the existing relational schema without changing the
current SQLite schema initializer. Core tables are used first because they map
cleanly to the current repository functions; ORM models can be introduced only
if the project later benefits from relationships and object mapping.
"""

from __future__ import annotations

import sqlalchemy as sa
from sqlalchemy import MetaData


metadata = MetaData()

stocks = sa.Table(
    "stocks",
    metadata,
    sa.Column("ticker", sa.String(length=12), primary_key=True),
    sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
)

portfolios = sa.Table(
    "portfolios",
    metadata,
    sa.Column("id", sa.Integer, primary_key=True),
    sa.Column("updated_at", sa.Text, nullable=False),
    sa.Column("note", sa.Text),
    sa.CheckConstraint("id = 1", name="ck_portfolios_singleton"),
)

holdings = sa.Table(
    "holdings",
    metadata,
    sa.Column("id", sa.Integer, primary_key=True),
    sa.Column("portfolio_id", sa.Integer, sa.ForeignKey("portfolios.id"), nullable=False),
    sa.Column("ticker", sa.String(length=12), sa.ForeignKey("stocks.ticker"), nullable=False),
    sa.Column("quantity", sa.Integer, nullable=False),
    sa.Column("avg_cost", sa.Integer, nullable=False),
    sa.Column("entry_date", sa.Text, nullable=False),
    sa.Column("stop_loss", sa.Integer),
    sa.Column("status", sa.String(length=40), nullable=False),
    sa.Column("note", sa.Text),
    sa.CheckConstraint("quantity >= 0", name="ck_holdings_quantity_nonnegative"),
    sa.CheckConstraint("avg_cost >= 0", name="ck_holdings_avg_cost_nonnegative"),
    sa.CheckConstraint("stop_loss IS NULL OR stop_loss >= 0", name="ck_holdings_stop_loss_nonnegative"),
    sa.UniqueConstraint("ticker", name="uq_holdings_ticker"),
)

holding_targets = sa.Table(
    "holding_targets",
    metadata,
    sa.Column("id", sa.Integer, primary_key=True),
    sa.Column("holding_id", sa.Integer, sa.ForeignKey("holdings.id", ondelete="CASCADE"), nullable=False),
    sa.Column("target_order", sa.Integer, nullable=False),
    sa.Column("price", sa.Integer, nullable=False),
    sa.CheckConstraint("target_order > 0", name="ck_holding_targets_order_positive"),
    sa.CheckConstraint("price >= 0", name="ck_holding_targets_price_nonnegative"),
    sa.UniqueConstraint("holding_id", "target_order", name="uq_holding_targets_order"),
)

watchlist_items = sa.Table(
    "watchlist_items",
    metadata,
    sa.Column("portfolio_id", sa.Integer, sa.ForeignKey("portfolios.id", ondelete="CASCADE"), nullable=False),
    sa.Column("ticker", sa.String(length=12), sa.ForeignKey("stocks.ticker"), nullable=False),
    sa.PrimaryKeyConstraint("portfolio_id", "ticker"),
)

journals = sa.Table(
    "journals",
    metadata,
    sa.Column("ticker", sa.String(length=12), sa.ForeignKey("stocks.ticker"), primary_key=True),
    sa.Column("buffett", sa.Text),
    sa.Column("updated_at", sa.Text),
)

journal_snapshots = sa.Table(
    "journal_snapshots",
    metadata,
    sa.Column("id", sa.Integer, primary_key=True),
    sa.Column("ticker", sa.String(length=12), sa.ForeignKey("journals.ticker", ondelete="CASCADE"), nullable=False),
    sa.Column("snapshot_date", sa.Text, nullable=False),
    sa.Column("price", sa.Integer, nullable=False),
    sa.Column("change_percent", sa.Float),
    sa.Column("rsi", sa.Float),
    sa.Column("macd", sa.Text),
    sa.Column("score", sa.Text),
    sa.Column("recommendation", sa.Text),
    sa.Column("note", sa.Text),
    sa.CheckConstraint("price >= 0", name="ck_journal_snapshots_price_nonnegative"),
    sa.CheckConstraint("rsi IS NULL OR (rsi >= 0 AND rsi <= 100)", name="ck_journal_snapshots_rsi_range"),
    sa.UniqueConstraint("ticker", "snapshot_date", name="uq_journal_snapshots_date"),
)

trades = sa.Table(
    "trades",
    metadata,
    sa.Column("id", sa.Integer, primary_key=True),
    sa.Column("ticker", sa.String(length=12), sa.ForeignKey("journals.ticker", ondelete="CASCADE"), nullable=False),
    sa.Column("trade_date", sa.Text, nullable=False),
    sa.Column("trade_type", sa.Text, nullable=False),
    sa.Column("price", sa.Integer, nullable=False),
    sa.Column("stop_loss", sa.Integer),
    sa.Column("pnl", sa.Text),
    sa.Column("note", sa.Text),
    sa.CheckConstraint("price >= 0", name="ck_trades_price_nonnegative"),
    sa.CheckConstraint("stop_loss IS NULL OR stop_loss >= 0", name="ck_trades_stop_loss_nonnegative"),
)

journal_entry_plans = sa.Table(
    "journal_entry_plans",
    metadata,
    sa.Column("id", sa.Integer, primary_key=True),
    sa.Column("ticker", sa.String(length=12), sa.ForeignKey("journals.ticker", ondelete="CASCADE"), nullable=False),
    sa.Column("plan_order", sa.Integer, nullable=False),
    sa.Column("condition", sa.Text, nullable=False),
    sa.Column("entry_text", sa.Text, nullable=False),
    sa.Column("stop_loss_action", sa.Text),
    sa.Column("target_text", sa.Text),
    sa.CheckConstraint("plan_order > 0", name="ck_journal_entry_plans_order_positive"),
    sa.UniqueConstraint("ticker", "plan_order", name="uq_journal_entry_plans_order"),
)

journal_positions = sa.Table(
    "journal_positions",
    metadata,
    sa.Column("ticker", sa.String(length=12), sa.ForeignKey("journals.ticker", ondelete="CASCADE"), primary_key=True),
    sa.Column("status", sa.Text, nullable=False),
    sa.Column("quantity", sa.Integer),
    sa.Column("avg_cost", sa.Integer),
    sa.Column("entry_date", sa.Text),
    sa.Column("invested_amount", sa.Integer),
    sa.CheckConstraint("quantity IS NULL OR quantity >= 0", name="ck_journal_positions_quantity_nonnegative"),
    sa.CheckConstraint("avg_cost IS NULL OR avg_cost >= 0", name="ck_journal_positions_avg_cost_nonnegative"),
    sa.CheckConstraint("invested_amount IS NULL OR invested_amount >= 0", name="ck_journal_positions_invested_nonnegative"),
)

journal_theses = sa.Table(
    "journal_theses",
    metadata,
    sa.Column("id", sa.Integer, primary_key=True),
    sa.Column("ticker", sa.String(length=12), sa.ForeignKey("journals.ticker", ondelete="CASCADE"), nullable=False),
    sa.Column("side", sa.Text, nullable=False),
    sa.Column("item_order", sa.Integer, nullable=False),
    sa.Column("content", sa.Text, nullable=False),
    sa.CheckConstraint("side IN ('bull', 'bear')", name="ck_journal_theses_side"),
    sa.CheckConstraint("item_order > 0", name="ck_journal_theses_order_positive"),
    sa.UniqueConstraint("ticker", "side", "item_order", name="uq_journal_theses_item"),
)

blog_posts = sa.Table(
    "blog_posts",
    metadata,
    sa.Column("id", sa.Integer, primary_key=True),
    sa.Column("slug", sa.String, nullable=False),
    sa.Column("title", sa.String, nullable=False),
    sa.Column("summary", sa.Text, nullable=False),
    sa.Column("content", sa.Text, nullable=False),
    sa.Column("category", sa.String, nullable=False),
    sa.Column("tags", sa.Text, nullable=False, server_default="[]"),
    sa.Column("status", sa.String, nullable=False),
    sa.Column("published_at", sa.String),
    sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
    sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
    sa.CheckConstraint("status IN ('draft', 'published')", name="ck_blog_posts_status"),
    sa.UniqueConstraint("slug", name="uq_blog_posts_slug"),
)
