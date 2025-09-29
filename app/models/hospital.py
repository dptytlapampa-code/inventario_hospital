"""Backwards compatibility wrapper for location models."""
from __future__ import annotations

from .ubicacion import Hospital, Oficina, Servicio

__all__ = ["Hospital", "Oficina", "Servicio"]
