"""Role model definition."""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base


class Rol(Base):
    """System role (Superadmin, Admin, Técnico, Lectura)."""

    __tablename__ = "roles"

    id: Mapped[int] = mapped_column(primary_key=True)
    nombre: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    descripcion: Mapped[str | None] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.current_timestamp(), nullable=False
    )

    usuarios = relationship("Usuario", back_populates="rol")
    permisos = relationship("Permiso", back_populates="rol", cascade="all, delete-orphan")
    usuarios_hospitales = relationship(
        "HospitalUsuarioRol", back_populates="rol", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:  # pragma: no cover
        return f"Rol(id={self.id!r}, nombre={self.nombre!r})"


__all__ = ["Rol"]
