"""Add locality and complexity level to hospitals."""
from alembic import op
from sqlalchemy import inspect
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "0006_hospital_localidad_complejidad"
down_revision = "0005_vlans"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)
    columns = {column["name"] for column in inspector.get_columns("hospitales")}

    if "localidad" not in columns:
        op.add_column("hospitales", sa.Column("localidad", sa.String(length=120), nullable=True))
        op.create_index("ix_hospitales_localidad", "hospitales", ["localidad"], unique=False)

    if "nivel_complejidad" not in columns:
        op.add_column("hospitales", sa.Column("nivel_complejidad", sa.Integer(), nullable=True))


def downgrade() -> None:
    op.drop_column("hospitales", "nivel_complejidad")
    op.drop_index("ix_hospitales_localidad", table_name="hospitales")
    op.drop_column("hospitales", "localidad")
