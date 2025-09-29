"""Add fields for new equipment intake details."""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "2f1a4b2b1234"
down_revision = "c6be45c2d4ab"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "equipos",
        sa.Column("es_nuevo", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.add_column(
        "equipos",
        sa.Column("expediente", sa.String(length=120), nullable=True),
    )
    op.add_column(
        "equipos",
        sa.Column("anio_expediente", sa.Integer(), nullable=True),
    )
    op.add_column(
        "equipos",
        sa.Column("orden_compra", sa.String(length=120), nullable=True),
    )
    op.add_column(
        "equipos",
        sa.Column("tipo_adquisicion", sa.String(length=50), nullable=True),
    )
    op.execute("UPDATE equipos SET es_nuevo = FALSE WHERE es_nuevo IS NULL")
    op.alter_column("equipos", "es_nuevo", server_default=None)


def downgrade() -> None:
    op.drop_column("equipos", "tipo_adquisicion")
    op.drop_column("equipos", "orden_compra")
    op.drop_column("equipos", "anio_expediente")
    op.drop_column("equipos", "expediente")
    op.drop_column("equipos", "es_nuevo")
