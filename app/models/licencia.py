"""Database model for leave requests."""

from datetime import date

from app.models import db


class Licencia(db.Model):
    """Licencia solicitada por un empleado."""

    __tablename__ = "licencias"

    id = db.Column(db.Integer, primary_key=True)
    empleado = db.Column(db.String(100), nullable=False)
    fecha_inicio = db.Column(db.Date, nullable=False)
    fecha_fin = db.Column(db.Date, nullable=False)
    motivo = db.Column(db.String(255), nullable=False)
    estado = db.Column(db.String(20), nullable=False, default="pendiente")

    def __repr__(self) -> str:  # pragma: no cover - debug helper
        return f"<Licencia {self.empleado} {self.fecha_inicio} - {self.fecha_fin}>"


__all__ = ["Licencia"]
