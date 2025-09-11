from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING

from sqlalchemy import (
    DateTime,
    Enum as SAEnum,
    ForeignKey,
    String,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base

if TYPE_CHECKING:  # pragma: no cover
    from .usuario import Usuario
    from .hospital import Hospital
    from .equipo import Equipo


class TipoActa(str, Enum):
    """Tipos de acta."""

    ENTREGA = "entrega"
    PRESTAMO = "prestamo"
    TRANSFERENCIA = "transferencia"


class Acta(Base):
    """Acta generada por el sistema."""

    __tablename__ = "actas"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    tipo: Mapped[TipoActa] = mapped_column(SAEnum(TipoActa, name="tipo_acta"), nullable=False)
    fecha: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    usuario_id: Mapped[int | None] = mapped_column(ForeignKey("usuarios.id"), nullable=True)
    hospital_id: Mapped[int | None] = mapped_column(ForeignKey("hospitales.id"), nullable=True)

    usuario: Mapped["Usuario"] = relationship("Usuario")
    hospital: Mapped["Hospital"] = relationship("Hospital")
    items: Mapped[list["ActaItem"]] = relationship("ActaItem", back_populates="acta")


class ActaItem(Base):
    """Ítems asociados a un acta."""

    __tablename__ = "acta_items"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    acta_id: Mapped[int] = mapped_column(ForeignKey("actas.id"), index=True)
    equipo_id: Mapped[int] = mapped_column(ForeignKey("equipos.id"), index=True)
    descripcion: Mapped[str | None] = mapped_column(String(255))

    acta: Mapped["Acta"] = relationship("Acta", back_populates="items")
    equipo: Mapped["Equipo"] = relationship("Equipo", back_populates="acta_items")


__all__ = ["TipoActa", "Acta", "ActaItem"]
