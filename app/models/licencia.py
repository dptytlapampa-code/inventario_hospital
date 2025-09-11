from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum as SAEnum,
    ForeignKey,
    Index,
    Integer,
    func,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

if TYPE_CHECKING:  # pragma: no cover - only for type checking
    from .hospital import Hospital
    from .usuario import Usuario


class Base(DeclarativeBase):
    """Base class for SQLAlchemy models."""


class TipoLicencia(str, Enum):
    """Tipos válidos de licencias."""

    TEMPORAL = "temporal"
    PERMANENTE = "permanente"


from .base_enums import EstadoLicencia


class Licencia(Base):
    """Modelo de licencia."""

    __tablename__ = "licencias"
    __table_args__ = (
        Index("ix_licencias_estado_tipo", "estado", "tipo"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    usuario_id: Mapped[int] = mapped_column(ForeignKey("usuarios.id"), index=True)
    hospital_id: Mapped[int | None] = mapped_column(
        ForeignKey("hospitales.id"), index=True, nullable=True
    )
    tipo: Mapped[TipoLicencia] = mapped_column(
        SAEnum(TipoLicencia, name="tipo_licencia"), nullable=False
    )
    estado: Mapped[EstadoLicencia] = mapped_column(
        SAEnum(EstadoLicencia, name="estado_licencia"), nullable=False
    )
    requires_replacement: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    usuario: Mapped["Usuario"] = relationship(
        "Usuario", back_populates="licencias"
    )
    hospital: Mapped["Hospital"] = relationship(
        "Hospital", back_populates="licencias"
    )


__all__ = [
    "Base",
    "TipoLicencia",
    "EstadoLicencia",
    "Licencia",
]
