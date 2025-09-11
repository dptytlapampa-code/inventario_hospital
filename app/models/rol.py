from __future__ import annotations

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base


class Rol(Base):
    """Rol del sistema (Superadmin, Admin, Técnico)."""

    __tablename__ = "roles"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    nombre: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)

    usuarios = relationship("Usuario", back_populates="rol")
    permisos = relationship("Permiso", back_populates="rol")


__all__ = ["Rol"]
