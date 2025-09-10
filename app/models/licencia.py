from datetime import date
from typing import Iterable, Optional

from app.utils.dates import business_days


class Licencia:
    """Representa una licencia con fechas de inicio y fin."""

    def __init__(self, inicio: date, fin: date, feriados: Optional[Iterable[date]] = None) -> None:
        self.inicio = inicio
        self.fin = fin
        self.feriados = feriados

    def dias_habiles(self) -> int:
        """Cantidad de días hábiles de la licencia."""
        return business_days(self.inicio, self.fin, self.feriados)
