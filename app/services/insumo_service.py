"""Utility helpers for insumo stock movements."""
from __future__ import annotations

from typing import Optional

from app.extensions import db
from sqlalchemy import select

from app.models import Insumo, InsumoMovimiento, InsumoSerie, MovimientoTipo, Usuario


def registrar_movimiento(
    *,
    insumo: Insumo,
    tipo: MovimientoTipo,
    cantidad: int,
    usuario: Optional[Usuario] = None,
    equipo_id: int | None = None,
    motivo: str | None = None,
    observaciones: str | None = None,
) -> InsumoMovimiento:
    """Create a movement adjusting stock accordingly."""

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
    db.session.commit()
    db.session.refresh(movimiento)
    db.session.expunge(movimiento)
    return movimiento


def agregar_series(
    *,
    insumo: Insumo,
    numeros_serie: list[str],
    ajustar_stock: bool = False,
) -> list[InsumoSerie]:
    """Crear registros de :class:`InsumoSerie` asegurando unicidad."""

    if not numeros_serie:
        raise ValueError("Debe indicar al menos un número de serie")

    # Normalizar eliminando espacios extras
    normalizados: list[str] = []
    vistos: set[str] = set()
    for numero in numeros_serie:
        valor = (numero or "").strip()
        if not valor:
            continue
        if valor in vistos:
            raise ValueError("Los números de serie no pueden repetirse en el mismo lote")
        vistos.add(valor)
        normalizados.append(valor)

    if not normalizados:
        raise ValueError("Debe indicar al menos un número de serie válido")

    existentes = db.session.scalars(
        select(InsumoSerie.nro_serie).where(InsumoSerie.nro_serie.in_(normalizados))
    ).all()
    if existentes:
        repetidos = ", ".join(sorted(existentes))
        raise ValueError(f"Ya existen series con estos números: {repetidos}")

    series_creadas = [InsumoSerie(insumo=insumo, nro_serie=valor) for valor in normalizados]
    db.session.add_all(series_creadas)

    if ajustar_stock:
        insumo.ajustar_stock(len(series_creadas))

    db.session.commit()
    return series_creadas


__all__ = ["registrar_movimiento", "agregar_series"]
