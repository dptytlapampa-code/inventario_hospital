from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Table,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base

if TYPE_CHECKING:  # pragma: no cover
    from .equipo import Equipo


equipo_insumos = Table(
    "equipo_insumos",
    Base.metadata,
    Column("equipo_id", ForeignKey("equipos.id"), primary_key=True),
    Column("insumo_id", ForeignKey("insumos.id"), primary_key=True),
)


class Insumo(Base):
    """Modelo de insumo o componente con stock."""

    __tablename__ = "insumos"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    nombre: Mapped[str] = mapped_column(String(100), nullable=False)
    numero_serie: Mapped[str | None] = mapped_column(String(100), index=True)
    stock: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    equipos: Mapped[list["Equipo"]] = relationship(
        "Equipo", secondary=equipo_insumos, back_populates="insumos"
    )


__all__ = ["Insumo", "equipo_insumos"]
