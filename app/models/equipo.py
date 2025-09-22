"""Equipment model with history tracking."""
from __future__ import annotations

from datetime import date, datetime
from enum import Enum
from typing import TYPE_CHECKING

from sqlalchemy import (
    Date,
    DateTime,
    Enum as SAEnum,
    ForeignKey,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base
from .insumo import equipo_insumos

if TYPE_CHECKING:  # pragma: no cover
    from .acta import ActaItem
    from .adjunto import Adjunto
    from .hospital import Hospital, Oficina, Servicio
    from .insumo import Insumo
    from .usuario import Usuario


class TipoEquipo(str, Enum):
    """Equipment categories."""

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
    """Operational state of the equipment."""

    OPERATIVO = "operativo"
    SERVICIO_TECNICO = "servicio_tecnico"
    DE_BAJA = "de_baja"
    PRESTADO = "prestado"


class Equipo(Base):
    """Inventoriable asset."""

    __tablename__ = "equipos"

    id: Mapped[int] = mapped_column(primary_key=True)
    codigo: Mapped[str | None] = mapped_column(String(50), unique=True)
    tipo: Mapped[TipoEquipo] = mapped_column(SAEnum(TipoEquipo, name="tipo_equipo"), nullable=False)
    estado: Mapped[EstadoEquipo] = mapped_column(
        SAEnum(EstadoEquipo, name="estado_equipo"),
        default=EstadoEquipo.OPERATIVO,
        nullable=False,
    )
    descripcion: Mapped[str | None] = mapped_column(Text())
    marca: Mapped[str | None] = mapped_column(String(100))
    modelo: Mapped[str | None] = mapped_column(String(100))
    numero_serie: Mapped[str | None] = mapped_column(String(120), index=True)
    hospital_id: Mapped[int] = mapped_column(ForeignKey("hospitales.id"), nullable=False)
    servicio_id: Mapped[int | None] = mapped_column(ForeignKey("servicios.id"))
    oficina_id: Mapped[int | None] = mapped_column(ForeignKey("oficinas.id"))
    responsable: Mapped[str | None] = mapped_column(String(120))
    fecha_compra: Mapped[date | None] = mapped_column(Date())
    fecha_instalacion: Mapped[date | None] = mapped_column(Date())
    garantia_hasta: Mapped[date | None] = mapped_column(Date())
    observaciones: Mapped[str | None] = mapped_column(Text())
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.current_timestamp(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.current_timestamp(),
        onupdate=func.current_timestamp(),
        nullable=False,
    )

    hospital: Mapped["Hospital"] = relationship("Hospital", back_populates="equipos")
    servicio: Mapped["Servicio | None"] = relationship("Servicio")
    oficina: Mapped["Oficina | None"] = relationship("Oficina", back_populates="equipos")
    insumos: Mapped[list["Insumo"]] = relationship(
        "Insumo", secondary=equipo_insumos, back_populates="equipos"
    )
    acta_items: Mapped[list["ActaItem"]] = relationship("ActaItem", back_populates="equipo")
    adjuntos: Mapped[list["Adjunto"]] = relationship("Adjunto", back_populates="equipo")
    historial: Mapped[list["EquipoHistorial"]] = relationship(
        "EquipoHistorial", back_populates="equipo", cascade="all, delete-orphan"
    )

    def registrar_evento(self, usuario: "Usuario | None", accion: str, descripcion: str | None = None) -> None:
        """Append an entry to the equipment history."""

        self.historial.append(
            EquipoHistorial(usuario=usuario, accion=accion, descripcion=descripcion)
        )


class EquipoHistorial(Base):
    """Historical actions associated with a piece of equipment."""

    __tablename__ = "equipos_historial"

    id: Mapped[int] = mapped_column(primary_key=True)
    equipo_id: Mapped[int] = mapped_column(ForeignKey("equipos.id"), nullable=False)
    usuario_id: Mapped[int | None] = mapped_column(ForeignKey("usuarios.id"))
    accion: Mapped[str] = mapped_column(String(120), nullable=False)
    descripcion: Mapped[str | None] = mapped_column(Text())
    fecha: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.current_timestamp(), nullable=False
    )

    equipo: Mapped["Equipo"] = relationship("Equipo", back_populates="historial")
    usuario: Mapped["Usuario | None"] = relationship("Usuario")


__all__ = ["TipoEquipo", "EstadoEquipo", "Equipo", "EquipoHistorial"]
