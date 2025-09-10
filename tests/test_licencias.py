import datetime as dt
import pytest

# Import the licencias module if available; otherwise, skip these tests.
licencias = pytest.importorskip("licencias")


def crear_licencia(**kwargs):
    """Helper to create a license instance using the target implementation."""
    return licencias.Licencia(**kwargs)


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


@pytest.mark.skip(reason="Authentication system not implemented yet")
def test_users_on_approved_license_restricted():
    """Users with approved licenses should be denied login or module access."""
    assert False, "To be implemented once auth system is available"
