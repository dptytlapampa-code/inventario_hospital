from __future__ import annotations

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .licencia import Base


class Usuario(Base):
    """Modelo de usuario del sistema."""

    __tablename__ = "usuarios"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    username: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    password: Mapped[str] = mapped_column(String(255), nullable=False)

    licencias = relationship("Licencia", back_populates="usuario")

    def check_password(self, password: str) -> bool:
        """Retorna ``True`` si la contraseña coincide."""
        return self.password == password


# In-memory user store for tests
USERS = {
    1: Usuario(id=1, username="admin", password="admin"),
}
USERNAME_TABLE = {u.username: u for u in USERS.values()}

__all__ = ["Usuario", "USERS", "USERNAME_TABLE"]
