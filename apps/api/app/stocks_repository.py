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


def _ensure_portfolio(session: Session) -> None:
    if session.scalar(select(portfolios.c.id).where(portfolios.c.id == 1)) is None:
        session.execute(
            insert(portfolios).values(
                id=1,
                updated_at=date.today().isoformat(),
                note="Managed through the API",
            )
        )


def _ensure_stock(session: Session, ticker: str) -> None:
    if session.scalar(select(stocks.c.ticker).where(stocks.c.ticker == ticker)) is None:
        session.execute(insert(stocks).values(ticker=ticker))


def _ensure_journal(session: Session, ticker: str) -> None:
    _ensure_stock(session, ticker)
    if session.scalar(select(journals.c.ticker).where(journals.c.ticker == ticker)) is None:
        session.execute(
            insert(journals).values(
                ticker=ticker,
                buffett="",
                updated_at=date.today().isoformat(),
            )
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
        _ensure_portfolio(session)
        _ensure_stock(session, holding["ticker"])

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


def watchlist_exists(session: Session, ticker: str) -> bool:
    return session.scalar(
        select(watchlist_items.c.ticker).where(
            (watchlist_items.c.portfolio_id == 1) & (watchlist_items.c.ticker == ticker)
        )
    ) is not None


def create_watchlist_item(session: Session, ticker: str) -> dict[str, str]:
    try:
        _ensure_portfolio(session)
        _ensure_stock(session, ticker)
        session.execute(insert(watchlist_items).values(portfolio_id=1, ticker=ticker))
        _touch_portfolio(session)
        session.commit()
    except Exception:
        session.rollback()
        raise
    return {"ticker": ticker}


def delete_watchlist_item(session: Session, ticker: str) -> bool:
    try:
        result = session.execute(
            delete(watchlist_items).where(
                (watchlist_items.c.portfolio_id == 1) & (watchlist_items.c.ticker == ticker)
            )
        )
        if result.rowcount:
            _touch_portfolio(session)
            session.commit()
            return True
        session.rollback()
        return False
    except Exception:
        session.rollback()
        raise


def get_trade(session: Session, trade_id: int) -> dict[str, Any] | None:
    row = session.execute(
        select(
            trades.c.id,
            trades.c.ticker,
            trades.c.trade_date.label("date"),
            trades.c.trade_type.label("type"),
            trades.c.price,
            trades.c.stop_loss,
            trades.c.pnl,
            trades.c.note,
        ).where(trades.c.id == trade_id)
    ).mappings().first()
    return _as_dict(row) if row else None


def create_trade(session: Session, trade: dict[str, Any]) -> dict[str, Any]:
    try:
        _ensure_journal(session, trade["ticker"])
        result = session.execute(
            insert(trades).values(
                ticker=trade["ticker"],
                trade_date=trade["date"],
                trade_type=trade["type"],
                price=trade["price"],
                stop_loss=trade["stop_loss"],
                pnl=trade["pnl"],
                note=trade["note"],
            )
        )
        trade_id = result.inserted_primary_key[0]
        session.commit()
    except Exception:
        session.rollback()
        raise

    created = get_trade(session, trade_id)
    assert created is not None
    return created


def update_trade(
    session: Session,
    trade_id: int,
    changes: dict[str, Any],
) -> dict[str, Any] | None:
    if get_trade(session, trade_id) is None:
        return None

    values = dict(changes)
    if "date" in values:
        values["trade_date"] = values.pop("date")
    if "type" in values:
        values["trade_type"] = values.pop("type")

    try:
        if values:
            session.execute(update(trades).where(trades.c.id == trade_id).values(**values))
            session.commit()
    except Exception:
        session.rollback()
        raise

    return get_trade(session, trade_id)


def delete_trade(session: Session, trade_id: int) -> bool:
    try:
        result = session.execute(delete(trades).where(trades.c.id == trade_id))
        if result.rowcount:
            session.commit()
            return True
        session.rollback()
        return False
    except Exception:
        session.rollback()
        raise


def journal_exists(session: Session, ticker: str) -> bool:
    return session.scalar(select(journals.c.ticker).where(journals.c.ticker == ticker)) is not None


def upsert_journal(
    session: Session,
    ticker: str,
    changes: dict[str, Any],
) -> dict[str, Any]:
    try:
        _ensure_stock(session, ticker)
        exists = journal_exists(session, ticker)
        values: dict[str, Any] = {"updated_at": date.today().isoformat()}
        if "buffett" in changes:
            values["buffett"] = changes["buffett"]

        if exists:
            session.execute(update(journals).where(journals.c.ticker == ticker).values(**values))
        else:
            values.setdefault("buffett", "")
            session.execute(insert(journals).values(ticker=ticker, **values))

        for side in ("bull", "bear"):
            if side not in changes:
                continue
            session.execute(
                delete(journal_theses).where(
                    (journal_theses.c.ticker == ticker) & (journal_theses.c.side == side)
                )
            )
            thesis_rows = [
                {"ticker": ticker, "side": side, "item_order": order, "content": item}
                for order, item in enumerate(changes[side], start=1)
                if item.strip()
            ]
            if thesis_rows:
                session.execute(insert(journal_theses), thesis_rows)

        session.commit()
    except Exception:
        session.rollback()
        raise

    return get_journals(session).get(ticker, {"ticker": ticker})


def delete_journal(session: Session, ticker: str) -> bool:
    try:
        if not journal_exists(session, ticker):
            session.rollback()
            return False
        for table in (
            journal_snapshots,
            trades,
            journal_entry_plans,
            journal_positions,
            journal_theses,
        ):
            session.execute(delete(table).where(table.c.ticker == ticker))
        session.execute(delete(journals).where(journals.c.ticker == ticker))
        session.commit()
        return True
    except Exception:
        session.rollback()
        raise


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
                    trades.c.id,
                    trades.c.ticker,
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
