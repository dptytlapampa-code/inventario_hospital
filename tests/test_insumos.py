"""Tests for insumo stock management."""
from __future__ import annotations

from app.models import Insumo, MovimientoTipo
from app.services import insumo_service


def login(client, username: str, password: str) -> None:
    client.post(
        "/auth/login",
        data={"username": username, "password": password},
        follow_redirects=False,
    )


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


def test_tecnico_puede_registrar_egreso(client, tecnico_credentials, data, app):
    login(client, **tecnico_credentials)
    insumo_id = data["insumo"].id
    stock_inicial = data["insumo"].stock

    respuesta = client.post(
        f"/insumos/{insumo_id}/movimiento",
        data={
            "tipo": MovimientoTipo.EGRESO.value,
            "cantidad": 2,
            "equipo_id": 0,
            "motivo": "Soporte en terreno",
            "observaciones": "Entrega por ticket",
        },
        follow_redirects=True,
    )
    assert respuesta.status_code == 200
    assert "Movimiento registrado" in respuesta.get_data(as_text=True)

    with app.app_context():
        insumo = Insumo.query.get(insumo_id)
        assert insumo is not None
        assert insumo.stock == stock_inicial - 2


def test_tecnico_no_puede_registrar_ingreso(client, tecnico_credentials, data, app):
    login(client, **tecnico_credentials)
    insumo_id = data["insumo"].id
    stock_inicial = data["insumo"].stock

    respuesta = client.post(
        f"/insumos/{insumo_id}/movimiento",
        data={
            "tipo": MovimientoTipo.INGRESO.value,
            "cantidad": 1,
            "equipo_id": 0,
            "motivo": "Reposición",
            "observaciones": "",
        },
        follow_redirects=True,
    )
    assert respuesta.status_code == 200
    assert "egresos de stock" in respuesta.get_data(as_text=True)

    with app.app_context():
        insumo = Insumo.query.get(insumo_id)
        assert insumo is not None
        assert insumo.stock == stock_inicial
