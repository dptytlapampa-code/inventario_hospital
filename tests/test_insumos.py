"""Tests for insumo stock management."""
from __future__ import annotations

import pytest

from app.models import Insumo, InsumoSerie, MovimientoTipo
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


def test_agregar_series_crea_registros(app, data):
    insumo_id = data["insumo"].id

    with app.app_context():
        insumo = Insumo.query.get(insumo_id)
        assert insumo is not None
        stock_inicial = insumo.stock
        series = insumo_service.agregar_series(
            insumo=insumo,
            numeros_serie=["SSD-001", "SSD-002", "SSD-003"],
            ajustar_stock=True,
        )

        assert len(series) == 3
        assert insumo.stock == stock_inicial + 3
        guardadas = (
            InsumoSerie.query.filter(InsumoSerie.nro_serie.in_(["SSD-001", "SSD-002", "SSD-003"]))
            .count()
        )
        assert guardadas == 3


def test_agregar_series_valida_duplicados(app, data):
    insumo_id = data["insumo"].id

    with app.app_context():
        insumo = Insumo.query.get(insumo_id)
        assert insumo is not None

        insumo_service.agregar_series(
            insumo=insumo,
            numeros_serie=["SSD-010"],
            ajustar_stock=False,
        )

        with pytest.raises(ValueError):
            insumo_service.agregar_series(
                insumo=insumo,
                numeros_serie=["SSD-010", "SSD-011", "SSD-011"],
            )
