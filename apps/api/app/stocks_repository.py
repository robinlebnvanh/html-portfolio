"""SQLAlchemy queries for the stocks API."""

from __future__ import annotations

from datetime import date
from typing import Any, Mapping

from sqlalchemy import delete, insert, select, update
from sqlalchemy.orm import Session

from app.sqlalchemy_tables import (
    holding_targets,
    holdings,
    journal_entry_plans,
    journal_positions,
    journal_snapshots,
    journal_theses,
    journals,
    portfolios,
    stocks,
    trades,
    watchlist_items,
)


def _as_dict(row: Mapping[str, Any]) -> dict[str, Any]:
    return dict(row)


def _touch_portfolio(session: Session) -> None:
    """Update the portfolio timestamp using database-independent Python data."""

    session.execute(
        update(portfolios)
        .where(portfolios.c.id == 1)
        .values(updated_at=date.today().isoformat())
    )


def _holding_from_row(
    session: Session,
    row: Mapping[str, Any],
    *,
    include_id: bool = False,
) -> dict[str, Any]:
    holding = _as_dict(row)
    holding["targets"] = list(
        session.scalars(
            select(holding_targets.c.price)
            .where(holding_targets.c.holding_id == row["id"])
            .order_by(holding_targets.c.target_order)
        ).all()
    )
    if not include_id:
        holding.pop("id", None)
    return holding


def get_holding(
    session: Session,
    holding_id: int,
    *,
    include_id: bool = True,
) -> dict[str, Any] | None:
    row = session.execute(
        select(
            holdings.c.id,
            holdings.c.ticker,
            holdings.c.quantity,
            holdings.c.avg_cost,
            holdings.c.entry_date,
            holdings.c.stop_loss,
            holdings.c.status,
            holdings.c.note,
        ).where(holdings.c.id == holding_id)
    ).mappings().first()
    return _holding_from_row(session, row, include_id=include_id) if row else None


def holding_exists(session: Session, ticker: str) -> bool:
    """Return whether a holding ticker already exists."""

    return session.scalar(
        select(holdings.c.id).where(holdings.c.ticker == ticker)
    ) is not None


def create_holding(
    session: Session,
    holding: dict[str, Any],
) -> dict[str, Any]:
    try:
        if session.scalar(select(stocks.c.ticker).where(stocks.c.ticker == holding["ticker"])) is None:
            session.execute(insert(stocks).values(ticker=holding["ticker"]))

        result = session.execute(
            insert(holdings).values(
                portfolio_id=1,
                ticker=holding["ticker"],
                quantity=holding["quantity"],
                avg_cost=holding["avg_cost"],
                entry_date=holding["entry_date"],
                stop_loss=holding["stop_loss"],
                status=holding["status"],
                note=holding["note"],
            )
        )
        holding_id = result.inserted_primary_key[0]
        targets = [
            {"holding_id": holding_id, "target_order": order, "price": target}
            for order, target in enumerate(holding["targets"], start=1)
        ]
        if targets:
            session.execute(insert(holding_targets), targets)
        _touch_portfolio(session)
        session.commit()
    except Exception:
        session.rollback()
        raise

    result = get_holding(session, holding_id)
    assert result is not None
    return result


def update_holding(
    session: Session,
    holding_id: int,
    changes: dict[str, Any],
) -> dict[str, Any] | None:
    existing = get_holding(session, holding_id)
    if existing is None:
        return None

    values = dict(changes)
    targets = values.pop("targets", None)
    try:
        if values:
            session.execute(
                update(holdings)
                .where(holdings.c.id == holding_id)
                .values(**values)
            )
        if targets is not None:
            session.execute(
                delete(holding_targets).where(holding_targets.c.holding_id == holding_id)
            )
            replacement_targets = [
                {"holding_id": holding_id, "target_order": order, "price": target}
                for order, target in enumerate(targets, start=1)
            ]
            if replacement_targets:
                session.execute(insert(holding_targets), replacement_targets)
        _touch_portfolio(session)
        session.commit()
    except Exception:
        session.rollback()
        raise

    return get_holding(session, holding_id)


def delete_holding(session: Session, holding_id: int) -> bool:
    try:
        result = session.execute(delete(holdings).where(holdings.c.id == holding_id))
        if result.rowcount:
            _touch_portfolio(session)
            session.commit()
            return True
        session.rollback()
        return False
    except Exception:
        session.rollback()
        raise


def get_portfolio(session: Session) -> dict[str, Any]:
    portfolio = session.execute(
        select(portfolios.c.updated_at, portfolios.c.note).where(portfolios.c.id == 1)
    ).mappings().first()

    if portfolio is None:
        return {"updated": None, "holdings": [], "watchlist": [], "summary": {}}

    holding_rows = session.execute(
        select(
            holdings.c.id,
            holdings.c.ticker,
            holdings.c.quantity,
            holdings.c.avg_cost,
            holdings.c.entry_date,
            holdings.c.stop_loss,
            holdings.c.status,
            holdings.c.note,
        )
        .where(holdings.c.portfolio_id == 1)
        .order_by(holdings.c.id)
    ).mappings().all()
    holdings_data = [
        _holding_from_row(session, row, include_id=True) for row in holding_rows
    ]
    watchlist = list(
        session.scalars(
            select(watchlist_items.c.ticker)
            .where(watchlist_items.c.portfolio_id == 1)
            .order_by(watchlist_items.c.ticker)
        ).all()
    )
    total_invested = sum(
        item["quantity"] * item["avg_cost"] for item in holdings_data
    )

    return {
        "updated": portfolio["updated_at"],
        "holdings": holdings_data,
        "watchlist": watchlist,
        "summary": {
            "total_invested": total_invested,
            "positions": len(holdings_data),
            "note": portfolio["note"],
        },
    }


def get_journals(session: Session) -> dict[str, Any]:
    journals_data: dict[str, Any] = {}
    journal_rows = session.execute(
        select(journals.c.ticker, journals.c.buffett).order_by(journals.c.ticker)
    ).mappings().all()

    for journal in journal_rows:
        ticker = journal["ticker"]
        snapshots = [
            _as_dict(row)
            for row in session.execute(
                select(
                    journal_snapshots.c.snapshot_date.label("date"),
                    journal_snapshots.c.price,
                    journal_snapshots.c.change_percent,
                    journal_snapshots.c.rsi,
                    journal_snapshots.c.macd,
                    journal_snapshots.c.score,
                    journal_snapshots.c.recommendation,
                    journal_snapshots.c.note,
                )
                .where(journal_snapshots.c.ticker == ticker)
                .order_by(journal_snapshots.c.snapshot_date)
            ).mappings().all()
        ]
        trades_data = [
            _as_dict(row)
            for row in session.execute(
                select(
                    trades.c.trade_date.label("date"),
                    trades.c.trade_type.label("type"),
                    trades.c.price,
                    trades.c.stop_loss,
                    trades.c.pnl,
                    trades.c.note,
                )
                .where(trades.c.ticker == ticker)
                .order_by(trades.c.id)
            ).mappings().all()
        ]
        entry_plan = [
            _as_dict(row)
            for row in session.execute(
                select(
                    journal_entry_plans.c.condition,
                    journal_entry_plans.c.entry_text,
                    journal_entry_plans.c.stop_loss_action,
                    journal_entry_plans.c.target_text,
                )
                .where(journal_entry_plans.c.ticker == ticker)
                .order_by(journal_entry_plans.c.plan_order)
            ).mappings().all()
        ]
        position_row = session.execute(
            select(
                journal_positions.c.status,
                journal_positions.c.quantity,
                journal_positions.c.avg_cost,
                journal_positions.c.entry_date,
                journal_positions.c.invested_amount,
            ).where(journal_positions.c.ticker == ticker)
        ).mappings().first()
        position = _as_dict(position_row) if position_row else None

        theses = {"bull": [], "bear": []}
        thesis_rows = session.execute(
            select(journal_theses.c.side, journal_theses.c.content)
            .where(journal_theses.c.ticker == ticker)
            .order_by(journal_theses.c.side, journal_theses.c.item_order)
        ).mappings().all()
        for row in thesis_rows:
            theses[row["side"]].append(row["content"])

        journals_data[ticker] = {
            "ticker": ticker,
            "snapshots": snapshots,
            "trades": trades_data,
            "entry_plan": entry_plan,
            "position": position,
            "buffett": journal["buffett"],
            "bull": theses["bull"],
            "bear": theses["bear"],
        }

    return journals_data
