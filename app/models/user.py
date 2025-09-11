from dataclasses import dataclass
import hashlib
import hmac


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


def generate_password_hash(password: str) -> str:
    """Minimal password hashing using SHA-256."""
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def check_password_hash(pwhash: str, password: str) -> bool:
    """Constant-time comparison of password hashes."""
    return hmac.compare_digest(pwhash, generate_password_hash(password))


# In-memory user store
USERS = {
    1: User.create(id=1, username="admin", password="admin"),
}
USERNAME_TABLE = {u.username: u for u in USERS.values()}

__all__ = ["User", "USERS", "USERNAME_TABLE"]
