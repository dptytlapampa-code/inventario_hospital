"""Restructure licencias table with new workflow fields."""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

revision = "d2f6f3b4a1c9"
down_revision = "c6be45c2d4ab"
branch_labels = None
depends_on = None

OLD_TIPO_VALUES = ("temporal", "permanente", "especial")
OLD_ESTADO_VALUES = ("borrador", "pendiente", "aprobada", "rechazada", "cancelada")
NEW_TIPO_VALUES = ("vacaciones", "enfermedad", "estudio", "otro")
NEW_ESTADO_VALUES = ("solicitada", "aprobada", "rechazada", "cancelada")


def _enum_values_sql(values: tuple[str, ...]) -> str:
    ordered: list[str] = []
    seen: set[str] = set()
    for value in values:
        for candidate in (value, value.upper()):
            if candidate not in seen:
                ordered.append(candidate)
                seen.add(candidate)
    return ", ".join(f"'{value}'" for value in ordered)


def _enum_check(column: str, values: tuple[str, ...], name: str) -> sa.CheckConstraint:
    return sa.CheckConstraint(f"{column} IN ({_enum_values_sql(values)})", name=name)


def _drop_licencias_if_exists(inspector: inspect.Inspector) -> None:
    if "licencias" not in inspector.get_table_names():
        return
    indexes = {index["name"] for index in inspector.get_indexes("licencias")}
    if "ix_licencias_fecha_inicio_fecha_fin" in indexes:
        op.drop_index("ix_licencias_fecha_inicio_fecha_fin", table_name="licencias")
    if "ix_licencias_estado" in indexes:
        op.drop_index("ix_licencias_estado", table_name="licencias")
    if "ix_licencias_user_id" in indexes:
        op.drop_index("ix_licencias_user_id", table_name="licencias")
    op.drop_table("licencias")


def upgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)

    _drop_licencias_if_exists(inspector)

    op.create_table(
        "licencias",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("usuarios.id"), nullable=False),
        sa.Column("hospital_id", sa.Integer(), sa.ForeignKey("hospitales.id")),
        sa.Column("tipo", sa.String(length=50), nullable=False),
        sa.Column("fecha_inicio", sa.Date(), nullable=False),
        sa.Column("fecha_fin", sa.Date(), nullable=False),
        sa.Column("motivo", sa.Text(), nullable=False),
        sa.Column("estado", sa.String(length=50), nullable=False, server_default=sa.text("'solicitada'")),
        sa.Column("decidido_por", sa.Integer(), sa.ForeignKey("usuarios.id")),
        sa.Column("decidido_en", sa.DateTime(timezone=True)),
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
        _enum_check("tipo", NEW_TIPO_VALUES, "ck_licencias_tipo"),
        _enum_check("estado", NEW_ESTADO_VALUES, "ck_licencias_estado"),
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

    _drop_licencias_if_exists(inspector)

    op.create_table(
        "licencias",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("usuario_id", sa.Integer(), sa.ForeignKey("usuarios.id"), nullable=False),
        sa.Column("hospital_id", sa.Integer(), sa.ForeignKey("hospitales.id")),
        sa.Column("tipo", sa.String(length=50), nullable=False),
        sa.Column("estado", sa.String(length=50), nullable=False, server_default=sa.text("'borrador'")),
        sa.Column("fecha_inicio", sa.Date(), nullable=False),
        sa.Column("fecha_fin", sa.Date(), nullable=False),
        sa.Column("motivo", sa.Text(), nullable=False),
        sa.Column("comentario", sa.Text()),
        sa.Column("requires_replacement", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("reemplazo_id", sa.Integer(), sa.ForeignKey("usuarios.id")),
        sa.Column("aprobado_por_id", sa.Integer(), sa.ForeignKey("usuarios.id")),
        sa.Column("aprobado_en", sa.DateTime(timezone=True)),
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
        _enum_check("tipo", OLD_TIPO_VALUES, "ck_licencias_tipo"),
        _enum_check("estado", OLD_ESTADO_VALUES, "ck_licencias_estado"),
    )

    op.create_index("ix_licencias_estado_tipo", "licencias", ["estado", "tipo"], unique=False)
    op.create_index("ix_licencias_usuario_id", "licencias", ["usuario_id"], unique=False)
