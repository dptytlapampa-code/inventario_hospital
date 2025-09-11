"""Helpers for working with :mod:`licencias` module."""

from __future__ import annotations

from datetime import date
from typing import List, Tuple

from licencias import LICENCIAS_APROBADAS, Licencia


def crear_licencia(
    usuario_id: int,
    fecha_inicio: date,
    fecha_fin: date,
    requires_replacement: bool = False,
) -> Licencia:
    """Create a :class:`licencias.Licencia` instance and return it."""

    return Licencia(
        usuario_id=usuario_id,
        fecha_inicio=fecha_inicio,
        fecha_fin=fecha_fin,
        requires_replacement=requires_replacement,
    )


def licencias_aprobadas(usuario_id: int) -> List[Tuple[date, date]]:
    """Return approved license ranges for ``usuario_id``."""

    return list(LICENCIAS_APROBADAS.get(usuario_id, []))
