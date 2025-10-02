"""Alembic configuration for the project."""
from __future__ import annotations

import sys
from logging.config import fileConfig
from pathlib import Path
from typing import Any

from alembic import context
from sqlalchemy import engine_from_config, pool
from sqlalchemy.engine import Connection, URL

# Ensure the application package is importable when Alembic runs from the
# ``migrations`` directory.
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:  # pragma: no cover - configuration hook
    sys.path.insert(0, str(PROJECT_ROOT))

from config import Config
from app.models.base import Base
from app.models import (  # noqa: F401 - imported for side effects
    acta,
    adjunto,
    auditoria,
    docscan,
    equipo,
    hospital,
    insumo,
    licencia,
    permisos,
    rol,
    usuario,
)

config = context.config

if config.config_file_name is not None:  # pragma: no cover - configuration hook
    ini_path = Path(config.config_file_name)
    if ini_path.exists():
        fileConfig(config.config_file_name)


def _database_url() -> str:
    uri = Config.SQLALCHEMY_DATABASE_URI
    if uri.startswith("sqlite:///") and not uri.startswith("sqlite:////"):
        database_name = uri.split("sqlite:///", 1)[1]
        instance_path = PROJECT_ROOT / "instance"
        instance_path.mkdir(exist_ok=True)
        return f"sqlite:///{(instance_path / database_name).resolve()}"
    return uri


def _is_sqlite_url(url: str | URL) -> bool:
    if isinstance(url, URL):
        return url.get_backend_name() == "sqlite"
    return str(url).startswith("sqlite")


def _common_config_kwargs(is_sqlite: bool) -> dict[str, Any]:
    kwargs: dict[str, Any] = {
        "target_metadata": Base.metadata,
        "compare_type": True,
        "compare_server_default": True,
    }
    if is_sqlite:
        kwargs["render_as_batch"] = True
    return kwargs


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""

    url = _database_url()
    config.set_main_option("sqlalchemy.url", url)

    context.configure(
        url=url,
        literal_binds=True,
        **_common_config_kwargs(_is_sqlite_url(url)),
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""

    configuration = config.get_section(config.config_ini_section)
    assert configuration is not None
    configuration["sqlalchemy.url"] = _database_url()

    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:  # type: Connection
        context.configure(
            connection=connection,
            **_common_config_kwargs(connection.dialect.name == "sqlite"),
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
