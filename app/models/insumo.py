"""Models representing consumables and their stock movements."""
from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING

from sqlalchemy import (
    Column,
    DateTime,
    Enum as SAEnum,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Table,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base

if TYPE_CHECKING:  # pragma: no cover
    from .equipo import Equipo
    from .usuario import Usuario


equipo_insumos = Table(
    "equipo_insumos",
    Base.metadata,
    Column("equipo_id", ForeignKey("equipos.id"), primary_key=True),
    Column("insumo_id", ForeignKey("insumos.id"), primary_key=True),
)


class MovimientoTipo(str, Enum):
    """Types of stock movement."""

    INGRESO = "ingreso"
    EGRESO = "egreso"


class Insumo(Base):
    """Consumable or component with stock."""

    __tablename__ = "insumos"

    id: Mapped[int] = mapped_column(primary_key=True)
    nombre: Mapped[str] = mapped_column(String(120), nullable=False)
    numero_serie: Mapped[str | None] = mapped_column(String(100), index=True)
    descripcion: Mapped[str | None] = mapped_column(Text())
    unidad_medida: Mapped[str | None] = mapped_column(String(20))
    stock: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    stock_minimo: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    costo_unitario: Mapped[float | None] = mapped_column(Numeric(10, 2))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.current_timestamp(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.current_timestamp(),
        onupdate=func.current_timestamp(),
        nullable=False,
    )

    equipos: Mapped[list["Equipo"]] = relationship(
        "Equipo", secondary=equipo_insumos, back_populates="insumos"
    )
    movimientos: Mapped[list["InsumoMovimiento"]] = relationship(
        "InsumoMovimiento", back_populates="insumo", cascade="all, delete-orphan"
    )

    def ajustar_stock(self, cantidad: int) -> None:
        """Increment or decrement stock ensuring it never goes negative."""

        nuevo = self.stock + cantidad
        if nuevo < 0:
            raise ValueError("El stock no puede quedar negativo")
        self.stock = nuevo


class InsumoMovimiento(Base):
    """Individual stock movement entry."""

    __tablename__ = "insumo_movimientos"

    id: Mapped[int] = mapped_column(primary_key=True)
    insumo_id: Mapped[int] = mapped_column(ForeignKey("insumos.id"), nullable=False)
    usuario_id: Mapped[int | None] = mapped_column(ForeignKey("usuarios.id"))
    equipo_id: Mapped[int | None] = mapped_column(ForeignKey("equipos.id"))
    tipo: Mapped[MovimientoTipo] = mapped_column(
        SAEnum(MovimientoTipo, name="tipo_movimiento"), nullable=False
    )
    cantidad: Mapped[int] = mapped_column(Integer, nullable=False)
    motivo: Mapped[str | None] = mapped_column(String(255))
    observaciones: Mapped[str | None] = mapped_column(Text())
    fecha: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.current_timestamp(), nullable=False
    )

    insumo: Mapped["Insumo"] = relationship("Insumo", back_populates="movimientos")
    usuario: Mapped["Usuario | None"] = relationship("Usuario")
    equipo: Mapped["Equipo | None"] = relationship("Equipo")


__all__ = ["Insumo", "InsumoMovimiento", "MovimientoTipo", "equipo_insumos"]
