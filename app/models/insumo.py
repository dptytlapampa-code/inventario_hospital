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
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base

if TYPE_CHECKING:  # pragma: no cover
    from .equipo import Equipo
    from .usuario import Usuario


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

    series: Mapped[list["InsumoSerie"]] = relationship(
        "InsumoSerie", back_populates="insumo", cascade="all, delete-orphan"
    )
    asignaciones: Mapped[list["EquipoInsumo"]] = relationship(
        "EquipoInsumo", back_populates="insumo", cascade="all, delete-orphan"
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


class SerieEstado(str, Enum):
    """Estado de una unidad de insumo identificada por número de serie."""

    LIBRE = "libre"
    ASIGNADO = "asignado"
    DADO_BAJA = "dado_baja"


class InsumoSerie(Base):
    """Unidad física de un insumo con número de serie único."""

    __tablename__ = "insumo_series"

    id: Mapped[int] = mapped_column(primary_key=True)
    insumo_id: Mapped[int] = mapped_column(ForeignKey("insumos.id"), nullable=False, index=True)
    nro_serie: Mapped[str] = mapped_column(String(128), unique=True, nullable=False, index=True)
    estado: Mapped[SerieEstado] = mapped_column(
        SAEnum(SerieEstado, name="insumo_serie_estado"),
        default=SerieEstado.LIBRE,
        nullable=False,
    )
    equipo_id: Mapped[int | None] = mapped_column(ForeignKey("equipos.id"), nullable=True, index=True)

    insumo: Mapped["Insumo"] = relationship("Insumo", back_populates="series")
    equipo: Mapped["Equipo | None"] = relationship("Equipo", back_populates="insumos_series")
    asignaciones: Mapped[list["EquipoInsumo"]] = relationship(
        "EquipoInsumo", back_populates="serie", cascade="all, delete-orphan"
    )


class EquipoInsumo(Base):
    """Asociación entre un equipo y una serie de insumo con trazabilidad."""

    __tablename__ = "equipos_insumos"

    id: Mapped[int] = mapped_column(primary_key=True)
    equipo_id: Mapped[int] = mapped_column(ForeignKey("equipos.id"), nullable=False, index=True)
    insumo_id: Mapped[int] = mapped_column(ForeignKey("insumos.id"), nullable=False, index=True)
    insumo_serie_id: Mapped[int] = mapped_column(
        ForeignKey("insumo_series.id"), nullable=False, unique=True
    )
    asociado_por_id: Mapped[int | None] = mapped_column(ForeignKey("usuarios.id"))
    fecha_asociacion: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.current_timestamp(), nullable=False
    )
    fecha_desasociacion: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    __table_args__ = (
        UniqueConstraint("equipo_id", "insumo_serie_id", name="uq_equipo_serie_unica"),
    )

    equipo: Mapped["Equipo"] = relationship("Equipo", back_populates="insumos_asociados")
    insumo: Mapped["Insumo"] = relationship("Insumo", back_populates="asignaciones")
    serie: Mapped["InsumoSerie"] = relationship("InsumoSerie", back_populates="asignaciones")
    asociado_por: Mapped["Usuario | None"] = relationship("Usuario")


__all__ = [
    "Insumo",
    "InsumoMovimiento",
    "MovimientoTipo",
    "InsumoSerie",
    "EquipoInsumo",
    "SerieEstado",
]
