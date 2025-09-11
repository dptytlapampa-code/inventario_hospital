import datetime as dt

from app.routes.licencias import routes
from licencias import Licencia


def test_creacion_y_consulta_solicitud():
    """Las solicitudes se almacenan en un diccionario indexado por ID."""
    routes.SOLICITUDES.clear()

    licencia = Licencia(
        usuario_id=1,
        fecha_inicio=dt.date(2024, 1, 1),
        fecha_fin=dt.date(2024, 1, 2),
    )
    licencia.enviar_pendiente()

    routes.SOLICITUDES[1] = licencia

    assert routes._get_solicitud(1) is licencia
    assert routes._get_solicitud(99) is None

