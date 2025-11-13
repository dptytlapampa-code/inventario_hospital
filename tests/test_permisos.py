"""Tests for permission scoping."""
from __future__ import annotations

from app.models import Modulo, Permiso, Usuario


def test_modulo_enum_accepts_case_insensitive_values() -> None:
    assert Modulo("INVENTARIO") is Modulo.INVENTARIO
    assert Modulo("equipos") is Modulo.EQUIPOS
    assert Modulo("VLANS") is Modulo.VLANS


def login(client, username: str, password: str) -> None:
    client.post(
        "/auth/login",
        data={"username": username, "password": password},
        follow_redirects=False,
    )


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


def test_tecnico_limitado_a_su_hospital(app, data):
    tecnico_id = data["tecnico"].id
    hospital_id = data["hospital"].id

    with app.app_context():
        tecnico = Usuario.query.get(tecnico_id)
        assert tecnico is not None
        hospitales = tecnico.allowed_hospital_ids(Modulo.INVENTARIO.value)
        assert hospitales == {hospital_id}


def test_guardar_permisos_usuario_superadmin(client, superadmin_credentials, data, app):
    login(client, **superadmin_credentials)
    admin = data["admin"]
    payload = {
        "hospitals": [0],
        "modules": {
            Modulo.INVENTARIO.value: {"can_read": True, "can_write": True, "allow_export": True},
            Modulo.INSUMOS.value: {"can_read": True, "can_write": False, "allow_export": False},
        },
    }
    resp = client.post(f"/permisos/usuarios/{admin.id}/guardar", json=payload)
    assert resp.status_code == 200
    data_resp = resp.get_json()
    assert data_resp["status"] == "ok"
    assert data_resp["payload"]["modules"][Modulo.INVENTARIO.value]["can_read"] is True
    with app.app_context():
        refreshed = Usuario.query.get(admin.id)
        assert refreshed is not None
        perms = Permiso.query.filter_by(rol_id=refreshed.rol_id, modulo=Modulo.INVENTARIO).all()
        assert any(p.hospital_id is None and p.can_read for p in perms)
        assert any(p.hospital_id is None and p.allow_export for p in perms)


def test_guardar_permisos_usuario_requiere_superadmin(client, admin_credentials, data):
    login(client, **admin_credentials)
    target = data["gestor"]
    resp = client.post(
        f"/permisos/usuarios/{target.id}/guardar",
        json={"hospitals": [0], "modules": {}},
    )
    assert resp.status_code == 403


def test_tecnico_no_puede_guardar_permisos(client, tecnico_credentials, data):
    login(client, **tecnico_credentials)
    target = data["gestor"]
    resp = client.post(
        f"/permisos/usuarios/{target.id}/guardar",
        json={"hospitals": [0], "modules": {}},
    )
    assert resp.status_code == 403
