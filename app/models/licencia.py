"""SQLAlchemy model describing leave requests for users."""
from __future__ import annotations

from datetime import date, datetime, timedelta
from enum import Enum
from typing import TYPE_CHECKING

from sqlalchemy import Date, DateTime, Enum as SAEnum, ForeignKey, Index, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base

if TYPE_CHECKING:  # pragma: no cover
    from .hospital import Hospital
    from .usuario import Usuario


class TipoLicencia(str, Enum):
    """Supported license types."""

    VACACIONES = "vacaciones"
    ENFERMEDAD = "enfermedad"
    ESTUDIO = "estudio"
    OTRO = "otro"


class EstadoLicencia(str, Enum):
    """Workflow states for a license request."""

    SOLICITADA = "solicitada"
    APROBADA = "aprobada"
    RECHAZADA = "rechazada"
    CANCELADA = "cancelada"


class Licencia(Base):
    """Leave request workflow for users."""

    __tablename__ = "licencias"
    __table_args__ = (
        Index("ix_licencias_user_id", "user_id"),
        Index("ix_licencias_estado", "estado"),
        Index("ix_licencias_fecha_inicio_fecha_fin", "fecha_inicio", "fecha_fin"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("usuarios.id"), nullable=False)
    hospital_id: Mapped[int | None] = mapped_column(ForeignKey("instituciones.id"))
    tipo: Mapped[TipoLicencia] = mapped_column(
        SAEnum(TipoLicencia, name="tipo_licencia"), nullable=False
    )
    fecha_inicio: Mapped[date] = mapped_column(Date(), nullable=False)
    fecha_fin: Mapped[date] = mapped_column(Date(), nullable=False)
    motivo: Mapped[str] = mapped_column(Text(), nullable=False)
    estado: Mapped[EstadoLicencia] = mapped_column(
        SAEnum(EstadoLicencia, name="estado_licencia"),
        default=EstadoLicencia.SOLICITADA,
        server_default=EstadoLicencia.SOLICITADA.value,
        nullable=False,
    )
    motivo_rechazo: Mapped[str | None] = mapped_column(Text())
    decidido_por: Mapped[int | None] = mapped_column(ForeignKey("usuarios.id"))
    decidido_en: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
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
        "Usuario", back_populates="licencias", foreign_keys=[user_id]
    )
    hospital: Mapped["Hospital | None"] = relationship("Hospital", back_populates="licencias")
    decisor: Mapped["Usuario | None"] = relationship(
        "Usuario", foreign_keys=[decidido_por], back_populates="licencias_decididas"
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

    def aprobar(self, aprobador: "Usuario", fecha: datetime | None = None) -> None:
        """Mark the license as approved by ``aprobador``."""

        if self.estado != EstadoLicencia.SOLICITADA:
            raise ValueError("La licencia debe estar solicitada para aprobarse")
        self.estado = EstadoLicencia.APROBADA
        self.decisor = aprobador
        self.decidido_en = fecha or datetime.utcnow()

    def rechazar(self, aprobador: "Usuario", motivo: str | None = None) -> None:
        """Reject the license request."""

        if self.estado != EstadoLicencia.SOLICITADA:
            raise ValueError("Solo se puede rechazar una licencia solicitada")
        self.estado = EstadoLicencia.RECHAZADA
        self.decisor = aprobador
        self.decidido_en = datetime.utcnow()
        self.motivo_rechazo = (motivo or "").strip() or None

    def cancelar(self, usuario: "Usuario") -> None:
        """Cancel the license request."""

        if self.estado not in {EstadoLicencia.SOLICITADA, EstadoLicencia.APROBADA}:
            raise ValueError("Solo se puede cancelar licencias solicitadas o aprobadas")
        self.estado = EstadoLicencia.CANCELADA
        self.decisor = usuario
        self.decidido_en = datetime.utcnow()

    def se_superpone(self, otra: "Licencia") -> bool:
        """Return True if the license range overlaps with ``otra``."""

        return max(self.fecha_inicio, otra.fecha_inicio) <= min(self.fecha_fin, otra.fecha_fin)


__all__ = ["Licencia", "TipoLicencia", "EstadoLicencia"]
