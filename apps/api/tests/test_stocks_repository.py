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
    delete_holding,
    get_holding,
    get_journals,
    get_portfolio,
    holding_exists,
    update_holding,
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
        self.assertEqual(result["ABC"]["entry_plan"][0]["condition"], "breakout")
        self.assertEqual(result["ABC"]["bull"], ["up"])
        self.assertEqual(result["ABC"]["bear"], ["down"])


if __name__ == "__main__":
    unittest.main()
