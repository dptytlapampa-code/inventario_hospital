"""License workflow tests."""
from __future__ import annotations

from datetime import date, timedelta

import pytest

from app.models import EstadoLicencia, Licencia, TipoLicencia, Usuario, Hospital
from app.services.licencia_service import (
    aprobar_licencia,
    cancelar_licencia,
    crear_licencia,
    enviar_licencia,
    licencias_superpuestas,
)


def test_crear_y_enviar_licencia(app, data):
    usuario_id = data["admin"].id
    hospital_id = data["hospital"].id

    with app.app_context():
        usuario = Usuario.query.get(usuario_id)
        hospital = Hospital.query.get(hospital_id)
        assert usuario is not None and hospital is not None
        licencia = crear_licencia(
            usuario=usuario,
            hospital_id=hospital.id,
            tipo=TipoLicencia.TEMPORAL,
            fecha_inicio=date.today() + timedelta(days=3),
            fecha_fin=date.today() + timedelta(days=6),
            motivo="Trámite",
            comentario=None,
            requires_replacement=False,
            reemplazo_id=None,
        )
        enviar_licencia(licencia)
        assert licencia.estado == EstadoLicencia.PENDIENTE


def test_aprobar_licencia_valida_superposicion(app, data):
    usuario_id = data["admin"].id
    hospital_id = data["hospital"].id
    superadmin_id = data["superadmin"].id

    with app.app_context():
        usuario = Usuario.query.get(usuario_id)
        hospital = Hospital.query.get(hospital_id)
        superadmin = Usuario.query.get(superadmin_id)
        assert usuario is not None and hospital is not None and superadmin is not None
        licencia = crear_licencia(
            usuario=usuario,
            hospital_id=hospital.id,
            tipo=TipoLicencia.TEMPORAL,
            fecha_inicio=date.today() + timedelta(days=10),
            fecha_fin=date.today() + timedelta(days=12),
            motivo="Capacitación",
            comentario=None,
            requires_replacement=False,
            reemplazo_id=None,
        )
        enviar_licencia(licencia)
        aprobar_licencia(licencia, superadmin)

        overlaps = licencias_superpuestas(
            usuario.id,
            licencia.fecha_inicio,
            licencia.fecha_fin,
        )
        assert overlaps == [licencia]

        with pytest.raises(ValueError):
            otra = crear_licencia(
                usuario=usuario,
                hospital_id=hospital.id,
                tipo=TipoLicencia.TEMPORAL,
                fecha_inicio=licencia.fecha_inicio,
                fecha_fin=licencia.fecha_fin,
                motivo="Duplicado",
                comentario=None,
                requires_replacement=False,
                reemplazo_id=None,
            )
            enviar_licencia(otra)
            aprobar_licencia(otra, superadmin)


def test_cancelar_licencia(app, data):
    licencia_id = data["licencia"].id
    admin_id = data["admin"].id

    with app.app_context():
        licencia = Licencia.query.get(licencia_id)
        admin = Usuario.query.get(admin_id)
        assert licencia is not None and admin is not None
        cancelar_licencia(licencia, admin)
        assert licencia.estado == EstadoLicencia.CANCELADA
