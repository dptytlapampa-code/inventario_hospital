"""Restructure licencias table with new workflow fields."""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

# revision identifiers, used by Alembic.
revision = "d2f6f3b4a1c9"
down_revision = "c6be45c2d4ab"
branch_labels = None
depends_on = None

old_tipo_enum = sa.Enum(
    "temporal",
    "permanente",
    "especial",
    name="tipo_licencia",
)

old_estado_enum = sa.Enum(
    "borrador",
    "pendiente",
    "aprobada",
    "rechazada",
    "cancelada",
    name="estado_licencia",
)

new_tipo_enum = sa.Enum(
    "vacaciones",
    "enfermedad",
    "estudio",
    "otro",
    name="tipo_licencia",
)

new_estado_enum = sa.Enum(
    "solicitada",
    "aprobada",
    "rechazada",
    "cancelada",
    name="estado_licencia",
)


def upgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)
    tables = inspector.get_table_names()

    if "licencias" in tables:
        op.drop_table("licencias")

    old_estado_enum.drop(bind, checkfirst=True)
    old_tipo_enum.drop(bind, checkfirst=True)

    new_tipo_enum.create(bind, checkfirst=True)
    new_estado_enum.create(bind, checkfirst=True)

    op.create_table(
        "licencias",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("usuarios.id"), nullable=False),
        sa.Column("hospital_id", sa.Integer(), sa.ForeignKey("hospitales.id"), nullable=True),
        sa.Column("tipo", new_tipo_enum, nullable=False),
        sa.Column("fecha_inicio", sa.Date(), nullable=False),
        sa.Column("fecha_fin", sa.Date(), nullable=False),
        sa.Column("motivo", sa.Text(), nullable=False),
        sa.Column(
            "estado",
            new_estado_enum,
            nullable=False,
            server_default=sa.text("'solicitada'"),
        ),
        sa.Column("decidido_por", sa.Integer(), sa.ForeignKey("usuarios.id"), nullable=True),
        sa.Column("decidido_en", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.current_timestamp(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.current_timestamp(),
            nullable=False,
        ),
    )

    op.create_index("ix_licencias_user_id", "licencias", ["user_id"], unique=False)
    op.create_index("ix_licencias_estado", "licencias", ["estado"], unique=False)
    op.create_index(
        "ix_licencias_fecha_inicio_fecha_fin",
        "licencias",
        ["fecha_inicio", "fecha_fin"],
        unique=False,
    )


def downgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)
    tables = inspector.get_table_names()

    if "licencias" in tables:
        indexes = {index["name"] for index in inspector.get_indexes("licencias")}
        if "ix_licencias_fecha_inicio_fecha_fin" in indexes:
            op.drop_index("ix_licencias_fecha_inicio_fecha_fin", table_name="licencias")
        if "ix_licencias_estado" in indexes:
            op.drop_index("ix_licencias_estado", table_name="licencias")
        if "ix_licencias_user_id" in indexes:
            op.drop_index("ix_licencias_user_id", table_name="licencias")

        op.drop_table("licencias")

    new_estado_enum.drop(bind, checkfirst=True)
    new_tipo_enum.drop(bind, checkfirst=True)

    old_tipo_enum.create(bind, checkfirst=True)
    old_estado_enum.create(bind, checkfirst=True)

    op.create_table(
        "licencias",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("usuario_id", sa.Integer(), nullable=False),
        sa.Column("hospital_id", sa.Integer(), nullable=True),
        sa.Column("tipo", old_tipo_enum, nullable=False),
        sa.Column(
            "estado",
            old_estado_enum,
            nullable=False,
            server_default=sa.text("'borrador'"),
        ),
        sa.Column("fecha_inicio", sa.Date(), nullable=False),
        sa.Column("fecha_fin", sa.Date(), nullable=False),
        sa.Column("motivo", sa.Text(), nullable=False),
        sa.Column("comentario", sa.Text(), nullable=True),
        sa.Column(
            "requires_replacement",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
        sa.Column("reemplazo_id", sa.Integer(), nullable=True),
        sa.Column("aprobado_por_id", sa.Integer(), nullable=True),
        sa.Column("aprobado_en", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.current_timestamp(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.current_timestamp(),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["usuario_id"], ["usuarios.id"], name="licencias_usuario_id_fkey"),
        sa.ForeignKeyConstraint(["hospital_id"], ["hospitales.id"], name="licencias_hospital_id_fkey"),
        sa.ForeignKeyConstraint(["reemplazo_id"], ["usuarios.id"], name="licencias_reemplazo_id_fkey"),
        sa.ForeignKeyConstraint(["aprobado_por_id"], ["usuarios.id"], name="licencias_aprobado_id_fkey"),
    )

    op.create_index("ix_licencias_estado_tipo", "licencias", ["estado", "tipo"], unique=False)
    op.create_index("ix_licencias_usuario_id", "licencias", ["usuario_id"], unique=False)
