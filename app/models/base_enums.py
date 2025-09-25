from enum import Enum


class EstadoLicencia(str, Enum):
    """Estados unificados de una licencia."""

    SOLICITADA = "solicitada"
    APROBADA = "aprobada"
    RECHAZADA = "rechazada"
    CANCELADA = "cancelada"


__all__ = ["EstadoLicencia"]
