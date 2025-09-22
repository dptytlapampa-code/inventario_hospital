from __future__ import with_statement

from logging.config import fileConfig
import os
import sys
from pathlib import Path

from alembic import context
from sqlalchemy import engine_from_config, pool

# Ensure the application package is importable when Alembic runs from the
# ``migrations`` directory.
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:  # pragma: no cover - configuration hook
    sys.path.insert(0, str(PROJECT_ROOT))

from config import Config


# Import the SQLAlchemy models so the metadata includes every table defined in
# ``app.models``.  Alembic's autogenerate feature relies on this metadata to
# compare the declared schema with the actual database.
from app.models.base import Base

# Importing the modules registers their tables on ``Base.metadata``.
from app.models import (  # noqa: F401  - imported for side effects
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

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:  # pragma: no cover - configuration hook
    ini_path = Path(config.config_file_name)
    if ini_path.exists():
        fileConfig(config.config_file_name)

# Configure the SQLAlchemy URL from the environment (if provided) or fall back
# to the application's default database URI.
database_url = os.getenv("DATABASE_URL", Config.SQLALCHEMY_DATABASE_URI)
config.set_main_option("sqlalchemy.url", database_url)

# Use the project's declarative ``Base`` metadata for autogeneration support.
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(url=url, target_metadata=target_metadata, literal_binds=True)

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section),
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
