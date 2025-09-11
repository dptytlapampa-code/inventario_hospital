from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import String, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base

if TYPE_CHECKING:  # pragma: no cover
    from .rol import Rol


class Usuario(Base):
    """Modelo de usuario del sistema."""

    __tablename__ = "usuarios"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    nombre: Mapped[str] = mapped_column(String(100), nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    rol_id: Mapped[int | None] = mapped_column(ForeignKey("roles.id"), nullable=True)

    licencias = relationship("Licencia", back_populates="usuario")
    rol: Mapped["Rol"] = relationship("Rol", back_populates="usuarios")


__all__ = ["Usuario"]
