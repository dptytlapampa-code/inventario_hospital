"""Aggregated model imports with graceful fallbacks."""
from __future__ import annotations

from .user import User, USERS, USERNAME_TABLE
from .base_enums import EstadoLicencia

try:  # pragma: no cover - these imports require SQLAlchemy
    from .base import Base
    from .hospital import Hospital
    from .licencia import Licencia, TipoLicencia
    from .usuario import Usuario
except Exception:  # pragma: no cover
    # Provide lightweight stand-ins when SQLAlchemy isn't available.
    Base = object  # type: ignore
    Hospital = object  # type: ignore
    Licencia = object  # type: ignore
    TipoLicencia = object  # type: ignore
    Usuario = object  # type: ignore

__all__ = [
    "Base",
    "Hospital",
    "Licencia",
    "TipoLicencia",
    "EstadoLicencia",
    "Usuario",
    "User",
    "USERS",
    "USERNAME_TABLE",
]
