"""Add attachment metadata and lookup indexes"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "c6be45c2d4ab"
down_revision = "bd8b7d50f9ac"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("equipos_adjuntos", recreate="always") as batch_op:
        batch_op.add_column(sa.Column("file_size", sa.Integer(), nullable=True))

    op.create_index("ix_servicios_nombre", "servicios", ["nombre"], unique=False)
    op.create_index("ix_oficinas_nombre", "oficinas", ["nombre"], unique=False)
    op.create_index("ix_hospitales_direccion", "hospitales", ["direccion"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_hospitales_direccion", table_name="hospitales")
    op.drop_index("ix_oficinas_nombre", table_name="oficinas")
    op.drop_index("ix_servicios_nombre", table_name="servicios")

    with op.batch_alter_table("equipos_adjuntos", recreate="always") as batch_op:
        batch_op.drop_column("file_size")
