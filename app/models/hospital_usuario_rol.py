"""Association table linking usuarios, hospitales and roles."""
from __future__ import annotations

from sqlalchemy import ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base


class HospitalUsuarioRol(Base):
    """Assignment of a ``Usuario`` to a ``Hospital`` with a specific ``Rol``."""

    __tablename__ = "hospital_usuario_rol"
    __table_args__ = (
        UniqueConstraint(
            "usuario_id",
            "hospital_id",
            name="uq_usuario_hospital_asignacion",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    usuario_id: Mapped[int] = mapped_column(ForeignKey("usuarios.id"), nullable=False)
    hospital_id: Mapped[int] = mapped_column(ForeignKey("instituciones.id"), nullable=False)
    rol_id: Mapped[int] = mapped_column(ForeignKey("roles.id"), nullable=False)

    usuario = relationship("Usuario", back_populates="hospitales_roles")
    hospital = relationship("Hospital", back_populates="usuarios_roles")
    rol = relationship("Rol", back_populates="usuarios_hospitales")


__all__ = ["HospitalUsuarioRol"]
