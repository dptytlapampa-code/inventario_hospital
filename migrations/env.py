"""Alembic environment integrating with the Flask application factory."""
from __future__ import annotations

import sys
from logging.config import fileConfig
from pathlib import Path

from alembic import context
from sqlalchemy import engine_from_config, pool

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app import create_app  # noqa: E402
from app.extensions import db  # noqa: E402

config = context.config

if config.config_file_name:
    ini_path = Path(config.config_file_name)
    if ini_path.is_file():
        fileConfig(config.config_file_name)

flask_app = create_app()
target_metadata = db.metadata


def _configure_context(**kwargs) -> None:
    context.configure(
        target_metadata=target_metadata,
        compare_type=True,
        compare_server_default=True,
        **kwargs,
    )


def run_migrations_offline() -> None:
    """Run migrations without creating a DB connection."""

    with flask_app.app_context():
        url = config.get_main_option("sqlalchemy.url") or str(db.engine.url)
        _configure_context(url=url, literal_binds=True)

        with context.begin_transaction():
            context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations with an active database connection."""

    with flask_app.app_context():
        section = config.get_section(config.config_ini_section)
        connectable = (
            engine_from_config(section, prefix="sqlalchemy.", poolclass=pool.NullPool)
            if section and config.get_main_option("sqlalchemy.url")
            else db.engine
        )

        with connectable.connect() as connection:
            _configure_context(connection=connection)

            with context.begin_transaction():
                context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
