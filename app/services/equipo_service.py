"""Utility helpers for equipment domain logic."""
from __future__ import annotations

from datetime import datetime

from sqlalchemy.orm import Session

from app.models import Equipo


def generate_internal_serial(session: Session, year: int | None = None) -> str:
    """Return a unique serial number for equipment without visible serial."""

    year = year or datetime.utcnow().year
    prefix = f"SNV-{year:04d}"
    like_expression = f"{prefix}-%"
    last_value = (
        session.query(Equipo.numero_serie)
        .filter(Equipo.numero_serie.ilike(like_expression))
        .order_by(Equipo.numero_serie.desc())
        .first()
    )
    next_sequence = 1
    if last_value and last_value[0]:
        try:
            last_sequence = int(str(last_value[0]).split("-")[-1])
        except (ValueError, IndexError):
            next_sequence = 1
        else:
            next_sequence = last_sequence + 1
    return f"{prefix}-{next_sequence:06d}"


__all__ = ["generate_internal_serial"]
