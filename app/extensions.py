"""Centralized extension instances for the Flask application."""
from __future__ import annotations

# Optional imports: if the required Flask extensions are not available in the
# environment (e.g., during lightweight tests), we fall back to minimal stub
# implementations so that importing this module does not raise errors.

try:  # pragma: no cover - executed when extensions are installed
    from flask_sqlalchemy import SQLAlchemy
except Exception:  # pragma: no cover - executed in simplified environments
    class SQLAlchemy:  # type: ignore[override]
        """Minimal stub compatible with :class:`flask_sqlalchemy.SQLAlchemy`."""

        class _Model:
            """Fallback base class used when SQLAlchemy isn't installed."""

            metadata = None

        def __init__(self, *_, **__):
            # Provide a ``Model`` attribute so modules can subclass it during
            # lightweight tests where Flask-SQLAlchemy isn't available.
            self.Model = type("Model", (self._Model,), {})
            self.metadata = getattr(self.Model, "metadata", None)

        def init_app(self, *_, **__):  # pragma: no cover - stubbed method
            pass

try:  # pragma: no cover - executed when extensions are installed
    from flask_migrate import Migrate
except Exception:  # pragma: no cover
    class Migrate:  # type: ignore[override]
        def __init__(self, *_, **__):
            pass

try:  # pragma: no cover
    from flask_login import LoginManager
except Exception:  # pragma: no cover
    class LoginManager:  # type: ignore[override]
        def __init__(self, *_, **__):
            self.login_view = None

try:  # pragma: no cover
    from flask_wtf import CSRFProtect
except Exception:  # pragma: no cover
    class CSRFProtect:  # type: ignore[override]
        def __init__(self, *_, **__):
            pass

# Instantiate extension objects. They are configured with the real Flask
# application elsewhere via ``init_app`` when running the actual app.

db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
csrf = CSRFProtect()

__all__ = ["db", "migrate", "login_manager", "csrf"]
