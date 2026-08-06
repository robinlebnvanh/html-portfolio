"""Rebuild portfolio data from the stocks app JSON fixture."""

from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any

from sqlalchemy import delete, func, insert, select
from sqlalchemy.orm import Session

from app.sqlalchemy_database import database_url, get_engine, get_session
from app.sqlalchemy_tables import (
    holding_targets,
    holdings,
    journal_entry_plans,
    journal_positions,
    journal_snapshots,
    journal_theses,
    journals,
    metadata,
    portfolios,
    stocks,
    trades,
    watchlist_items,
)


API_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = API_ROOT.parents[1]
SOURCE_PATH = REPO_ROOT / "apps" / "stocks-app" / "data" / "data.json"
DELETE_ORDER = [
    journal_theses,
    journal_positions,
    journal_entry_plans,
    trades,
    journal_snapshots,
    journals,
    watchlist_items,
    holding_targets,
    holdings,
    portfolios,
    stocks,
]


def parse_date(value: str | None) -> str | None:
    if not value or value in {"—", "-"}:
        return None
    for date_format in ("%Y-%m-%d", "%d/%m/%Y"):
        try:
            return datetime.strptime(value, date_format).date().isoformat()
        except ValueError:
            continue
    raise ValueError(f"Unsupported date format: {value}")


def parse_integer(value: Any) -> int | None:
    if value is None or value in {"", "—", "-"}:
        return None
    if isinstance(value, int):
        return value
    match = re.search(r"-?\d[\d,]*", str(value))
    return int(match.group(0).replace(",", "")) if match else None


def parse_float(value: Any) -> float | None:
    if value is None or value in {"", "—", "-"}:
        return None
    match = re.search(r"-?\d+(?:\.\d+)?", str(value))
    return float(match.group(0)) if match else None


def seed(session: Session, payload: dict[str, Any]) -> None:
    """Seed stocks data through SQLAlchemy while preserving blog posts."""
    metadata.create_all(bind=get_engine())
    try:
        for table in DELETE_ORDER:
            session.execute(delete(table))

        portfolio = payload["portfolio"]
        journals_payload = payload["journals"]
        all_tickers = set(portfolio["watchlist"])
        all_tickers.update(item["ticker"] for item in portfolio["holdings"])
        all_tickers.update(journals_payload.keys())

        session.execute(
            insert(stocks),
            [{"ticker": ticker} for ticker in sorted(all_tickers)],
        )
        session.execute(
            insert(portfolios).values(
                id=1,
                updated_at=parse_date(portfolio["updated"]),
                note=portfolio["summary"].get("note"),
            )
        )

        for holding in portfolio["holdings"]:
            result = session.execute(
                insert(holdings).values(
                    portfolio_id=1,
                    ticker=holding["ticker"],
                    quantity=holding["quantity"],
                    avg_cost=holding["avg_cost"],
                    entry_date=parse_date(holding["entry_date"]),
                    stop_loss=holding["stop_loss"],
                    status=holding["status"],
                    note=holding.get("note"),
                )
            )
            holding_id = result.inserted_primary_key[0]
            targets = [
                {"holding_id": holding_id, "target_order": order, "price": target}
                for order, target in enumerate(holding.get("targets", []), start=1)
            ]
            if targets:
                session.execute(insert(holding_targets), targets)

        session.execute(
            insert(watchlist_items),
            [
                {"portfolio_id": 1, "ticker": ticker}
                for ticker in portfolio["watchlist"]
            ],
        )

        for ticker, journal in journals_payload.items():
            session.execute(
                insert(journals).values(ticker=ticker, buffett=journal.get("buffett"))
            )
            snapshots = [
                {
                    "ticker": ticker,
                    "snapshot_date": parse_date(snapshot["date"]),
                    "price": parse_integer(snapshot["price"]),
                    "change_percent": parse_float(snapshot["chg"]),
                    "rsi": parse_float(snapshot["rsi"]),
                    "macd": snapshot.get("macd"),
                    "score": snapshot.get("score"),
                    "recommendation": snapshot.get("rec"),
                    "note": snapshot.get("note"),
                }
                for snapshot in journal.get("snapshots", [])
            ]
            if snapshots:
                session.execute(insert(journal_snapshots), snapshots)

            trades_data = [
                {
                    "ticker": ticker,
                    "trade_date": parse_date(trade["date"]),
                    "trade_type": trade["type"],
                    "price": parse_integer(trade["price"]),
                    "stop_loss": parse_integer(trade.get("sl")),
                    "pnl": trade.get("pl"),
                    "note": trade.get("note"),
                }
                for trade in journal.get("trades", [])
            ]
            if trades_data:
                session.execute(insert(trades), trades_data)

            entry_plans = [
                {
                    "ticker": ticker,
                    "plan_order": order,
                    "condition": plan["cond"],
                    "entry_text": plan.get("entry", ""),
                    "stop_loss_action": plan.get("sl"),
                    "target_text": plan.get("target", ""),
                }
                for order, plan in enumerate(journal.get("entryPlan", []), start=1)
            ]
            if entry_plans:
                session.execute(insert(journal_entry_plans), entry_plans)

            position = journal.get("position", {})
            session.execute(
                insert(journal_positions).values(
                    ticker=ticker,
                    status=position.get("Trạng thái", ""),
                    quantity=parse_integer(position.get("Số lượng")),
                    avg_cost=parse_integer(position.get("Giá vốn")),
                    entry_date=parse_date(position.get("Ngày vào")),
                    invested_amount=parse_integer(position.get("Vốn đầu tư")),
                )
            )

            thesis_rows = []
            for side in ("bull", "bear"):
                thesis_rows.extend(
                    {
                        "ticker": ticker,
                        "side": side,
                        "item_order": order,
                        "content": content,
                    }
                    for order, content in enumerate(journal.get(side, []), start=1)
                )
            if thesis_rows:
                session.execute(insert(journal_theses), thesis_rows)

        session.commit()
    except Exception:
        session.rollback()
        raise


def main() -> None:
    payload = json.loads(SOURCE_PATH.read_text(encoding="utf-8"))
    with get_session() as session:
        seed(session, payload)
        counts = {
            table.name: session.scalar(select(func.count()).select_from(table))
            for table in (holdings, watchlist_items, journals, trades)
        }
    print(f"Seeded {SOURCE_PATH}")
    print(f"Database URL: {database_url()}")
    print(f"Rows: {counts}")


if __name__ == "__main__":
    main()
