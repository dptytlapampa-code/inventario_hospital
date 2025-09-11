from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, timedelta
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


def calcular_dias_habiles(fecha_inicio: date, fecha_fin: date) -> int:
    """Calcula la cantidad de días hábiles entre dos fechas inclusive."""
    if fecha_fin < fecha_inicio:
        raise ValueError("La fecha de fin debe ser posterior a la fecha de inicio")
    dias = 0
    delta = (fecha_fin - fecha_inicio).days + 1
    for i in range(delta):
        dia = fecha_inicio + timedelta(days=i)
        if dia.weekday() < 5:  # 0 = lunes, 6 = domingo
            dias += 1
    return dias


def usuario_con_licencia_activa(
    usuario_id: int, fecha: Optional[date] = None
) -> bool:
    """Verifica si el usuario tiene una licencia aprobada vigente."""

    fecha = fecha or date.today()
    for inicio, fin in LICENCIAS_APROBADAS.get(usuario_id, []):
        if inicio <= fecha <= fin:
            return True
    return False


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
    requires_replacement: bool = False
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
        if self.requires_replacement and self.reemplazo_id is None:
            raise ValueError("Debe asignar un reemplazo antes de aprobar")
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

    @property
    def dias_habiles(self) -> int:
        """Devuelve la cantidad de días hábiles de la licencia."""
        return calcular_dias_habiles(self.fecha_inicio, self.fecha_fin)


__all__ = [
    "EstadoLicencia",
    "TraslapeError",
    "LICENCIAS_APROBADAS",
    "usuario_con_licencia_activa",
    "calcular_dias_habiles",
    "Licencia",
]
