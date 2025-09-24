"""Utility helpers for equipment domain logic."""
from __future__ import annotations

from datetime import datetime

from sqlalchemy.orm import Session

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


__all__ = ["generate_internal_serial"]
