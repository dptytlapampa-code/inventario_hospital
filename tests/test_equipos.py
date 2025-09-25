from io import BytesIO
from pathlib import Path

from app.models import Equipo, EquipoAdjunto, EquipoInsumo, EstadoEquipo, Insumo, TipoEquipo


def login(client, username: str, password: str) -> None:
    client.post(
        "/auth/login",
        data={"username": username, "password": password},
        follow_redirects=False,
    )


def _base_equipo_form(hospital, include_serial: bool = True) -> dict[str, str]:
    data = {
        "descripcion": "Router de prueba",
        "tipo": TipoEquipo.ROUTER.value,
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
    form_data = _base_equipo_form(data["hospital"], include_serial=False)
    response = client.post("/equipos/crear", data=form_data, follow_redirects=True)
    assert response.status_code == 200
    assert "Ingrese un número de serie" in response.get_data(as_text=True)


def test_equipo_generates_internal_serial(client, admin_credentials, data):
    login(client, **admin_credentials)
    form_data = _base_equipo_form(data["hospital"], include_serial=False)
    form_data["sin_numero_serie"] = "y"
    response = client.post("/equipos/crear", data=form_data, follow_redirects=False)
    assert response.status_code == 302
    nuevo = Equipo.query.order_by(Equipo.id.desc()).first()
    assert nuevo is not None
    assert nuevo.sin_numero_serie is True
    assert nuevo.numero_serie and nuevo.numero_serie.startswith("EQ-")


def test_equipo_requires_valid_hospital_lookup(client, admin_credentials, data):
    login(client, **admin_credentials)
    form_data = _base_equipo_form(data["hospital"], include_serial=True)
    form_data["hospital_id"] = ""
    response = client.post("/equipos/crear", data=form_data, follow_redirects=True)
    assert response.status_code == 200
    assert "Seleccione una opción válida" in response.get_data(as_text=True)


def test_equipo_adjuntos_upload_download_and_delete(client, admin_credentials, data):
    login(client, **admin_credentials)
    equipo = data["equipo"]
    upload_data = {
        "archivo": (BytesIO(b"fake image data"), "foto.jpg"),
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

    preview = client.get(
        f"/equipos/{equipo.id}/adjuntos/{adjunto.id}/descargar?preview=1",
        follow_redirects=False,
    )
    assert preview.status_code == 200
    assert preview.mimetype.startswith("image/")

    delete_resp = client.post(
        f"/equipos/{equipo.id}/adjuntos/{adjunto.id}/eliminar",
        follow_redirects=False,
    )
    assert delete_resp.status_code == 302
    assert not stored_path.exists()
    assert EquipoAdjunto.query.get(adjunto.id) is None


def test_tecnico_vincula_insumo_a_equipo(client, tecnico_credentials, data, app):
    login(client, **tecnico_credentials)
    equipo = data["equipo"]
    insumo = data["insumo"]

    response = client.post(
        f"/equipos/{equipo.id}/insumos",
        data={
            "insumo_busqueda": insumo.nombre,
            "insumo_id": str(insumo.id),
            "cantidad": 3,
            "comentario": "Asignación de prueba",
        },
        follow_redirects=False,
    )
    assert response.status_code == 302

    with app.app_context():
        asignacion = (
            EquipoInsumo.query.filter_by(equipo_id=equipo.id, insumo_id=insumo.id)
            .order_by(EquipoInsumo.id.desc())
            .first()
        )
        assert asignacion is not None
        assert asignacion.cantidad == 3
        assert asignacion.comentario == "Asignación de prueba"

        refreshed_insumo = Insumo.query.get(insumo.id)
        assert refreshed_insumo is not None
        assert refreshed_insumo.stock == insumo.stock - 3

        equipo_db = Equipo.query.get(equipo.id)
        assert equipo_db is not None
        assert any(
            entry.accion == "Asignación de insumo"
            and "Asignación de prueba" in (entry.descripcion or "")
            for entry in equipo_db.historial
        )
