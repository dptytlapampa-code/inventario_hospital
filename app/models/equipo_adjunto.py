"""Binary attachments associated to equipment records."""
from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base

if TYPE_CHECKING:  # pragma: no cover
    from .equipo import Equipo
    from .usuario import Usuario


class EquipoAdjunto(Base):
    """Stores uploaded files linked to equipment entries."""

    __tablename__ = "equipos_adjuntos"

    id: Mapped[int] = mapped_column(primary_key=True)
    equipo_id: Mapped[int] = mapped_column(ForeignKey("equipos.id"), nullable=False, index=True)
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    filepath: Mapped[str] = mapped_column(String(255), nullable=False)
    mime_type: Mapped[str] = mapped_column(String(120), nullable=False)
    uploaded_by_id: Mapped[int | None] = mapped_column(ForeignKey("usuarios.id"))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.current_timestamp(), nullable=False
    )

    equipo: Mapped["Equipo"] = relationship("Equipo", back_populates="archivos")
    uploaded_by: Mapped["Usuario | None"] = relationship("Usuario")


__all__ = ["EquipoAdjunto"]
