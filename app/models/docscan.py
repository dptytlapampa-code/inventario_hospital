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


class TipoDocscan(str, Enum):
    """Tipos de documentación escaneada."""

    NOTA = "nota"
    INFORME = "informe"
    OTRO = "otro"


class Docscan(Base):
    """Documento escaneado independiente."""

    __tablename__ = "docscan"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    tipo: Mapped[TipoDocscan] = mapped_column(SAEnum(TipoDocscan, name="tipo_docscan"), nullable=False)
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    uploaded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    usuario_id: Mapped[int | None] = mapped_column(ForeignKey("usuarios.id"), nullable=True)

    usuario: Mapped["Usuario"] = relationship("Usuario")


__all__ = ["TipoDocscan", "Docscan"]
