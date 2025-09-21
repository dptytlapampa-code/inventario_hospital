"""Minimal user model for authentication tests.

The original project relied on ``werkzeug.security`` for password hashing, but
that package is not available in the execution environment. For testing
purposes we implement minimal hashing helpers using :mod:`hashlib`.
"""

from dataclasses import dataclass, field
import hashlib
from typing import Set


def generate_password_hash(password: str) -> str:
    """Return a SHA-256 hash for the given ``password``.

    The helper mirrors :func:`werkzeug.security.generate_password_hash` but
    uses only the standard library.  It is intentionally simple and suitable
    solely for test environments.
    """

    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def check_password_hash(hash: str, password: str) -> bool:
    """Validate that ``password`` matches the provided ``hash``."""

    return hash == generate_password_hash(password)


@dataclass
class User:
    """Simple user model without external dependencies."""

    id: int
    username: str
    password_hash: str
    roles: Set[str] = field(default_factory=set)
    permissions: Set[str] = field(default_factory=set)

    @property
    def is_authenticated(self) -> bool:
        """Users provided by the in-memory table are always authenticated."""

        return True

    @property
    def is_active(self) -> bool:
        """All in-memory users are active by definition."""

        return True

    @property
    def is_anonymous(self) -> bool:
        """The application never treats these users as anonymous."""

        return False

    def get_id(self) -> str:
        """Return the unique identifier stored in Flask's session."""

        return self.username

    @staticmethod
    def _hash_password(password: str) -> str:
        """Return a stable hash for the provided password."""

        return generate_password_hash(password)

    @classmethod
    def create(
        cls,
        id: int,
        username: str,
        password: str,
        roles: Set[str] | None = None,
        permissions: Set[str] | None = None,
    ) -> "User":
        """Factory method to create users with a hashed password."""

        return cls(
            id=id,
            username=username,
            password_hash=cls._hash_password(password),
            roles=roles or set(),
            permissions=permissions or set(),
        )

    def check_password(self, password: str) -> bool:
        """Verify a plaintext password against the stored hash."""

        return check_password_hash(self.password_hash, password)


# In-memory user store
USERS = {
    1: User.create(
        id=1,
        username="admin",
        password="admin",
        roles={"admin"},
        permissions={"licencias:read", "licencias:write"},
    ),
}
USERNAME_TABLE = {u.username: u for u in USERS.values()}

__all__ = [
    "User",
    "USERS",
    "USERNAME_TABLE",
    "generate_password_hash",
    "check_password_hash",
]

