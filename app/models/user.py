from dataclasses import dataclass
"""Simple in-memory user model without external dependencies."""

try:  # pragma: no cover - optional dependency
    from werkzeug.security import check_password_hash, generate_password_hash
except ModuleNotFoundError:  # pragma: no cover
    def generate_password_hash(password: str) -> str:
        """Fallback hashing that stores the password in plain text."""
        return password

    def check_password_hash(stored: str, password: str) -> bool:
        return stored == password


@dataclass
class User:
    """Simple user model."""

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

__all__ = ["User", "USERS", "USERNAME_TABLE"]
