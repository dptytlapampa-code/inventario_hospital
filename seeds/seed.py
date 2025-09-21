"""Database seed script that loads core catalogues and sample data."""
from __future__ import annotations

import os

from sqlalchemy import create_engine, delete
from sqlalchemy.orm import Session

from config import Config
from app.models.acta import Acta, ActaItem, TipoActa
from app.models.adjunto import Adjunto, TipoAdjunto
from app.models.auditoria import Auditoria
from app.models.equipo import Equipo, EstadoEquipo, TipoEquipo
from app.models.hospital import Hospital
from app.models.insumo import Insumo, equipo_insumos
from app.models.licencia import EstadoLicencia, Licencia, TipoLicencia
from app.models.permisos import Modulo, Permiso
from app.models.rol import Rol
from app.models.usuario import Usuario


def get_engine_url() -> str:
    """Return the database URL configured for the application."""

    return os.getenv("DATABASE_URL", Config.SQLALCHEMY_DATABASE_URI)


def reset_tables(session: Session) -> None:
    """Clear existing data so the seed script can be re-run safely."""

    # Delete child tables first to avoid foreign key violations.
    session.execute(delete(ActaItem))
    session.execute(delete(Acta))
    session.execute(delete(Adjunto))
    session.execute(delete(Auditoria))
    session.execute(delete(Permiso))
    session.execute(delete(Licencia))
    session.execute(delete(equipo_insumos))
    session.execute(delete(Equipo))
    session.execute(delete(Insumo))
    session.execute(delete(Usuario))
    session.execute(delete(Rol))
    session.execute(delete(Hospital))


def create_catalogs(session: Session) -> dict[str, object]:
    """Insert hospitals, roles and core catalogues."""

    hospitales = [
        Hospital(nombre="Hospital Dr. Lucio Molas"),
        Hospital(nombre="Hospital René Favaloro"),
    ]
    roles = [
        Rol(nombre="Superadmin"),
        Rol(nombre="Admin"),
        Rol(nombre="Tecnico"),
    ]
    session.add_all(hospitales + roles)
    session.flush()

    return {
        "hospitales": hospitales,
        "roles": {role.nombre.lower(): role for role in roles},
    }


def create_users(session: Session, roles: dict[str, Rol]) -> dict[str, Usuario]:
    """Create base application users linked to their roles."""

    usuarios = {
        "superadmin": Usuario(
            nombre="Super Administrador",
            email="superadmin@salud.gob.ar",
            rol=roles["superadmin"],
        ),
        "admin_molas": Usuario(
            nombre="Admin Molas",
            email="admin.molas@salud.gob.ar",
            rol=roles["admin"],
        ),
        "admin_favaloro": Usuario(
            nombre="Admin Favaloro",
            email="admin.favaloro@salud.gob.ar",
            rol=roles["admin"],
        ),
        "tecnico_molas": Usuario(
            nombre="Tecnico Molas",
            email="tecnico.molas@salud.gob.ar",
            rol=roles["tecnico"],
        ),
        "tecnico_favaloro": Usuario(
            nombre="Tecnico Favaloro",
            email="tecnico.favaloro@salud.gob.ar",
            rol=roles["tecnico"],
        ),
    }
    session.add_all(usuarios.values())
    session.flush()
    return usuarios


def create_permissions(session: Session, roles: dict[str, Rol], hospitales: list[Hospital]) -> None:
    """Generate role/hospital permissions reflecting the documented matrix."""

    permisos: list[Permiso] = []

    # Superadmin has full access across all modules without restricting to a hospital.
    for modulo in Modulo:
        permisos.append(
            Permiso(
                rol=roles["superadmin"],
                modulo=modulo,
                hospital=None,
                can_read=True,
                can_write=True,
            )
        )

    # Admin role: full management but scoped per hospital.
    admin_modules = [
        Modulo.INVENTARIO,
        Modulo.INSUMOS,
        Modulo.ACTAS,
        Modulo.ADJUNTOS,
        Modulo.LICENCIAS,
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
                )
            )

    # Técnicos: operación diaria con permisos de lectura y carga básica.
    tecnico_modules = [Modulo.INVENTARIO, Modulo.INSUMOS, Modulo.ADJUNTOS, Modulo.DOCSCAN]
    for hospital in hospitales:
        for modulo in tecnico_modules:
            permisos.append(
                Permiso(
                    rol=roles["tecnico"],
                    modulo=modulo,
                    hospital=hospital,
                    can_read=True,
                    can_write=modulo in {Modulo.INVENTARIO, Modulo.ADJUNTOS},
                )
            )

    session.add_all(permisos)


def create_inventory(session: Session, hospitales: list[Hospital]) -> dict[str, object]:
    """Populate sample inventory (equipos e insumos)."""

    equipos = [
        Equipo(
            tipo=TipoEquipo.NOTEBOOK,
            estado=EstadoEquipo.OPERATIVO,
            descripcion="Notebook Lenovo ThinkPad",
            numero_serie="NB-0001",
            hospital=hospitales[0],
        ),
        Equipo(
            tipo=TipoEquipo.IMPRESORA,
            estado=EstadoEquipo.SERVICIO_TECNICO,
            descripcion="Impresora HP LaserJet en revisión",
            numero_serie="PR-042",
            hospital=hospitales[1],
        ),
    ]

    insumos = [
        Insumo(nombre="Tóner 85A", numero_serie="TN-85A", stock=12),
        Insumo(nombre="Cable de red CAT6", numero_serie="CB-100", stock=30),
    ]
    session.add_all(equipos + insumos)
    session.flush()

    # Asociar insumos a los equipos.
    equipos[0].insumos.append(insumos[1])  # Notebook con cable de red de repuesto.
    equipos[1].insumos.append(insumos[0])  # Impresora con tóner asignado.

    # Generar un acta de entrega vinculada al equipo operativo.
    acta = Acta(tipo=TipoActa.ENTREGA, usuario_id=None, hospital=hospitales[0])
    acta.items.append(
        ActaItem(
            equipo=equipos[0],
            descripcion="Entrega de notebook operativa para el área administrativa.",
        )
    )
    session.add(acta)

    # Documentos de respaldo y auditoría básica.
    adjunto = Adjunto(
        equipo=equipos[0],
        filename="factura_notebook.pdf",
        tipo=TipoAdjunto.FACTURA,
    )
    auditoria = Auditoria(
        usuario_id=None,
        accion="Carga inicial de inventario",
        tabla="equipos",
        registro_id=equipos[0].id,
    )
    session.add_all([adjunto, auditoria])

    return {"equipos": equipos, "insumos": insumos}


def create_licenses(session: Session, usuarios: dict[str, Usuario], hospitales: list[Hospital]) -> None:
    """Create sample licenses to exercise workflow states."""

    licencias = [
        Licencia(
            usuario=usuarios["admin_molas"],
            hospital=hospitales[0],
            tipo=TipoLicencia.PERMANENTE,
            estado=EstadoLicencia.APROBADA,
            requires_replacement=False,
        ),
        Licencia(
            usuario=usuarios["tecnico_favaloro"],
            hospital=hospitales[1],
            tipo=TipoLicencia.TEMPORAL,
            estado=EstadoLicencia.PENDIENTE,
            requires_replacement=True,
        ),
        Licencia(
            usuario=usuarios["tecnico_molas"],
            hospital=hospitales[0],
            tipo=TipoLicencia.TEMPORAL,
            estado=EstadoLicencia.BORRADOR,
            requires_replacement=False,
        ),
    ]

    session.add_all(licencias)


def seed() -> None:
    """Execute the full seed workflow."""

    engine = create_engine(get_engine_url(), future=True)
    with Session(engine) as session:
        with session.begin():
            reset_tables(session)
        with session.begin():
            context = create_catalogs(session)
            usuarios = create_users(session, context["roles"])
            create_permissions(session, context["roles"], context["hospitales"])
            create_inventory(session, context["hospitales"])
            create_licenses(session, usuarios, context["hospitales"])

    engine.dispose()
    print("Base de datos poblada con datos iniciales.")


if __name__ == "__main__":
    seed()
