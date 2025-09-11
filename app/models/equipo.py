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
from .insumo import equipo_insumos

if TYPE_CHECKING:  # pragma: no cover
    from .hospital import Hospital
    from .acta import ActaItem
    from .adjunto import Adjunto
    from .insumo import Insumo


class TipoEquipo(str, Enum):
    """Tipos predefinidos de equipos."""

    IMPRESORA = "impresora"
    ROUTER = "router"
    SWITCH = "switch"
    NOTEBOOK = "notebook"
    CPU = "cpu"
    MONITOR = "monitor"
    ACCESS_POINT = "access_point"
    SCANNER = "scanner"
    PROYECTOR = "proyector"
    TELEFONO_IP = "telefono_ip"
    UPS = "ups"
    OTRO = "otro"


class EstadoEquipo(str, Enum):
    """Estados posibles del equipo."""

    OPERATIVO = "operativo"
    SERVICIO_TECNICO = "servicio_tecnico"
    DE_BAJA = "de_baja"


class Equipo(Base):
    """Modelo de equipo inventariable."""

    __tablename__ = "equipos"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    tipo: Mapped[TipoEquipo] = mapped_column(SAEnum(TipoEquipo, name="tipo_equipo"), nullable=False)
    estado: Mapped[EstadoEquipo] = mapped_column(
        SAEnum(EstadoEquipo, name="estado_equipo"),
        default=EstadoEquipo.OPERATIVO,
        nullable=False,
    )
    descripcion: Mapped[str | None] = mapped_column(String(255))
    numero_serie: Mapped[str | None] = mapped_column(String(100), index=True)
    hospital_id: Mapped[int] = mapped_column(ForeignKey("hospitales.id"), index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    hospital: Mapped["Hospital"] = relationship("Hospital", backref="equipos")
    insumos: Mapped[list["Insumo"]] = relationship(
        "Insumo", secondary=equipo_insumos, back_populates="equipos"
    )
    acta_items: Mapped[list["ActaItem"]] = relationship("ActaItem", back_populates="equipo")
    adjuntos: Mapped[list["Adjunto"]] = relationship("Adjunto", back_populates="equipo")


__all__ = ["TipoEquipo", "EstadoEquipo", "Equipo"]
