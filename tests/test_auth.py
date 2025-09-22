"""Authentication flow tests."""
from __future__ import annotations

import pytest


def login(client, username: str, password: str):
    return client.post(
        "/auth/login",
        data={"username": username, "password": password},
        follow_redirects=False,
    )


def test_login_success_redirects(client, superadmin_credentials):
    resp = login(client, **superadmin_credentials)
    assert resp.status_code == 302
    assert resp.headers["Location"].endswith("/")


def test_login_failure(client, superadmin_credentials):
    resp = login(client, superadmin_credentials["username"], "badpass")
    assert resp.status_code == 200
    assert "Usuario o contraseña inválidos" in resp.get_data(as_text=True)


def test_logout_flow(client, superadmin_credentials):
    resp = client.get("/licencias/listar")
    assert resp.status_code == 302
    assert "/auth/login" in resp.headers["Location"]

    login(client, **superadmin_credentials)
    resp = client.get("/licencias/listar")
    assert resp.status_code == 200

    resp = client.get("/auth/logout", follow_redirects=False)
    assert resp.status_code == 302
    assert "/auth/login" in resp.headers["Location"]


@pytest.mark.parametrize("username", ["admin", "tecnico"])
def test_users_can_access_dashboard(client, username):
    login(client, username=username, password="Cambiar123!")
    resp = client.get("/")
    assert resp.status_code == 200
