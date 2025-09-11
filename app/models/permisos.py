from __future__ import annotations

from enum import Enum
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Enum as SAEnum, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base

if TYPE_CHECKING:  # pragma: no cover
    from .rol import Rol
    from .hospital import Hospital


class Modulo(str, Enum):
    """Módulos del sistema sobre los que se otorgan permisos."""

    INVENTARIO = "inventario"
    INSUMOS = "insumos"
    ACTAS = "actas"
    ADJUNTOS = "adjuntos"
    DOCSCAN = "docscan"
    REPORTES = "reportes"
    AUDITORIA = "auditoria"
    LICENCIAS = "licencias"


class Permiso(Base):
    """Permisos por rol y hospital (lectura/escritura)."""

    __tablename__ = "permisos"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    rol_id: Mapped[int] = mapped_column(ForeignKey("roles.id"), index=True, nullable=False)
    modulo: Mapped[Modulo] = mapped_column(SAEnum(Modulo, name="modulo_permiso"), nullable=False)
    hospital_id: Mapped[int | None] = mapped_column(ForeignKey("hospitales.id"), index=True, nullable=True)
    can_read: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    can_write: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    rol: Mapped["Rol"] = relationship("Rol", back_populates="permisos")
    hospital: Mapped["Hospital"] = relationship("Hospital")


__all__ = ["Modulo", "Permiso"]
