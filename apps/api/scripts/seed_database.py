"""Rebuild the local SQLite database from the stocks app JSON fixture."""

from __future__ import annotations

import json
import re
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any

from app.database import get_connection


API_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = API_ROOT.parents[1]
SOURCE_PATH = REPO_ROOT / "apps" / "stocks-app" / "data" / "data.json"
DROP_ORDER = [
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


def seed(connection: sqlite3.Connection, payload: dict[str, Any]) -> None:
    connection.execute("PRAGMA foreign_keys = ON")
    for table in DROP_ORDER:
        connection.execute(f"DROP TABLE IF EXISTS {table}")
    connection.executescript(
        (API_ROOT / "database" / "schema.sql").read_text(encoding="utf-8")
    )

    portfolio = payload["portfolio"]
    journals = payload["journals"]
    all_tickers = set(portfolio["watchlist"])
    all_tickers.update(item["ticker"] for item in portfolio["holdings"])
    all_tickers.update(journals.keys())

    connection.executemany(
        "INSERT INTO stocks (ticker) VALUES (?)",
        ((ticker,) for ticker in sorted(all_tickers)),
    )
    connection.execute(
        "INSERT INTO portfolios (id, updated_at, note) VALUES (1, ?, ?)",
        (parse_date(portfolio["updated"]), portfolio["summary"].get("note")),
    )

    for holding in portfolio["holdings"]:
        cursor = connection.execute(
            """
            INSERT INTO holdings
                (portfolio_id, ticker, quantity, avg_cost, entry_date,
                 stop_loss, status, note)
            VALUES (1, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                holding["ticker"], holding["quantity"], holding["avg_cost"],
                parse_date(holding["entry_date"]), holding["stop_loss"],
                holding["status"], holding.get("note"),
            ),
        )
        connection.executemany(
            "INSERT INTO holding_targets (holding_id, target_order, price) VALUES (?, ?, ?)",
            (
                (cursor.lastrowid, order, target)
                for order, target in enumerate(holding.get("targets", []), start=1)
            ),
        )

    connection.executemany(
        "INSERT INTO watchlist_items (portfolio_id, ticker) VALUES (1, ?)",
        ((ticker,) for ticker in portfolio["watchlist"]),
    )

    for ticker, journal in journals.items():
        connection.execute(
            "INSERT INTO journals (ticker, buffett) VALUES (?, ?)",
            (ticker, journal.get("buffett")),
        )
        connection.executemany(
            """
            INSERT INTO journal_snapshots
                (ticker, snapshot_date, price, change_percent, rsi, macd,
                 score, recommendation, note)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                (
                    ticker, parse_date(snapshot["date"]),
                    parse_integer(snapshot["price"]), parse_float(snapshot["chg"]),
                    parse_float(snapshot["rsi"]), snapshot.get("macd"),
                    snapshot.get("score"), snapshot.get("rec"), snapshot.get("note"),
                )
                for snapshot in journal.get("snapshots", [])
            ),
        )
        connection.executemany(
            """
            INSERT INTO trades
                (ticker, trade_date, trade_type, price, stop_loss, pnl, note)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                (
                    ticker, parse_date(trade["date"]), trade["type"],
                    parse_integer(trade["price"]), parse_integer(trade.get("sl")),
                    trade.get("pl"), trade.get("note"),
                )
                for trade in journal.get("trades", [])
            ),
        )
        connection.executemany(
            """
            INSERT INTO journal_entry_plans
                (ticker, plan_order, condition, entry_text, stop_loss_action, target_text)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                (
                    ticker, order, plan["cond"], plan.get("entry", ""),
                    plan.get("sl"), plan.get("target", ""),
                )
                for order, plan in enumerate(journal.get("entryPlan", []), start=1)
            ),
        )

        position = journal.get("position", {})
        connection.execute(
            """
            INSERT INTO journal_positions
                (ticker, status, quantity, avg_cost, entry_date, invested_amount)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                ticker, position.get("Trạng thái", ""),
                parse_integer(position.get("Số lượng")),
                parse_integer(position.get("Giá vốn")),
                parse_date(position.get("Ngày vào")),
                parse_integer(position.get("Vốn đầu tư")),
            ),
        )
        thesis_rows = []
        for side in ("bull", "bear"):
            thesis_rows.extend(
                (ticker, side, order, content)
                for order, content in enumerate(journal.get(side, []), start=1)
            )
        connection.executemany(
            "INSERT INTO journal_theses (ticker, side, item_order, content) VALUES (?, ?, ?, ?)",
            thesis_rows,
        )

    connection.commit()


def main() -> None:
    payload = json.loads(SOURCE_PATH.read_text(encoding="utf-8"))
    with get_connection() as connection:
        seed(connection, payload)
        counts = {
            table: connection.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
            for table in ("holdings", "watchlist_items", "journals", "trades")
        }
    print(f"Seeded {SOURCE_PATH}")
    print(f"Database: {API_ROOT / 'database' / 'prj008.sqlite3'}")
    print(f"Rows: {counts}")


if __name__ == "__main__":
    main()
