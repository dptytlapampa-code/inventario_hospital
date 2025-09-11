import pytest

actas = pytest.importorskip("app.models.acta")


def test_acta_model_placeholder():
    assert hasattr(actas, "Acta")
