"""Registro de modelos del sistema.

Este módulo intenta importar todos los modelos basados en SQLAlchemy. En
entornos mínimos de testing donde SQLAlchemy no está disponible, los
imports fallarán silenciosamente, permitiendo que los tests que solo
requieren usuarios en memoria continúen ejecutándose.
"""

from __future__ import annotations

try:  # pragma: no cover - best effort if SQLAlchemy is missing
    from .base import Base
    from .hospital import Hospital
    from .licencia import Licencia, TipoLicencia, EstadoLicencia
    from .usuario import Usuario
    from .rol import Rol
    from .permisos import Permiso, Modulo
    from .equipo import Equipo, TipoEquipo, EstadoEquipo
    from .insumo import Insumo, equipo_insumos
    from .acta import Acta, ActaItem, TipoActa
    from .adjunto import Adjunto, TipoAdjunto
    from .docscan import Docscan, TipoDocscan
    from .auditoria import Auditoria
except ModuleNotFoundError:  # pragma: no cover
    Base = Hospital = Licencia = TipoLicencia = EstadoLicencia = Usuario = Rol = Permiso = Modulo = Equipo = TipoEquipo = EstadoEquipo = Insumo = equipo_insumos = Acta = ActaItem = TipoActa = Adjunto = TipoAdjunto = Docscan = TipoDocscan = Auditoria = object  # type: ignore

from .user import User, USERS, USERNAME_TABLE

__all__ = [
    "Base",
    "Hospital",
    "Licencia",
    "TipoLicencia",
    "EstadoLicencia",
    "Usuario",
    "Rol",
    "Permiso",
    "Modulo",
    "Equipo",
    "TipoEquipo",
    "EstadoEquipo",
    "Insumo",
    "equipo_insumos",
    "Acta",
    "ActaItem",
    "TipoActa",
    "Adjunto",
    "TipoAdjunto",
    "Docscan",
    "TipoDocscan",
    "Auditoria",
    "User",
    "USERS",
    "USERNAME_TABLE",
]
