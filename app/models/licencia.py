"""License model storing leave requests and workflow state."""
from __future__ import annotations

from datetime import date, datetime, timedelta
from enum import Enum
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Date, DateTime, Enum as SAEnum, ForeignKey, Index, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base

if TYPE_CHECKING:  # pragma: no cover
    from .hospital import Hospital
    from .usuario import Usuario


class TipoLicencia(str, Enum):
    """Types of licenses."""

    TEMPORAL = "temporal"
    PERMANENTE = "permanente"
    ESPECIAL = "especial"


class EstadoLicencia(str, Enum):
    """Workflow states for a license."""

    BORRADOR = "borrador"
    PENDIENTE = "pendiente"
    APROBADA = "aprobada"
    RECHAZADA = "rechazada"
    CANCELADA = "cancelada"


class Licencia(Base):
    """Leave request workflow for users."""

    __tablename__ = "licencias"
    __table_args__ = (Index("ix_licencias_estado_tipo", "estado", "tipo"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    usuario_id: Mapped[int] = mapped_column(ForeignKey("usuarios.id"), nullable=False)
    hospital_id: Mapped[int | None] = mapped_column(ForeignKey("hospitales.id"))
    tipo: Mapped[TipoLicencia] = mapped_column(
        SAEnum(TipoLicencia, name="tipo_licencia"), nullable=False
    )
    estado: Mapped[EstadoLicencia] = mapped_column(
        SAEnum(EstadoLicencia, name="estado_licencia"), default=EstadoLicencia.BORRADOR, nullable=False
    )
    fecha_inicio: Mapped[date] = mapped_column(Date(), nullable=False)
    fecha_fin: Mapped[date] = mapped_column(Date(), nullable=False)
    motivo: Mapped[str] = mapped_column(Text(), nullable=False)
    comentario: Mapped[str | None] = mapped_column(Text())
    requires_replacement: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    reemplazo_id: Mapped[int | None] = mapped_column(ForeignKey("usuarios.id"))
    aprobado_por_id: Mapped[int | None] = mapped_column(ForeignKey("usuarios.id"))
    aprobado_en: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.current_timestamp(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.current_timestamp(),
        onupdate=func.current_timestamp(),
        nullable=False,
    )

    usuario: Mapped["Usuario"] = relationship(
        "Usuario", back_populates="licencias", foreign_keys=[usuario_id]
    )
    hospital: Mapped["Hospital | None"] = relationship("Hospital", back_populates="licencias")
    reemplazo: Mapped["Usuario | None"] = relationship(
        "Usuario", foreign_keys=[reemplazo_id], back_populates="reemplazos"
    )
    aprobado_por: Mapped["Usuario | None"] = relationship(
        "Usuario", foreign_keys=[aprobado_por_id]
    )

    def dias_habiles(self) -> int:
        """Return the number of business days for the license period."""

        if self.fecha_fin < self.fecha_inicio:
            raise ValueError("La fecha de fin debe ser posterior a la fecha de inicio")
        dias = 0
        delta = (self.fecha_fin - self.fecha_inicio).days + 1
        for i in range(delta):
            dia = self.fecha_inicio + timedelta(days=i)
            if dia.weekday() < 5:
                dias += 1
        return dias

    def enviar_pendiente(self) -> None:
        if self.estado != EstadoLicencia.BORRADOR:
            raise ValueError("Solo se puede enviar una licencia en borrador")
        self.estado = EstadoLicencia.PENDIENTE

    def aprobar(self, aprobador: "Usuario", fecha: datetime | None = None) -> None:
        if self.estado not in {EstadoLicencia.PENDIENTE, EstadoLicencia.BORRADOR}:
            raise ValueError("La licencia debe estar pendiente para aprobarse")
        if self.requires_replacement and not self.reemplazo_id:
            raise ValueError("Debe asignar un reemplazo antes de aprobar")
        self.estado = EstadoLicencia.APROBADA
        self.aprobado_por = aprobador
        self.aprobado_en = fecha or datetime.utcnow()

    def rechazar(self, aprobador: "Usuario", comentario: str | None = None) -> None:
        if self.estado != EstadoLicencia.PENDIENTE:
            raise ValueError("Solo se puede rechazar una licencia pendiente")
        self.estado = EstadoLicencia.RECHAZADA
        self.aprobado_por = aprobador
        self.aprobado_en = datetime.utcnow()
        if comentario:
            self.comentario = comentario

    def cancelar(self, usuario: "Usuario") -> None:
        if self.estado not in {EstadoLicencia.BORRADOR, EstadoLicencia.PENDIENTE}:
            raise ValueError("Solo se puede cancelar licencias pendientes o en borrador")
        self.estado = EstadoLicencia.CANCELADA
        self.aprobado_por = usuario
        self.aprobado_en = datetime.utcnow()

    def se_superpone(self, otra: "Licencia") -> bool:
        return max(self.fecha_inicio, otra.fecha_inicio) <= min(self.fecha_fin, otra.fecha_fin)
