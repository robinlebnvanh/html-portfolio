"""Alembic environment for the incremental PRJ008 database migration."""

from __future__ import annotations

from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

from app.sqlalchemy_database import database_url


config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Models will be added in the repository migration task. The first migration
# is intentionally hand-written so SQLite and PostgreSQL receive the same
# explicit schema before ORM model generation is enabled.
target_metadata = None


def configured_url_for_alembic() -> str:
    """Return the runtime database URL for Alembic."""

    return database_url()


def run_migrations_offline() -> None:
    """Run migrations without opening a database connection."""

    context.configure(
        url=configured_url_for_alembic(),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations using the configured database connection."""

    configuration = config.get_section(config.config_ini_section, {})
    configuration["sqlalchemy.url"] = configured_url_for_alembic()
    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
