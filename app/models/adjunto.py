"""Attachment model for equipment documents."""
from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Enum as SAEnum, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base

if TYPE_CHECKING:  # pragma: no cover
    from .equipo import Equipo
    from .usuario import Usuario


class TipoAdjunto(str, Enum):
    """Attachment types."""

    FACTURA = "factura"
    PRESUPUESTO = "presupuesto"
    ACTA = "acta"
    PLANILLA_PATRIMONIAL = "planilla_patrimonial"
    REMITO = "remito"
    OTRO = "otro"


class Adjunto(Base):
    """Document attached to an equipment."""

    __tablename__ = "adjuntos"

    id: Mapped[int] = mapped_column(primary_key=True)
    equipo_id: Mapped[int] = mapped_column(ForeignKey("equipos.id"), nullable=False)
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    path: Mapped[str] = mapped_column(String(255), nullable=False)
    tipo: Mapped[TipoAdjunto] = mapped_column(SAEnum(TipoAdjunto, name="tipo_adjunto"), nullable=False)
    descripcion: Mapped[str | None] = mapped_column(Text())
    uploaded_by_id: Mapped[int | None] = mapped_column(ForeignKey("usuarios.id"))
    uploaded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.current_timestamp(), nullable=False
    )

    equipo: Mapped["Equipo"] = relationship("Equipo", back_populates="adjuntos")
    uploaded_by: Mapped["Usuario | None"] = relationship("Usuario")


__all__ = ["TipoAdjunto", "Adjunto"]
