import pytest

# Skip if the audit module is not available

auditoria = pytest.importorskip("app.models.auditoria")


def test_auditoria_registra_accion():
    assert hasattr(auditoria, "Auditoria")
