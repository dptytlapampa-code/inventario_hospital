from urllib.parse import urlparse


def login(client, username: str, password: str) -> None:
    client.post(
        "/auth/login",
        data={"username": username, "password": password},
        follow_redirects=False,
    )


def test_usuarios_requires_login(client):
    resp = client.get("/usuarios/")
    assert resp.status_code == 302
    assert urlparse(resp.headers["Location"]).path == "/auth/login"


def test_usuarios_create_forbidden_for_visor(client, visor_credentials):
    login(client, **visor_credentials)
    resp = client.get("/usuarios/crear")
    assert resp.status_code == 403


def test_usuarios_create_accessible_for_admin(client, admin_credentials):
    login(client, **admin_credentials)
    resp = client.get("/usuarios/crear")
    assert resp.status_code == 200
