"""Utility helpers for insumo stock movements."""
from __future__ import annotations

from typing import Optional

from app.extensions import db
from app.models import Insumo, InsumoMovimiento, MovimientoTipo, Usuario


def registrar_movimiento(
    *,
    insumo: Insumo,
    tipo: MovimientoTipo,
    cantidad: int,
    usuario: Optional[Usuario] = None,
    equipo_id: int | None = None,
    motivo: str | None = None,
    observaciones: str | None = None,
    commit: bool = True,
) -> InsumoMovimiento:
    """Create a movement adjusting stock accordingly.

    When ``commit`` is ``False`` the caller becomes responsible for finalising the
    transaction. This is useful when the stock update must be coordinated with
    other writes (e.g. vincular un insumo a un equipo) to guarantee atomicity.
    """

    if cantidad <= 0:
        raise ValueError("La cantidad debe ser mayor a cero")

    ajuste = cantidad if tipo == MovimientoTipo.INGRESO else -cantidad
    insumo.ajustar_stock(ajuste)

    movimiento = InsumoMovimiento(
        insumo=insumo,
        usuario=usuario,
        equipo_id=equipo_id,
        tipo=tipo,
        cantidad=cantidad,
        motivo=motivo,
        observaciones=observaciones,
    )
    db.session.add(movimiento)
    if commit:
        db.session.commit()
        db.session.refresh(movimiento)
        db.session.expunge(movimiento)
    return movimiento


__all__ = ["registrar_movimiento"]
