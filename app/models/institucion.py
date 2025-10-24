"""Institución base model used to describe health facilities."""
from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

import sqlalchemy as sa
from sqlalchemy import DateTime, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base

if TYPE_CHECKING:  # pragma: no cover
    from .equipo import Equipo
    from .hospital_usuario_rol import HospitalUsuarioRol
    from .licencia import Licencia
    from .permisos import Permiso
    from .ubicacion import Oficina, Servicio
    from .usuario import Usuario
    from .vlan import Vlan, VlanDispositivo


class Institucion(Base):
    """Entidad base para instituciones de salud provinciales."""

    __tablename__ = "instituciones"

    id: Mapped[int] = mapped_column(primary_key=True)
    nombre: Mapped[str] = mapped_column(String(255), nullable=False)
    tipo_institucion: Mapped[str] = mapped_column(String(50), nullable=False)
    codigo: Mapped[str | None] = mapped_column(String(50), nullable=True, index=True)
    localidad: Mapped[str] = mapped_column(String(120), nullable=False)
    provincia: Mapped[str] = mapped_column(String(120), nullable=False, default="La Pampa")
    zona_sanitaria: Mapped[str | None] = mapped_column(String(120), nullable=True)
    direccion: Mapped[str | None] = mapped_column(String(255), nullable=True)
    estado: Mapped[str] = mapped_column(String(50), nullable=False, default="Activa")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=sa.func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=sa.func.now(),
        onupdate=sa.func.now(),
        nullable=False,
    )

    __table_args__ = (
        UniqueConstraint("nombre", "localidad", name="uq_institucion_nombre_localidad"),
    )

    servicios: Mapped[list["Servicio"]] = relationship(
        "Servicio", back_populates="institucion", cascade="all, delete-orphan"
    )
    oficinas: Mapped[list["Oficina"]] = relationship(
        "Oficina", back_populates="institucion", cascade="all, delete-orphan"
    )
    usuarios: Mapped[list["Usuario"]] = relationship("Usuario", back_populates="hospital")
    usuarios_roles: Mapped[list["HospitalUsuarioRol"]] = relationship(
        "HospitalUsuarioRol", back_populates="hospital", cascade="all, delete-orphan"
    )
    licencias: Mapped[list["Licencia"]] = relationship("Licencia", back_populates="hospital")
    equipos: Mapped[list["Equipo"]] = relationship("Equipo", back_populates="hospital")
    permisos: Mapped[list["Permiso"]] = relationship("Permiso", back_populates="hospital")
    vlans: Mapped[list["Vlan"]] = relationship(
        "Vlan", back_populates="hospital", cascade="all, delete-orphan"
    )
    vlan_dispositivos: Mapped[list["VlanDispositivo"]] = relationship(
        "VlanDispositivo", back_populates="hospital", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:  # pragma: no cover - helper for debugging
        return f"Institucion(id={self.id!r}, nombre={self.nombre!r})"


__all__ = ["Institucion"]

# Compatibilidad: permitir que el nombre "Hospital" resuelva al nuevo modelo.
Base.registry._class_registry.setdefault("Hospital", Institucion)
