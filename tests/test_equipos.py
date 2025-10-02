from io import BytesIO
from pathlib import Path

from app.models import Equipo, EquipoAdjunto, EstadoEquipo


def login(client, username: str, password: str) -> None:
    client.post(
        "/auth/login",
        data={"username": username, "password": password},
        follow_redirects=False,
    )


def _base_equipo_form(hospital, tipo_id: int, include_serial: bool = True) -> dict[str, str]:
    data = {
        "descripcion": "Router de prueba",
        "tipo": str(tipo_id),
        "estado": EstadoEquipo.OPERATIVO.value,
        "hospital_busqueda": hospital.nombre,
        "hospital_id": str(hospital.id),
        "servicio_busqueda": "",
        "servicio_id": "",
        "oficina_busqueda": "",
        "oficina_id": "",
        "numero_serie": "SN-12345" if include_serial else "",
    }
    return data


def test_equipo_requires_serial_when_flag_not_checked(client, admin_credentials, data):
    login(client, **admin_credentials)
    form_data = _base_equipo_form(
        data["hospital"], data["tipos_equipo"]["router"].id, include_serial=False
    )
    response = client.post("/equipos/crear", data=form_data, follow_redirects=True)
    assert response.status_code == 200
    assert "Ingrese un número de serie" in response.get_data(as_text=True)


def test_equipo_generates_internal_serial(client, admin_credentials, data):
    login(client, **admin_credentials)
    form_data = _base_equipo_form(
        data["hospital"], data["tipos_equipo"]["router"].id, include_serial=False
    )
    form_data["sin_numero_serie"] = "y"
    response = client.post("/equipos/crear", data=form_data, follow_redirects=False)
    assert response.status_code == 302
    nuevo = Equipo.query.order_by(Equipo.id.desc()).first()
    assert nuevo is not None
    assert nuevo.sin_numero_serie is True
    assert nuevo.numero_serie and nuevo.numero_serie.startswith("EQ-")


def test_equipo_requires_valid_hospital_lookup(client, admin_credentials, data):
    login(client, **admin_credentials)
    form_data = _base_equipo_form(
        data["hospital"], data["tipos_equipo"]["router"].id, include_serial=True
    )
    form_data["hospital_id"] = ""
    response = client.post("/equipos/crear", data=form_data, follow_redirects=True)
    assert response.status_code == 200
    assert "Seleccione una opción válida" in response.get_data(as_text=True)


def test_equipo_adjuntos_upload_download_and_delete(client, admin_credentials, data):
    login(client, **admin_credentials)
    equipo = data["equipo"]
    png_bytes = (
        b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89"
        b"\x00\x00\x00\x0cIDATx\x9cc`\x00\x00\x00\x02\x00\x01\xe2!\xbc3\x00\x00\x00\x00IEND\xaeB`\x82"
    )
    upload_data = {
        "archivo": (BytesIO(png_bytes), "foto.png"),
    }
    response = client.post(
        f"/equipos/{equipo.id}/adjuntos/subir",
        data=upload_data,
        content_type="multipart/form-data",
        follow_redirects=False,
    )
    assert response.status_code == 302
    adjunto = EquipoAdjunto.query.filter_by(equipo_id=equipo.id).order_by(EquipoAdjunto.id.desc()).first()
    assert adjunto is not None
    stored_path = Path(adjunto.filepath)
    assert stored_path.exists()

    preview = client.get(f"/files/view/{adjunto.id}", follow_redirects=False)
    assert preview.status_code == 200
    assert preview.mimetype.startswith("image/")

    thumb_path = Path(adjunto.filepath).with_name(Path(adjunto.filepath).stem + "_thumb.webp")
    assert thumb_path.exists()

    delete_resp = client.post(f"/files/delete/{adjunto.id}", follow_redirects=False)
    assert delete_resp.status_code == 302
    assert not stored_path.exists()
    assert not thumb_path.exists()
    assert EquipoAdjunto.query.get(adjunto.id) is None
