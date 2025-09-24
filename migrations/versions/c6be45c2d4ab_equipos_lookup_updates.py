"""Add attachment metadata and lookup indexes"""
from __future__ import annotations

from alembic import op
from sqlalchemy import inspect

# revision identifiers, used by Alembic.
revision = "c6be45c2d4ab"
down_revision = "bd8b7d50f9ac"
branch_labels = None
depends_on = None


def upgrade() -> None:
    inspector = inspect(op.get_bind())

    existing_indexes = {index["name"] for index in inspector.get_indexes("servicios")}
    if "ix_servicios_nombre" not in existing_indexes:
        op.create_index("ix_servicios_nombre", "servicios", ["nombre"], unique=False)

    existing_indexes = {index["name"] for index in inspector.get_indexes("oficinas")}
    if "ix_oficinas_nombre" not in existing_indexes:
        op.create_index("ix_oficinas_nombre", "oficinas", ["nombre"], unique=False)

    existing_indexes = {index["name"] for index in inspector.get_indexes("hospitales")}
    if "ix_hospitales_direccion" not in existing_indexes:
        op.create_index("ix_hospitales_direccion", "hospitales", ["direccion"], unique=False)


def downgrade() -> None:
    inspector = inspect(op.get_bind())

    existing_indexes = {index["name"] for index in inspector.get_indexes("hospitales")}
    if "ix_hospitales_direccion" in existing_indexes:
        op.drop_index("ix_hospitales_direccion", table_name="hospitales")

    existing_indexes = {index["name"] for index in inspector.get_indexes("oficinas")}
    if "ix_oficinas_nombre" in existing_indexes:
        op.drop_index("ix_oficinas_nombre", table_name="oficinas")

    existing_indexes = {index["name"] for index in inspector.get_indexes("servicios")}
    if "ix_servicios_nombre" in existing_indexes:
        op.drop_index("ix_servicios_nombre", table_name="servicios")
