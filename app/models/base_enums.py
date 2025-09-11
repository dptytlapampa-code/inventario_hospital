from enum import Enum


class EstadoLicencia(str, Enum):
    """Estados unificados de una licencia."""

    BORRADOR = "borrador"
    PENDIENTE = "pendiente"
    APROBADA = "aprobada"
    RECHAZADA = "rechazada"


__all__ = ["EstadoLicencia"]
