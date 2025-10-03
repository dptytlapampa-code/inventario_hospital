"""Add serialised insumo tracking and equipo association history."""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.engine import Connection


# revision identifiers, used by Alembic.
revision = "0003_insumo_series_equipo_insumos"
down_revision = "0002_equipo_search_tipo_desc"
branch_labels = None
depends_on = None


def _table_exists(bind: Connection, table_name: str) -> bool:
    return sa.inspect(bind).has_table(table_name)


def _index_exists(bind: Connection, table_name: str, index_name: str) -> bool:
    if not _table_exists(bind, table_name):
        return False
    inspector = sa.inspect(bind)
    return index_name in {index["name"] for index in inspector.get_indexes(table_name)}


def _unique_exists(bind: Connection, table_name: str, constraint_name: str) -> bool:
    if not _table_exists(bind, table_name):
        return False
    inspector = sa.inspect(bind)
    return constraint_name in {
        constraint["name"] for constraint in inspector.get_unique_constraints(table_name)
    }


def upgrade() -> None:
    """Create tables to gestionar series de insumos y asociaciones."""

    bind = op.get_bind()

    if _table_exists(bind, "equipo_insumos"):
        op.drop_table("equipo_insumos")

    estado_enum = sa.Enum("libre", "asignado", "dado_baja", name="insumo_serie_estado")
    estado_enum.create(bind, checkfirst=True)

    if not _table_exists(bind, "insumo_series"):
        op.create_table(
            "insumo_series",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("insumo_id", sa.Integer(), sa.ForeignKey("insumos.id"), nullable=False),
            sa.Column("nro_serie", sa.String(length=128), nullable=False),
            sa.Column(
                "estado",
                estado_enum,
                nullable=False,
                server_default="libre",
            ),
            sa.Column("equipo_id", sa.Integer(), sa.ForeignKey("equipos.id"), nullable=True),
        )
    if not _index_exists(bind, "insumo_series", "ix_insumo_series_insumo_id"):
        op.create_index("ix_insumo_series_insumo_id", "insumo_series", ["insumo_id"])
    if not _index_exists(bind, "insumo_series", "ix_insumo_series_nro_serie"):
        op.create_index(
            "ix_insumo_series_nro_serie", "insumo_series", ["nro_serie"], unique=True
        )
    if not _index_exists(bind, "insumo_series", "ix_insumo_series_equipo_id"):
        op.create_index("ix_insumo_series_equipo_id", "insumo_series", ["equipo_id"])

    if not _table_exists(bind, "equipos_insumos"):
        op.create_table(
            "equipos_insumos",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("equipo_id", sa.Integer(), sa.ForeignKey("equipos.id"), nullable=False),
            sa.Column("insumo_id", sa.Integer(), sa.ForeignKey("insumos.id"), nullable=False),
            sa.Column(
                "insumo_serie_id",
                sa.Integer(),
                sa.ForeignKey("insumo_series.id"),
                nullable=False,
                unique=True,
            ),
            sa.Column("asociado_por_id", sa.Integer(), sa.ForeignKey("usuarios.id")),
            sa.Column(
                "fecha_asociacion",
                sa.DateTime(timezone=True),
                server_default=sa.func.now(),
                nullable=False,
            ),
            sa.Column("fecha_desasociacion", sa.DateTime(timezone=True)),
            sa.UniqueConstraint("equipo_id", "insumo_serie_id", name="uq_equipo_serie_unica"),
        )
    if not _index_exists(bind, "equipos_insumos", "ix_equipos_insumos_equipo_id"):
        op.create_index("ix_equipos_insumos_equipo_id", "equipos_insumos", ["equipo_id"])
    if not _index_exists(bind, "equipos_insumos", "ix_equipos_insumos_insumo_id"):
        op.create_index("ix_equipos_insumos_insumo_id", "equipos_insumos", ["insumo_id"])
    if not _unique_exists(bind, "equipos_insumos", "uq_equipo_serie_unica"):
        op.create_unique_constraint(
            "uq_equipo_serie_unica",
            "equipos_insumos",
            ["equipo_id", "insumo_serie_id"],
        )


def downgrade() -> None:
    """Revert the creation of insumo series and association tables."""

    bind = op.get_bind()

    if _index_exists(bind, "equipos_insumos", "ix_equipos_insumos_insumo_id"):
        op.drop_index("ix_equipos_insumos_insumo_id", table_name="equipos_insumos")
    if _index_exists(bind, "equipos_insumos", "ix_equipos_insumos_equipo_id"):
        op.drop_index("ix_equipos_insumos_equipo_id", table_name="equipos_insumos")
    if _unique_exists(bind, "equipos_insumos", "uq_equipo_serie_unica"):
        op.drop_constraint("uq_equipo_serie_unica", "equipos_insumos", type_="unique")
    if _table_exists(bind, "equipos_insumos"):
        op.drop_table("equipos_insumos")

    if _index_exists(bind, "insumo_series", "ix_insumo_series_equipo_id"):
        op.drop_index("ix_insumo_series_equipo_id", table_name="insumo_series")
    if _index_exists(bind, "insumo_series", "ix_insumo_series_nro_serie"):
        op.drop_index("ix_insumo_series_nro_serie", table_name="insumo_series")
    if _index_exists(bind, "insumo_series", "ix_insumo_series_insumo_id"):
        op.drop_index("ix_insumo_series_insumo_id", table_name="insumo_series")
    if _table_exists(bind, "insumo_series"):
        op.drop_table("insumo_series")

    estado_enum = sa.Enum("libre", "asignado", "dado_baja", name="insumo_serie_estado")
    estado_enum.drop(bind, checkfirst=True)

    if not _table_exists(bind, "equipo_insumos"):
        op.create_table(
            "equipo_insumos",
            sa.Column(
                "equipo_id", sa.Integer(), sa.ForeignKey("equipos.id"), primary_key=True
            ),
            sa.Column(
                "insumo_id", sa.Integer(), sa.ForeignKey("insumos.id"), primary_key=True
            ),
        )
