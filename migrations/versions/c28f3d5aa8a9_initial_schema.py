"""Initial database schema."""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "c28f3d5aa8a9"
down_revision = None
branch_labels = None
depends_on = None


# Enumerated types reused across multiple tables. Defining them once allows us
# to create and drop them explicitly during migrations which keeps PostgreSQL
# databases tidy when downgrading.
modulo_permiso_enum = sa.Enum(
    "inventario",
    "insumos",
    "actas",
    "adjuntos",
    "docscan",
    "reportes",
    "auditoria",
    "licencias",
    name="modulo_permiso",
)

tipo_equipo_enum = sa.Enum(
    "impresora",
    "router",
    "switch",
    "notebook",
    "cpu",
    "monitor",
    "access_point",
    "scanner",
    "proyector",
    "telefono_ip",
    "ups",
    "otro",
    name="tipo_equipo",
)

estado_equipo_enum = sa.Enum(
    "operativo",
    "servicio_tecnico",
    "de_baja",
    name="estado_equipo",
)

tipo_acta_enum = sa.Enum(
    "entrega",
    "prestamo",
    "transferencia",
    name="tipo_acta",
)

tipo_adjunto_enum = sa.Enum(
    "factura",
    "presupuesto",
    "acta",
    "planilla_patrimonial",
    "otro",
    name="tipo_adjunto",
)

tipo_docscan_enum = sa.Enum(
    "nota",
    "informe",
    "otro",
    name="tipo_docscan",
)

tipo_licencia_enum = sa.Enum(
    "temporal",
    "permanente",
    name="tipo_licencia",
)

estado_licencia_enum = sa.Enum(
    "borrador",
    "pendiente",
    "aprobada",
    "rechazada",
    name="estado_licencia",
)


def upgrade() -> None:
    modulo_permiso_enum.create(op.get_bind(), checkfirst=True)
    tipo_equipo_enum.create(op.get_bind(), checkfirst=True)
    estado_equipo_enum.create(op.get_bind(), checkfirst=True)
    tipo_acta_enum.create(op.get_bind(), checkfirst=True)
    tipo_adjunto_enum.create(op.get_bind(), checkfirst=True)
    tipo_docscan_enum.create(op.get_bind(), checkfirst=True)
    tipo_licencia_enum.create(op.get_bind(), checkfirst=True)
    estado_licencia_enum.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "hospitales",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("nombre", sa.String(length=100), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "roles",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("nombre", sa.String(length=50), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("nombre"),
    )

    op.create_table(
        "usuarios",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("nombre", sa.String(length=100), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("rol_id", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(["rol_id"], ["roles.id"], name="usuarios_rol_id_fkey"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email"),
    )

    op.create_table(
        "insumos",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("nombre", sa.String(length=100), nullable=False),
        sa.Column("numero_serie", sa.String(length=100), nullable=True),
        sa.Column("stock", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_insumos_numero_serie", "insumos", ["numero_serie"], unique=False)

    op.create_table(
        "equipos",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("tipo", tipo_equipo_enum, nullable=False),
        sa.Column(
            "estado",
            estado_equipo_enum,
            nullable=False,
            server_default=sa.text("'operativo'"),
        ),
        sa.Column("descripcion", sa.String(length=255), nullable=True),
        sa.Column("numero_serie", sa.String(length=100), nullable=True),
        sa.Column("hospital_id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["hospital_id"], ["hospitales.id"], name="equipos_hospital_id_fkey"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_equipos_hospital_id", "equipos", ["hospital_id"], unique=False)
    op.create_index("ix_equipos_numero_serie", "equipos", ["numero_serie"], unique=False)

    op.create_table(
        "actas",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("tipo", tipo_acta_enum, nullable=False),
        sa.Column("fecha", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("usuario_id", sa.Integer(), nullable=True),
        sa.Column("hospital_id", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(["hospital_id"], ["hospitales.id"], name="actas_hospital_id_fkey"),
        sa.ForeignKeyConstraint(["usuario_id"], ["usuarios.id"], name="actas_usuario_id_fkey"),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "adjuntos",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("equipo_id", sa.Integer(), nullable=False),
        sa.Column("filename", sa.String(length=255), nullable=False),
        sa.Column("tipo", tipo_adjunto_enum, nullable=False),
        sa.Column("uploaded_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["equipo_id"], ["equipos.id"], name="adjuntos_equipo_id_fkey"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_adjuntos_equipo_id", "adjuntos", ["equipo_id"], unique=False)

    op.create_table(
        "docscan",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("tipo", tipo_docscan_enum, nullable=False),
        sa.Column("filename", sa.String(length=255), nullable=False),
        sa.Column("uploaded_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("usuario_id", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(["usuario_id"], ["usuarios.id"], name="docscan_usuario_id_fkey"),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "permisos",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("rol_id", sa.Integer(), nullable=False),
        sa.Column("modulo", modulo_permiso_enum, nullable=False),
        sa.Column("hospital_id", sa.Integer(), nullable=True),
        sa.Column("can_read", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("can_write", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.ForeignKeyConstraint(["hospital_id"], ["hospitales.id"], name="permisos_hospital_id_fkey"),
        sa.ForeignKeyConstraint(["rol_id"], ["roles.id"], name="permisos_rol_id_fkey"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_permisos_hospital_id", "permisos", ["hospital_id"], unique=False)
    op.create_index("ix_permisos_rol_id", "permisos", ["rol_id"], unique=False)

    op.create_table(
        "licencias",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("usuario_id", sa.Integer(), nullable=False),
        sa.Column("hospital_id", sa.Integer(), nullable=True),
        sa.Column("tipo", tipo_licencia_enum, nullable=False),
        sa.Column("estado", estado_licencia_enum, nullable=False),
        sa.Column("requires_replacement", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["hospital_id"], ["hospitales.id"], name="licencias_hospital_id_fkey"),
        sa.ForeignKeyConstraint(["usuario_id"], ["usuarios.id"], name="licencias_usuario_id_fkey"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_licencias_hospital_id", "licencias", ["hospital_id"], unique=False)
    op.create_index("ix_licencias_usuario_id", "licencias", ["usuario_id"], unique=False)
    op.create_index(
        "ix_licencias_estado_tipo",
        "licencias",
        ["estado", "tipo"],
        unique=False,
    )

    op.create_table(
        "auditoria",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("usuario_id", sa.Integer(), nullable=True),
        sa.Column("accion", sa.String(length=100), nullable=False),
        sa.Column("tabla", sa.String(length=100), nullable=True),
        sa.Column("registro_id", sa.Integer(), nullable=True),
        sa.Column("fecha", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["usuario_id"], ["usuarios.id"], name="auditoria_usuario_id_fkey"),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "acta_items",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("acta_id", sa.Integer(), nullable=False),
        sa.Column("equipo_id", sa.Integer(), nullable=False),
        sa.Column("descripcion", sa.String(length=255), nullable=True),
        sa.ForeignKeyConstraint(["acta_id"], ["actas.id"], name="acta_items_acta_id_fkey"),
        sa.ForeignKeyConstraint(["equipo_id"], ["equipos.id"], name="acta_items_equipo_id_fkey"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_acta_items_acta_id", "acta_items", ["acta_id"], unique=False)
    op.create_index("ix_acta_items_equipo_id", "acta_items", ["equipo_id"], unique=False)

    op.create_table(
        "equipo_insumos",
        sa.Column("equipo_id", sa.Integer(), nullable=False),
        sa.Column("insumo_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["equipo_id"], ["equipos.id"], name="equipo_insumos_equipo_id_fkey"),
        sa.ForeignKeyConstraint(["insumo_id"], ["insumos.id"], name="equipo_insumos_insumo_id_fkey"),
        sa.PrimaryKeyConstraint("equipo_id", "insumo_id"),
    )


def downgrade() -> None:
    op.drop_table("equipo_insumos")
    op.drop_index("ix_acta_items_equipo_id", table_name="acta_items")
    op.drop_index("ix_acta_items_acta_id", table_name="acta_items")
    op.drop_table("acta_items")
    op.drop_table("auditoria")
    op.drop_index("ix_licencias_estado_tipo", table_name="licencias")
    op.drop_index("ix_licencias_usuario_id", table_name="licencias")
    op.drop_index("ix_licencias_hospital_id", table_name="licencias")
    op.drop_table("licencias")
    op.drop_index("ix_permisos_rol_id", table_name="permisos")
    op.drop_index("ix_permisos_hospital_id", table_name="permisos")
    op.drop_table("permisos")
    op.drop_table("docscan")
    op.drop_index("ix_adjuntos_equipo_id", table_name="adjuntos")
    op.drop_table("adjuntos")
    op.drop_table("actas")
    op.drop_index("ix_equipos_numero_serie", table_name="equipos")
    op.drop_index("ix_equipos_hospital_id", table_name="equipos")
    op.drop_table("equipos")
    op.drop_index("ix_insumos_numero_serie", table_name="insumos")
    op.drop_table("insumos")
    op.drop_table("usuarios")
    op.drop_table("roles")
    op.drop_table("hospitales")

    estado_licencia_enum.drop(op.get_bind(), checkfirst=True)
    tipo_licencia_enum.drop(op.get_bind(), checkfirst=True)
    tipo_docscan_enum.drop(op.get_bind(), checkfirst=True)
    tipo_adjunto_enum.drop(op.get_bind(), checkfirst=True)
    tipo_acta_enum.drop(op.get_bind(), checkfirst=True)
    estado_equipo_enum.drop(op.get_bind(), checkfirst=True)
    tipo_equipo_enum.drop(op.get_bind(), checkfirst=True)
    modulo_permiso_enum.drop(op.get_bind(), checkfirst=True)
