"""Password hashing utilities with optional Flask-Bcrypt compatibility."""
from __future__ import annotations

from typing import Any

from werkzeug.security import check_password_hash, generate_password_hash


class PasswordHasher:
    """Lightweight replacement for :class:`flask_bcrypt.Bcrypt`.

    The real Flask-Bcrypt extension cannot always be installed in constrained
    environments (e.g. offline CI).  This helper mimics the public API used by
    the project so application code keeps working while relying on
    :func:`werkzeug.security.generate_password_hash` under the hood.  When the
    optional dependency is available the project will use it instead.
    """

    def __init__(self, app: Any | None = None) -> None:
        self.method = "pbkdf2:sha256:390000"
        self.salt_length = 16
        if app is not None:
            self.init_app(app)

    def init_app(self, app: Any) -> None:  # pragma: no cover - simple setter
        """Load configuration overrides from ``app`` if present."""

        self.method = app.config.get("PASSWORD_HASH_METHOD", self.method)
        self.salt_length = int(app.config.get("PASSWORD_SALT_LENGTH", self.salt_length))

    def generate_password_hash(self, password: str, rounds: int | None = None) -> bytes:
        """Return a hashed password as bytes.

        ``Flask-Bcrypt`` usually returns bytes so we keep the behaviour to avoid
        touching the call sites (``decode`` is still expected downstream).
        """

        method = self.method
        if rounds:
            method = f"pbkdf2:sha256:{rounds}"
        return generate_password_hash(password, method=method, salt_length=self.salt_length).encode()

    @staticmethod
    def check_password_hash(pw_hash: str, password: str) -> bool:
        """Validate that ``password`` matches ``pw_hash``."""

        return check_password_hash(pw_hash, password)


__all__ = ["PasswordHasher"]
