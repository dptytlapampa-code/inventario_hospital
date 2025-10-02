"""Equipment model with history tracking."""
from __future__ import annotations

import re
from datetime import date, datetime
from enum import Enum
from typing import TYPE_CHECKING
from unicodedata import normalize

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    Enum as SAEnum,
    ForeignKey,
    Integer,
    String,
    Text,
    event,
    func,
    Index,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base
if TYPE_CHECKING:  # pragma: no cover
    from .acta import ActaItem
    from .adjunto import Adjunto
    from .equipo_adjunto import EquipoAdjunto
    from .hospital import Hospital, Oficina, Servicio
    from .insumo import EquipoInsumo, Insumo, InsumoSerie
    from .usuario import Usuario


class TipoEquipo(Base):
    """Catalogue of equipment types managed by superadmins."""

    __tablename__ = "tipo_equipo"

    id: Mapped[int] = mapped_column(primary_key=True)
    slug: Mapped[str] = mapped_column(String(80), unique=True, nullable=False)
    nombre: Mapped[str] = mapped_column(String(160), unique=True, nullable=False)
    descripcion: Mapped[str | None] = mapped_column(Text())
    activo: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.current_timestamp(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.current_timestamp(),
        onupdate=func.current_timestamp(),
        nullable=False,
    )

    equipos: Mapped[list["Equipo"]] = relationship("Equipo", back_populates="tipo")

    def __repr__(self) -> str:  # pragma: no cover - debugging helper
        return (
            "TipoEquipo("
            f"id={self.id!r}, slug={self.slug!r}, nombre={self.nombre!r}, activo={self.activo!r}"
            ")"
        )

    @staticmethod
    def _slug_source(value: str | None) -> str:
        return (value or "").strip()

    @classmethod
    def slug_from_nombre(cls, value: str | None) -> str:
        base = cls._slug_source(value)
        if not base:
            return "tipo"
        normalized = normalize("NFKD", base).encode("ascii", "ignore").decode("ascii")
        slug = re.sub(r"[^a-z0-9]+", "-", normalized.lower()).strip("-")
        return slug or "tipo"


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
    tipo_id: Mapped[int] = mapped_column(ForeignKey("tipo_equipo.id"), nullable=False)
    estado: Mapped[EstadoEquipo] = mapped_column(
        SAEnum(EstadoEquipo, name="estado_equipo"),
        default=EstadoEquipo.OPERATIVO,
        nullable=False,
    )
    descripcion: Mapped[str | None] = mapped_column(Text())
    marca: Mapped[str | None] = mapped_column(String(100), index=True)
    modelo: Mapped[str | None] = mapped_column(String(100), index=True)
    numero_serie: Mapped[str | None] = mapped_column(String(120), index=True)
    sin_numero_serie: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    hospital_id: Mapped[int] = mapped_column(ForeignKey("hospitales.id"), nullable=False)
    servicio_id: Mapped[int | None] = mapped_column(ForeignKey("servicios.id"))
    oficina_id: Mapped[int | None] = mapped_column(ForeignKey("oficinas.id"))
    responsable: Mapped[str | None] = mapped_column(String(120))
    fecha_ingreso: Mapped[date | None] = mapped_column("fecha_compra", Date())
    fecha_instalacion: Mapped[date | None] = mapped_column(Date())
    garantia_hasta: Mapped[date | None] = mapped_column(Date())
    observaciones: Mapped[str | None] = mapped_column(Text())
    es_nuevo: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    expediente: Mapped[str | None] = mapped_column(String(120))
    anio_expediente: Mapped[int | None] = mapped_column(Integer())
    orden_compra: Mapped[str | None] = mapped_column(String(120))
    tipo_adquisicion: Mapped[str | None] = mapped_column(String(50))
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
    tipo: Mapped["TipoEquipo"] = relationship("TipoEquipo", back_populates="equipos")
    servicio: Mapped["Servicio | None"] = relationship("Servicio")
    oficina: Mapped["Oficina | None"] = relationship("Oficina", back_populates="equipos")
    insumos_asociados: Mapped[list["EquipoInsumo"]] = relationship(
        "EquipoInsumo",
        back_populates="equipo",
        cascade="all, delete-orphan",
    )
    insumos_series: Mapped[list["InsumoSerie"]] = relationship(
        "InsumoSerie",
        back_populates="equipo",
    )
    acta_items: Mapped[list["ActaItem"]] = relationship("ActaItem", back_populates="equipo")
    adjuntos: Mapped[list["Adjunto"]] = relationship("Adjunto", back_populates="equipo")
    archivos: Mapped[list["EquipoAdjunto"]] = relationship(
        "EquipoAdjunto", back_populates="equipo", cascade="all, delete-orphan"
    )
    historial: Mapped[list["EquipoHistorial"]] = relationship(
        "EquipoHistorial", back_populates="equipo", cascade="all, delete-orphan"
    )

    @property
    def titulo(self) -> str:
        """Return a human friendly title for listings and detail views."""

        tipo_nombre = (self.tipo.nombre if self.tipo and self.tipo.nombre else "").strip()
        marca = (self.marca or "").strip()
        modelo = (self.modelo or "").strip()
        marca_modelo = " ".join(part for part in [marca, modelo] if part)
        if tipo_nombre and marca_modelo:
            return f"{tipo_nombre} - {marca_modelo}"
        if tipo_nombre:
            return tipo_nombre
        return marca_modelo or "Equipo"

    def registrar_evento(self, usuario: "Usuario | None", accion: str, descripcion: str | None = None) -> None:
        """Append an entry to the equipment history."""

        self.historial.append(
            EquipoHistorial(usuario=usuario, accion=accion, descripcion=descripcion)
        )

    @property
    def insumos(self) -> list["Insumo"]:
        """Return insumos currently asociados al equipo (compat API)."""

        activos = [
            asignacion
            for asignacion in self.insumos_asociados
            if asignacion.fecha_desasociacion is None
        ]
        vistos: set[int] = set()
        resultado: list["Insumo"] = []
        for asignacion in activos:
            if asignacion.insumo_id in vistos:
                continue
            vistos.add(asignacion.insumo_id)
            resultado.append(asignacion.insumo)
        return resultado


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


def _ensure_tipo_equipo_slug(target: TipoEquipo) -> None:
    target.slug = TipoEquipo.slug_from_nombre(target.slug or target.nombre)


@event.listens_for(TipoEquipo, "before_insert")
def _tipo_equipo_before_insert(mapper, connection, target: TipoEquipo) -> None:  # pragma: no cover
    _ensure_tipo_equipo_slug(target)


@event.listens_for(TipoEquipo, "before_update")
def _tipo_equipo_before_update(mapper, connection, target: TipoEquipo) -> None:  # pragma: no cover
    _ensure_tipo_equipo_slug(target)


Index("ix_equipos_descripcion", Equipo.descripcion)
