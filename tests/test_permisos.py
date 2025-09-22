"""Tests for permission scoping."""
from __future__ import annotations

from app.models import Modulo, Usuario


def test_superadmin_tiene_acceso_global(app, data):
    superadmin_id = data["superadmin"].id

    with app.app_context():
        superadmin = Usuario.query.get(superadmin_id)
        assert superadmin is not None
        hospitales = superadmin.allowed_hospital_ids(Modulo.INVENTARIO.value)
        assert hospitales == set()


def test_admin_limitado_a_su_hospital(app, data):
    admin_id = data["admin"].id
    hospital_id = data["hospital"].id

    with app.app_context():
        admin = Usuario.query.get(admin_id)
        assert admin is not None
        hospitales = admin.allowed_hospital_ids(Modulo.INVENTARIO.value)
        assert hospitales == {hospital_id}
