"""User model for authentication and permission checks."""
from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Iterable, TYPE_CHECKING

from flask_login import UserMixin
from sqlalchemy import Boolean, DateTime, Enum as SAEnum, ForeignKey, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from werkzeug.security import check_password_hash as wz_check_password_hash
from werkzeug.security import generate_password_hash as wz_generate_password_hash

from app.extensions import bcrypt

from .base import Base


class ThemePreference(str, Enum):
    """Available theme options for the UI."""

    LIGHT = "light"
    DARK = "dark"
    SYSTEM = "system"

if TYPE_CHECKING:  # pragma: no cover
    from .hospital import Hospital, Oficina, Servicio
    from .hospital_usuario_rol import HospitalUsuarioRol
    from .licencia import Licencia
    from .permisos import Permiso
    from .rol import Rol


class Usuario(Base, UserMixin):
    """Authenticated system user."""

    __tablename__ = "usuarios"
    __table_args__ = (
        UniqueConstraint("username", name="uq_usuario_username"),
        UniqueConstraint("dni", name="uq_usuario_dni"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(80), nullable=False, unique=True)
    nombre: Mapped[str] = mapped_column(String(120), nullable=False)
    dni: Mapped[str] = mapped_column(String(20), nullable=False, unique=True)
    apellido: Mapped[str | None] = mapped_column(String(120))
    email: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    telefono: Mapped[str | None] = mapped_column(String(50))
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    activo: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    rol_id: Mapped[int] = mapped_column(ForeignKey("roles.id"), nullable=False)
    hospital_id: Mapped[int | None] = mapped_column(ForeignKey("hospitales.id"))
    servicio_id: Mapped[int | None] = mapped_column(ForeignKey("servicios.id"))
    oficina_id: Mapped[int | None] = mapped_column(ForeignKey("oficinas.id"))
    theme_pref: Mapped[ThemePreference] = mapped_column(
        SAEnum(ThemePreference, name="theme_preference"),
        default=ThemePreference.SYSTEM,
        server_default=ThemePreference.SYSTEM.value,
        nullable=False,
    )
    ultimo_login: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.current_timestamp(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.current_timestamp(),
        onupdate=func.current_timestamp(),
        nullable=False,
    )

    rol: Mapped["Rol"] = relationship("Rol", back_populates="usuarios")
    hospital: Mapped["Hospital | None"] = relationship("Hospital", back_populates="usuarios")
    servicio: Mapped["Servicio | None"] = relationship("Servicio")
    oficina: Mapped["Oficina | None"] = relationship("Oficina")
    licencias: Mapped[list["Licencia"]] = relationship(
        "Licencia", back_populates="usuario", foreign_keys="Licencia.user_id"
    )
    licencias_decididas: Mapped[list["Licencia"]] = relationship(
        "Licencia", back_populates="decisor", foreign_keys="Licencia.decidido_por"
    )
    hospitales_roles: Mapped[list["HospitalUsuarioRol"]] = relationship(
        "HospitalUsuarioRol",
        back_populates="usuario",
        cascade="all, delete-orphan",
    )

    @property
    def role(self) -> str | None:
        """Return the normalized role name or ``None`` when missing."""

        return self.rol.nombre.lower() if self.rol and self.rol.nombre else None

    def set_password(self, password: str) -> None:
        """Hash and store ``password`` using Werkzeug for new records."""

        self.password_hash = wz_generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        """Return True when ``password`` matches the stored hash."""

        if not self.password_hash:
            return False

        # Legacy bcrypt hashes remain compatible for existing users.
        if self.password_hash.startswith("$2"):
            return bcrypt.check_password_hash(self.password_hash, password)
        return wz_check_password_hash(self.password_hash, password)

    @property
    def roles(self) -> list[str]:
        """Return the user's role name for decorator checks."""

        return [self.role] if self.role else []

    @property
    def permissions(self) -> list[str]:
        """Flattened permission strings (``module:action``)."""

        if not self.rol:
            return []
        perms: list[str] = []
        for permiso in self.rol.permisos:
            prefix = permiso.modulo.value
            if permiso.can_read:
                perms.append(f"{prefix}:read")
            if permiso.can_write:
                perms.append(f"{prefix}:write")
        return perms

    def has_role(self, *roles: str) -> bool:
        if not roles:
            return False
        current = self.role
        return bool(current and any(current == role.lower() for role in roles))

    def has_permission(self, permiso: str) -> bool:
        return permiso in self.permissions

    def allowed_hospital_ids(self, modulo: str | None = None) -> set[int]:
        """Return hospital IDs where the user has access to ``modulo``."""

        if not self.rol:
            return set()
        if self.rol.nombre.lower() == "superadmin":
            ids = {permiso.hospital_id for permiso in self.rol.permisos if permiso.hospital_id}
            if not ids:
                ids = {rel.hospital_id for rel in self.hospitales_roles}
            return ids

        hospital_ids: set[int] = set()
        for permiso in self.rol.permisos:
            if modulo and permiso.modulo.value != modulo:
                continue
            if permiso.hospital_id:
                hospital_ids.add(permiso.hospital_id)
        if self.hospital_id:
            hospital_ids.add(self.hospital_id)
        hospital_ids.update(rel.hospital_id for rel in self.hospitales_roles)
        return hospital_ids

    @property
    def hospitales_asignados(self) -> list[int]:
        """Return the hospital IDs assigned via the pivot table."""

        return [rel.hospital_id for rel in self.hospitales_roles]

    def update_permissions(self, permisos: Iterable["Permiso"]) -> None:
        """Synchronise permission relationship."""

        self.rol.permisos = list(permisos)


__all__ = ["Usuario", "ThemePreference"]
