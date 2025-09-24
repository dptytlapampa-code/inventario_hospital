"""Add equipo adjuntos table and serial flag"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

# revision identifiers, used by Alembic.
revision = "bd8b7d50f9ac"
down_revision = "8a9f4ce0f1a7"
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    inspector = inspect(bind)

    if not inspector.has_table("equipos_adjuntos"):
        op.create_table(
            "equipos_adjuntos",
            sa.Column("id", sa.Integer, primary_key=True),
            sa.Column("equipo_id", sa.Integer, sa.ForeignKey("equipos.id"), nullable=False),
            sa.Column("filename", sa.String(255), nullable=False),
            sa.Column("filepath", sa.String(512), nullable=False),
            sa.Column("mime_type", sa.String(100)),
            sa.Column("file_size", sa.Integer),
            sa.Column("uploaded_by_id", sa.Integer, sa.ForeignKey("usuarios.id")),
            sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
        )
    else:
        columns = {column["name"] for column in inspector.get_columns("equipos_adjuntos")}
        if "file_size" not in columns:
            with op.batch_alter_table("equipos_adjuntos") as batch:
                batch.add_column(sa.Column("file_size", sa.Integer, nullable=True))

    equipo_columns = {column["name"] for column in inspector.get_columns("equipos")}
    added_column = False
    if "sin_numero_serie" not in equipo_columns:
        op.add_column(
            "equipos",
            sa.Column(
                "sin_numero_serie",
                sa.Boolean(),
                nullable=False,
                server_default=sa.false(),
            ),
        )
        added_column = True

    with op.batch_alter_table("equipos", recreate="always") as batch:
        batch.alter_column(
            "sin_numero_serie",
            existing_type=sa.Boolean(),
            server_default=None,
            existing_server_default=sa.false() if added_column else None,
        )


def downgrade():
    with op.batch_alter_table("equipos", recreate="always") as batch:
        batch.alter_column(
            "sin_numero_serie",
            existing_type=sa.Boolean(),
            server_default=sa.text("0"),
        )

    inspector = inspect(op.get_bind())
    columns = {column["name"] for column in inspector.get_columns("equipos_adjuntos")}
    if "file_size" in columns:
        with op.batch_alter_table("equipos_adjuntos") as batch:
            batch.drop_column("file_size")

    tables = inspector.get_table_names()
    if "equipos_adjuntos" in tables:
        op.drop_table("equipos_adjuntos")
