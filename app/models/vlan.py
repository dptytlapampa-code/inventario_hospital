"""Models to manage VLAN catalogues and registered devices."""
from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base

if TYPE_CHECKING:  # pragma: no cover
    from .hospital import Hospital, Oficina, Servicio


class Vlan(Base):
    """Representa una VLAN registrada dentro de la organización."""

    __tablename__ = "vlans"
    __table_args__ = (
        UniqueConstraint(
            "hospital_id",
            "identificador",
            name="uq_vlan_hospital_identificador",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    nombre: Mapped[str] = mapped_column(String(120), nullable=False)
    identificador: Mapped[str] = mapped_column(String(50), nullable=False)
    descripcion: Mapped[str | None] = mapped_column(String(255))
    hospital_id: Mapped[int] = mapped_column(
        ForeignKey("instituciones.id", ondelete="CASCADE"), nullable=False
    )
    servicio_id: Mapped[int | None] = mapped_column(
        ForeignKey("servicios.id", ondelete="SET NULL")
    )
    oficina_id: Mapped[int | None] = mapped_column(
        ForeignKey("oficinas.id", ondelete="SET NULL")
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.current_timestamp(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.current_timestamp(),
        onupdate=func.current_timestamp(),
        nullable=False,
    )

    hospital: Mapped["Hospital"] = relationship("Hospital", back_populates="vlans")
    servicio: Mapped["Servicio | None"] = relationship("Servicio")
    oficina: Mapped["Oficina | None"] = relationship("Oficina")
    dispositivos: Mapped[list["VlanDispositivo"]] = relationship(
        "VlanDispositivo",
        back_populates="vlan",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:  # pragma: no cover - helper
        return f"Vlan(id={self.id!r}, identificador={self.identificador!r})"


class VlanDispositivo(Base):
    """Dispositivo con IP fija registrado dentro de una VLAN."""

    __tablename__ = "vlan_dispositivos"
    __table_args__ = (
        UniqueConstraint(
            "direccion_ip",
            name="uq_vlan_dispositivo_ip",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    vlan_id: Mapped[int] = mapped_column(
        ForeignKey("vlans.id", ondelete="CASCADE"), nullable=False
    )
    nombre_equipo: Mapped[str] = mapped_column(String(150), nullable=False)
    host: Mapped[str | None] = mapped_column(String(120))
    direccion_ip: Mapped[str] = mapped_column(String(45), nullable=False)
    direccion_mac: Mapped[str | None] = mapped_column(String(32))
    hospital_id: Mapped[int] = mapped_column(
        ForeignKey("instituciones.id", ondelete="CASCADE"), nullable=False
    )
    servicio_id: Mapped[int | None] = mapped_column(
        ForeignKey("servicios.id", ondelete="SET NULL")
    )
    oficina_id: Mapped[int | None] = mapped_column(
        ForeignKey("oficinas.id", ondelete="SET NULL")
    )
    notas: Mapped[str | None] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.current_timestamp(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.current_timestamp(),
        onupdate=func.current_timestamp(),
        nullable=False,
    )

    vlan: Mapped["Vlan"] = relationship("Vlan", back_populates="dispositivos")
    hospital: Mapped["Hospital"] = relationship("Hospital", back_populates="vlan_dispositivos")
    servicio: Mapped["Servicio | None"] = relationship("Servicio")
    oficina: Mapped["Oficina | None"] = relationship("Oficina")

    def __repr__(self) -> str:  # pragma: no cover - helper
        return f"VlanDispositivo(id={self.id!r}, ip={self.direccion_ip!r})"


__all__ = ["Vlan", "VlanDispositivo"]
