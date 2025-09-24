def login(client, username: str, password: str) -> None:
    client.post(
        "/auth/login",
        data={"username": username, "password": password},
        follow_redirects=False,
    )


def test_search_servicios_endpoint(client, admin_credentials):
    login(client, **admin_credentials)
    resp = client.get("/api/servicios/search?q=eme")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["results"]
    assert any("Emergencias" in item["text"] for item in data["results"])


def test_search_oficinas_requires_servicio(client, admin_credentials, data):
    login(client, **admin_credentials)
    resp = client.get("/api/oficinas/search?q=principal")
    assert resp.status_code == 400
    servicio_id = data["servicio"].id
    resp = client.get(f"/api/oficinas/search?servicio_id={servicio_id}&q=principal")
    assert resp.status_code == 200
    payload = resp.get_json()
    assert payload["results"]


def test_search_insumos_endpoint(client, admin_credentials):
    login(client, **admin_credentials)
    resp = client.get("/api/insumos/search?q=mouse")
    assert resp.status_code == 200
    data = resp.get_json()
    assert any("Mouse" in item["text"] for item in data["results"])
