"""SQLite connection and schema initialization for the PRJ008 API."""

from __future__ import annotations

import os
import sqlite3
from pathlib import Path


API_ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = API_ROOT / "database" / "schema.sql"
DEFAULT_DATABASE_PATH = API_ROOT / "database" / "prj008.sqlite3"


def database_path() -> Path:
    """Return the configured database path, defaulting to the local SQLite file."""
    configured_path = os.getenv("PRJ008_DB_PATH")
    return Path(configured_path) if configured_path else DEFAULT_DATABASE_PATH


def get_connection() -> sqlite3.Connection:
    """Open a SQLite connection with row access and foreign keys enabled."""
    path = database_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(path)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def initialize_database(connection: sqlite3.Connection | None = None) -> None:
    """Create the schema if it does not exist yet."""
    owns_connection = connection is None
    connection = connection or get_connection()
    try:
        connection.executescript(SCHEMA_PATH.read_text(encoding="utf-8"))
        connection.commit()
    finally:
        if owns_connection:
            connection.close()
