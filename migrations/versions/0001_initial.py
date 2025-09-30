"""Initial schema for Inventario Hospital."""
from __future__ import annotations

from alembic import op

from app import create_app
from app.models import *  # noqa: F401,F403 - populate SQLAlchemy metadata
from app.extensions import db

# revision identifiers, used by Alembic.
revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create all tables defined in the SQLAlchemy metadata."""

    bind = op.get_bind()
    app = create_app()
    with app.app_context():
        db.metadata.create_all(bind=bind, checkfirst=True)


def downgrade() -> None:
    """Drop all application tables."""

    bind = op.get_bind()
    app = create_app()
    with app.app_context():
        for table in reversed(db.metadata.sorted_tables):
            table.drop(bind=bind, checkfirst=True)
