"""Utility helpers for equipment domain logic."""
from __future__ import annotations

from datetime import datetime
from typing import Sequence

from sqlalchemy.orm import Session, joinedload

from app.extensions import db
from app.models import Equipo


def generate_internal_serial(session: Session, moment: datetime | None = None) -> str:
    """Return a unique serial number for equipment without a visible serial."""

    timestamp = moment or datetime.utcnow()
    prefix = f"EQ-{timestamp:%Y%m%d}"
    like_expression = f"{prefix}-%"
    last_value = (
        session.query(Equipo.numero_serie)
        .filter(Equipo.numero_serie.ilike(like_expression))
        .order_by(Equipo.numero_serie.desc())
        .first()
    )
    sequence = 1
    if last_value and last_value[0]:
        try:
            sequence = int(str(last_value[0]).rsplit("-", maxsplit=1)[-1]) + 1
        except (ValueError, IndexError):  # pragma: no cover - defensive
            sequence = 1
    return f"{prefix}-{sequence:04d}"


def format_equipo_option(equipo: Equipo) -> dict[str, str]:
    """Return a serialisable representation used by remote selects."""

    tipo = (equipo.tipo.nombre if equipo.tipo else "Sin tipo").strip()
    marca = (equipo.marca or "").strip()
    modelo = (equipo.modelo or "").strip()
    serie = (equipo.numero_serie or "N/A").strip() or "N/A"
    marca_modelo = " ".join(part for part in [marca, modelo] if part)
    label_parts = [tipo or "Equipo"]
    if marca_modelo:
        label_parts.append(marca_modelo)
    label_parts.append(f"S/N: {serie}")
    return {"id": str(equipo.id), "text": " - ".join(label_parts)}


def equipment_options_for_ids(ids: Sequence[int | str | None]) -> list[dict[str, str]]:
    """Return option dictionaries preserving ``ids`` order."""

    ordered: list[int] = []
    seen: set[int] = set()
    for value in ids:
        if value in (None, ""):
            continue
        try:
            item = int(value)  # type: ignore[arg-type]
        except (TypeError, ValueError):
            continue
        if item not in seen:
            seen.add(item)
            ordered.append(item)
    if not ordered:
        return []
    equipos = (
        db.session.query(Equipo)
        .options(joinedload(Equipo.tipo))
        .filter(Equipo.id.in_(ordered))
        .all()
    )
    mapping = {equipo.id: format_equipo_option(equipo) for equipo in equipos}
    return [mapping[item] for item in ordered if item in mapping]


__all__ = ["generate_internal_serial", "format_equipo_option", "equipment_options_for_ids"]
