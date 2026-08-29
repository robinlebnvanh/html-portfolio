"""Behavior tests for the SQLAlchemy stocks repository."""

from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path

from sqlalchemy import insert, select

from app.database import initialize_database
from app.sqlalchemy_database import get_engine, get_session, get_session_factory
from app.sqlalchemy_tables import (
    journal_entry_plans,
    journal_positions,
    journal_snapshots,
    journal_theses,
    journals,
    holdings,
    portfolios,
    stocks,
    trades,
)
from app.stocks_repository import (
    create_holding,
    create_trade,
    create_watchlist_item,
    delete_journal,
    delete_holding,
    delete_trade,
    delete_watchlist_item,
    get_holding,
    get_journals,
    get_portfolio,
    holding_exists,
    upsert_journal,
    update_trade,
    update_holding,
    watchlist_exists,
)


class StocksRepositoryTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        database_path = Path(self.temp_dir.name) / "stocks.sqlite3"
        os.environ["PRJ008_DB_PATH"] = str(database_path)
        get_engine.cache_clear()
        get_session_factory.cache_clear()
        initialize_database()
        self.session = get_session()
        self.session.execute(
            insert(portfolios).values(id=1, updated_at="2026-08-05", note="test")
        )
        self.session.commit()

    def tearDown(self) -> None:
        self.session.close()
        get_session_factory.cache_clear()
        get_engine.cache_clear()
        os.environ.pop("PRJ008_DB_PATH", None)
        self.temp_dir.cleanup()

    def test_holding_crud_preserves_api_shape(self) -> None:
        payload = {
            "ticker": "ABC",
            "quantity": 10,
            "avg_cost": 100,
            "entry_date": "2026-08-05",
            "stop_loss": 90,
            "status": "HOLDING",
            "note": "test holding",
            "targets": [120, 140],
        }

        created = create_holding(self.session, payload)
        self.assertEqual(created["ticker"], "ABC")
        self.assertEqual(created["targets"], [120, 140])
        self.assertIn("id", created)
        self.assertTrue(holding_exists(self.session, "ABC"))

        portfolio = get_portfolio(self.session)
        self.assertEqual(portfolio["summary"]["total_invested"], 1000)
        self.assertEqual(portfolio["holdings"][0]["targets"], [120, 140])

        holding_row = self.session.scalar(
            select(holdings.c.id).where(holdings.c.ticker == "ABC")
        )
        self.assertIsNotNone(holding_row)

        updated = update_holding(
            self.session,
            holding_row,
            {"quantity": 12, "targets": [150]},
        )
        self.assertIsNotNone(updated)
        self.assertEqual(updated["quantity"], 12)
        self.assertEqual(updated["targets"], [150])

        self.assertTrue(delete_holding(self.session, holding_row))
        self.assertIsNone(get_holding(self.session, holding_row))
        self.assertEqual(get_portfolio(self.session)["holdings"], [])

    def test_journal_read_shape_is_preserved(self) -> None:
        self.session.execute(insert(stocks).values(ticker="ABC"))
        self.session.execute(
            insert(journals).values(ticker="ABC", buffett="test thesis")
        )
        self.session.execute(
            insert(journal_snapshots).values(
                ticker="ABC",
                snapshot_date="2026-08-05",
                price=100,
                change_percent=1.5,
                rsi=50,
                macd="positive",
                score="A",
                recommendation="BUY",
                note="test",
            )
        )
        self.session.execute(
            insert(trades).values(
                ticker="ABC",
                trade_date="2026-08-05",
                trade_type="BUY",
                quantity=10,
                price=100,
                stop_loss=90,
                pnl="0",
                note="test",
            )
        )
        self.session.execute(
            insert(journal_entry_plans).values(
                ticker="ABC",
                plan_order=1,
                condition="breakout",
                entry_text="buy",
                stop_loss_action="exit",
                target_text="120",
            )
        )
        self.session.execute(
            insert(journal_positions).values(
                ticker="ABC",
                status="HOLDING",
                quantity=10,
                avg_cost=100,
                entry_date="2026-08-05",
                invested_amount=1000,
            )
        )
        self.session.execute(
            insert(journal_theses),
            [
                {"ticker": "ABC", "side": "bull", "item_order": 1, "content": "up"},
                {"ticker": "ABC", "side": "bear", "item_order": 1, "content": "down"},
            ],
        )
        self.session.commit()

        result = get_journals(self.session)
        self.assertEqual(result["ABC"]["snapshots"][0]["date"], "2026-08-05")
        self.assertEqual(result["ABC"]["trades"][0]["type"], "BUY")
        self.assertEqual(result["ABC"]["trades"][0]["ticker"], "ABC")
        self.assertIn("id", result["ABC"]["trades"][0])
        self.assertEqual(result["ABC"]["entry_plan"][0]["condition"], "breakout")
        self.assertEqual(result["ABC"]["bull"], ["up"])
        self.assertEqual(result["ABC"]["bear"], ["down"])

    def test_watchlist_crud_updates_portfolio(self) -> None:
        created = create_watchlist_item(self.session, "ABC")

        self.assertEqual(created, {"ticker": "ABC"})
        self.assertTrue(watchlist_exists(self.session, "ABC"))
        self.assertEqual(get_portfolio(self.session)["watchlist"], ["ABC"])

        self.assertTrue(delete_watchlist_item(self.session, "ABC"))
        self.assertFalse(watchlist_exists(self.session, "ABC"))
        self.assertEqual(get_portfolio(self.session)["watchlist"], [])

    def test_trade_crud_creates_journal_when_missing(self) -> None:
        created = create_trade(
            self.session,
            {
                "ticker": "ABC",
                "date": "2026-08-27",
                "type": "BUY",
                "quantity": 10,
                "price": 100,
                "stop_loss": 90,
                "pnl": "0",
                "note": "test trade",
            },
        )

        self.assertEqual(created["ticker"], "ABC")
        self.assertEqual(created["type"], "BUY")
        self.assertEqual(created["quantity"], 10)
        self.assertIn("id", created)
        self.assertIn("ABC", get_journals(self.session))
        self.assertEqual(get_portfolio(self.session)["holdings"][0]["quantity"], 10)

        updated = update_trade(
            self.session,
            created["id"],
            {"price": 120, "type": "SELL", "quantity": 4, "note": "updated"},
        )
        self.assertIsNotNone(updated)
        self.assertEqual(updated["price"], 120)
        self.assertEqual(updated["type"], "SELL")
        self.assertEqual(updated["quantity"], 4)
        self.assertEqual(updated["note"], "updated")
        self.assertEqual(get_portfolio(self.session)["holdings"][0]["quantity"], 0)

        self.assertTrue(delete_trade(self.session, created["id"]))
        self.assertEqual(get_journals(self.session)["ABC"]["trades"], [])

    def test_trades_rebuild_holding_with_weighted_average_cost(self) -> None:
        first_buy = create_trade(
            self.session,
            {
                "ticker": "ABC",
                "date": "2026-08-27",
                "type": "MUA",
                "quantity": 10,
                "price": 100,
                "stop_loss": 90,
                "pnl": None,
                "note": "first buy",
            },
        )
        second_buy = create_trade(
            self.session,
            {
                "ticker": "ABC",
                "date": "2026-08-28",
                "type": "BUY",
                "quantity": 10,
                "price": 200,
                "stop_loss": 120,
                "pnl": None,
                "note": "second buy",
            },
        )

        holding = get_portfolio(self.session)["holdings"][0]
        self.assertEqual(holding["quantity"], 20)
        self.assertEqual(holding["avg_cost"], 150)
        self.assertEqual(holding["entry_date"], "2026-08-27")
        self.assertEqual(holding["stop_loss"], 120)

        update_trade(
            self.session,
            second_buy["id"],
            {"type": "BAN", "quantity": 5, "price": 220},
        )
        holding = get_portfolio(self.session)["holdings"][0]
        self.assertEqual(holding["quantity"], 5)
        self.assertEqual(holding["avg_cost"], 100)

        self.assertTrue(delete_trade(self.session, first_buy["id"]))
        holding = get_portfolio(self.session)["holdings"][0]
        self.assertEqual(holding["quantity"], 0)
        self.assertEqual(holding["status"], "CLOSED")

    def test_manual_holding_creates_sync_trade(self) -> None:
        created = create_holding(
            self.session,
            {
                "ticker": "ABC",
                "quantity": 8,
                "avg_cost": 125,
                "entry_date": "2026-08-27",
                "stop_loss": 100,
                "status": "HOLDING",
                "note": "manual holding",
                "targets": [],
            },
        )

        trades_data = get_journals(self.session)["ABC"]["trades"]
        self.assertEqual(len(trades_data), 1)
        self.assertEqual(trades_data[0]["quantity"], 8)
        self.assertEqual(trades_data[0]["price"], 125)

        update_holding(self.session, created["id"], {"quantity": 9, "avg_cost": 130})
        trades_data = get_journals(self.session)["ABC"]["trades"]
        self.assertEqual(trades_data[0]["quantity"], 9)
        self.assertEqual(trades_data[0]["price"], 130)

    def test_journal_upsert_and_delete(self) -> None:
        created = upsert_journal(
            self.session,
            "ABC",
            {
                "buffett": "Buffett check",
                "bull": ["strong cashflow", "clear catalyst"],
                "bear": ["valuation risk"],
            },
        )

        self.assertEqual(created["ticker"], "ABC")
        self.assertEqual(created["buffett"], "Buffett check")
        self.assertEqual(created["bull"], ["strong cashflow", "clear catalyst"])
        self.assertEqual(created["bear"], ["valuation risk"])

        updated = upsert_journal(
            self.session,
            "ABC",
            {"buffett": "Updated", "bull": ["new bull"]},
        )
        self.assertEqual(updated["buffett"], "Updated")
        self.assertEqual(updated["bull"], ["new bull"])
        self.assertEqual(updated["bear"], ["valuation risk"])

        self.assertTrue(delete_journal(self.session, "ABC"))
        self.assertNotIn("ABC", get_journals(self.session))


if __name__ == "__main__":
    unittest.main()
