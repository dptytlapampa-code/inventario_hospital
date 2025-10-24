"""Backwards compatibility wrapper for institution models."""
from __future__ import annotations

from .institucion import Institucion
from .ubicacion import Oficina, Servicio

Hospital = Institucion

__all__ = ["Hospital", "Oficina", "Servicio", "Institucion"]
