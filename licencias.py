"""Domain helpers for license workflow used in tests and services."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, timedelta
from typing import Dict, List, Optional, Tuple

from app.models.base_enums import EstadoLicencia


class TraslapeError(Exception):
    """Raised when two licenses overlap."""


LICENCIAS_APROBADAS: Dict[int, List[Tuple[date, date]]] = {}


def calcular_dias_habiles(fecha_inicio: date, fecha_fin: date) -> int:
    """Return business days between ``fecha_inicio`` and ``fecha_fin`` inclusive."""

    if fecha_fin < fecha_inicio:
        raise ValueError("La fecha de fin debe ser posterior a la fecha de inicio")
    dias = 0
    delta = (fecha_fin - fecha_inicio).days + 1
    for offset in range(delta):
        dia = fecha_inicio + timedelta(days=offset)
        if dia.weekday() < 5:
            dias += 1
    return dias


def usuario_con_licencia_activa(usuario_id: int, fecha: Optional[date] = None) -> bool:
    """Return True if ``usuario_id`` has an approved license covering ``fecha``."""

    fecha = fecha or date.today()
    for inicio, fin in LICENCIAS_APROBADAS.get(usuario_id, []):
        if inicio <= fecha <= fin:
            return True
    return False


def _rango_superpuesto(inicio1: date, fin1: date, inicio2: date, fin2: date) -> bool:
    return max(inicio1, inicio2) <= min(fin1, fin2)


@dataclass
class Licencia:
    """Lightweight licence representation for pure-Python tests."""

    usuario_id: int
    fecha_inicio: date
    fecha_fin: date
    motivo: str = ""
    estado: EstadoLicencia = field(default=EstadoLicencia.SOLICITADA, init=False)

    def __post_init__(self) -> None:
        if self.fecha_fin < self.fecha_inicio:
            raise ValueError("La fecha de fin debe ser posterior a la fecha de inicio")
        self._verificar_traslape()

    def _verificar_traslape(self) -> None:
        for inicio, fin in LICENCIAS_APROBADAS.get(self.usuario_id, []):
            if _rango_superpuesto(self.fecha_inicio, self.fecha_fin, inicio, fin):
                raise TraslapeError("La licencia se superpone con otra aprobada")

    def enviar_pendiente(self) -> None:
        if self.estado != EstadoLicencia.SOLICITADA:
            raise ValueError("La licencia ya fue procesada")

    def aprobar(self) -> None:
        if self.estado != EstadoLicencia.SOLICITADA:
            raise ValueError("Solo se puede aprobar una licencia solicitada")
        self._verificar_traslape()
        self.estado = EstadoLicencia.APROBADA
        LICENCIAS_APROBADAS.setdefault(self.usuario_id, []).append(
            (self.fecha_inicio, self.fecha_fin)
        )

    def rechazar(self) -> None:
        if self.estado != EstadoLicencia.SOLICITADA:
            raise ValueError("Solo se puede rechazar una licencia solicitada")
        self.estado = EstadoLicencia.RECHAZADA

    def cancelar(self) -> None:
        if self.estado not in (EstadoLicencia.SOLICITADA, EstadoLicencia.APROBADA):
            raise ValueError("Solo se puede cancelar licencias solicitadas o aprobadas")
        self.estado = EstadoLicencia.CANCELADA

    @property
    def dias_habiles(self) -> int:
        return calcular_dias_habiles(self.fecha_inicio, self.fecha_fin)


__all__ = [
    "EstadoLicencia",
    "TraslapeError",
    "LICENCIAS_APROBADAS",
    "usuario_con_licencia_activa",
    "calcular_dias_habiles",
    "Licencia",
]
