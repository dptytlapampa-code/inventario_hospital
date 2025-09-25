"""Initial schema."""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "c28f3d5aa8a9"
down_revision = None
branch_labels = None
depends_on = None

PERMISSION_MODULES = (
    "inventario",
    "insumos",
    "actas",
    "adjuntos",
    "docscan",
    "reportes",
    "auditoria",
    "licencias",
)

EQUIPO_TYPES = (
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
)

EQUIPO_STATES = (
    "operativo",
    "servicio_tecnico",
    "de_baja",
    "prestado",
)

ACTA_TYPES = (
    "entrega",
    "prestamo",
    "transferencia",
)

ADJUNTO_TYPES = (
    "factura",
    "presupuesto",
    "acta",
    "planilla_patrimonial",
    "remito",
    "otro",
)

DOCSCAN_TYPES = (
    "nota",
    "informe",
    "contrato",
    "otro",
)

LICENCIA_TYPES = (
    "temporal",
    "permanente",
    "especial",
)

LICENCIA_STATES = (
    "borrador",
    "pendiente",
    "aprobada",
    "rechazada",
    "cancelada",
)

MOVIMIENTO_TYPES = (
    "ingreso",
    "egreso",
)


def _enum_check(column: str, values: tuple[str, ...], constraint: str) -> sa.CheckConstraint:
    ordered: list[str] = []
    seen: set[str] = set()
    for value in values:
        for candidate in (value, value.upper()):
            if candidate not in seen:
                ordered.append(candidate)
                seen.add(candidate)
    options = ", ".join(f"'{value}'" for value in ordered)
    return sa.CheckConstraint(f"{column} IN ({options})", name=constraint)


def upgrade() -> None:
    op.create_table(
        "hospitales",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("nombre", sa.String(length=120), nullable=False, unique=True),
        sa.Column("codigo", sa.String(length=20), unique=True),
        sa.Column("direccion", sa.String(length=255)),
        sa.Column("telefono", sa.String(length=50)),
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

    op.create_table(
        "roles",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("nombre", sa.String(length=50), nullable=False, unique=True),
        sa.Column("descripcion", sa.String(length=255)),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.current_timestamp(),
            nullable=False,
        ),
    )

    op.create_table(
        "servicios",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("nombre", sa.String(length=120), nullable=False),
        sa.Column("descripcion", sa.String(length=255)),
        sa.Column("hospital_id", sa.Integer(), sa.ForeignKey("hospitales.id"), nullable=False),
        sa.UniqueConstraint("nombre", "hospital_id", name="uq_servicio_nombre_hospital"),
    )

    op.create_table(
        "oficinas",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("nombre", sa.String(length=120), nullable=False),
        sa.Column("piso", sa.String(length=20)),
        sa.Column("servicio_id", sa.Integer(), sa.ForeignKey("servicios.id"), nullable=False),
        sa.Column("hospital_id", sa.Integer(), sa.ForeignKey("hospitales.id"), nullable=False),
        sa.UniqueConstraint("nombre", "servicio_id", name="uq_oficina_nombre_servicio"),
    )

    op.create_table(
        "usuarios",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("username", sa.String(length=80), nullable=False, unique=True),
        sa.Column("nombre", sa.String(length=120), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False, unique=True),
        sa.Column("telefono", sa.String(length=50)),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("activo", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("rol_id", sa.Integer(), sa.ForeignKey("roles.id"), nullable=False),
        sa.Column("hospital_id", sa.Integer(), sa.ForeignKey("hospitales.id")),
        sa.Column("servicio_id", sa.Integer(), sa.ForeignKey("servicios.id")),
        sa.Column("oficina_id", sa.Integer(), sa.ForeignKey("oficinas.id")),
        sa.Column("ultimo_login", sa.DateTime(timezone=True)),
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

    op.create_table(
        "permisos",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("rol_id", sa.Integer(), sa.ForeignKey("roles.id"), nullable=False),
        sa.Column("modulo", sa.String(length=50), nullable=False),
        sa.Column("hospital_id", sa.Integer(), sa.ForeignKey("hospitales.id")),
        sa.Column("can_read", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("can_write", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("allow_export", sa.Boolean(), nullable=False, server_default=sa.false()),
        _enum_check("modulo", PERMISSION_MODULES, "ck_permisos_modulo"),
    )

    op.create_table(
        "equipos",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("codigo", sa.String(length=50), unique=True),
        sa.Column("tipo", sa.String(length=50), nullable=False),
        sa.Column("estado", sa.String(length=50), nullable=False, server_default=sa.text("'operativo'")),
        sa.Column("descripcion", sa.Text()),
        sa.Column("marca", sa.String(length=100)),
        sa.Column("modelo", sa.String(length=100)),
        sa.Column("numero_serie", sa.String(length=120)),
        sa.Column("hospital_id", sa.Integer(), sa.ForeignKey("hospitales.id"), nullable=False),
        sa.Column("servicio_id", sa.Integer(), sa.ForeignKey("servicios.id")),
        sa.Column("oficina_id", sa.Integer(), sa.ForeignKey("oficinas.id")),
        sa.Column("responsable", sa.String(length=120)),
        sa.Column("fecha_compra", sa.Date()),
        sa.Column("fecha_instalacion", sa.Date()),
        sa.Column("garantia_hasta", sa.Date()),
        sa.Column("observaciones", sa.Text()),
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
        _enum_check("estado", EQUIPO_STATES, "ck_equipos_estado"),
    )
    op.create_index("ix_equipos_numero_serie", "equipos", ["numero_serie"], unique=False)

    op.create_table(
        "equipos_historial",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("equipo_id", sa.Integer(), sa.ForeignKey("equipos.id"), nullable=False),
        sa.Column("usuario_id", sa.Integer(), sa.ForeignKey("usuarios.id")),
        sa.Column("accion", sa.String(length=120), nullable=False),
        sa.Column("descripcion", sa.Text()),
        sa.Column(
            "fecha",
            sa.DateTime(timezone=True),
            server_default=sa.func.current_timestamp(),
            nullable=False,
        ),
    )

    op.create_table(
        "insumos",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("nombre", sa.String(length=120), nullable=False),
        sa.Column("numero_serie", sa.String(length=100)),
        sa.Column("descripcion", sa.Text()),
        sa.Column("unidad_medida", sa.String(length=20)),
        sa.Column("stock", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("stock_minimo", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("costo_unitario", sa.Numeric(10, 2)),
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
    op.create_index("ix_insumos_numero_serie", "insumos", ["numero_serie"], unique=False)

    op.create_table(
        "insumo_movimientos",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("insumo_id", sa.Integer(), sa.ForeignKey("insumos.id"), nullable=False),
        sa.Column("usuario_id", sa.Integer(), sa.ForeignKey("usuarios.id")),
        sa.Column("equipo_id", sa.Integer(), sa.ForeignKey("equipos.id")),
        sa.Column("tipo", sa.String(length=20), nullable=False),
        sa.Column("cantidad", sa.Integer(), nullable=False),
        sa.Column("motivo", sa.String(length=255)),
        sa.Column("observaciones", sa.Text()),
        sa.Column(
            "fecha",
            sa.DateTime(timezone=True),
            server_default=sa.func.current_timestamp(),
            nullable=False,
        ),
        _enum_check("tipo", MOVIMIENTO_TYPES, "ck_insumo_movimientos_tipo"),
    )

    op.create_table(
        "equipo_insumos",
        sa.Column("equipo_id", sa.Integer(), sa.ForeignKey("equipos.id"), primary_key=True),
        sa.Column("insumo_id", sa.Integer(), sa.ForeignKey("insumos.id"), primary_key=True),
    )

    op.create_table(
        "actas",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("numero", sa.String(length=50), unique=True),
        sa.Column("tipo", sa.String(length=50), nullable=False),
        sa.Column(
            "fecha",
            sa.DateTime(timezone=True),
            server_default=sa.func.current_timestamp(),
            nullable=False,
        ),
        sa.Column("usuario_id", sa.Integer(), sa.ForeignKey("usuarios.id")),
        sa.Column("hospital_id", sa.Integer(), sa.ForeignKey("hospitales.id")),
        sa.Column("servicio_id", sa.Integer(), sa.ForeignKey("servicios.id")),
        sa.Column("oficina_id", sa.Integer(), sa.ForeignKey("oficinas.id")),
        sa.Column("observaciones", sa.Text()),
        sa.Column("pdf_path", sa.String(length=255)),
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
        _enum_check("tipo", ACTA_TYPES, "ck_actas_tipo"),
    )

    op.create_table(
        "acta_items",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("acta_id", sa.Integer(), sa.ForeignKey("actas.id"), nullable=False),
        sa.Column("equipo_id", sa.Integer(), sa.ForeignKey("equipos.id")),
        sa.Column("cantidad", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("descripcion", sa.Text()),
    )

    op.create_table(
        "adjuntos",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("equipo_id", sa.Integer(), sa.ForeignKey("equipos.id"), nullable=False),
        sa.Column("filename", sa.String(length=255), nullable=False),
        sa.Column("path", sa.String(length=255), nullable=False),
        sa.Column("tipo", sa.String(length=50), nullable=False),
        sa.Column("descripcion", sa.Text()),
        sa.Column("uploaded_by_id", sa.Integer(), sa.ForeignKey("usuarios.id")),
        sa.Column(
            "uploaded_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.current_timestamp(),
            nullable=False,
        ),
        _enum_check("tipo", ADJUNTO_TYPES, "ck_adjuntos_tipo"),
    )

    op.create_table(
        "docscan",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("titulo", sa.String(length=150), nullable=False),
        sa.Column("tipo", sa.String(length=50), nullable=False),
        sa.Column("filename", sa.String(length=255), nullable=False),
        sa.Column("path", sa.String(length=255), nullable=False),
        sa.Column("fecha_documento", sa.Date()),
        sa.Column("comentario", sa.Text()),
        sa.Column("usuario_id", sa.Integer(), sa.ForeignKey("usuarios.id")),
        sa.Column("hospital_id", sa.Integer(), sa.ForeignKey("hospitales.id")),
        sa.Column("servicio_id", sa.Integer(), sa.ForeignKey("servicios.id")),
        sa.Column("oficina_id", sa.Integer(), sa.ForeignKey("oficinas.id")),
        sa.Column(
            "uploaded_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.current_timestamp(),
            nullable=False,
        ),
        _enum_check("tipo", DOCSCAN_TYPES, "ck_docscan_tipo"),
    )

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
        _enum_check("tipo", LICENCIA_TYPES, "ck_licencias_tipo"),
        _enum_check("estado", LICENCIA_STATES, "ck_licencias_estado"),
    )
    op.create_index("ix_licencias_estado_tipo", "licencias", ["estado", "tipo"], unique=False)
    op.create_index("ix_licencias_usuario_id", "licencias", ["usuario_id"], unique=False)

    op.create_table(
        "auditoria",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("usuario_id", sa.Integer(), sa.ForeignKey("usuarios.id")),
        sa.Column("accion", sa.String(length=150), nullable=False),
        sa.Column("modulo", sa.String(length=50)),
        sa.Column("tabla", sa.String(length=100)),
        sa.Column("registro_id", sa.Integer()),
        sa.Column("ip_address", sa.String(length=45)),
        sa.Column("datos", sa.Text()),
        sa.Column(
            "fecha",
            sa.DateTime(timezone=True),
            server_default=sa.func.current_timestamp(),
            nullable=False,
        ),
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
