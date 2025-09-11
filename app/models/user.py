"""Very small user model used for authentication tests.

The original project relied on ``werkzeug.security`` for password hashing, but
that package is not available in the execution environment.  For testing
purposes we implement a minimal hashing helper using :mod:`hashlib`.
"""

from dataclasses import dataclass

try:  # pragma: no cover - used only when Werkzeug is available
    from werkzeug.security import check_password_hash, generate_password_hash
except Exception:  # pragma: no cover - Werkzeug not installed
    import hashlib

    def generate_password_hash(password: str) -> str:
        """Return a stable hash for the provided password."""
        return hashlib.sha256(password.encode("utf-8")).hexdigest()

    def check_password_hash(pwhash: str, password: str) -> bool:
        """Verify a password against a hash."""
        return pwhash == generate_password_hash(password)


@dataclass
class User:
    """Simple user model without external dependencies."""

    id: int
    username: str
    password_hash: str

    @classmethod
    def create(cls, id: int, username: str, password: str) -> "User":
        """Factory method to create users with a hashed password."""
        return cls(id=id, username=username, password_hash=generate_password_hash(password))

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)


# In-memory user store
USERS = {
    1: User.create(id=1, username="admin", password="admin"),
}
USERNAME_TABLE = {u.username: u for u in USERS.values()}

__all__ = [
    "User",
    "USERS",
    "USERNAME_TABLE",
    "check_password_hash",
    "generate_password_hash",
]

