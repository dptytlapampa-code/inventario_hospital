import datetime as dt
import pytest

from app import create_app

# Import the licencias module if available; otherwise, skip these tests.
licencias = pytest.importorskip("licencias")


def crear_licencia(**kwargs):
    """Helper to create a license instance using the target implementation."""
    return licencias.Licencia(**kwargs)


@pytest.fixture(autouse=True)
def limpiar_licencias():
    licencias.LICENCIAS_APROBADAS.clear()


@pytest.fixture()
def app():
    app = create_app()
    app.config.update(TESTING=True, WTF_CSRF_ENABLED=False)
    return app


@pytest.fixture()
def client(app):
    return app.test_client()


def login(client, username="admin", password="admin"):
    return client.post(
        "/auth/login",
        data={"username": username, "password": password},
        follow_redirects=False,
    )


def test_state_transitions():
    """License should progress Borrador -> Pendiente -> Aprobada/Rechazada."""
    lic = crear_licencia(usuario_id=1, fecha_inicio=dt.date(2024, 1, 1), fecha_fin=dt.date(2024, 1, 10))
    assert lic.estado == licencias.EstadoLicencia.BORRADOR

    lic.enviar_pendiente()
    assert lic.estado == licencias.EstadoLicencia.PENDIENTE

    lic.aprobar()
    assert lic.estado == licencias.EstadoLicencia.APROBADA

    lic2 = crear_licencia(usuario_id=2, fecha_inicio=dt.date(2024, 2, 1), fecha_fin=dt.date(2024, 2, 10))
    lic2.enviar_pendiente()
    lic2.rechazar()
    assert lic2.estado == licencias.EstadoLicencia.RECHAZADA


def test_replacement_assignment():
    """A replacement user can be assigned to the license."""
    lic = crear_licencia(usuario_id=1, fecha_inicio=dt.date(2024, 3, 1), fecha_fin=dt.date(2024, 3, 5))
    lic.asignar_reemplazo(2)
    assert lic.reemplazo_id == 2


def test_overlap_detection():
    """Overlapping licenses for the same user should be detected."""
    lic = crear_licencia(usuario_id=1, fecha_inicio=dt.date(2024, 4, 1), fecha_fin=dt.date(2024, 4, 10))
    lic.aprobar()
    with pytest.raises(licencias.TraslapeError):
        crear_licencia(usuario_id=1, fecha_inicio=dt.date(2024, 4, 5), fecha_fin=dt.date(2024, 4, 15))
    

def test_users_on_approved_license_restricted(client):
    """Users with approved licenses should be denied login or module access."""

    hoy = dt.date.today()
    lic = crear_licencia(
        usuario_id=1,
        fecha_inicio=hoy - dt.timedelta(days=1),
        fecha_fin=hoy + dt.timedelta(days=1),
    )
    lic.aprobar()

    resp = login(client)
    assert resp.status_code == 200

    protegido = client.get("/licencias/listar")
    assert protegido.status_code == 302
    assert "/auth/login" in protegido.headers["Location"]


def test_users_with_future_approved_license_can_login(client):
    """Approved licenses in the future should not restrict login."""

    hoy = dt.date.today()
    lic = crear_licencia(
        usuario_id=1,
        fecha_inicio=hoy + dt.timedelta(days=1),
        fecha_fin=hoy + dt.timedelta(days=2),
    )
    lic.aprobar()

    resp = login(client)
    assert resp.status_code == 302

    protegido = client.get("/licencias/listar")
    assert protegido.status_code == 200


def test_users_with_rejected_license_can_login(client):
    """Rejected licenses should not restrict user access."""

    hoy = dt.date.today()
    lic = crear_licencia(
        usuario_id=1,
        fecha_inicio=hoy - dt.timedelta(days=1),
        fecha_fin=hoy + dt.timedelta(days=1),
    )
    lic.enviar_pendiente()
    lic.rechazar()

    resp = login(client)
    assert resp.status_code == 302

    protegido = client.get("/licencias/listar")
    assert protegido.status_code == 200
