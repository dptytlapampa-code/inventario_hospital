"""Permission matrix per role and hospital."""
from __future__ import annotations

from enum import Enum
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Enum as SAEnum, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base

if TYPE_CHECKING:  # pragma: no cover
    from .hospital import Hospital
    from .rol import Rol


class Modulo(str, Enum):
    """Modules governed by permissions."""

    INVENTARIO = "inventario"
    INSUMOS = "insumos"
    ACTAS = "actas"
    ADJUNTOS = "adjuntos"
    DOCSCAN = "docscan"
    REPORTES = "reportes"
    AUDITORIA = "auditoria"
    LICENCIAS = "licencias"


class Permiso(Base):
    """Role permission optionally scoped to a hospital."""

    __tablename__ = "permisos"

    id: Mapped[int] = mapped_column(primary_key=True)
    rol_id: Mapped[int] = mapped_column(ForeignKey("roles.id"), nullable=False)
    modulo: Mapped[Modulo] = mapped_column(SAEnum(Modulo, name="modulo_permiso"), nullable=False)
    hospital_id: Mapped[int | None] = mapped_column(ForeignKey("instituciones.id"))
    can_read: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    can_write: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    allow_export: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    rol: Mapped["Rol"] = relationship("Rol", back_populates="permisos")
    hospital: Mapped["Hospital | None"] = relationship("Hospital", back_populates="permisos")

    def __repr__(self) -> str:  # pragma: no cover
        scope = self.hospital.nombre if self.hospital else "global"
        return f"Permiso(rol={self.rol.nombre!r}, modulo={self.modulo.value!r}, scope={scope!r})"


__all__ = ["Modulo", "Permiso"]
