"""Initial database schema with base data."""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None

ADMIN_PASSWORD_HASH = (
    "pbkdf2:sha256:1000000$TLgLFsQLudDtkY29$25757fc97d0948e2faf9174eb0946e4e250a7c2d9ee3611dee5fd9dbb3b5d72d"
)

ENUM_DEFINITIONS: list[tuple[str, tuple[str, ...]]] = [
    ("theme_preference", ("light", "dark", "system")),
    (
        "estado_equipo",
        ("operativo", "servicio_tecnico", "en_taller", "de_baja", "prestado"),
    ),
    ("tipo_acta", ("entrega", "prestamo", "transferencia")),
    (
        "tipo_adjunto",
        ("factura", "presupuesto", "acta", "planilla_patrimonial", "remito", "otro"),
    ),
    ("tipo_docscan", ("nota", "informe", "contrato", "otro")),
    ("tipo_licencia", ("vacaciones", "enfermedad", "estudio", "otro")),
    ("estado_licencia", ("solicitada", "aprobada", "rechazada", "cancelada")),
    ("tipo_movimiento", ("ingreso", "egreso")),
    ("insumo_serie_estado", ("libre", "asignado", "dado_baja")),
    (
        "modulo_permiso",
        ("inventario", "insumos", "actas", "adjuntos", "docscan", "reportes", "auditoria", "licencias"),
    ),
]


def _create_enums(bind) -> dict[str, sa.types.TypeEngine]:
    enum_map: dict[str, sa.types.TypeEngine] = {}
    is_postgres = bind.dialect.name == "postgresql"
    for name, values in ENUM_DEFINITIONS:
        if is_postgres:
            enum = postgresql.ENUM(*values, name=name, create_type=False)
            enum.create(bind, checkfirst=True)
        else:
            enum = sa.Enum(*values, name=name, native_enum=False)
        enum_map[name] = enum
    return enum_map


def _drop_enums(bind) -> None:
    if bind.dialect.name != "postgresql":
        return
    for name, values in reversed(ENUM_DEFINITIONS):
        enum = postgresql.ENUM(*values, name=name, create_type=False)
        enum.drop(bind, checkfirst=True)


def upgrade() -> None:
    bind = op.get_bind()
    enums = _create_enums(bind)

    op.create_table(
        "roles",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("nombre", sa.String(length=50), nullable=False, unique=True),
        sa.Column("descripcion", sa.String(length=255), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
    )

    op.create_table(
        "instituciones",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("nombre", sa.String(length=255), nullable=False),
        sa.Column("tipo_institucion", sa.String(length=50), nullable=False),
        sa.Column("codigo", sa.String(length=50), nullable=True),
        sa.Column("localidad", sa.String(length=120), nullable=False),
        sa.Column(
            "provincia",
            sa.String(length=120),
            nullable=False,
            server_default=sa.text("'La Pampa'"),
        ),
        sa.Column("zona_sanitaria", sa.String(length=120), nullable=True),
        sa.Column("direccion", sa.String(length=255), nullable=True),
        sa.Column(
            "estado", sa.String(length=50), nullable=False, server_default=sa.text("'Activa'"),
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.UniqueConstraint("nombre", "localidad", name="uq_institucion_nombre_localidad"),
    )
    op.create_index("ix_instituciones_codigo", "instituciones", ["codigo"])

    op.create_table(
        "insumos",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("nombre", sa.String(length=120), nullable=False),
        sa.Column("numero_serie", sa.String(length=100), nullable=True),
        sa.Column("descripcion", sa.Text(), nullable=True),
        sa.Column("unidad_medida", sa.String(length=20), nullable=True),
        sa.Column(
            "stock", sa.Integer(), nullable=False, server_default=sa.text("0"),
        ),
        sa.Column(
            "stock_minimo", sa.Integer(), nullable=False, server_default=sa.text("0"),
        ),
        sa.Column("costo_unitario", sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
    )
    op.create_index("ix_insumos_numero_serie", "insumos", ["numero_serie"])

    op.create_table(
        "tipo_equipo",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("slug", sa.String(length=80), nullable=False, unique=True),
        sa.Column("nombre", sa.String(length=160), nullable=False, unique=True),
        sa.Column("descripcion", sa.Text(), nullable=True),
        sa.Column(
            "activo", sa.Boolean(), nullable=False, server_default=sa.true(),
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
    )

    op.create_table(
        "servicios",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("nombre", sa.String(length=200), nullable=False),
        sa.Column("descripcion", sa.String(length=255), nullable=True),
        sa.Column("institucion_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ["institucion_id"], ["instituciones.id"], ondelete="CASCADE"
        ),
        sa.UniqueConstraint("institucion_id", "nombre", name="uq_servicio_nombre_institucion"),
    )
    op.create_index("ix_servicios_nombre", "servicios", ["nombre"])

    op.create_table(
        "oficinas",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("nombre", sa.String(length=200), nullable=False),
        sa.Column("piso", sa.String(length=20), nullable=True),
        sa.Column("servicio_id", sa.Integer(), nullable=False),
        sa.Column("institucion_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ["servicio_id"], ["servicios.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["institucion_id"], ["instituciones.id"], ondelete="CASCADE"
        ),
        sa.UniqueConstraint("servicio_id", "nombre", name="uq_oficina_nombre_servicio"),
    )
    op.create_index("ix_oficinas_nombre", "oficinas", ["nombre"])

    op.create_table(
        "permisos",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("rol_id", sa.Integer(), nullable=False),
        sa.Column("modulo", enums["modulo_permiso"], nullable=False),
        sa.Column("hospital_id", sa.Integer(), nullable=True),
        sa.Column(
            "can_read", sa.Boolean(), nullable=False, server_default=sa.true(),
        ),
        sa.Column(
            "can_write", sa.Boolean(), nullable=False, server_default=sa.false(),
        ),
        sa.Column(
            "allow_export", sa.Boolean(), nullable=False, server_default=sa.false(),
        ),
        sa.ForeignKeyConstraint(["rol_id"], ["roles.id"]),
        sa.ForeignKeyConstraint(["hospital_id"], ["instituciones.id"]),
    )

    op.create_table(
        "usuarios",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("username", sa.String(length=80), nullable=False),
        sa.Column("nombre", sa.String(length=120), nullable=False),
        sa.Column("dni", sa.String(length=20), nullable=False),
        sa.Column("apellido", sa.String(length=120), nullable=True),
        sa.Column("email", sa.String(length=255), nullable=False, unique=True),
        sa.Column("telefono", sa.String(length=50), nullable=True),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column(
            "activo", sa.Boolean(), nullable=False, server_default=sa.true(),
        ),
        sa.Column("rol_id", sa.Integer(), nullable=False),
        sa.Column("hospital_id", sa.Integer(), nullable=True),
        sa.Column("servicio_id", sa.Integer(), nullable=True),
        sa.Column("oficina_id", sa.Integer(), nullable=True),
        sa.Column(
            "theme_pref",
            enums["theme_preference"],
            nullable=False,
            server_default="system",
        ),
        sa.Column("ultimo_login", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["rol_id"], ["roles.id"]),
        sa.ForeignKeyConstraint(["hospital_id"], ["instituciones.id"]),
        sa.ForeignKeyConstraint(["servicio_id"], ["servicios.id"]),
        sa.ForeignKeyConstraint(["oficina_id"], ["oficinas.id"]),
        sa.UniqueConstraint("username", name="uq_usuario_username"),
        sa.UniqueConstraint("dni", name="uq_usuario_dni"),
        sa.UniqueConstraint("email", name="uq_usuario_email"),
    )

    op.create_table(
        "equipos",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("codigo", sa.String(length=50), nullable=True, unique=True),
        sa.Column("tipo_id", sa.Integer(), nullable=False),
        sa.Column("estado", enums["estado_equipo"], nullable=False),
        sa.Column("descripcion", sa.Text(), nullable=True),
        sa.Column("marca", sa.String(length=100), nullable=True),
        sa.Column("modelo", sa.String(length=100), nullable=True),
        sa.Column("numero_serie", sa.String(length=120), nullable=True),
        sa.Column(
            "sin_numero_serie",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),
        sa.Column("hospital_id", sa.Integer(), nullable=False),
        sa.Column("servicio_id", sa.Integer(), nullable=True),
        sa.Column("oficina_id", sa.Integer(), nullable=True),
        sa.Column("responsable", sa.String(length=120), nullable=True),
        sa.Column("fecha_compra", sa.Date(), nullable=True),
        sa.Column("fecha_instalacion", sa.Date(), nullable=True),
        sa.Column("garantia_hasta", sa.Date(), nullable=True),
        sa.Column("observaciones", sa.Text(), nullable=True),
        sa.Column(
            "es_nuevo", sa.Boolean(), nullable=False, server_default=sa.false(),
        ),
        sa.Column("expediente", sa.String(length=120), nullable=True),
        sa.Column("anio_expediente", sa.Integer(), nullable=True),
        sa.Column("orden_compra", sa.String(length=120), nullable=True),
        sa.Column("tipo_adquisicion", sa.String(length=50), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["tipo_id"], ["tipo_equipo.id"]),
        sa.ForeignKeyConstraint(["hospital_id"], ["instituciones.id"]),
        sa.ForeignKeyConstraint(["servicio_id"], ["servicios.id"]),
        sa.ForeignKeyConstraint(["oficina_id"], ["oficinas.id"]),
    )
    op.create_index("ix_equipos_descripcion", "equipos", ["descripcion"])
    op.create_index("ix_equipos_marca", "equipos", ["marca"])
    op.create_index("ix_equipos_modelo", "equipos", ["modelo"])
    op.create_index("ix_equipos_numero_serie", "equipos", ["numero_serie"])

    op.create_table(
        "vlans",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("nombre", sa.String(length=120), nullable=False),
        sa.Column("identificador", sa.String(length=50), nullable=False),
        sa.Column("descripcion", sa.String(length=255), nullable=True),
        sa.Column("hospital_id", sa.Integer(), nullable=False),
        sa.Column("servicio_id", sa.Integer(), nullable=True),
        sa.Column("oficina_id", sa.Integer(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["hospital_id"], ["instituciones.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["servicio_id"], ["servicios.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["oficina_id"], ["oficinas.id"], ondelete="SET NULL"),
        sa.UniqueConstraint("hospital_id", "identificador", name="uq_vlan_hospital_identificador"),
    )

    op.create_table(
        "actas",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("numero", sa.String(length=50), nullable=True, unique=True),
        sa.Column("tipo", enums["tipo_acta"], nullable=False),
        sa.Column(
            "fecha", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.Column("usuario_id", sa.Integer(), nullable=True),
        sa.Column("hospital_id", sa.Integer(), nullable=True),
        sa.Column("servicio_id", sa.Integer(), nullable=True),
        sa.Column("oficina_id", sa.Integer(), nullable=True),
        sa.Column("observaciones", sa.Text(), nullable=True),
        sa.Column("pdf_path", sa.String(length=255), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["usuario_id"], ["usuarios.id"]),
        sa.ForeignKeyConstraint(["hospital_id"], ["instituciones.id"]),
        sa.ForeignKeyConstraint(["servicio_id"], ["servicios.id"]),
        sa.ForeignKeyConstraint(["oficina_id"], ["oficinas.id"]),
    )

    op.create_table(
        "adjuntos",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("equipo_id", sa.Integer(), nullable=False),
        sa.Column("filename", sa.String(length=255), nullable=False),
        sa.Column("path", sa.String(length=255), nullable=False),
        sa.Column("tipo", enums["tipo_adjunto"], nullable=False),
        sa.Column("descripcion", sa.Text(), nullable=True),
        sa.Column("uploaded_by_id", sa.Integer(), nullable=True),
        sa.Column(
            "uploaded_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["equipo_id"], ["equipos.id"]),
        sa.ForeignKeyConstraint(["uploaded_by_id"], ["usuarios.id"]),
    )

    op.create_table(
        "auditorias",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("usuario_id", sa.Integer(), nullable=True),
        sa.Column("hospital_id", sa.Integer(), nullable=True),
        sa.Column("modulo", sa.String(length=50), nullable=True),
        sa.Column("accion", sa.String(length=50), nullable=False),
        sa.Column("entidad", sa.String(length=50), nullable=True),
        sa.Column("entidad_id", sa.Integer(), nullable=True),
        sa.Column("descripcion", sa.Text(), nullable=True),
        sa.Column("cambios", sa.JSON(), nullable=True),
        sa.Column("ip_address", sa.String(length=45), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["usuario_id"], ["usuarios.id"]),
        sa.ForeignKeyConstraint(["hospital_id"], ["instituciones.id"]),
    )

    op.create_table(
        "docscan",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("titulo", sa.String(length=150), nullable=False),
        sa.Column("tipo", enums["tipo_docscan"], nullable=False),
        sa.Column("filename", sa.String(length=255), nullable=False),
        sa.Column("path", sa.String(length=255), nullable=False),
        sa.Column("fecha_documento", sa.Date(), nullable=True),
        sa.Column("comentario", sa.Text(), nullable=True),
        sa.Column("usuario_id", sa.Integer(), nullable=True),
        sa.Column("hospital_id", sa.Integer(), nullable=True),
        sa.Column("servicio_id", sa.Integer(), nullable=True),
        sa.Column("oficina_id", sa.Integer(), nullable=True),
        sa.Column(
            "uploaded_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["usuario_id"], ["usuarios.id"]),
        sa.ForeignKeyConstraint(["hospital_id"], ["instituciones.id"]),
        sa.ForeignKeyConstraint(["servicio_id"], ["servicios.id"]),
        sa.ForeignKeyConstraint(["oficina_id"], ["oficinas.id"]),
    )

    op.create_table(
        "equipos_adjuntos",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("equipo_id", sa.Integer(), nullable=False),
        sa.Column("filename", sa.String(length=255), nullable=False),
        sa.Column("filepath", sa.String(length=512), nullable=False),
        sa.Column("mime_type", sa.String(length=120), nullable=False),
        sa.Column("uploaded_by_id", sa.Integer(), nullable=True),
        sa.Column("file_size", sa.Integer(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["equipo_id"], ["equipos.id"]),
        sa.ForeignKeyConstraint(["uploaded_by_id"], ["usuarios.id"]),
    )
    op.create_index("ix_equipos_adjuntos_equipo_id", "equipos_adjuntos", ["equipo_id"])

    op.create_table(
        "equipos_historial",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("equipo_id", sa.Integer(), nullable=False),
        sa.Column("usuario_id", sa.Integer(), nullable=True),
        sa.Column("accion", sa.String(length=120), nullable=False),
        sa.Column("descripcion", sa.Text(), nullable=True),
        sa.Column(
            "fecha", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.ForeignKeyConstraint(["equipo_id"], ["equipos.id"]),
        sa.ForeignKeyConstraint(["usuario_id"], ["usuarios.id"]),
    )

    op.create_table(
        "hospital_usuario_rol",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("usuario_id", sa.Integer(), nullable=False),
        sa.Column("hospital_id", sa.Integer(), nullable=False),
        sa.Column("rol_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["usuario_id"], ["usuarios.id"]),
        sa.ForeignKeyConstraint(["hospital_id"], ["instituciones.id"]),
        sa.ForeignKeyConstraint(["rol_id"], ["roles.id"]),
        sa.UniqueConstraint("usuario_id", "hospital_id", name="uq_usuario_hospital_asignacion"),
    )

    op.create_table(
        "insumo_movimientos",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("insumo_id", sa.Integer(), nullable=False),
        sa.Column("usuario_id", sa.Integer(), nullable=True),
        sa.Column("equipo_id", sa.Integer(), nullable=True),
        sa.Column("tipo", enums["tipo_movimiento"], nullable=False),
        sa.Column("cantidad", sa.Integer(), nullable=False),
        sa.Column("motivo", sa.String(length=255), nullable=True),
        sa.Column("observaciones", sa.Text(), nullable=True),
        sa.Column(
            "fecha", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.ForeignKeyConstraint(["insumo_id"], ["insumos.id"]),
        sa.ForeignKeyConstraint(["usuario_id"], ["usuarios.id"]),
        sa.ForeignKeyConstraint(["equipo_id"], ["equipos.id"]),
    )

    op.create_table(
        "insumo_series",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("insumo_id", sa.Integer(), nullable=False),
        sa.Column("nro_serie", sa.String(length=128), nullable=False),
        sa.Column("estado", enums["insumo_serie_estado"], nullable=False),
        sa.Column("equipo_id", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(["insumo_id"], ["insumos.id"]),
        sa.ForeignKeyConstraint(["equipo_id"], ["equipos.id"]),
    )
    op.create_index("ix_insumo_series_insumo_id", "insumo_series", ["insumo_id"])
    op.create_index("ix_insumo_series_equipo_id", "insumo_series", ["equipo_id"])
    op.create_index("ix_insumo_series_nro_serie", "insumo_series", ["nro_serie"], unique=True)

    op.create_table(
        "licencias",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("hospital_id", sa.Integer(), nullable=True),
        sa.Column("tipo", enums["tipo_licencia"], nullable=False),
        sa.Column("fecha_inicio", sa.Date(), nullable=False),
        sa.Column("fecha_fin", sa.Date(), nullable=False),
        sa.Column("motivo", sa.Text(), nullable=False),
        sa.Column(
            "estado",
            enums["estado_licencia"],
            nullable=False,
            server_default="solicitada",
        ),
        sa.Column("motivo_rechazo", sa.Text(), nullable=True),
        sa.Column("decidido_por", sa.Integer(), nullable=True),
        sa.Column("decidido_en", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["user_id"], ["usuarios.id"]),
        sa.ForeignKeyConstraint(["hospital_id"], ["instituciones.id"]),
        sa.ForeignKeyConstraint(["decidido_por"], ["usuarios.id"]),
    )
    op.create_index("ix_licencias_user_id", "licencias", ["user_id"])
    op.create_index("ix_licencias_estado", "licencias", ["estado"])
    op.create_index(
        "ix_licencias_fecha_inicio_fecha_fin",
        "licencias",
        ["fecha_inicio", "fecha_fin"],
    )

    op.create_table(
        "vlan_dispositivos",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("vlan_id", sa.Integer(), nullable=False),
        sa.Column("nombre_equipo", sa.String(length=150), nullable=False),
        sa.Column("host", sa.String(length=120), nullable=True),
        sa.Column("direccion_ip", sa.String(length=45), nullable=False),
        sa.Column("direccion_mac", sa.String(length=32), nullable=True),
        sa.Column("hospital_id", sa.Integer(), nullable=False),
        sa.Column("servicio_id", sa.Integer(), nullable=True),
        sa.Column("oficina_id", sa.Integer(), nullable=True),
        sa.Column("notas", sa.String(length=255), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["vlan_id"], ["vlans.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["hospital_id"], ["instituciones.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["servicio_id"], ["servicios.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["oficina_id"], ["oficinas.id"], ondelete="SET NULL"),
        sa.UniqueConstraint("direccion_ip", name="uq_vlan_dispositivo_ip"),
    )

    op.create_table(
        "acta_items",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("acta_id", sa.Integer(), nullable=False),
        sa.Column("equipo_id", sa.Integer(), nullable=True),
        sa.Column(
            "cantidad", sa.Integer(), nullable=False, server_default=sa.text("1"),
        ),
        sa.Column("descripcion", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(["acta_id"], ["actas.id"]),
        sa.ForeignKeyConstraint(["equipo_id"], ["equipos.id"]),
    )

    op.create_table(
        "equipos_insumos",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("equipo_id", sa.Integer(), nullable=False),
        sa.Column("insumo_id", sa.Integer(), nullable=False),
        sa.Column("insumo_serie_id", sa.Integer(), nullable=False),
        sa.Column("asociado_por_id", sa.Integer(), nullable=True),
        sa.Column(
            "fecha_asociacion",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column("fecha_desasociacion", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["equipo_id"], ["equipos.id"]),
        sa.ForeignKeyConstraint(["insumo_id"], ["insumos.id"]),
        sa.ForeignKeyConstraint(["insumo_serie_id"], ["insumo_series.id"]),
        sa.ForeignKeyConstraint(["asociado_por_id"], ["usuarios.id"]),
        sa.UniqueConstraint("equipo_id", "insumo_serie_id", name="uq_equipo_serie_unica"),
        sa.UniqueConstraint("insumo_serie_id", name="uq_equipos_insumos_insumo_serie_id"),
    )
    op.create_index("ix_equipos_insumos_equipo_id", "equipos_insumos", ["equipo_id"])
    op.create_index("ix_equipos_insumos_insumo_id", "equipos_insumos", ["insumo_id"])

    roles_table = sa.table(
        "roles",
        sa.column("id", sa.Integer()),
        sa.column("nombre", sa.String(length=50)),
        sa.column("descripcion", sa.String(length=255)),
    )
    op.bulk_insert(
        roles_table,
        [
            {"id": 1, "nombre": "Superadmin", "descripcion": "Acceso completo"},
            {"id": 2, "nombre": "Admin", "descripcion": "Administración por hospital"},
            {"id": 3, "nombre": "Tecnico", "descripcion": "Gestión operativa"},
            {"id": 4, "nombre": "Lectura", "descripcion": "Solo consulta"},
        ],
    )

    permisos_table = sa.table(
        "permisos",
        sa.column("rol_id", sa.Integer()),
        sa.column("modulo", sa.String(length=50)),
        sa.column("hospital_id", sa.Integer()),
        sa.column("can_read", sa.Boolean()),
        sa.column("can_write", sa.Boolean()),
        sa.column("allow_export", sa.Boolean()),
    )
    op.bulk_insert(
        permisos_table,
        [
            {
                "rol_id": 1,
                "modulo": modulo,
                "hospital_id": None,
                "can_read": True,
                "can_write": True,
                "allow_export": True,
            }
            for modulo in (
                "inventario",
                "insumos",
                "actas",
                "adjuntos",
                "docscan",
                "reportes",
                "auditoria",
                "licencias",
            )
        ],
    )

    usuarios_table = sa.table(
        "usuarios",
        sa.column("username", sa.String(length=80)),
        sa.column("nombre", sa.String(length=120)),
        sa.column("apellido", sa.String(length=120)),
        sa.column("dni", sa.String(length=20)),
        sa.column("email", sa.String(length=255)),
        sa.column("telefono", sa.String(length=50)),
        sa.column("password_hash", sa.String(length=255)),
        sa.column("activo", sa.Boolean()),
        sa.column("rol_id", sa.Integer()),
        sa.column("hospital_id", sa.Integer()),
        sa.column("servicio_id", sa.Integer()),
        sa.column("oficina_id", sa.Integer()),
        sa.column("theme_pref", sa.String(length=20)),
    )
    op.bulk_insert(
        usuarios_table,
        [
            {
                "username": "admin",
                "nombre": "Super Administrador",
                "apellido": "Principal",
                "dni": "20000000",
                "email": "admin@example.com",
                "telefono": None,
                "password_hash": ADMIN_PASSWORD_HASH,
                "activo": True,
                "rol_id": 1,
                "hospital_id": None,
                "servicio_id": None,
                "oficina_id": None,
                "theme_pref": "system",
            }
        ],
    )


def downgrade() -> None:
    op.drop_index("ix_equipos_insumos_insumo_id", table_name="equipos_insumos")
    op.drop_index("ix_equipos_insumos_equipo_id", table_name="equipos_insumos")
    op.drop_table("equipos_insumos")

    op.drop_table("acta_items")

    op.drop_table("vlan_dispositivos")

    op.drop_index("ix_licencias_fecha_inicio_fecha_fin", table_name="licencias")
    op.drop_index("ix_licencias_estado", table_name="licencias")
    op.drop_index("ix_licencias_user_id", table_name="licencias")
    op.drop_table("licencias")

    op.drop_index("ix_insumo_series_nro_serie", table_name="insumo_series")
    op.drop_index("ix_insumo_series_equipo_id", table_name="insumo_series")
    op.drop_index("ix_insumo_series_insumo_id", table_name="insumo_series")
    op.drop_table("insumo_series")

    op.drop_table("insumo_movimientos")

    op.drop_table("hospital_usuario_rol")

    op.drop_table("equipos_historial")

    op.drop_index("ix_equipos_adjuntos_equipo_id", table_name="equipos_adjuntos")
    op.drop_table("equipos_adjuntos")

    op.drop_table("docscan")

    op.drop_table("auditorias")

    op.drop_table("adjuntos")

    op.drop_table("actas")

    op.drop_table("vlans")

    op.drop_index("ix_equipos_numero_serie", table_name="equipos")
    op.drop_index("ix_equipos_modelo", table_name="equipos")
    op.drop_index("ix_equipos_marca", table_name="equipos")
    op.drop_index("ix_equipos_descripcion", table_name="equipos")
    op.drop_table("equipos")

    op.drop_table("usuarios")

    op.drop_table("permisos")

    op.drop_index("ix_oficinas_nombre", table_name="oficinas")
    op.drop_table("oficinas")

    op.drop_index("ix_servicios_nombre", table_name="servicios")
    op.drop_table("servicios")

    op.drop_table("tipo_equipo")

    op.drop_index("ix_insumos_numero_serie", table_name="insumos")
    op.drop_table("insumos")

    op.drop_table("roles")

    op.drop_index("ix_instituciones_codigo", table_name="instituciones")
    op.drop_table("instituciones")

    bind = op.get_bind()
    _drop_enums(bind)
