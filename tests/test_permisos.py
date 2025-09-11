import pytest

permisos = pytest.importorskip("app.models.permisos")


def test_permiso_model_available():
    assert hasattr(permisos, "Permiso")
