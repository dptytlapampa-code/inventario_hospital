"""Model package exports with graceful fallbacks.

This module attempts to import all SQLAlchemy-based models but degrades
gracefully when SQLAlchemy isn't installed.  The tests in this kata only
require the simple in-memory ``User`` implementation, so missing optional
dependencies shouldn't raise ``ModuleNotFoundError`` during import.
"""

from .user import User, USERS, USERNAME_TABLE

try:  # pragma: no cover - optional SQLAlchemy models
    from .base import Base
    from .hospital import Hospital
    from .licencia import Licencia, TipoLicencia, EstadoLicencia
    from .usuario import Usuario
except ModuleNotFoundError:  # pragma: no cover
    Base = Hospital = Licencia = TipoLicencia = EstadoLicencia = Usuario = None

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
