"""SQLAlchemy queries for the stocks API."""

from __future__ import annotations

from datetime import date
import json
from typing import Any, Mapping

from sqlalchemy import delete, insert, or_, select, update
from sqlalchemy.orm import Session

from app.sqlalchemy_tables import (
    admin_audit_logs,
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

HOLDING_SYNC_NOTE = "[HOLDING_SYNC] Mirror trade for manual holding edits."
HOLDING_ADJUSTMENT_NOTE = "[HOLDING_ADJUSTMENT] Snapshot created from manual holding edit."


def _as_dict(row: Mapping[str, Any]) -> dict[str, Any]:
    return dict(row)


def _is_buy_trade(trade_type: str) -> bool:
    return trade_type.strip().upper() in {"BUY", "MUA"}


def _is_sell_trade(trade_type: str) -> bool:
    return trade_type.strip().upper() in {"SELL", "BAN", "BÁN"}


def _is_adjustment_trade(trade_type: str, note: str | None = None) -> bool:
    return trade_type.strip().upper() == "ADJUSTMENT" or note == HOLDING_SYNC_NOTE


def _record_audit(
    session: Session,
    *,
    actor: str,
    action: str,
    entity_type: str,
    entity_id: int | str | None = None,
    ticker: str | None = None,
    before: dict[str, Any] | None = None,
    after: dict[str, Any] | None = None,
) -> None:
    session.execute(
        insert(admin_audit_logs).values(
            actor=actor,
            action=action,
            entity_type=entity_type,
            entity_id=str(entity_id) if entity_id is not None else None,
            ticker=ticker,
            before_json=json.dumps(before, sort_keys=True) if before is not None else None,
            after_json=json.dumps(after, sort_keys=True) if after is not None else None,
        )
    )


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


def _get_holding_by_ticker(session: Session, ticker: str) -> dict[str, Any] | None:
    holding_id = session.scalar(select(holdings.c.id).where(holdings.c.ticker == ticker))
    return get_holding(session, holding_id) if holding_id is not None else None


def _replace_holding_targets(session: Session, holding_id: int, targets: list[int]) -> None:
    session.execute(delete(holding_targets).where(holding_targets.c.holding_id == holding_id))
    replacement_targets = [
        {"holding_id": holding_id, "target_order": order, "price": target}
        for order, target in enumerate(targets, start=1)
    ]
    if replacement_targets:
        session.execute(insert(holding_targets), replacement_targets)


def _create_holding_adjustment(session: Session, holding: dict[str, Any]) -> int:
    """Append a position snapshot so manual corrections remain auditable."""

    _ensure_journal(session, holding["ticker"])
    result = session.execute(
        insert(trades).values(
            ticker=holding["ticker"],
            trade_date=date.today().isoformat(),
            trade_type="ADJUSTMENT",
            quantity=holding["quantity"],
            price=holding["avg_cost"],
            stop_loss=holding["stop_loss"],
            pnl=None,
            note=HOLDING_ADJUSTMENT_NOTE,
        )
    )
    return int(result.inserted_primary_key[0])


def _sync_holding_from_trades(session: Session, ticker: str) -> None:
    trade_rows = session.execute(
        select(
            trades.c.trade_date.label("date"),
            trades.c.trade_type.label("type"),
            trades.c.quantity,
            trades.c.price,
            trades.c.stop_loss,
            trades.c.note,
        )
        .where(trades.c.ticker == ticker)
        .order_by(trades.c.trade_date, trades.c.id)
    ).mappings().all()

    existing = _get_holding_by_ticker(session, ticker)
    if not trade_rows:
        if existing is not None:
            session.execute(
                update(holdings)
                .where(holdings.c.id == existing["id"])
                .values(quantity=0, avg_cost=0, status="CLOSED")
            )
            _touch_portfolio(session)
        return

    quantity = 0
    cost_basis = 0
    first_entry_date: str | None = None
    latest_stop_loss: int | None = None

    for trade in trade_rows:
        trade_quantity = trade["quantity"] or 0
        if _is_adjustment_trade(trade["type"], trade["note"]):
            quantity = trade_quantity
            cost_basis = trade_quantity * trade["price"]
            if quantity and first_entry_date is None:
                first_entry_date = trade["date"]
            latest_stop_loss = trade["stop_loss"]
        elif trade_quantity <= 0:
            continue
        elif _is_buy_trade(trade["type"]):
            if quantity == 0:
                first_entry_date = trade["date"]
            cost_basis += trade_quantity * trade["price"]
            quantity += trade_quantity
        elif _is_sell_trade(trade["type"]):
            closed_quantity = trade_quantity
            average_cost = round(cost_basis / quantity) if quantity else 0
            quantity -= closed_quantity
            cost_basis = average_cost * quantity
            if quantity == 0:
                cost_basis = 0

        if trade["stop_loss"] is not None:
            latest_stop_loss = trade["stop_loss"]

    avg_cost = round(cost_basis / quantity) if quantity else 0
    status = "HOLDING" if quantity else "CLOSED"
    entry_date = first_entry_date or date.today().isoformat()
    note = existing["note"] if existing else "Synced from trades."
    targets = existing["targets"] if existing else []

    _ensure_portfolio(session)
    _ensure_stock(session, ticker)
    if existing is None:
        result = session.execute(
            insert(holdings).values(
                portfolio_id=1,
                ticker=ticker,
                quantity=quantity,
                avg_cost=avg_cost,
                entry_date=entry_date,
                stop_loss=latest_stop_loss,
                status=status,
                note=note,
            )
        )
        holding_id = result.inserted_primary_key[0]
    else:
        holding_id = existing["id"]
        session.execute(
            update(holdings)
            .where(holdings.c.id == holding_id)
            .values(
                quantity=quantity,
                avg_cost=avg_cost,
                entry_date=entry_date,
                stop_loss=latest_stop_loss,
                status=status,
                note=note,
            )
        )
    _replace_holding_targets(session, holding_id, targets)
    _touch_portfolio(session)


def _assert_trade_timeline_is_valid(session: Session, ticker: str) -> None:
    """Reject trade histories that would sell more shares than they hold."""

    quantity = 0
    rows = session.execute(
        select(trades.c.trade_type, trades.c.quantity, trades.c.note)
        .where(trades.c.ticker == ticker)
        .order_by(trades.c.trade_date, trades.c.id)
    ).mappings().all()
    for row in rows:
        trade_quantity = row["quantity"] or 0
        if _is_adjustment_trade(row["trade_type"], row["note"]):
            quantity = trade_quantity
        elif _is_buy_trade(row["trade_type"]):
            quantity += trade_quantity
        elif _is_sell_trade(row["trade_type"]):
            if trade_quantity > quantity:
                raise ValueError(
                    f"oversell blocked for {ticker}: attempting to sell {trade_quantity} with only {quantity} available"
                )
            quantity -= trade_quantity


def holding_exists(session: Session, ticker: str) -> bool:
    """Return whether a holding ticker already exists."""

    return session.scalar(
        select(holdings.c.id).where(holdings.c.ticker == ticker)
    ) is not None


def create_holding(
    session: Session,
    holding: dict[str, Any],
    *,
    actor: str = "system",
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
        adjustment_id = _create_holding_adjustment(session, holding)
        _sync_holding_from_trades(session, holding["ticker"])
        session.execute(
            update(holdings)
            .where(holdings.c.id == holding_id)
            .values(entry_date=holding["entry_date"], status=holding["status"], note=holding["note"])
        )
        _record_audit(
            session,
            actor=actor,
            action="create",
            entity_type="holding_adjustment",
            entity_id=adjustment_id,
            ticker=holding["ticker"],
            after=holding,
        )
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
    *,
    actor: str = "system",
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
            _replace_holding_targets(session, holding_id, targets)
        updated = get_holding(session, holding_id)
        if updated is not None and {"quantity", "avg_cost", "entry_date", "stop_loss"}.intersection(changes):
            adjustment_id = _create_holding_adjustment(session, updated)
            _sync_holding_from_trades(session, updated["ticker"])
            metadata_values = {
                key: values[key]
                for key in ("entry_date", "status", "note")
                if key in values
            }
            if metadata_values:
                session.execute(
                    update(holdings)
                    .where(holdings.c.id == holding_id)
                    .values(**metadata_values)
                )
            updated = get_holding(session, holding_id)
            _record_audit(
                session,
                actor=actor,
                action="adjust",
                entity_type="holding_adjustment",
                entity_id=adjustment_id,
                ticker=existing["ticker"],
                before=existing,
                after=updated,
            )
        else:
            _record_audit(
                session,
                actor=actor,
                action="update",
                entity_type="holding",
                entity_id=holding_id,
                ticker=existing["ticker"],
                before=existing,
                after=updated,
            )
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


def create_watchlist_item(
    session: Session,
    ticker: str,
    *,
    actor: str = "system",
) -> dict[str, str]:
    try:
        _ensure_portfolio(session)
        _ensure_stock(session, ticker)
        session.execute(insert(watchlist_items).values(portfolio_id=1, ticker=ticker))
        _record_audit(
            session,
            actor=actor,
            action="create",
            entity_type="watchlist_item",
            entity_id=ticker,
            ticker=ticker,
            after={"ticker": ticker},
        )
        _touch_portfolio(session)
        session.commit()
    except Exception:
        session.rollback()
        raise
    return {"ticker": ticker}


def delete_watchlist_item(session: Session, ticker: str, *, actor: str = "system") -> bool:
    try:
        result = session.execute(
            delete(watchlist_items).where(
                (watchlist_items.c.portfolio_id == 1) & (watchlist_items.c.ticker == ticker)
            )
        )
        if result.rowcount:
            _record_audit(
                session,
                actor=actor,
                action="delete",
                entity_type="watchlist_item",
                entity_id=ticker,
                ticker=ticker,
                before={"ticker": ticker},
            )
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
            trades.c.quantity,
            trades.c.price,
            trades.c.stop_loss,
            trades.c.pnl,
            trades.c.note,
        ).where(trades.c.id == trade_id)
    ).mappings().first()
    return _as_dict(row) if row else None


def create_trade(session: Session, trade: dict[str, Any], *, actor: str = "system") -> dict[str, Any]:
    try:
        _ensure_journal(session, trade["ticker"])
        result = session.execute(
            insert(trades).values(
                ticker=trade["ticker"],
                trade_date=trade["date"],
                trade_type=trade["type"],
                quantity=trade["quantity"],
                price=trade["price"],
                stop_loss=trade["stop_loss"],
                pnl=trade["pnl"],
                note=trade["note"],
            )
        )
        trade_id = result.inserted_primary_key[0]
        _assert_trade_timeline_is_valid(session, trade["ticker"])
        _sync_holding_from_trades(session, trade["ticker"])
        _record_audit(
            session,
            actor=actor,
            action="create",
            entity_type="trade",
            entity_id=trade_id,
            ticker=trade["ticker"],
            after=trade,
        )
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
    *,
    actor: str = "system",
) -> dict[str, Any] | None:
    existing = get_trade(session, trade_id)
    if existing is None:
        return None

    values = dict(changes)
    if "date" in values:
        values["trade_date"] = values.pop("date")
    if "type" in values:
        values["trade_type"] = values.pop("type")

    try:
        if values:
            session.execute(update(trades).where(trades.c.id == trade_id).values(**values))
        _assert_trade_timeline_is_valid(session, existing["ticker"])
        _sync_holding_from_trades(session, existing["ticker"])
        _record_audit(
            session,
            actor=actor,
            action="update",
            entity_type="trade",
            entity_id=trade_id,
            ticker=existing["ticker"],
            before=existing,
            after=get_trade(session, trade_id),
        )
        session.commit()
    except Exception:
        session.rollback()
        raise

    return get_trade(session, trade_id)


def delete_trade(session: Session, trade_id: int, *, actor: str = "system") -> bool:
    try:
        existing = get_trade(session, trade_id)
        if existing is None:
            session.rollback()
            return False
        result = session.execute(delete(trades).where(trades.c.id == trade_id))
        if result.rowcount:
            _assert_trade_timeline_is_valid(session, existing["ticker"])
            _sync_holding_from_trades(session, existing["ticker"])
            _record_audit(
                session,
                actor=actor,
                action="delete",
                entity_type="trade",
                entity_id=trade_id,
                ticker=existing["ticker"],
                before=existing,
            )
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
    *,
    actor: str = "system",
) -> dict[str, Any]:
    before = get_journals(session).get(ticker)
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

    result = get_journals(session).get(ticker, {"ticker": ticker})
    try:
        _record_audit(
            session,
            actor=actor,
            action="update" if before else "create",
            entity_type="journal",
            entity_id=ticker,
            ticker=ticker,
            before=before,
            after=result,
        )
        session.commit()
    except Exception:
        session.rollback()
        raise
    return result


def delete_journal(session: Session, ticker: str, *, actor: str = "system") -> bool:
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
        _record_audit(
            session,
            actor=actor,
            action="delete",
            entity_type="journal",
            entity_id=ticker,
            ticker=ticker,
            before={"ticker": ticker},
        )
        session.commit()
        return True
    except Exception:
        session.rollback()
        raise


def delete_holding(session: Session, holding_id: int, *, actor: str = "system") -> bool:
    try:
        existing = get_holding(session, holding_id)
        if existing is None:
            session.rollback()
            return False
        adjustment_id = _create_holding_adjustment(
            session,
            {**existing, "quantity": 0, "avg_cost": 0, "stop_loss": None},
        )
        _sync_holding_from_trades(session, existing["ticker"])
        if get_holding(session, holding_id) is not None:
            _record_audit(
                session,
                actor=actor,
                action="close",
                entity_type="holding_adjustment",
                entity_id=adjustment_id,
                ticker=existing["ticker"],
                before=existing,
                after=get_holding(session, holding_id),
            )
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


def get_stock_audit_logs(session: Session, limit: int = 100) -> list[dict[str, Any]]:
    """Return the newest immutable admin changes for the Stocks console."""

    rows = session.execute(
        select(
            admin_audit_logs.c.id,
            admin_audit_logs.c.actor,
            admin_audit_logs.c.action,
            admin_audit_logs.c.entity_type,
            admin_audit_logs.c.entity_id,
            admin_audit_logs.c.ticker,
            admin_audit_logs.c.before_json,
            admin_audit_logs.c.after_json,
            admin_audit_logs.c.created_at,
        )
        .order_by(admin_audit_logs.c.id.desc())
        .limit(limit)
    ).mappings().all()
    return [_as_dict(row) for row in rows]


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
                    trades.c.quantity,
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
