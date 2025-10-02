"""Add serialised insumo tracking and equipo association history."""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "0003_insumo_series_equipo_insumos"
down_revision = "0002_equipo_search_tipo_desc"
branch_labels = None
depends_on = None


def _ensure_index(
    inspector: sa.engine.reflection.Inspector,
    table_name: str,
    index_name: str,
    columns: list[str],
    *,
    unique: bool = False,
) -> None:
    if index_name in {index["name"] for index in inspector.get_indexes(table_name)}:
        return
    op.create_index(index_name, table_name, columns, unique=unique)


def upgrade() -> None:
    """Create tables to gestionar series de insumos y asociaciones."""

    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if inspector.has_table("equipo_insumos"):
        op.drop_table("equipo_insumos")

    estado_enum = sa.Enum("libre", "asignado", "dado_baja", name="insumo_serie_estado")
    estado_enum.create(bind, checkfirst=True)

    if not inspector.has_table("insumo_series"):
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
        op.create_index("ix_insumo_series_insumo_id", "insumo_series", ["insumo_id"])
        op.create_index(
            "ix_insumo_series_nro_serie", "insumo_series", ["nro_serie"], unique=True
        )
        op.create_index("ix_insumo_series_equipo_id", "insumo_series", ["equipo_id"])
        inspector = sa.inspect(bind)
    else:
        _ensure_index(inspector, "insumo_series", "ix_insumo_series_insumo_id", ["insumo_id"])
        _ensure_index(
            inspector,
            "insumo_series",
            "ix_insumo_series_nro_serie",
            ["nro_serie"],
            unique=True,
        )
        _ensure_index(inspector, "insumo_series", "ix_insumo_series_equipo_id", ["equipo_id"])

    if not inspector.has_table("equipos_insumos"):
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
        op.create_index("ix_equipos_insumos_equipo_id", "equipos_insumos", ["equipo_id"])
        op.create_index("ix_equipos_insumos_insumo_id", "equipos_insumos", ["insumo_id"])
    else:
        inspector = sa.inspect(bind)
        _ensure_index(
            inspector, "equipos_insumos", "ix_equipos_insumos_equipo_id", ["equipo_id"]
        )
        _ensure_index(
            inspector, "equipos_insumos", "ix_equipos_insumos_insumo_id", ["insumo_id"]
        )
        if "uq_equipo_serie_unica" not in {
            constraint["name"]
            for constraint in inspector.get_unique_constraints("equipos_insumos")
        }:
            op.create_unique_constraint(
                "uq_equipo_serie_unica",
                "equipos_insumos",
                ["equipo_id", "insumo_serie_id"],
            )


def downgrade() -> None:
    """Revert the creation of insumo series and association tables."""

    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if inspector.has_table("equipos_insumos"):
        existing_indexes = {index["name"] for index in inspector.get_indexes("equipos_insumos")}
        if "ix_equipos_insumos_insumo_id" in existing_indexes:
            op.drop_index("ix_equipos_insumos_insumo_id", table_name="equipos_insumos")
        if "ix_equipos_insumos_equipo_id" in existing_indexes:
            op.drop_index("ix_equipos_insumos_equipo_id", table_name="equipos_insumos")
        unique_constraints = {
            constraint["name"]
            for constraint in inspector.get_unique_constraints("equipos_insumos")
        }
        if "uq_equipo_serie_unica" in unique_constraints:
            op.drop_constraint(
                "uq_equipo_serie_unica", "equipos_insumos", type_="unique"
            )
        op.drop_table("equipos_insumos")
        inspector = sa.inspect(bind)

    if inspector.has_table("insumo_series"):
        existing_indexes = {index["name"] for index in inspector.get_indexes("insumo_series")}
        if "ix_insumo_series_equipo_id" in existing_indexes:
            op.drop_index("ix_insumo_series_equipo_id", table_name="insumo_series")
        if "ix_insumo_series_nro_serie" in existing_indexes:
            op.drop_index("ix_insumo_series_nro_serie", table_name="insumo_series")
        if "ix_insumo_series_insumo_id" in existing_indexes:
            op.drop_index("ix_insumo_series_insumo_id", table_name="insumo_series")
        op.drop_table("insumo_series")

    estado_enum = sa.Enum("libre", "asignado", "dado_baja", name="insumo_serie_estado")
    estado_enum.drop(bind, checkfirst=True)

    inspector = sa.inspect(bind)
    if not inspector.has_table("equipo_insumos"):
        op.create_table(
            "equipo_insumos",
            sa.Column(
                "equipo_id", sa.Integer(), sa.ForeignKey("equipos.id"), primary_key=True
            ),
            sa.Column(
                "insumo_id", sa.Integer(), sa.ForeignKey("insumos.id"), primary_key=True
            ),
        )
