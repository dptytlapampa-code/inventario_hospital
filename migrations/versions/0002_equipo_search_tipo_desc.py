"""Add equipment search helpers and type description."""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "0002_equipo_search_tipo_desc"
down_revision = "0001_initial"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    existing_columns = {column["name"] for column in inspector.get_columns("tipo_equipo")}

    if "descripcion" not in existing_columns:
        op.add_column("tipo_equipo", sa.Column("descripcion", sa.Text(), nullable=True))

    existing_indexes = {index["name"] for index in inspector.get_indexes("equipos")}

    if "ix_equipos_descripcion" not in existing_indexes:
        op.create_index(
            "ix_equipos_descripcion",
            "equipos",
            ["descripcion"],
            unique=False,
        )
    if "ix_equipos_marca" not in existing_indexes:
        op.create_index(
            "ix_equipos_marca",
            "equipos",
            ["marca"],
            unique=False,
        )
    if "ix_equipos_modelo" not in existing_indexes:
        op.create_index(
            "ix_equipos_modelo",
            "equipos",
            ["modelo"],
            unique=False,
        )


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    existing_columns = {column["name"] for column in inspector.get_columns("tipo_equipo")}
    existing_indexes = {index["name"] for index in inspector.get_indexes("equipos")}

    if "ix_equipos_modelo" in existing_indexes:
        op.drop_index("ix_equipos_modelo", table_name="equipos")
    if "ix_equipos_marca" in existing_indexes:
        op.drop_index("ix_equipos_marca", table_name="equipos")
    if "ix_equipos_descripcion" in existing_indexes:
        op.drop_index("ix_equipos_descripcion", table_name="equipos")

    if "descripcion" in existing_columns:
        op.drop_column("tipo_equipo", "descripcion")
