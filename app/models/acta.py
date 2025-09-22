"""Models representing delivery/loan/transfer acts."""
from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING

from sqlalchemy import (
    DateTime,
    Enum as SAEnum,
    ForeignKey,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base

if TYPE_CHECKING:  # pragma: no cover
    from .equipo import Equipo
    from .hospital import Hospital, Oficina, Servicio
    from .usuario import Usuario


class TipoActa(str, Enum):
    """Types of acta documents."""

    ENTREGA = "entrega"
    PRESTAMO = "prestamo"
    TRANSFERENCIA = "transferencia"


class Acta(Base):
    """Document generated when assets change custody."""

    __tablename__ = "actas"

    id: Mapped[int] = mapped_column(primary_key=True)
    numero: Mapped[str | None] = mapped_column(String(50), unique=True)
    tipo: Mapped[TipoActa] = mapped_column(SAEnum(TipoActa, name="tipo_acta"), nullable=False)
    fecha: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.current_timestamp(), nullable=False
    )
    usuario_id: Mapped[int | None] = mapped_column(ForeignKey("usuarios.id"))
    hospital_id: Mapped[int | None] = mapped_column(ForeignKey("hospitales.id"))
    servicio_id: Mapped[int | None] = mapped_column(ForeignKey("servicios.id"))
    oficina_id: Mapped[int | None] = mapped_column(ForeignKey("oficinas.id"))
    observaciones: Mapped[str | None] = mapped_column(Text())
    pdf_path: Mapped[str | None] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.current_timestamp(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.current_timestamp(),
        onupdate=func.current_timestamp(),
        nullable=False,
    )

    usuario: Mapped["Usuario | None"] = relationship("Usuario")
    hospital: Mapped["Hospital | None"] = relationship("Hospital")
    servicio: Mapped["Servicio | None"] = relationship("Servicio")
    oficina: Mapped["Oficina | None"] = relationship("Oficina")
    items: Mapped[list["ActaItem"]] = relationship(
        "ActaItem", back_populates="acta", cascade="all, delete-orphan"
    )


class ActaItem(Base):
    """Assets included in an acta."""

    __tablename__ = "acta_items"

    id: Mapped[int] = mapped_column(primary_key=True)
    acta_id: Mapped[int] = mapped_column(ForeignKey("actas.id"), nullable=False)
    equipo_id: Mapped[int | None] = mapped_column(ForeignKey("equipos.id"))
    cantidad: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    descripcion: Mapped[str | None] = mapped_column(Text())

    acta: Mapped["Acta"] = relationship("Acta", back_populates="items")
    equipo: Mapped["Equipo | None"] = relationship("Equipo", back_populates="acta_items")


__all__ = ["Acta", "ActaItem", "TipoActa"]
