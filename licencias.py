from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from enum import Enum
from typing import Dict, List, Tuple, Optional


class EstadoLicencia(Enum):
    """Posibles estados de una licencia."""

    BORRADOR = "borrador"
    PENDIENTE = "pendiente"
    APROBADA = "aprobada"
    RECHAZADA = "rechazada"


class TraslapeError(Exception):
    """Se lanza cuando una licencia se superpone con otra aprobada."""


# Registro global de licencias aprobadas por usuario
LICENCIAS_APROBADAS: Dict[int, List[Tuple[date, date]]] = {}


def _rango_superpuesto(inicio1: date, fin1: date, inicio2: date, fin2: date) -> bool:
    """Determina si dos rangos de fechas se superponen."""
    return max(inicio1, inicio2) <= min(fin1, fin2)


@dataclass
class Licencia:
    """Modelo simple de licencia para el sistema."""

    usuario_id: int
    fecha_inicio: date
    fecha_fin: date
    estado: EstadoLicencia = field(default=EstadoLicencia.BORRADOR, init=False)
    reemplazo_id: Optional[int] = None

    def __post_init__(self) -> None:
        if self.fecha_fin < self.fecha_inicio:
            raise ValueError("La fecha de fin debe ser posterior a la fecha de inicio")
        self._verificar_traslape()

    def _verificar_traslape(self) -> None:
        for inicio, fin in LICENCIAS_APROBADAS.get(self.usuario_id, []):
            if _rango_superpuesto(self.fecha_inicio, self.fecha_fin, inicio, fin):
                raise TraslapeError("La licencia se superpone con otra aprobada")

    def enviar_pendiente(self) -> None:
        if self.estado != EstadoLicencia.BORRADOR:
            raise ValueError("Solo se puede enviar una licencia en borrador")
        self.estado = EstadoLicencia.PENDIENTE

    def aprobar(self) -> None:
        if self.estado not in (EstadoLicencia.PENDIENTE, EstadoLicencia.BORRADOR):
            raise ValueError("Solo se puede aprobar una licencia pendiente o en borrador")
        self._verificar_traslape()
        self.estado = EstadoLicencia.APROBADA
        LICENCIAS_APROBADAS.setdefault(self.usuario_id, []).append(
            (self.fecha_inicio, self.fecha_fin)
        )

    def rechazar(self) -> None:
        if self.estado != EstadoLicencia.PENDIENTE:
            raise ValueError("Solo se puede rechazar una licencia pendiente")
        self.estado = EstadoLicencia.RECHAZADA

    def asignar_reemplazo(self, usuario_id: int) -> None:
        self.reemplazo_id = usuario_id
