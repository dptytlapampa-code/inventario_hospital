"""Database seed script that loads core catalogues and sample data."""
from __future__ import annotations

from datetime import date, timedelta
from pathlib import Path
import sys
import os

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:  # pragma: no cover - script bootstrap
    sys.path.insert(0, str(PROJECT_ROOT))

try:
    from flask_bcrypt import Bcrypt  # type: ignore
except ModuleNotFoundError:  # pragma: no cover - fallback for offline envs
    from app.passwords import PasswordHasher as Bcrypt
from sqlalchemy import create_engine, delete
from sqlalchemy.orm import Session

from config import Config
from app.models.acta import Acta, ActaItem, TipoActa
from app.models.adjunto import Adjunto, TipoAdjunto
from app.models.auditoria import Auditoria
from app.models.docscan import Docscan, TipoDocscan
from app.models.equipo import Equipo, EquipoHistorial, EstadoEquipo, TipoEquipo
from app.models.hospital import Hospital, Oficina, Servicio
from app.models.insumo import Insumo, InsumoMovimiento, MovimientoTipo, equipo_insumos
from app.models.licencia import EstadoLicencia, Licencia, TipoLicencia
from app.models.permisos import Modulo, Permiso
from app.models.rol import Rol
from app.models.usuario import Usuario

bcrypt = Bcrypt()
DEFAULT_PASSWORD = "Cambiar123!"


def get_engine_url() -> str:
    """Return the database URL configured for the application."""

    return os.getenv("DATABASE_URL", Config.SQLALCHEMY_DATABASE_URI)


def reset_tables(session: Session) -> None:
    """Clear existing data so the seed script can be re-run safely."""

    session.execute(delete(ActaItem))
    session.execute(delete(Acta))
    session.execute(delete(Adjunto))
    session.execute(delete(Docscan))
    session.execute(delete(EquipoHistorial))
    session.execute(delete(InsumoMovimiento))
    session.execute(delete(Auditoria))
    session.execute(delete(Permiso))
    session.execute(delete(Licencia))
    session.execute(delete(equipo_insumos))
    session.execute(delete(Equipo))
    session.execute(delete(TipoEquipo))
    session.execute(delete(Insumo))
    session.execute(delete(Oficina))
    session.execute(delete(Servicio))
    session.execute(delete(Usuario))
    session.execute(delete(Rol))
    session.execute(delete(Hospital))


def create_catalogs(session: Session) -> dict[str, object]:
    """Insert hospitals, services, roles and equipment types."""

    hospitales = [
        Hospital(
            nombre="Hospital Dr. Lucio Molas",
            codigo="HLM",
            direccion="Av. Spinetto 1225, Santa Rosa",
            telefono="02954-450000",
        ),
        Hospital(
            nombre="Hospital René Favaloro",
            codigo="HRF",
            direccion="Balcarce 222, Pico",
            telefono="02302-430000",
        ),
    ]
    session.add_all(hospitales)
    session.flush()

    servicios = []
    oficinas = []
    for hospital in hospitales:
        servicio = Servicio(
            nombre="Soporte Informático",
            descripcion="Área responsable del parque informático",
            hospital=hospital,
        )
        session.add(servicio)
        session.flush()
        servicios.append(servicio)
        oficina = Oficina(
            nombre="Deposito Central",
            piso="PB",
            servicio=servicio,
            hospital=hospital,
        )
        session.add(oficina)
        oficinas.append(oficina)

    roles = [
        Rol(nombre="Superadmin", descripcion="Acceso completo"),
        Rol(nombre="Admin", descripcion="Administración por hospital"),
        Rol(nombre="Tecnico", descripcion="Gestión operativa"),
        Rol(nombre="Lectura", descripcion="Solo consulta"),
    ]
    session.add_all(roles)
    session.flush()

    tipos_equipo = create_equipment_types(session)

    return {
        "hospitales": hospitales,
        "servicios": servicios,
        "oficinas": oficinas,
        "roles": {role.nombre.lower(): role for role in roles},
        "tipos_equipo": tipos_equipo,
    }


def create_equipment_types(session: Session) -> dict[str, TipoEquipo]:
    """Insert the default equipment types expected by the application."""

    defaults = [
        ("impresora", "Impresora"),
        ("router", "Router"),
        ("switch", "Switch"),
        ("notebook", "Notebook"),
        ("cpu", "CPU"),
        ("monitor", "Monitor"),
        ("access_point", "Access Point"),
        ("scanner", "Scanner"),
        ("proyector", "Proyector"),
        ("telefono_ip", "Teléfono IP"),
        ("ups", "UPS"),
        ("otro", "Otro"),
    ]
    registros = [
        TipoEquipo(slug=slug, nombre=nombre, activo=True) for slug, nombre in defaults
    ]
    session.add_all(registros)
    session.flush()
    return {slug: registro for (slug, _), registro in zip(defaults, registros)}


def hashed_password() -> str:
    """Return a bcrypt hash for the default password."""

    return bcrypt.generate_password_hash(DEFAULT_PASSWORD).decode("utf-8")


def create_users(session: Session, ctx: dict[str, object]) -> dict[str, Usuario]:
    """Create base application users linked to their roles."""

    hospitales: list[Hospital] = ctx["hospitales"]  # type: ignore[assignment]
    roles: dict[str, Rol] = ctx["roles"]  # type: ignore[assignment]

    usuarios = {
        "superadmin": Usuario(
            username="superadmin",
            nombre="Super Administrador",
            dni="20000000",
            email="superadmin@salud.gob.ar",
            rol=roles["superadmin"],
            password_hash=hashed_password(),
        ),
        "admin_molas": Usuario(
            username="admin_molas",
            nombre="Admin Molas",
            dni="20000001",
            email="admin.molas@salud.gob.ar",
            rol=roles["admin"],
            hospital=hospitales[0],
            password_hash=hashed_password(),
        ),
        "admin_favaloro": Usuario(
            username="admin_favaloro",
            nombre="Admin Favaloro",
            dni="20000002",
            email="admin.favaloro@salud.gob.ar",
            rol=roles["admin"],
            hospital=hospitales[1],
            password_hash=hashed_password(),
        ),
        "tecnico_molas": Usuario(
            username="tecnico_molas",
            nombre="Tecnico Molas",
            dni="20000003",
            email="tecnico.molas@salud.gob.ar",
            rol=roles["tecnico"],
            hospital=hospitales[0],
            password_hash=hashed_password(),
        ),
        "tecnico_favaloro": Usuario(
            username="tecnico_favaloro",
            nombre="Tecnico Favaloro",
            dni="20000004",
            email="tecnico.favaloro@salud.gob.ar",
            rol=roles["tecnico"],
            hospital=hospitales[1],
            password_hash=hashed_password(),
        ),
        "lector": Usuario(
            username="consulta",
            nombre="Usuario Lectura",
            dni="20000005",
            email="lectura@salud.gob.ar",
            rol=roles["lectura"],
            hospital=hospitales[0],
            password_hash=hashed_password(),
        ),
    }
    session.add_all(usuarios.values())
    session.flush()
    return usuarios


def create_permissions(session: Session, ctx: dict[str, object]) -> None:
    """Generate role/hospital permissions reflecting the documented matrix."""

    roles: dict[str, Rol] = ctx["roles"]  # type: ignore[assignment]
    hospitales: list[Hospital] = ctx["hospitales"]  # type: ignore[assignment]

    permisos: list[Permiso] = []

    for modulo in Modulo:
        permisos.append(
            Permiso(
                rol=roles["superadmin"],
                modulo=modulo,
                hospital=None,
                can_read=True,
                can_write=True,
                allow_export=True,
            )
        )

    admin_modules = [
        Modulo.INVENTARIO,
        Modulo.INSUMOS,
        Modulo.ACTAS,
        Modulo.ADJUNTOS,
        Modulo.LICENCIAS,
        Modulo.DOCSCAN,
        Modulo.REPORTES,
    ]
    for hospital in hospitales:
        for modulo in admin_modules:
            permisos.append(
                Permiso(
                    rol=roles["admin"],
                    modulo=modulo,
                    hospital=hospital,
                    can_read=True,
                    can_write=True,
                    allow_export=modulo in {Modulo.REPORTES},
                )
            )
        permisos.append(
            Permiso(
                rol=roles["tecnico"],
                modulo=Modulo.INVENTARIO,
                hospital=hospital,
                can_read=True,
                can_write=True,
            )
        )
        permisos.append(
            Permiso(
                rol=roles["tecnico"],
                modulo=Modulo.ADJUNTOS,
                hospital=hospital,
                can_read=True,
                can_write=True,
            )
        )
        permisos.append(
            Permiso(
                rol=roles["tecnico"],
                modulo=Modulo.INSUMOS,
                hospital=hospital,
                can_read=True,
                can_write=False,
            )
        )
        permisos.append(
            Permiso(
                rol=roles["lectura"],
                modulo=Modulo.INVENTARIO,
                hospital=hospital,
                can_read=True,
                can_write=False,
            )
        )

    session.add_all(permisos)


def create_inventory(session: Session, ctx: dict[str, object], usuarios: dict[str, Usuario]) -> dict[str, object]:
    """Populate sample inventory (equipos e insumos)."""

    hospitales: list[Hospital] = ctx["hospitales"]  # type: ignore[assignment]
    servicios: list[Servicio] = ctx["servicios"]  # type: ignore[assignment]
    oficinas: list[Oficina] = ctx["oficinas"]  # type: ignore[assignment]
    tipos_equipo: dict[str, TipoEquipo] = ctx["tipos_equipo"]  # type: ignore[assignment]

    equipos = [
        Equipo(
            codigo="EQ-0001",
            tipo=tipos_equipo["notebook"],
            estado=EstadoEquipo.OPERATIVO,
            descripcion="Notebook Lenovo ThinkPad",
            marca="Lenovo",
            modelo="T14",
            numero_serie="NB-0001",
            hospital=hospitales[0],
            servicio=servicios[0],
            oficina=oficinas[0],
        ),
        Equipo(
            codigo="EQ-0002",
            tipo=tipos_equipo["impresora"],
            estado=EstadoEquipo.SERVICIO_TECNICO,
            descripcion="Impresora HP LaserJet en revisión",
            marca="HP",
            modelo="M404",
            numero_serie="PR-0042",
            hospital=hospitales[1],
            servicio=servicios[1],
            oficina=oficinas[1],
        ),
    ]
    session.add_all(equipos)
    session.flush()

    equipos[0].registrar_evento(usuarios["admin_molas"], "Alta", "Carga inicial de inventario")
    equipos[1].registrar_evento(usuarios["admin_favaloro"], "Alta", "Carga inicial de inventario")

    insumos = [
        Insumo(
            nombre="Tóner 85A",
            numero_serie="TN-85A",
            descripcion="Tóner negro para impresoras HP",
            unidad_medida="unidad",
            stock=12,
            stock_minimo=3,
            costo_unitario=85.50,
        ),
        Insumo(
            nombre="Cable de red CAT6",
            numero_serie="CB-100",
            descripcion="Cable UTP de 3 metros",
            unidad_medida="unidad",
            stock=30,
            stock_minimo=10,
            costo_unitario=6.75,
        ),
    ]
    session.add_all(insumos)
    session.flush()

    equipos[0].insumos.append(insumos[1])
    equipos[1].insumos.append(insumos[0])

    movimiento = InsumoMovimiento(
        insumo=insumos[0],
        usuario=usuarios["tecnico_favaloro"],
        tipo=MovimientoTipo.EGRESO,
        cantidad=2,
        motivo="Entrega a servicio técnico",
    )
    insumos[0].ajustar_stock(-2)
    session.add(movimiento)

    return {"equipos": equipos, "insumos": insumos}


def create_licenses(session: Session, usuarios: dict[str, Usuario], hospitales: list[Hospital]) -> None:
    """Create sample licenses to exercise workflow states."""

    licencias = [
        Licencia(
            usuario=usuarios["admin_molas"],
            hospital=hospitales[0],
            tipo=TipoLicencia.VACACIONES,
            estado=EstadoLicencia.APROBADA,
            fecha_inicio=date.today() - timedelta(days=15),
            fecha_fin=date.today() + timedelta(days=5),
            motivo="Vacaciones programadas",
        ),
        Licencia(
            usuario=usuarios["tecnico_favaloro"],
            hospital=hospitales[1],
            tipo=TipoLicencia.ENFERMEDAD,
            estado=EstadoLicencia.SOLICITADA,
            fecha_inicio=date.today() + timedelta(days=7),
            fecha_fin=date.today() + timedelta(days=12),
            motivo="Licencia médica",
        ),
        Licencia(
            usuario=usuarios["tecnico_molas"],
            hospital=hospitales[0],
            tipo=TipoLicencia.ESTUDIO,
            estado=EstadoLicencia.CANCELADA,
            fecha_inicio=date.today() + timedelta(days=30),
            fecha_fin=date.today() + timedelta(days=35),
            motivo="Capacitación externa",
        ),
    ]

    session.add_all(licencias)


def create_supporting_records(session: Session, ctx: dict[str, object], usuarios: dict[str, Usuario], inventory: dict[str, object]) -> None:
    """Create actas, adjuntos, docscan and audit trail entries."""

    hospitales: list[Hospital] = ctx["hospitales"]  # type: ignore[assignment]
    equipos: list[Equipo] = inventory["equipos"]  # type: ignore[assignment]

    acta = Acta(
        tipo=TipoActa.ENTREGA,
        hospital=hospitales[0],
        usuario=usuarios["admin_molas"],
        observaciones="Entrega inicial de equipamiento para el área administrativa.",
    )
    acta.items.append(
        ActaItem(
            equipo=equipos[0],
            cantidad=1,
            descripcion="Notebook asignada al sector administrativo",
        )
    )
    session.add(acta)

    adjunto = Adjunto(
        equipo=equipos[0],
        filename="factura_notebook.pdf",
        path="uploads/adjuntos/factura_notebook.pdf",
        tipo=TipoAdjunto.FACTURA,
        descripcion="Factura de compra",
        uploaded_by=usuarios["admin_molas"],
    )
    session.add(adjunto)

    documento = Docscan(
        titulo="Nota de pedido",
        tipo=TipoDocscan.NOTA,
        filename="nota_pedido.pdf",
        path="uploads/docscan/nota_pedido.pdf",
        comentario="Solicitud firmada por dirección",
        usuario=usuarios["superadmin"],
        hospital=hospitales[0],
    )
    session.add(documento)

    auditoria = Auditoria(
        usuario_id=usuarios["superadmin"].id,
        accion="seed",
        modulo="setup",
        tabla="usuarios",
        registro_id=usuarios["superadmin"].id,
        datos="{'detalle': 'Carga inicial de datos'}",
    )
    session.add(auditoria)


def seed() -> None:
    """Execute the full seed workflow."""

    engine = create_engine(get_engine_url(), future=True)
    with Session(engine) as session:
        with session.begin():
            reset_tables(session)
        with session.begin():
            ctx = create_catalogs(session)
            usuarios = create_users(session, ctx)
            create_permissions(session, ctx)
            inventory = create_inventory(session, ctx, usuarios)
            create_supporting_records(session, ctx, usuarios, inventory)
            create_licenses(session, usuarios, ctx["hospitales"])  # type: ignore[arg-type]

    engine.dispose()
    print("Base de datos poblada con datos iniciales. Usuarios por defecto: superadmin/admin_molas/etc. Contraseña: Cambiar123!")


if __name__ == "__main__":
    seed()
