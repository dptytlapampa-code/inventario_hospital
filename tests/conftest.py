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
    Vlan,
    VlanDispositivo,
)
from app.services import insumo_service
from app.services.licencia_service import crear_licencia, enviar_licencia
from config import TestingConfig

DEFAULT_PASSWORD = "Cambiar123!"


def _populate_database() -> dict[str, object]:
    hospital = Hospital(
        nombre="Hospital Central",
        tipo_institucion="Hospital",
        codigo="HCN",
        localidad="Santa Rosa",
        provincia="La Pampa",
        estado="Activa",
    )
    db.session.add(hospital)
    db.session.flush()

    second_hospital = Hospital(
        nombre="Hospital Regional",
        tipo_institucion="Hospital",
        codigo="HRG",
        localidad="General Pico",
        provincia="La Pampa",
        estado="Activa",
    )
    db.session.add(second_hospital)
    db.session.flush()

    rol_super = Rol(nombre="superadmin")
    rol_admin = Rol(nombre="admin")
    rol_gestor = Rol(nombre="gestor")
    rol_visor = Rol(nombre="visor")
    rol_tecnico = Rol(nombre="tecnico")
    db.session.add_all([rol_super, rol_admin, rol_gestor, rol_visor, rol_tecnico])
    db.session.flush()

    superadmin = Usuario(
        username="superadmin",
        nombre="Super",
        apellido="Admin",
        dni="30000000",
        email="super@hospital.test",
        rol=rol_super,
        hospital=hospital,
    )
    superadmin.set_password(DEFAULT_PASSWORD)

    admin = Usuario(
        username="admin",
        nombre="Ana",
        apellido="Gestión",
        dni="30000001",
        email="admin@hospital.test",
        rol=rol_admin,
        hospital=hospital,
    )
    admin.set_password(DEFAULT_PASSWORD)

    gestor = Usuario(
        username="gestor",
        nombre="Gesto",
        apellido="Operativo",
        dni="30000002",
        email="gestor@hospital.test",
        rol=rol_gestor,
        hospital=hospital,
    )
    gestor.set_password(DEFAULT_PASSWORD)

    visor = Usuario(
        username="visor",
        nombre="Violeta",
        apellido="Consulta",
        dni="30000003",
        email="visor@hospital.test",
        rol=rol_visor,
        hospital=hospital,
    )
    visor.set_password(DEFAULT_PASSWORD)

    tecnico = Usuario(
        username="tecnico",
        nombre="Teresita",
        apellido="Tecnica",
        dni="30000004",
        email="tecnico@hospital.test",
        rol=rol_tecnico,
        hospital=hospital,
    )
    tecnico.set_password(DEFAULT_PASSWORD)

    db.session.add_all([superadmin, admin, gestor, visor, tecnico])
    db.session.flush()

    tipo_notebook = TipoEquipo(nombre="Notebook", activo=True)
    tipo_impresora = TipoEquipo(nombre="Impresora", activo=True)
    tipo_router = TipoEquipo(nombre="Router", activo=True)
    db.session.add_all([tipo_notebook, tipo_impresora, tipo_router])
    db.session.flush()

    permisos = [
        Permiso(
            rol=rol_super,
            modulo=modulo,
            can_read=True,
            can_write=True,
            allow_export=True,
        )
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
    permisos.append(
        Permiso(
            rol=rol_tecnico,
            modulo=Modulo.INVENTARIO,
            hospital=hospital,
            can_read=True,
            can_write=True,
        )
    )
    permisos.append(
        Permiso(
            rol=rol_tecnico,
            modulo=Modulo.ADJUNTOS,
            hospital=hospital,
            can_read=True,
            can_write=True,
        )
    )
    permisos.append(
        Permiso(
            rol=rol_tecnico,
            modulo=Modulo.INSUMOS,
            hospital=hospital,
            can_read=True,
            can_write=False,
        )
    )
    db.session.add_all(permisos)

    servicio = Servicio(nombre="Emergencias", hospital=hospital)
    db.session.add(servicio)
    db.session.flush()

    oficina = Oficina(nombre="Oficina Principal", servicio=servicio, hospital=hospital)
    db.session.add(oficina)

    secondary_service = Servicio(nombre="Diagnóstico", hospital=second_hospital)
    db.session.add(secondary_service)
    db.session.flush()

    secondary_office = Oficina(
        nombre="Oficina Regional",
        servicio=secondary_service,
        hospital=second_hospital,
    )
    db.session.add(secondary_office)

    equipo = Equipo(
        codigo="EQ-100",
        tipo=tipo_notebook,
        estado=EstadoEquipo.OPERATIVO,
        descripcion="Notebook Lenovo",
        marca="Lenovo",
        modelo="ThinkPad",
        numero_serie="SN-001",
        hospital=hospital,
        servicio=servicio,
        oficina=oficina,
    )
    db.session.add(equipo)

    printer_central = Equipo(
        codigo="EQ-200",
        tipo=tipo_impresora,
        estado=EstadoEquipo.OPERATIVO,
        descripcion="Impresora HP Central",
        marca="HP",
        modelo="LaserJet",
        numero_serie="IMP-001",
        hospital=hospital,
        servicio=servicio,
        oficina=oficina,
    )
    db.session.add(printer_central)

    printer_regional = Equipo(
        codigo="EQ-300",
        tipo=tipo_impresora,
        estado=EstadoEquipo.OPERATIVO,
        descripcion="Impresora HP Regional",
        marca="HP",
        modelo="LaserJet",
        numero_serie="IMP-002",
        hospital=second_hospital,
        servicio=secondary_service,
        oficina=secondary_office,
    )
    db.session.add(printer_regional)

    vlan_central = Vlan(
        nombre="Administración",
        identificador="10",
        hospital=hospital,
        servicio=servicio,
        oficina=oficina,
    )
    db.session.add(vlan_central)

    vlan_regional = Vlan(
        nombre="Soporte",
        identificador="20",
        hospital=second_hospital,
        servicio=secondary_service,
        oficina=secondary_office,
    )
    db.session.add(vlan_regional)

    dispositivo_central = VlanDispositivo(
        vlan=vlan_central,
        nombre_equipo="Servidor Central",
        host="srv-central",
        direccion_ip="10.0.0.10",
        direccion_mac="AA:BB:CC:DD:EE:FF",
        hospital=hospital,
        servicio=servicio,
        oficina=oficina,
    )
    db.session.add(dispositivo_central)

    dispositivo_regional = VlanDispositivo(
        vlan=vlan_regional,
        nombre_equipo="Servidor Regional",
        host="srv-regional",
        direccion_ip="10.1.0.10",
        direccion_mac="11:22:33:44:55:66",
        hospital=second_hospital,
        servicio=secondary_service,
        oficina=secondary_office,
    )
    db.session.add(dispositivo_regional)

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
        "hospital_secundario": second_hospital,
        "superadmin": superadmin,
        "admin": admin,
        "gestor": gestor,
        "visor": visor,
        "tecnico": tecnico,
        "servicio": servicio,
        "oficina": oficina,
        "servicio_secundario": secondary_service,
        "oficina_secundaria": secondary_office,
        "equipo": equipo,
        "equipo_impresora": printer_central,
        "equipo_impresora_regional": printer_regional,
        "insumo": insumo,
        "acta": acta,
        "tipos_equipo": {
            "notebook": tipo_notebook,
            "impresora": tipo_impresora,
            "router": tipo_router,
        },
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
            "hospital": Hospital.query.filter_by(codigo="HCN").first(),
            "hospital_secundario": Hospital.query.filter_by(codigo="HRG").first(),
            "superadmin": Usuario.query.filter_by(username="superadmin").first(),
            "admin": Usuario.query.filter_by(username="admin").first(),
            "gestor": Usuario.query.filter_by(username="gestor").first(),
            "visor": Usuario.query.filter_by(username="visor").first(),
            "tecnico": Usuario.query.filter_by(username="tecnico").first(),
            "equipo": Equipo.query.filter_by(numero_serie="SN-001").first(),
            "equipo_impresora": Equipo.query.filter_by(numero_serie="IMP-001").first(),
            "equipo_impresora_regional": Equipo.query.filter_by(numero_serie="IMP-002").first(),
            "insumo": Insumo.query.first(),
            "acta": Acta.query.first(),
            "licencia": Licencia.query.first(),
            "servicio": Servicio.query.filter_by(nombre="Emergencias").first(),
            "servicio_secundario": Servicio.query.filter_by(nombre="Diagnóstico").first(),
            "oficina": Oficina.query.filter_by(nombre="Oficina Principal").first(),
            "oficina_secundaria": Oficina.query.filter_by(nombre="Oficina Regional").first(),
            "tipos_equipo": {
                "notebook": TipoEquipo.query.filter_by(nombre="Notebook").first(),
                "impresora": TipoEquipo.query.filter_by(nombre="Impresora").first(),
                "router": TipoEquipo.query.filter_by(nombre="Router").first(),
            },
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


@pytest.fixture()
def tecnico_credentials():
    return {"username": "tecnico", "password": DEFAULT_PASSWORD}

