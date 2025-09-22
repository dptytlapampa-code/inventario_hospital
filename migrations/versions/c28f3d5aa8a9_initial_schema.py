"""Initial schema.

Revision ID: c28f3d5aa8a9
Revises: 
Create Date: 2024-01-01 00:00:00
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "c28f3d5aa8a9"
down_revision = None
branch_labels = None
depends_on = None


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
    "prestado",
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
    "remito",
    "otro",
    name="tipo_adjunto",
)

tipo_docscan_enum = sa.Enum(
    "nota",
    "informe",
    "contrato",
    "otro",
    name="tipo_docscan",
)

tipo_licencia_enum = sa.Enum(
    "temporal",
    "permanente",
    "especial",
    name="tipo_licencia",
)

estado_licencia_enum = sa.Enum(
    "borrador",
    "pendiente",
    "aprobada",
    "rechazada",
    "cancelada",
    name="estado_licencia",
)

tipo_movimiento_enum = sa.Enum("ingreso", "egreso", name="tipo_movimiento")


def upgrade() -> None:
    modulo_permiso_enum.create(op.get_bind(), checkfirst=True)
    tipo_equipo_enum.create(op.get_bind(), checkfirst=True)
    estado_equipo_enum.create(op.get_bind(), checkfirst=True)
    tipo_acta_enum.create(op.get_bind(), checkfirst=True)
    tipo_adjunto_enum.create(op.get_bind(), checkfirst=True)
    tipo_docscan_enum.create(op.get_bind(), checkfirst=True)
    tipo_licencia_enum.create(op.get_bind(), checkfirst=True)
    estado_licencia_enum.create(op.get_bind(), checkfirst=True)
    tipo_movimiento_enum.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "hospitales",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("nombre", sa.String(length=120), nullable=False),
        sa.Column("codigo", sa.String(length=20), nullable=True),
        sa.Column("direccion", sa.String(length=255), nullable=True),
        sa.Column("telefono", sa.String(length=50), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("nombre"),
        sa.UniqueConstraint("codigo"),
    )

    op.create_table(
        "roles",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("nombre", sa.String(length=50), nullable=False),
        sa.Column("descripcion", sa.String(length=255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("nombre"),
    )

    op.create_table(
        "servicios",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("nombre", sa.String(length=120), nullable=False),
        sa.Column("descripcion", sa.String(length=255), nullable=True),
        sa.Column("hospital_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["hospital_id"], ["hospitales.id"], name="servicios_hospital_id_fkey"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("nombre", "hospital_id", name="uq_servicio_nombre_hospital"),
    )

    op.create_table(
        "oficinas",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("nombre", sa.String(length=120), nullable=False),
        sa.Column("piso", sa.String(length=20), nullable=True),
        sa.Column("servicio_id", sa.Integer(), nullable=False),
        sa.Column("hospital_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["servicio_id"], ["servicios.id"], name="oficinas_servicio_id_fkey"),
        sa.ForeignKeyConstraint(["hospital_id"], ["hospitales.id"], name="oficinas_hospital_id_fkey"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("nombre", "servicio_id", name="uq_oficina_nombre_servicio"),
    )

    op.create_table(
        "usuarios",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("username", sa.String(length=80), nullable=False),
        sa.Column("nombre", sa.String(length=120), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("telefono", sa.String(length=50), nullable=True),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("activo", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("rol_id", sa.Integer(), nullable=False),
        sa.Column("hospital_id", sa.Integer(), nullable=True),
        sa.Column("servicio_id", sa.Integer(), nullable=True),
        sa.Column("oficina_id", sa.Integer(), nullable=True),
        sa.Column("ultimo_login", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.ForeignKeyConstraint(["rol_id"], ["roles.id"], name="usuarios_rol_id_fkey"),
        sa.ForeignKeyConstraint(["hospital_id"], ["hospitales.id"], name="usuarios_hospital_id_fkey"),
        sa.ForeignKeyConstraint(["servicio_id"], ["servicios.id"], name="usuarios_servicio_id_fkey"),
        sa.ForeignKeyConstraint(["oficina_id"], ["oficinas.id"], name="usuarios_oficina_id_fkey"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email"),
        sa.UniqueConstraint("username"),
    )

    op.create_table(
        "permisos",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("rol_id", sa.Integer(), nullable=False),
        sa.Column("modulo", modulo_permiso_enum, nullable=False),
        sa.Column("hospital_id", sa.Integer(), nullable=True),
        sa.Column("can_read", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("can_write", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("allow_export", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.ForeignKeyConstraint(["rol_id"], ["roles.id"], name="permisos_rol_id_fkey"),
        sa.ForeignKeyConstraint(["hospital_id"], ["hospitales.id"], name="permisos_hospital_id_fkey"),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "equipos",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("codigo", sa.String(length=50), nullable=True),
        sa.Column("tipo", tipo_equipo_enum, nullable=False),
        sa.Column("estado", estado_equipo_enum, nullable=False, server_default=sa.text("'operativo'")),
        sa.Column("descripcion", sa.Text(), nullable=True),
        sa.Column("marca", sa.String(length=100), nullable=True),
        sa.Column("modelo", sa.String(length=100), nullable=True),
        sa.Column("numero_serie", sa.String(length=120), nullable=True),
        sa.Column("hospital_id", sa.Integer(), nullable=False),
        sa.Column("servicio_id", sa.Integer(), nullable=True),
        sa.Column("oficina_id", sa.Integer(), nullable=True),
        sa.Column("responsable", sa.String(length=120), nullable=True),
        sa.Column("fecha_compra", sa.Date(), nullable=True),
        sa.Column("fecha_instalacion", sa.Date(), nullable=True),
        sa.Column("garantia_hasta", sa.Date(), nullable=True),
        sa.Column("observaciones", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.ForeignKeyConstraint(["hospital_id"], ["hospitales.id"], name="equipos_hospital_id_fkey"),
        sa.ForeignKeyConstraint(["servicio_id"], ["servicios.id"], name="equipos_servicio_id_fkey"),
        sa.ForeignKeyConstraint(["oficina_id"], ["oficinas.id"], name="equipos_oficina_id_fkey"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("codigo"),
    )
    op.create_index("ix_equipos_numero_serie", "equipos", ["numero_serie"], unique=False)

    op.create_table(
        "equipos_historial",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("equipo_id", sa.Integer(), nullable=False),
        sa.Column("usuario_id", sa.Integer(), nullable=True),
        sa.Column("accion", sa.String(length=120), nullable=False),
        sa.Column("descripcion", sa.Text(), nullable=True),
        sa.Column("fecha", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.ForeignKeyConstraint(["equipo_id"], ["equipos.id"], name="equipos_historial_equipo_id_fkey"),
        sa.ForeignKeyConstraint(["usuario_id"], ["usuarios.id"], name="equipos_historial_usuario_id_fkey"),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "insumos",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("nombre", sa.String(length=120), nullable=False),
        sa.Column("numero_serie", sa.String(length=100), nullable=True),
        sa.Column("descripcion", sa.Text(), nullable=True),
        sa.Column("unidad_medida", sa.String(length=20), nullable=True),
        sa.Column("stock", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("stock_minimo", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("costo_unitario", sa.Numeric(10, 2), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_insumos_numero_serie", "insumos", ["numero_serie"], unique=False)

    op.create_table(
        "insumo_movimientos",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("insumo_id", sa.Integer(), nullable=False),
        sa.Column("usuario_id", sa.Integer(), nullable=True),
        sa.Column("equipo_id", sa.Integer(), nullable=True),
        sa.Column("tipo", tipo_movimiento_enum, nullable=False),
        sa.Column("cantidad", sa.Integer(), nullable=False),
        sa.Column("motivo", sa.String(length=255), nullable=True),
        sa.Column("observaciones", sa.Text(), nullable=True),
        sa.Column("fecha", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.ForeignKeyConstraint(["insumo_id"], ["insumos.id"], name="insumo_movimientos_insumo_id_fkey"),
        sa.ForeignKeyConstraint(["usuario_id"], ["usuarios.id"], name="insumo_movimientos_usuario_id_fkey"),
        sa.ForeignKeyConstraint(["equipo_id"], ["equipos.id"], name="insumo_movimientos_equipo_id_fkey"),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "equipo_insumos",
        sa.Column("equipo_id", sa.Integer(), nullable=False),
        sa.Column("insumo_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["equipo_id"], ["equipos.id"], name="equipo_insumos_equipo_id_fkey"),
        sa.ForeignKeyConstraint(["insumo_id"], ["insumos.id"], name="equipo_insumos_insumo_id_fkey"),
        sa.PrimaryKeyConstraint("equipo_id", "insumo_id"),
    )

    op.create_table(
        "actas",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("numero", sa.String(length=50), nullable=True),
        sa.Column("tipo", tipo_acta_enum, nullable=False),
        sa.Column("fecha", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("usuario_id", sa.Integer(), nullable=True),
        sa.Column("hospital_id", sa.Integer(), nullable=True),
        sa.Column("servicio_id", sa.Integer(), nullable=True),
        sa.Column("oficina_id", sa.Integer(), nullable=True),
        sa.Column("observaciones", sa.Text(), nullable=True),
        sa.Column("pdf_path", sa.String(length=255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.ForeignKeyConstraint(["usuario_id"], ["usuarios.id"], name="actas_usuario_id_fkey"),
        sa.ForeignKeyConstraint(["hospital_id"], ["hospitales.id"], name="actas_hospital_id_fkey"),
        sa.ForeignKeyConstraint(["servicio_id"], ["servicios.id"], name="actas_servicio_id_fkey"),
        sa.ForeignKeyConstraint(["oficina_id"], ["oficinas.id"], name="actas_oficina_id_fkey"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("numero"),
    )

    op.create_table(
        "acta_items",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("acta_id", sa.Integer(), nullable=False),
        sa.Column("equipo_id", sa.Integer(), nullable=True),
        sa.Column("cantidad", sa.Integer(), nullable=False, server_default=sa.text("1")),
        sa.Column("descripcion", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(["acta_id"], ["actas.id"], name="acta_items_acta_id_fkey"),
        sa.ForeignKeyConstraint(["equipo_id"], ["equipos.id"], name="acta_items_equipo_id_fkey"),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "adjuntos",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("equipo_id", sa.Integer(), nullable=False),
        sa.Column("filename", sa.String(length=255), nullable=False),
        sa.Column("path", sa.String(length=255), nullable=False),
        sa.Column("tipo", tipo_adjunto_enum, nullable=False),
        sa.Column("descripcion", sa.Text(), nullable=True),
        sa.Column("uploaded_by_id", sa.Integer(), nullable=True),
        sa.Column("uploaded_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.ForeignKeyConstraint(["equipo_id"], ["equipos.id"], name="adjuntos_equipo_id_fkey"),
        sa.ForeignKeyConstraint(["uploaded_by_id"], ["usuarios.id"], name="adjuntos_usuario_id_fkey"),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "docscan",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("titulo", sa.String(length=150), nullable=False),
        sa.Column("tipo", tipo_docscan_enum, nullable=False),
        sa.Column("filename", sa.String(length=255), nullable=False),
        sa.Column("path", sa.String(length=255), nullable=False),
        sa.Column("fecha_documento", sa.Date(), nullable=True),
        sa.Column("comentario", sa.Text(), nullable=True),
        sa.Column("usuario_id", sa.Integer(), nullable=True),
        sa.Column("hospital_id", sa.Integer(), nullable=True),
        sa.Column("servicio_id", sa.Integer(), nullable=True),
        sa.Column("oficina_id", sa.Integer(), nullable=True),
        sa.Column("uploaded_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.ForeignKeyConstraint(["usuario_id"], ["usuarios.id"], name="docscan_usuario_id_fkey"),
        sa.ForeignKeyConstraint(["hospital_id"], ["hospitales.id"], name="docscan_hospital_id_fkey"),
        sa.ForeignKeyConstraint(["servicio_id"], ["servicios.id"], name="docscan_servicio_id_fkey"),
        sa.ForeignKeyConstraint(["oficina_id"], ["oficinas.id"], name="docscan_oficina_id_fkey"),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "licencias",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("usuario_id", sa.Integer(), nullable=False),
        sa.Column("hospital_id", sa.Integer(), nullable=True),
        sa.Column("tipo", tipo_licencia_enum, nullable=False),
        sa.Column("estado", estado_licencia_enum, nullable=False, server_default=sa.text("'borrador'")),
        sa.Column("fecha_inicio", sa.Date(), nullable=False),
        sa.Column("fecha_fin", sa.Date(), nullable=False),
        sa.Column("motivo", sa.Text(), nullable=False),
        sa.Column("comentario", sa.Text(), nullable=True),
        sa.Column("requires_replacement", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("reemplazo_id", sa.Integer(), nullable=True),
        sa.Column("aprobado_por_id", sa.Integer(), nullable=True),
        sa.Column("aprobado_en", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.ForeignKeyConstraint(["usuario_id"], ["usuarios.id"], name="licencias_usuario_id_fkey"),
        sa.ForeignKeyConstraint(["hospital_id"], ["hospitales.id"], name="licencias_hospital_id_fkey"),
        sa.ForeignKeyConstraint(["reemplazo_id"], ["usuarios.id"], name="licencias_reemplazo_id_fkey"),
        sa.ForeignKeyConstraint(["aprobado_por_id"], ["usuarios.id"], name="licencias_aprobado_id_fkey"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_licencias_estado_tipo", "licencias", ["estado", "tipo"], unique=False)
    op.create_index("ix_licencias_usuario_id", "licencias", ["usuario_id"], unique=False)

    op.create_table(
        "auditoria",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("usuario_id", sa.Integer(), nullable=True),
        sa.Column("accion", sa.String(length=150), nullable=False),
        sa.Column("modulo", sa.String(length=50), nullable=True),
        sa.Column("tabla", sa.String(length=100), nullable=True),
        sa.Column("registro_id", sa.Integer(), nullable=True),
        sa.Column("ip_address", sa.String(length=45), nullable=True),
        sa.Column("datos", sa.Text(), nullable=True),
        sa.Column("fecha", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.ForeignKeyConstraint(["usuario_id"], ["usuarios.id"], name="auditoria_usuario_id_fkey"),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("auditoria")
    op.drop_index("ix_licencias_usuario_id", table_name="licencias")
    op.drop_index("ix_licencias_estado_tipo", table_name="licencias")
    op.drop_table("licencias")
    op.drop_table("docscan")
    op.drop_table("adjuntos")
    op.drop_table("acta_items")
    op.drop_table("actas")
    op.drop_table("equipo_insumos")
    op.drop_table("insumo_movimientos")
    op.drop_index("ix_insumos_numero_serie", table_name="insumos")
    op.drop_table("insumos")
    op.drop_table("equipos_historial")
    op.drop_index("ix_equipos_numero_serie", table_name="equipos")
    op.drop_table("equipos")
    op.drop_table("permisos")
    op.drop_table("usuarios")
    op.drop_table("oficinas")
    op.drop_table("servicios")
    op.drop_table("roles")
    op.drop_table("hospitales")

    tipo_movimiento_enum.drop(op.get_bind(), checkfirst=True)
    estado_licencia_enum.drop(op.get_bind(), checkfirst=True)
    tipo_licencia_enum.drop(op.get_bind(), checkfirst=True)
    tipo_docscan_enum.drop(op.get_bind(), checkfirst=True)
    tipo_adjunto_enum.drop(op.get_bind(), checkfirst=True)
    tipo_acta_enum.drop(op.get_bind(), checkfirst=True)
    estado_equipo_enum.drop(op.get_bind(), checkfirst=True)
    tipo_equipo_enum.drop(op.get_bind(), checkfirst=True)
    modulo_permiso_enum.drop(op.get_bind(), checkfirst=True)
