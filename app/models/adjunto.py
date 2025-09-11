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
    from .equipo import Equipo


class TipoAdjunto(str, Enum):
    """Tipos de documentos adjuntos."""

    FACTURA = "factura"
    PRESUPUESTO = "presupuesto"
    ACTA = "acta"
    PLANILLA_PATRIMONIAL = "planilla_patrimonial"
    OTRO = "otro"


class Adjunto(Base):
    """Documento adjunto a un equipo."""

    __tablename__ = "adjuntos"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    equipo_id: Mapped[int] = mapped_column(ForeignKey("equipos.id"), index=True)
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    tipo: Mapped[TipoAdjunto] = mapped_column(SAEnum(TipoAdjunto, name="tipo_adjunto"), nullable=False)
    uploaded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    equipo: Mapped["Equipo"] = relationship("Equipo", back_populates="adjuntos")


__all__ = ["TipoAdjunto", "Adjunto"]
