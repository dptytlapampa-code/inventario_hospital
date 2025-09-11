import pytest

from app import create_app


@pytest.fixture()
def app():
    app = create_app()
    app.config.update(TESTING=True)
    return app


@pytest.fixture()
def client(app):
    return app.test_client()


def login(client, username="admin", password="admin"):
    return client.post("/auth/login", data={"username": username, "password": password})


def test_login_success_redirects(client):
    resp = login(client)
    assert resp.status_code == 302
    assert resp.headers["Location"] == "/"


def test_login_failure(client):
    resp = login(client, password="bad")
    assert resp.status_code == 200


def test_logout_flow(client):
    # unauthenticated access should redirect
    resp = client.get("/licencias/listar")
    assert resp.status_code == 302
    assert "/auth/login" in resp.headers["Location"]

    # login and access protected route
    resp = login(client)
    assert resp.status_code == 302
    resp = client.get("/licencias/listar")
    assert resp.status_code == 200

    # logout and ensure protected route is locked again
    resp = client.get("/auth/logout")
    assert resp.status_code == 302
    assert "/auth/login" in resp.headers["Location"]
    resp = client.get("/licencias/listar")
    assert resp.status_code == 302
    assert "/auth/login" in resp.headers["Location"]
