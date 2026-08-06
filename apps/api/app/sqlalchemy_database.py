"""SQLAlchemy connection foundation for SQLite and PostgreSQL."""

from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path

from sqlalchemy import create_engine, event, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker


API_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SQLITE_PATH = API_ROOT / "database" / "prj008.sqlite3"


def database_url() -> str:
    """Return the configured database URL."""

    configured_url = os.getenv("DATABASE_URL")
    if configured_url:
        if configured_url.startswith("postgres://"):
            return "postgresql+psycopg://" + configured_url.removeprefix("postgres://")
        if configured_url.startswith("postgresql://"):
            return "postgresql+psycopg://" + configured_url.removeprefix(
                "postgresql://"
            )
        return configured_url

    configured_path = os.getenv("PRJ008_DB_PATH")
    sqlite_path = Path(configured_path) if configured_path else DEFAULT_SQLITE_PATH
    return f"sqlite:///{sqlite_path.as_posix()}"


@lru_cache(maxsize=1)
def get_engine() -> Engine:
    """Create one lazy SQLAlchemy engine for the configured database."""

    url = database_url()
    connect_args = {"check_same_thread": False} if url.startswith("sqlite") else {}
    engine = create_engine(url, pool_pre_ping=True, connect_args=connect_args)
    if url.startswith("sqlite"):
        event.listen(engine, "connect", _enable_sqlite_foreign_keys)
    return engine


def _enable_sqlite_foreign_keys(dbapi_connection: object, _: object) -> None:
    """Enable SQLite foreign-key enforcement for SQLAlchemy connections."""

    cursor = dbapi_connection.cursor()
    try:
        cursor.execute("PRAGMA foreign_keys = ON")
    finally:
        cursor.close()


@lru_cache(maxsize=1)
def get_session_factory() -> sessionmaker[Session]:
    """Return the application session factory."""

    return sessionmaker(bind=get_engine(), autoflush=False, expire_on_commit=False)


def get_session() -> Session:
    """Open a SQLAlchemy session for one unit of work."""

    return get_session_factory()()


def ping_database() -> None:
    """Raise an exception if the configured database cannot answer a query."""

    with get_engine().connect() as connection:
        connection.execute(text("SELECT 1"))
