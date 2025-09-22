"""Audit trail for user actions."""
from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base

if TYPE_CHECKING:  # pragma: no cover
    from .usuario import Usuario


class Auditoria(Base):
    """Audit entry storing who, what and when."""

    __tablename__ = "auditoria"

    id: Mapped[int] = mapped_column(primary_key=True)
    usuario_id: Mapped[int | None] = mapped_column(ForeignKey("usuarios.id"))
    accion: Mapped[str] = mapped_column(String(150), nullable=False)
    modulo: Mapped[str | None] = mapped_column(String(50))
    tabla: Mapped[str | None] = mapped_column(String(100))
    registro_id: Mapped[int | None] = mapped_column(Integer)
    ip_address: Mapped[str | None] = mapped_column(String(45))
    datos: Mapped[str | None] = mapped_column(Text())
    fecha: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.current_timestamp(), nullable=False
    )

    usuario: Mapped["Usuario | None"] = relationship("Usuario")


__all__ = ["Auditoria"]
