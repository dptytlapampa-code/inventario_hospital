from dataclasses import dataclass

from flask_login import UserMixin
from werkzeug.security import check_password_hash, generate_password_hash


@dataclass
class User(UserMixin):
    """Simple user model for demonstration purposes."""

    id: int
    username: str
    password_hash: str

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)


# In-memory user store
USERS = {
    1: User(id=1, username="admin", password_hash=generate_password_hash("admin"))
}
USERNAME_TABLE = {u.username: u for u in USERS.values()}

__all__ = ["User", "USERS", "USERNAME_TABLE"]
