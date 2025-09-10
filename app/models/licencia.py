from __future__ import annotations

from datetime import datetime
from enum import Enum

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


class Base(DeclarativeBase):
    """Base class for SQLAlchemy models."""


class TipoLicencia(str, Enum):
    """Tipos válidos de licencias."""

    TEMPORAL = "temporal"
    PERMANENTE = "permanente"


class EstadoLicencia(str, Enum):
    """Estados válidos de una licencia."""

    ACTIVA = "activa"
    INACTIVA = "inactiva"
    EXPIRADA = "expirada"
    REVOCADA = "revocada"


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

    usuario = relationship("Usuario", back_populates="licencias")
    hospital = relationship("Hospital", back_populates="licencias")


__all__ = [
    "Base",
    "TipoLicencia",
    "EstadoLicencia",
    "Licencia",
]
