from __future__ import with_statement

from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

from config import Config

# Import models so Alembic's autogeneration can discover tables.
from app.models import Base  # noqa: F401 - imported for side effects
import app.models.acta  # noqa: F401
import app.models.adjunto  # noqa: F401
import app.models.auditoria  # noqa: F401
import app.models.docscan  # noqa: F401
import app.models.equipo  # noqa: F401
import app.models.hospital  # noqa: F401
import app.models.insumo  # noqa: F401
import app.models.licencia  # noqa: F401
import app.models.permisos  # noqa: F401
import app.models.rol  # noqa: F401
import app.models.usuario  # noqa: F401

from app.extensions import db

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:  # pragma: no cover - configuration hook
    fileConfig(config.config_file_name)

# Ensure Alembic knows which database URL to use when not provided via CLI.
if not config.get_main_option("sqlalchemy.url"):
    config.set_main_option("sqlalchemy.url", Config.SQLALCHEMY_DATABASE_URI)

# Bind Alembic to the metadata managed by Flask-SQLAlchemy.
target_metadata = db.Model.metadata


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
