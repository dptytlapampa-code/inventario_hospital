from dataclasses import dataclass


@dataclass
class User:
    """Simple user model without external dependencies."""

    id: int
    username: str
    password: str

    def check_password(self, password: str) -> bool:
        return self.password == password


# In-memory user store
USERS = {
    1: User(id=1, username="admin", password="admin"),
}
USERNAME_TABLE = {u.username: u for u in USERS.values()}

__all__ = ["User", "USERS", "USERNAME_TABLE"]
