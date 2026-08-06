"""Smoke tests for the new SQLAlchemy connection foundation."""

from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path

from sqlalchemy import text

from app import sqlalchemy_database


class SQLAlchemyDatabaseTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        database_path = Path(self.temp_dir.name) / "smoke.sqlite3"
        os.environ["DATABASE_URL"] = f"sqlite:///{database_path.as_posix()}"
        sqlalchemy_database.get_engine.cache_clear()
        sqlalchemy_database.get_session_factory.cache_clear()

    def tearDown(self) -> None:
        sqlalchemy_database.get_session_factory.cache_clear()
        sqlalchemy_database.get_engine.cache_clear()
        os.environ.pop("DATABASE_URL", None)
        self.temp_dir.cleanup()

    def test_database_url_and_session_can_execute_query(self) -> None:
        self.assertTrue(sqlalchemy_database.database_url().startswith("sqlite:///"))

        with sqlalchemy_database.get_session() as session:
            result = session.execute(text("SELECT 1")).scalar_one()

        self.assertEqual(result, 1)

    def test_postgresql_urls_are_normalized_to_psycopg_driver(self) -> None:
        os.environ["DATABASE_URL"] = "postgres://user:password@localhost:5432/prj008"
        self.assertEqual(
            sqlalchemy_database.database_url(),
            "postgresql+psycopg://user:password@localhost:5432/prj008",
        )


if __name__ == "__main__":
    unittest.main()
