"""Integration tests for licencias blueprint access control."""
from __future__ import annotations


def login(client, username: str, password: str):
    return client.post(
        "/auth/login",
        data={"username": username, "password": password},
        follow_redirects=False,
    )


def test_listar_requires_authentication(client):
    resp = client.get("/licencias/listar")
    assert resp.status_code == 302
    assert "/auth/login" in resp.headers["Location"]


def test_listar_forbidden_without_permission(client, gestor_credentials):
    login(client, **gestor_credentials)
    resp = client.get("/licencias/listar")
    assert resp.status_code == 403
    page = resp.get_data(as_text=True)
    assert "Permiso denegado" in page


def test_listar_accessible_with_permission(client, admin_credentials):
    login(client, **admin_credentials)
    resp = client.get("/licencias/listar")
    assert resp.status_code == 200


def test_superadmin_cannot_request_license(client, superadmin_credentials):
    login(client, **superadmin_credentials)
    resp = client.get("/licencias/solicitar")
    assert resp.status_code == 403


def test_superadmin_post_license_forbidden(client, superadmin_credentials):
    login(client, **superadmin_credentials)
    resp = client.post("/licencias/solicitar", data={"tipo": "temporal"})
    assert resp.status_code == 403


def test_aprobar_requires_csrf_token_when_enabled(app, client, superadmin_credentials, data):
    login(client, **superadmin_credentials)
    licencia_id = data["licencia"].id
    app.config["WTF_CSRF_ENABLED"] = True
    try:
        resp = client.post(
            f"/licencias/{licencia_id}/aprobar",
            data={"accion": "aprobar", "comentario": ""},
            follow_redirects=False,
        )
    finally:
        app.config["WTF_CSRF_ENABLED"] = False

    assert resp.status_code == 400
