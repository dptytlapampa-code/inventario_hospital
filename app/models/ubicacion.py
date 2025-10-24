"""Models describing the institution/service/office hierarchy."""
from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship, synonym

from .base import Base
from .institucion import Institucion

if TYPE_CHECKING:  # pragma: no cover
    from .equipo import Equipo


class Servicio(Base):
    """Intermediate level grouping multiple offices."""

    __tablename__ = "servicios"
    __table_args__ = (
        UniqueConstraint("institucion_id", "nombre", name="uq_servicio_nombre_institucion"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    nombre: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    descripcion: Mapped[str | None] = mapped_column(String(255))
    institucion_id: Mapped[int] = mapped_column(
        ForeignKey("instituciones.id", ondelete="CASCADE"), nullable=False
    )

    institucion: Mapped["Institucion"] = relationship(
        "Institucion", back_populates="servicios"
    )
    oficinas: Mapped[list["Oficina"]] = relationship(
        "Oficina", back_populates="servicio", cascade="all, delete-orphan"
    )
    hospital = synonym("institucion")
    hospital_id = synonym("institucion_id")

    def __repr__(self) -> str:  # pragma: no cover
        return f"Servicio(id={self.id!r}, nombre={self.nombre!r})"


class Oficina(Base):
    """Concrete physical location inside a service."""

    __tablename__ = "oficinas"
    __table_args__ = (
        UniqueConstraint("servicio_id", "nombre", name="uq_oficina_nombre_servicio"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    nombre: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    piso: Mapped[str | None] = mapped_column(String(20))
    servicio_id: Mapped[int] = mapped_column(
        ForeignKey("servicios.id", ondelete="CASCADE"), nullable=False
    )
    institucion_id: Mapped[int] = mapped_column(
        ForeignKey("instituciones.id", ondelete="CASCADE"), nullable=False
    )

    servicio: Mapped["Servicio"] = relationship("Servicio", back_populates="oficinas")
    institucion: Mapped["Institucion"] = relationship("Institucion", back_populates="oficinas")
    equipos: Mapped[list["Equipo"]] = relationship("Equipo", back_populates="oficina")
    hospital = synonym("institucion")
    hospital_id = synonym("institucion_id")

    def __repr__(self) -> str:  # pragma: no cover
        return f"Oficina(id={self.id!r}, nombre={self.nombre!r})"


__all__ = ["Institucion", "Servicio", "Oficina"]
