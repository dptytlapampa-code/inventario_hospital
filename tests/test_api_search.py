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
    assert data["items"]
    assert any("Emergencias" in item["label"] for item in data["items"])
    assert all(item["label"] == item["text"] for item in data["items"])
    assert data["total"] >= len(data["items"])


def test_search_hospitales_lookup(client, admin_credentials):
    login(client, **admin_credentials)
    resp = client.get("/api/search/hospitales?q=Central")
    assert resp.status_code == 200
    data = resp.get_json()
    assert any("Hospital Central" in item["label"] for item in data["items"])
    assert all(item["label"] == item["text"] for item in data["items"])
    resp_all = client.get("/api/search/hospitales?q=...")
    assert resp_all.status_code == 200
    assert resp_all.get_json()["items"]


def test_search_servicios_lookup_requires_hospital(client, admin_credentials, data):
    login(client, **admin_credentials)
    resp = client.get("/api/search/servicios?q=eme")
    assert resp.status_code == 400
    hospital_id = data["hospital"].id
    resp_ok = client.get(f"/api/search/servicios?hospital_id={hospital_id}&q=eme")
    assert resp_ok.status_code == 200
    payload = resp_ok.get_json()
    assert any(item["label"] == "Emergencias" for item in payload["items"])
    assert all(item["label"] == item["text"] for item in payload["items"])


def test_search_oficinas_lookup_requires_hospital(client, admin_credentials, data):
    login(client, **admin_credentials)
    resp = client.get("/api/search/oficinas?q=principal")
    assert resp.status_code == 400
    hospital_id = data["hospital"].id
    servicio_id = data["servicio"].id
    resp_ok = client.get(
        f"/api/search/oficinas?hospital_id={hospital_id}&servicio_id={servicio_id}&q=principal"
    )
    assert resp_ok.status_code == 200
    payload = resp_ok.get_json()
    assert payload["items"]
    assert all(item["label"] == item["text"] for item in payload["items"])


def test_search_oficinas_requires_servicio(client, admin_credentials, data):
    login(client, **admin_credentials)
    resp = client.get("/api/oficinas/search?q=principal")
    assert resp.status_code == 400
    servicio_id = data["servicio"].id
    resp = client.get(f"/api/oficinas/search?servicio_id={servicio_id}&q=principal")
    assert resp.status_code == 200
    payload = resp.get_json()
    assert payload["items"]
    assert all(item["label"] == item["text"] for item in payload["items"])


def test_search_insumos_endpoint(client, admin_credentials):
    login(client, **admin_credentials)
    resp = client.get("/api/insumos/search?q=mouse")
    assert resp.status_code == 200
    data = resp.get_json()
    assert any("Mouse" in item["label"] for item in data["items"])
    assert all(item["label"] == item["text"] for item in data["items"])


def test_search_equipos_respects_user_hospital_scope(client, tecnico_credentials):
    login(client, **tecnico_credentials)
    resp = client.get("/api/equipos/search?q=Impresora")
    assert resp.status_code == 200
    payload = resp.get_json()
    results = payload.get("results", [])
    assert results
    assert any("IMP-001" in item["text"] for item in results)
    assert all("IMP-002" not in item["text"] for item in results)


def test_search_equipos_allows_hospital_filter(client, superadmin_credentials, data):
    login(client, **superadmin_credentials)
    hospital_id = data["hospital"].id
    other_id = data["hospital_secundario"].id

    resp_primary = client.get(f"/api/equipos/search?q=Impresora&hospital_id={hospital_id}")
    assert resp_primary.status_code == 200
    primary_payload = resp_primary.get_json()
    assert primary_payload["results"]
    assert all("IMP-001" in item["text"] for item in primary_payload["results"])

    resp_secondary = client.get(f"/api/equipos/search?q=Impresora&hospital_id={other_id}")
    assert resp_secondary.status_code == 200
    secondary_payload = resp_secondary.get_json()
    assert secondary_payload["results"]
    assert all("IMP-002" in item["text"] for item in secondary_payload["results"])
