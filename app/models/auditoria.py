"""Audit trail for user actions."""
from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Integer, JSON, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base

if TYPE_CHECKING:  # pragma: no cover
    from .hospital import Hospital
    from .usuario import Usuario


class Auditoria(Base):
    """Audit entry storing who, what and when."""

    __tablename__ = "auditorias"

    id: Mapped[int] = mapped_column(primary_key=True)
    usuario_id: Mapped[int | None] = mapped_column(ForeignKey("usuarios.id"))
    hospital_id: Mapped[int | None] = mapped_column(ForeignKey("instituciones.id"))
    modulo: Mapped[str | None] = mapped_column(String(50))
    accion: Mapped[str] = mapped_column(String(50), nullable=False)
    entidad: Mapped[str | None] = mapped_column(String(50))
    entidad_id: Mapped[int | None] = mapped_column(Integer)
    descripcion: Mapped[str | None] = mapped_column(Text())
    cambios: Mapped[dict | None] = mapped_column(JSON)
    ip_address: Mapped[str | None] = mapped_column(String(45))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.current_timestamp(), nullable=False
    )

    usuario: Mapped["Usuario | None"] = relationship("Usuario")
    hospital: Mapped["Hospital | None"] = relationship("Hospital")


__all__ = ["Auditoria"]
