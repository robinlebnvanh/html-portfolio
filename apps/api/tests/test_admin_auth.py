"""Behavior tests for Admin Console email/password authentication."""

from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from sqlalchemy import select

from app.admin_auth import (
    authenticate_admin_user,
    create_access_token,
    create_admin_user,
    ensure_bootstrap_admin_user,
    hash_password,
    verify_access_token,
    verify_password,
)
from app.database import initialize_database
from app.sqlalchemy_database import get_engine, get_session, get_session_factory
from app.sqlalchemy_tables import admin_users


class AdminAuthTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        database_path = Path(self.temp_dir.name) / "auth.sqlite3"
        os.environ["PRJ008_DB_PATH"] = str(database_path)
        get_engine.cache_clear()
        get_session_factory.cache_clear()
        initialize_database()
        self.session = get_session()

    def tearDown(self) -> None:
        self.session.close()
        get_session_factory.cache_clear()
        get_engine.cache_clear()
        os.environ.pop("PRJ008_DB_PATH", None)
        self.temp_dir.cleanup()

    def test_password_hash_verification(self) -> None:
        password_hash = hash_password("correct-password")

        self.assertTrue(verify_password("correct-password", password_hash))
        self.assertFalse(verify_password("wrong-password", password_hash))
        self.assertNotIn("correct-password", password_hash)

    def test_admin_user_authentication(self) -> None:
        create_admin_user(self.session, "Admin@Example.com", "secret-password")

        user = authenticate_admin_user(
            self.session,
            "admin@example.com",
            "secret-password",
        )

        self.assertIsNotNone(user)
        self.assertEqual(user["email"], "admin@example.com")
        self.assertEqual(user["role"], "admin")
        self.assertIsNone(
            authenticate_admin_user(self.session, "admin@example.com", "wrong")
        )

    def test_bootstrap_admin_user_uses_environment_once(self) -> None:
        with patch.dict(
            "os.environ",
            {"ADMIN_EMAIL": "admin@example.com", "ADMIN_PASSWORD": "first-secret"},
        ):
            ensure_bootstrap_admin_user(self.session)

        row = self.session.execute(select(admin_users.c.email)).scalar_one()
        self.assertEqual(row, "admin@example.com")

        with patch.dict(
            "os.environ",
            {"ADMIN_EMAIL": "second@example.com", "ADMIN_PASSWORD": "second-secret"},
        ):
            ensure_bootstrap_admin_user(self.session)

        count = self.session.execute(select(admin_users.c.email)).all()
        self.assertEqual(len(count), 1)

    def test_signed_access_token_verification(self) -> None:
        user = {"id": 1, "email": "admin@example.com", "role": "admin"}

        with patch.dict("os.environ", {"ADMIN_AUTH_SECRET": "secret"}, clear=True):
            token = create_access_token(user, now=100)
            claims = verify_access_token(token, now=101)
            expired = verify_access_token(token, now=100 + 60 * 60 * 9)

        self.assertIsNotNone(claims)
        self.assertEqual(claims["email"], "admin@example.com")
        self.assertIsNone(expired)


if __name__ == "__main__":
    unittest.main()
