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
    op.add_column("tipo_equipo", sa.Column("descripcion", sa.Text(), nullable=True))

    op.create_index(
        "ix_equipos_descripcion",
        "equipos",
        ["descripcion"],
        unique=False,
    )
    op.create_index(
        "ix_equipos_marca",
        "equipos",
        ["marca"],
        unique=False,
    )
    op.create_index(
        "ix_equipos_modelo",
        "equipos",
        ["modelo"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_equipos_modelo", table_name="equipos")
    op.drop_index("ix_equipos_marca", table_name="equipos")
    op.drop_index("ix_equipos_descripcion", table_name="equipos")
    op.drop_column("tipo_equipo", "descripcion")
