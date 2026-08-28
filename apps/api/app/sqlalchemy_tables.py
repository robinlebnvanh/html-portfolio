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

admin_users = sa.Table(
    "admin_users",
    metadata,
    sa.Column("id", sa.Integer, primary_key=True),
    sa.Column("email", sa.String, nullable=False),
    sa.Column("password_hash", sa.Text, nullable=False),
    sa.Column("role", sa.String, nullable=False, server_default="admin"),
    sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
    sa.Column("last_login_at", sa.DateTime(timezone=True)),
    sa.CheckConstraint("role IN ('admin')", name="ck_admin_users_role"),
    sa.UniqueConstraint("email", name="uq_admin_users_email"),
)

portfolio_content = sa.Table(
    "portfolio_content",
    metadata,
    sa.Column("id", sa.Integer, primary_key=True),
    sa.Column("hero_eyebrow", sa.String(length=120), nullable=False),
    sa.Column("hero_title", sa.String(length=220), nullable=False),
    sa.Column("hero_intro", sa.Text, nullable=False),
    sa.Column("hero_location", sa.String(length=120), nullable=False),
    sa.Column("hero_experience", sa.String(length=120), nullable=False),
    sa.Column("about_title", sa.String(length=220), nullable=False),
    sa.Column("about_body", sa.Text, nullable=False),
    sa.Column("github_url", sa.String(length=300), nullable=False),
    sa.Column("studio_title", sa.String(length=220), nullable=False),
    sa.Column("studio_intro", sa.Text, nullable=False),
    sa.Column("offers", sa.Text, nullable=False),
    sa.Column("contact_title", sa.String(length=220), nullable=False),
    sa.Column("contact_intro", sa.Text, nullable=False),
    sa.Column("contact_email", sa.String(length=254), nullable=False),
    sa.Column("skills", sa.Text, nullable=False),
    sa.Column("projects", sa.Text, nullable=False),
    sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
    sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
    sa.CheckConstraint("id = 1", name="ck_portfolio_content_singleton"),
)

service_leads = sa.Table(
    "service_leads",
    metadata,
    sa.Column("id", sa.Integer, primary_key=True),
    sa.Column("source", sa.String(length=80), nullable=False),
    sa.Column("channel", sa.String(length=40), nullable=False, server_default="form"),
    sa.Column("business_name", sa.String(length=160), nullable=False),
    sa.Column("customer_name", sa.String(length=160), nullable=False),
    sa.Column("email", sa.String(length=254)),
    sa.Column("phone", sa.String(length=40)),
    sa.Column("preferred_date", sa.String(length=20)),
    sa.Column("follow_up_at", sa.String(length=20)),
    sa.Column("package_name", sa.String(length=160), nullable=False),
    sa.Column("message", sa.Text, nullable=False),
    sa.Column("status", sa.String(length=30), nullable=False, server_default="new"),
    sa.Column("admin_note", sa.Text),
    sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
    sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
    sa.CheckConstraint(
        "status IN ('new', 'contacted', 'proposal_sent', 'booked', 'closed')",
        name="ck_service_leads_status",
    ),
)

service_lead_activities = sa.Table(
    "service_lead_activities",
    metadata,
    sa.Column("id", sa.Integer, primary_key=True),
    sa.Column("lead_id", sa.Integer, sa.ForeignKey("service_leads.id", ondelete="CASCADE"), nullable=False),
    sa.Column("activity_type", sa.String(length=40), nullable=False, server_default="note"),
    sa.Column("note", sa.Text, nullable=False),
    sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
)
