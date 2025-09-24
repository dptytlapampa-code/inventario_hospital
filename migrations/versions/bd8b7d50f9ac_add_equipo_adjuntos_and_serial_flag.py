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


def _ensure_adjuntos_table(inspector) -> None:
    tables = inspector.get_table_names()
    if "equipos_adjuntos" not in tables:
        op.create_table(
            "equipos_adjuntos",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("equipo_id", sa.Integer(), sa.ForeignKey("equipos.id"), nullable=False),
            sa.Column("filename", sa.String(length=255), nullable=False),
            sa.Column("filepath", sa.String(length=512), nullable=False),
            sa.Column("mime_type", sa.String(length=120), nullable=False),
            sa.Column("file_size", sa.Integer(), nullable=True),
            sa.Column("uploaded_by_id", sa.Integer(), sa.ForeignKey("usuarios.id")),
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                server_default=sa.func.current_timestamp(),
                nullable=False,
            ),
        )
        op.create_index(
            "ix_equipos_adjuntos_equipo_id",
            "equipos_adjuntos",
            ["equipo_id"],
        )
        return

    columns = {column["name"] for column in inspector.get_columns("equipos_adjuntos")}
    if "file_size" not in columns:
        with op.batch_alter_table("equipos_adjuntos", schema=None) as batch:
            batch.add_column(sa.Column("file_size", sa.Integer(), nullable=True))

    indexes = {index["name"] for index in inspector.get_indexes("equipos_adjuntos")}
    if "ix_equipos_adjuntos_equipo_id" not in indexes:
        op.create_index(
            "ix_equipos_adjuntos_equipo_id",
            "equipos_adjuntos",
            ["equipo_id"],
        )


def upgrade():
    bind = op.get_bind()
    inspector = inspect(bind)

    columns = {column["name"] for column in inspector.get_columns("equipos")}
    added_column = False
    if "sin_numero_serie" not in columns:
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

    _ensure_adjuntos_table(inspector)

    if added_column or "sin_numero_serie" in columns:
        with op.batch_alter_table("equipos", recreate="always") as batch:
            batch.alter_column(
                "sin_numero_serie",
                existing_type=sa.Boolean(),
                server_default=None,
            )


def downgrade():
    bind = op.get_bind()
    inspector = inspect(bind)

    columns = {column["name"] for column in inspector.get_columns("equipos")}
    if "sin_numero_serie" in columns:
        with op.batch_alter_table("equipos", recreate="always") as batch:
            batch.drop_column("sin_numero_serie")

    columns = {column["name"] for column in inspector.get_columns("equipos_adjuntos")}
    if "file_size" in columns:
        with op.batch_alter_table("equipos_adjuntos", schema=None) as batch:
            batch.drop_column("file_size")

    indexes = {index["name"] for index in inspector.get_indexes("equipos_adjuntos")}
    if "ix_equipos_adjuntos_equipo_id" in indexes:
        op.drop_index("ix_equipos_adjuntos_equipo_id", table_name="equipos_adjuntos")

    tables = inspector.get_table_names()
    if "equipos_adjuntos" in tables:
        op.drop_table("equipos_adjuntos")
