from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import String, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base

if TYPE_CHECKING:  # pragma: no cover
    from .rol import Rol


class Usuario(Base):
    """Modelo de usuario del sistema."""

    __tablename__ = "usuarios"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    nombre: Mapped[str] = mapped_column(String(100), nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    rol_id: Mapped[int | None] = mapped_column(ForeignKey("roles.id"), nullable=True)

    licencias = relationship("Licencia", back_populates="usuario")
    rol: Mapped["Rol"] = relationship("Rol", back_populates="usuarios")

    @property
    def roles(self) -> list[str]:
        """Return a list with the user's role name for decorator checks."""

        return [self.rol.nombre] if self.rol else []

    @property
    def permissions(self) -> list[str]:
        """Aggregate permissions derived from the user's role."""

        if not self.rol:
            return []
        perms: list[str] = []
        for perm in self.rol.permisos:
            if perm.can_read:
                perms.append(f"{perm.modulo.value}:read")
            if perm.can_write:
                perms.append(f"{perm.modulo.value}:write")
        return perms


__all__ = ["Usuario"]
