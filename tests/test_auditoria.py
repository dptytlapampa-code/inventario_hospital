"""Audit logging tests."""
from __future__ import annotations

from app.models import Auditoria
from app.services.audit_service import log_action


def test_log_action_crea_registro(app, data):
    with app.app_context():
        entry = log_action(
            usuario_id=data["superadmin"].id,
            accion="prueba",
            modulo="tests",
            tabla="tabla_demo",
            registro_id=1,
            datos={"detalle": "ok"},
        )
        assert entry.id is not None
        stored = Auditoria.query.get(entry.id)
        assert stored is not None
        assert stored.accion == "prueba"
