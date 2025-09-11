from __future__ import annotations

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .licencia import Base


class Usuario(Base):
    """Modelo de usuario del sistema."""

    __tablename__ = "usuarios"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    nombre: Mapped[str] = mapped_column(String(100), nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)

    licencias = relationship("Licencia", back_populates="usuario")


__all__ = ["Usuario"]
