"""Model for scanned documents not tied to a specific equipment."""
from __future__ import annotations

from datetime import date, datetime
from enum import Enum
from typing import TYPE_CHECKING

from sqlalchemy import Date, DateTime, Enum as SAEnum, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base

if TYPE_CHECKING:  # pragma: no cover
    from .hospital import Hospital, Oficina, Servicio
    from .usuario import Usuario


class TipoDocscan(str, Enum):
    """Types for scanned documentation."""

    NOTA = "nota"
    INFORME = "informe"
    CONTRATO = "contrato"
    OTRO = "otro"


class Docscan(Base):
    """Scanned document with metadata."""

    __tablename__ = "docscan"

    id: Mapped[int] = mapped_column(primary_key=True)
    titulo: Mapped[str] = mapped_column(String(150), nullable=False)
    tipo: Mapped[TipoDocscan] = mapped_column(SAEnum(TipoDocscan, name="tipo_docscan"), nullable=False)
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    path: Mapped[str] = mapped_column(String(255), nullable=False)
    fecha_documento: Mapped[date | None] = mapped_column(Date())
    comentario: Mapped[str | None] = mapped_column(Text())
    usuario_id: Mapped[int | None] = mapped_column(ForeignKey("usuarios.id"))
    hospital_id: Mapped[int | None] = mapped_column(ForeignKey("hospitales.id"))
    servicio_id: Mapped[int | None] = mapped_column(ForeignKey("servicios.id"))
    oficina_id: Mapped[int | None] = mapped_column(ForeignKey("oficinas.id"))
    uploaded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.current_timestamp(), nullable=False
    )

    usuario: Mapped["Usuario | None"] = relationship("Usuario")
    hospital: Mapped["Hospital | None"] = relationship("Hospital")
    servicio: Mapped["Servicio | None"] = relationship("Servicio")
    oficina: Mapped["Oficina | None"] = relationship("Oficina")


__all__ = ["Docscan", "TipoDocscan"]
