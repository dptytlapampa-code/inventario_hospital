import pytest

ubicaciones = pytest.importorskip("app.routes.ubicaciones")


def test_ubicaciones_blueprint_exists():
    assert hasattr(ubicaciones, "ubicaciones_bp")
