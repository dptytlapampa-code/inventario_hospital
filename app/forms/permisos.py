"""Forms for assigning permissions to roles."""
from __future__ import annotations

from flask_wtf import FlaskForm
from wtforms import BooleanField, SelectField, SubmitField
from wtforms.validators import DataRequired

from app.models import Hospital, Modulo, Rol


class PermisoForm(FlaskForm):
    rol_id = SelectField("Rol", coerce=int, validators=[DataRequired()])
    modulo = SelectField(
        "Módulo",
        choices=[(m.value, m.name.title()) for m in Modulo],
        validators=[DataRequired()],
    )
    hospital_id = SelectField("Hospital", coerce=int, validators=[DataRequired()])
    can_read = BooleanField("Puede leer", default=True)
    can_write = BooleanField("Puede editar")
    allow_export = BooleanField("Puede exportar")
    submit = SubmitField("Guardar")

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.rol_id.choices = [(r.id, r.nombre) for r in Rol.query.order_by(Rol.nombre)]
        self.hospital_id.choices = [(0, "Todos")] + [
            (h.id, h.nombre) for h in Hospital.query.order_by(Hospital.nombre)
        ]


__all__ = ["PermisoForm"]
