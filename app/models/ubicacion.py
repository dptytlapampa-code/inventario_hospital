"""Models describing the hospital/service/office hierarchy."""
from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base

if TYPE_CHECKING:  # pragma: no cover
    from .equipo import Equipo
    from .hospital_usuario_rol import HospitalUsuarioRol
    from .licencia import Licencia
    from .permisos import Permiso
    from .usuario import Usuario
    from .vlan import Vlan, VlanDispositivo


class Hospital(Base):
    """Hospital or health institution."""

    __tablename__ = "hospitales"

    id: Mapped[int] = mapped_column(primary_key=True)
    nombre: Mapped[str] = mapped_column(String(200), nullable=False, unique=True)
    codigo: Mapped[str | None] = mapped_column(String(20), unique=True)
    direccion: Mapped[str | None] = mapped_column(String(255), index=True)
    telefono: Mapped[str | None] = mapped_column(String(50))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.current_timestamp(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.current_timestamp(),
        onupdate=func.current_timestamp(),
        nullable=False,
    )

    servicios: Mapped[list["Servicio"]] = relationship(
        "Servicio", back_populates="hospital", cascade="all, delete-orphan"
    )
    oficinas: Mapped[list["Oficina"]] = relationship(
        "Oficina", back_populates="hospital", cascade="all, delete-orphan"
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
        "VlanDispositivo",
        back_populates="hospital",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:  # pragma: no cover - representation helper
        return f"Hospital(id={self.id!r}, nombre={self.nombre!r})"


class Servicio(Base):
    """Intermediate level grouping multiple offices."""

    __tablename__ = "servicios"
    __table_args__ = (
        UniqueConstraint("hospital_id", "nombre", name="uq_servicio_nombre_hospital"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    nombre: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    descripcion: Mapped[str | None] = mapped_column(String(255))
    hospital_id: Mapped[int] = mapped_column(
        ForeignKey("hospitales.id", ondelete="CASCADE"), nullable=False
    )

    hospital: Mapped["Hospital"] = relationship("Hospital", back_populates="servicios")
    oficinas: Mapped[list["Oficina"]] = relationship(
        "Oficina", back_populates="servicio", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:  # pragma: no cover
        return f"Servicio(id={self.id!r}, nombre={self.nombre!r})"


class Oficina(Base):
    """Concrete physical location inside a service."""

    __tablename__ = "oficinas"
    __table_args__ = (
        UniqueConstraint("servicio_id", "nombre", name="uq_oficina_nombre_servicio"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    nombre: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    piso: Mapped[str | None] = mapped_column(String(20))
    servicio_id: Mapped[int] = mapped_column(
        ForeignKey("servicios.id", ondelete="CASCADE"), nullable=False
    )
    hospital_id: Mapped[int] = mapped_column(
        ForeignKey("hospitales.id", ondelete="CASCADE"), nullable=False
    )

    servicio: Mapped["Servicio"] = relationship("Servicio", back_populates="oficinas")
    hospital: Mapped["Hospital"] = relationship("Hospital", back_populates="oficinas")
    equipos: Mapped[list["Equipo"]] = relationship("Equipo", back_populates="oficina")

    def __repr__(self) -> str:  # pragma: no cover
        return f"Oficina(id={self.id!r}, nombre={self.nombre!r})"


__all__ = ["Hospital", "Servicio", "Oficina"]
