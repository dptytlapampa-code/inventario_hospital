"""add equipo adjuntos table and serial flag"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "bd8b7d50f9ac"
down_revision = "8a9f4ce0f1a7"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "equipos",
        sa.Column("sin_numero_serie", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.create_table(
        "equipos_adjuntos",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("equipo_id", sa.Integer(), sa.ForeignKey("equipos.id"), nullable=False),
        sa.Column("filename", sa.String(length=255), nullable=False),
        sa.Column("filepath", sa.String(length=255), nullable=False),
        sa.Column("mime_type", sa.String(length=120), nullable=False),
        sa.Column("uploaded_by_id", sa.Integer(), sa.ForeignKey("usuarios.id")),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.current_timestamp(),
            nullable=False,
        ),
    )
    op.create_index("ix_equipos_adjuntos_equipo_id", "equipos_adjuntos", ["equipo_id"])
    op.alter_column("equipos", "sin_numero_serie", server_default=None)


def downgrade():
    op.drop_index("ix_equipos_adjuntos_equipo_id", table_name="equipos_adjuntos")
    op.drop_table("equipos_adjuntos")
    op.drop_column("equipos", "sin_numero_serie")
