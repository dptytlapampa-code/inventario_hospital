"""Shared fixtures for the test suite."""
from __future__ import annotations

from datetime import date, timedelta
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:  # pragma: no cover - test helper
    sys.path.insert(0, str(PROJECT_ROOT))

import pytest

from app import create_app
from app.extensions import db
from app.models import (
    Acta,
    ActaItem,
    Equipo,
    EstadoEquipo,
    Hospital,
    Insumo,
    Licencia,
    Modulo,
    MovimientoTipo,
    Oficina,
    Permiso,
    Rol,
    Servicio,
    TipoActa,
    TipoEquipo,
    TipoLicencia,
    Usuario,
)
from app.services import insumo_service
from app.services.licencia_service import crear_licencia, enviar_licencia
from config import TestingConfig

DEFAULT_PASSWORD = "Cambiar123!"


def _populate_database() -> dict[str, object]:
    hospital = Hospital(nombre="Hospital Central", codigo="HCN")
    db.session.add(hospital)
    db.session.flush()

    rol_super = Rol(nombre="superadmin")
    rol_admin = Rol(nombre="admin")
    rol_gestor = Rol(nombre="gestor")
    rol_visor = Rol(nombre="visor")
    db.session.add_all([rol_super, rol_admin, rol_gestor, rol_visor])
    db.session.flush()

    superadmin = Usuario(
        username="superadmin",
        nombre="Super",
        apellido="Admin",
        email="super@hospital.test",
        rol=rol_super,
        hospital=hospital,
    )
    superadmin.set_password(DEFAULT_PASSWORD)

    admin = Usuario(
        username="admin",
        nombre="Ana",
        apellido="Gestión",
        email="admin@hospital.test",
        rol=rol_admin,
        hospital=hospital,
    )
    admin.set_password(DEFAULT_PASSWORD)

    gestor = Usuario(
        username="gestor",
        nombre="Gesto",
        apellido="Operativo",
        email="gestor@hospital.test",
        rol=rol_gestor,
        hospital=hospital,
    )
    gestor.set_password(DEFAULT_PASSWORD)

    visor = Usuario(
        username="visor",
        nombre="Violeta",
        apellido="Consulta",
        email="visor@hospital.test",
        rol=rol_visor,
        hospital=hospital,
    )
    visor.set_password(DEFAULT_PASSWORD)

    db.session.add_all([superadmin, admin, gestor, visor])
    db.session.flush()

    permisos = [
        Permiso(rol=rol_super, modulo=modulo, can_read=True, can_write=True)
        for modulo in Modulo
    ]
    permisos.append(
        Permiso(
            rol=rol_admin,
            modulo=Modulo.INVENTARIO,
            hospital=hospital,
            can_read=True,
            can_write=True,
        )
    )
    permisos.append(
        Permiso(
            rol=rol_admin,
            modulo=Modulo.LICENCIAS,
            hospital=hospital,
            can_read=True,
            can_write=True,
        )
    )
    permisos.append(
        Permiso(
            rol=rol_gestor,
            modulo=Modulo.INSUMOS,
            hospital=hospital,
            can_read=True,
            can_write=True,
        )
    )
    db.session.add_all(permisos)

    servicio = Servicio(nombre="Emergencias", hospital=hospital)
    db.session.add(servicio)
    db.session.flush()

    oficina = Oficina(nombre="Oficina Principal", servicio=servicio, hospital=hospital)
    db.session.add(oficina)

    equipo = Equipo(
        codigo="EQ-100",
        tipo=TipoEquipo.NOTEBOOK,
        estado=EstadoEquipo.OPERATIVO,
        descripcion="Notebook de prueba",
        hospital=hospital,
    )
    db.session.add(equipo)

    insumo = Insumo(nombre="Mouse óptico", stock=15, stock_minimo=5)
    db.session.add(insumo)
    db.session.flush()

    insumo_service.registrar_movimiento(
        insumo=insumo,
        tipo=MovimientoTipo.EGRESO,
        cantidad=1,
        usuario=superadmin,
        equipo_id=None,
        motivo="Entrega inicial",
        observaciones=None,
    )

    acta = Acta(
        tipo=TipoActa.ENTREGA,
        hospital=hospital,
        usuario=admin,
        observaciones="Entrega de equipo",
    )
    acta.items.append(ActaItem(equipo=equipo, cantidad=1))
    db.session.add(acta)

    licencia = crear_licencia(
        usuario=admin,
        hospital_id=hospital.id,
        tipo=TipoLicencia.VACACIONES,
        fecha_inicio=date.today() + timedelta(days=1),
        fecha_fin=date.today() + timedelta(days=5),
        motivo="Trámite personal",
    )
    enviar_licencia(licencia)

    db.session.commit()
    return {
        "hospital": hospital,
        "superadmin": superadmin,
        "admin": admin,
        "gestor": gestor,
        "visor": visor,
        "servicio": servicio,
        "oficina": oficina,
        "equipo": equipo,
        "insumo": insumo,
        "acta": acta,
        "licencia": licencia,
    }


@pytest.fixture()
def app():
    app = create_app(TestingConfig)
    with app.app_context():
        db.create_all()
        context = _populate_database()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture()
def client(app):
    return app.test_client()


@pytest.fixture()
def data(app):
    """Return seeded objects for direct access in tests."""

    with app.app_context():
        return {
            "hospital": Hospital.query.first(),
            "superadmin": Usuario.query.filter_by(username="superadmin").first(),
            "admin": Usuario.query.filter_by(username="admin").first(),
            "gestor": Usuario.query.filter_by(username="gestor").first(),
            "visor": Usuario.query.filter_by(username="visor").first(),
            "equipo": Equipo.query.first(),
            "insumo": Insumo.query.first(),
            "acta": Acta.query.first(),
            "licencia": Licencia.query.first(),
            "servicio": Servicio.query.first(),
            "oficina": Oficina.query.first(),
        }


@pytest.fixture()
def superadmin_credentials():
    return {"username": "superadmin", "password": DEFAULT_PASSWORD}


@pytest.fixture()
def admin_credentials():
    return {"username": "admin", "password": DEFAULT_PASSWORD}


@pytest.fixture()
def gestor_credentials():
    return {"username": "gestor", "password": DEFAULT_PASSWORD}


@pytest.fixture()
def visor_credentials():
    return {"username": "visor", "password": DEFAULT_PASSWORD}

