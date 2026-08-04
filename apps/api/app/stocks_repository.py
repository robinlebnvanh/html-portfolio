"""SQLite queries for the stocks API."""

from __future__ import annotations

import sqlite3
from typing import Any


def _as_dict(row: sqlite3.Row) -> dict[str, Any]:
    return dict(row)


def _holding_from_row(
    connection: sqlite3.Connection,
    row: sqlite3.Row,
    *,
    include_id: bool = False,
) -> dict[str, Any]:
    holding = _as_dict(row)
    holding["targets"] = [
        target[0]
        for target in connection.execute(
            """
            SELECT price
            FROM holding_targets
            WHERE holding_id = ?
            ORDER BY target_order
            """,
            (row["id"],),
        ).fetchall()
    ]
    if not include_id:
        holding.pop("id", None)
    return holding


def get_holding(
    connection: sqlite3.Connection,
    holding_id: int,
    *,
    include_id: bool = True,
) -> dict[str, Any] | None:
    row = connection.execute(
        """
        SELECT id, ticker, quantity, avg_cost, entry_date, stop_loss, status, note
        FROM holdings
        WHERE id = ?
        """,
        (holding_id,),
    ).fetchone()
    return _holding_from_row(connection, row, include_id=include_id) if row else None


def create_holding(
    connection: sqlite3.Connection,
    holding: dict[str, Any],
) -> dict[str, Any]:
    connection.execute(
        "INSERT OR IGNORE INTO stocks (ticker) VALUES (?)",
        (holding["ticker"],),
    )
    cursor = connection.execute(
        """
        INSERT INTO holdings
            (portfolio_id, ticker, quantity, avg_cost, entry_date,
             stop_loss, status, note)
        VALUES (1, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            holding["ticker"], holding["quantity"], holding["avg_cost"],
            holding["entry_date"], holding["stop_loss"], holding["status"],
            holding["note"],
        ),
    )
    connection.executemany(
        "INSERT INTO holding_targets (holding_id, target_order, price) VALUES (?, ?, ?)",
        (
            (cursor.lastrowid, order, target)
            for order, target in enumerate(holding["targets"], start=1)
        ),
    )
    connection.execute(
        "UPDATE portfolios SET updated_at = date('now') WHERE id = 1"
    )
    result = get_holding(connection, cursor.lastrowid)
    assert result is not None
    return result


def update_holding(
    connection: sqlite3.Connection,
    holding_id: int,
    changes: dict[str, Any],
) -> dict[str, Any] | None:
    existing = get_holding(connection, holding_id)
    if existing is None:
        return None

    targets = changes.pop("targets", None)
    if changes:
        assignments = ", ".join(f"{column} = ?" for column in changes)
        connection.execute(
            f"UPDATE holdings SET {assignments} WHERE id = ?",
            (*changes.values(), holding_id),
        )
    if targets is not None:
        connection.execute(
            "DELETE FROM holding_targets WHERE holding_id = ?",
            (holding_id,),
        )
        connection.executemany(
            "INSERT INTO holding_targets (holding_id, target_order, price) VALUES (?, ?, ?)",
            ((holding_id, order, target) for order, target in enumerate(targets, start=1)),
        )
    connection.execute(
        "UPDATE portfolios SET updated_at = date('now') WHERE id = 1"
    )
    return get_holding(connection, holding_id)


def delete_holding(connection: sqlite3.Connection, holding_id: int) -> bool:
    cursor = connection.execute("DELETE FROM holdings WHERE id = ?", (holding_id,))
    if cursor.rowcount:
        connection.execute(
            "UPDATE portfolios SET updated_at = date('now') WHERE id = 1"
        )
    return cursor.rowcount > 0


def get_portfolio(connection: sqlite3.Connection) -> dict[str, Any]:
    portfolio = connection.execute(
        "SELECT updated_at, note FROM portfolios WHERE id = 1"
    ).fetchone()

    if portfolio is None:
        return {"updated": None, "holdings": [], "watchlist": [], "summary": {}}

    holdings: list[dict[str, Any]] = []
    holding_rows = connection.execute(
        """
        SELECT id, ticker, quantity, avg_cost, entry_date, stop_loss, status, note
        FROM holdings
        WHERE portfolio_id = 1
        ORDER BY id
        """
    ).fetchall()
    for row in holding_rows:
        # The stable database id is needed by the admin UI for PATCH/DELETE.
        holdings.append(_holding_from_row(connection, row, include_id=True))

    watchlist = [
        row[0]
        for row in connection.execute(
            """
            SELECT ticker
            FROM watchlist_items
            WHERE portfolio_id = 1
            ORDER BY ticker
            """
        ).fetchall()
    ]
    total_invested = sum(item["quantity"] * item["avg_cost"] for item in holdings)

    return {
        "updated": portfolio["updated_at"],
        "holdings": holdings,
        "watchlist": watchlist,
        "summary": {
            "total_invested": total_invested,
            "positions": len(holdings),
            "note": portfolio["note"],
        },
    }


def get_journals(connection: sqlite3.Connection) -> dict[str, Any]:
    journals: dict[str, Any] = {}
    journal_rows = connection.execute(
        "SELECT ticker, buffett FROM journals ORDER BY ticker"
    ).fetchall()

    for journal in journal_rows:
        ticker = journal["ticker"]
        snapshots = [
            _as_dict(row)
            for row in connection.execute(
                """
                SELECT snapshot_date AS date, price, change_percent, rsi, macd,
                       score, recommendation, note
                FROM journal_snapshots
                WHERE ticker = ?
                ORDER BY snapshot_date
                """,
                (ticker,),
            ).fetchall()
        ]
        trades = [
            _as_dict(row)
            for row in connection.execute(
                """
                SELECT trade_date AS date, trade_type AS type, price,
                       stop_loss, pnl, note
                FROM trades
                WHERE ticker = ?
                ORDER BY id
                """,
                (ticker,),
            ).fetchall()
        ]
        entry_plan = [
            _as_dict(row)
            for row in connection.execute(
                """
                SELECT condition, entry_text, stop_loss_action, target_text
                FROM journal_entry_plans
                WHERE ticker = ?
                ORDER BY plan_order
                """,
                (ticker,),
            ).fetchall()
        ]
        position_row = connection.execute(
            """
            SELECT status, quantity, avg_cost, entry_date, invested_amount
            FROM journal_positions
            WHERE ticker = ?
            """,
            (ticker,),
        ).fetchone()
        position = _as_dict(position_row) if position_row else None

        theses = {"bull": [], "bear": []}
        for row in connection.execute(
            """
            SELECT side, content
            FROM journal_theses
            WHERE ticker = ?
            ORDER BY side, item_order
            """,
            (ticker,),
        ).fetchall():
            theses[row["side"]].append(row["content"])

        journals[ticker] = {
            "ticker": ticker,
            "snapshots": snapshots,
            "trades": trades,
            "entry_plan": entry_plan,
            "position": position,
            "buffett": journal["buffett"],
            "bull": theses["bull"],
            "bear": theses["bear"],
        }

    return journals
