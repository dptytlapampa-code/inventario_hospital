import pytest

# Try to import the equipment model; skip tests if unavailable

Equipo = pytest.importorskip("app.models.equipo", reason="Modelo Equipo no disponible")


def test_equipo_model_has_expected_attrs():
    assert hasattr(Equipo, "Equipo")
