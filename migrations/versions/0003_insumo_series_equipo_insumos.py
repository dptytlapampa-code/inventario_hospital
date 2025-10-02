"""Add serialised insumo tracking and equipo association history."""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "0003_insumo_series_equipo_insumos"
down_revision = "0002_equipo_search_tipo_desc"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create tables to gestionar series de insumos y asociaciones."""

    op.drop_table("equipo_insumos")

    estado_enum = sa.Enum("libre", "asignado", "dado_baja", name="insumo_serie_estado")
    estado_enum.create(op.get_bind(), checkfirst=True)

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
    op.create_index("ix_insumo_series_nro_serie", "insumo_series", ["nro_serie"], unique=True)
    op.create_index("ix_insumo_series_equipo_id", "insumo_series", ["equipo_id"])

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


def downgrade() -> None:
    """Revert the creation of insumo series and association tables."""

    op.drop_index("ix_equipos_insumos_insumo_id", table_name="equipos_insumos")
    op.drop_index("ix_equipos_insumos_equipo_id", table_name="equipos_insumos")
    op.drop_table("equipos_insumos")

    op.drop_index("ix_insumo_series_equipo_id", table_name="insumo_series")
    op.drop_index("ix_insumo_series_nro_serie", table_name="insumo_series")
    op.drop_index("ix_insumo_series_insumo_id", table_name="insumo_series")
    op.drop_table("insumo_series")

    estado_enum = sa.Enum("libre", "asignado", "dado_baja", name="insumo_serie_estado")
    estado_enum.drop(op.get_bind(), checkfirst=True)

    op.create_table(
        "equipo_insumos",
        sa.Column("equipo_id", sa.Integer(), sa.ForeignKey("equipos.id"), primary_key=True),
        sa.Column("insumo_id", sa.Integer(), sa.ForeignKey("insumos.id"), primary_key=True),
    )
