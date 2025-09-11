"""Model package with optional imports for lightweight testing.

This project primarily exercises a few simple models during tests.  Many of the
modules in ``app.models`` depend on external libraries such as SQLAlchemy
which are not available in the execution environment.  Importing the package
would normally raise :class:`ModuleNotFoundError` when those dependencies are
missing and prevent the lightweight tests from running.

To keep the public API stable while avoiding hard dependencies, the heavy
imports are wrapped in ``try``/``except`` blocks.  If an optional dependency is
unavailable the corresponding names are set to ``None`` so that importing the
package still succeeds.
"""

from .user import User, USERS, USERNAME_TABLE

# Optional models -----------------------------------------------------------
try:  # pragma: no cover - exercised only when dependencies are installed
    from .base import Base
    from .hospital import Hospital
    from .licencia import Licencia, TipoLicencia, EstadoLicencia
    from .usuario import Usuario
except Exception:  # pragma: no cover - missing optional dependencies
    Base = Hospital = Licencia = TipoLicencia = EstadoLicencia = Usuario = None  # type: ignore


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
