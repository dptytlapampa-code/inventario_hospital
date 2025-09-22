"""Tests for insumo stock management."""
from __future__ import annotations

from app.models import Insumo, MovimientoTipo
from app.services import insumo_service


def test_registrar_movimiento_actualiza_stock(app, data):
    insumo_id = data["insumo"].id

    with app.app_context():
        insumo = Insumo.query.get(insumo_id)
        assert insumo is not None
        stock_inicial = insumo.stock
        movimiento = insumo_service.registrar_movimiento(
            insumo=insumo,
            tipo=MovimientoTipo.INGRESO,
            cantidad=5,
            usuario=data["admin"],  # type: ignore[arg-type]
            equipo_id=None,
            motivo="Reposición",
            observaciones="Compra en proveedor local",
        )
        db_insumo = Insumo.query.get(insumo.id)

    assert movimiento.cantidad == 5
    assert db_insumo and db_insumo.stock == stock_inicial + 5


def test_registrar_movimiento_valida_stock(app, data):
    insumo_id = data["insumo"].id

    with app.app_context():
        insumo = Insumo.query.get(insumo_id)
        assert insumo is not None
        try:
            insumo_service.registrar_movimiento(
                insumo=insumo,
                tipo=MovimientoTipo.EGRESO,
                cantidad=100,
                usuario=data["admin"],  # type: ignore[arg-type]
                equipo_id=None,
                motivo="Consumo",
                observaciones=None,
            )
        except ValueError as exc:
            assert "stock" in str(exc)
        else:  # pragma: no cover
            raise AssertionError("Esperaba ValueError por stock negativo")
