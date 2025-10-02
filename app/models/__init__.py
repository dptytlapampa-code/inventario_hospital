"""Expose SQLAlchemy models for external usage."""
from __future__ import annotations

from .acta import Acta, ActaItem, TipoActa
from .adjunto import Adjunto, TipoAdjunto
from .auditoria import Auditoria
from .base import Base
from .docscan import Docscan, TipoDocscan
from .equipo import Equipo, EquipoHistorial, EstadoEquipo, TipoEquipo
from .equipo_adjunto import EquipoAdjunto
from .hospital import Hospital, Oficina, Servicio
from .hospital_usuario_rol import HospitalUsuarioRol
from .insumo import EquipoInsumo, Insumo, InsumoMovimiento, InsumoSerie, MovimientoTipo, SerieEstado
from .licencia import Licencia, TipoLicencia, EstadoLicencia
from .permisos import Modulo, Permiso
from .rol import Rol
from .usuario import Usuario

__all__ = [
    "Acta",
    "ActaItem",
    "TipoActa",
    "Adjunto",
    "TipoAdjunto",
    "Auditoria",
    "Base",
    "Docscan",
    "TipoDocscan",
    "Equipo",
    "EquipoHistorial",
    "EstadoEquipo",
    "TipoEquipo",
    "EquipoAdjunto",
    "Hospital",
    "Servicio",
    "Oficina",
    "HospitalUsuarioRol",
    "Insumo",
    "InsumoMovimiento",
    "InsumoSerie",
    "EquipoInsumo",
    "MovimientoTipo",
    "SerieEstado",
    "Licencia",
    "TipoLicencia",
    "EstadoLicencia",
    "Modulo",
    "Permiso",
    "Rol",
    "Usuario",
]
