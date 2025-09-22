"""Forms for acta generation."""
from __future__ import annotations

from flask_wtf import FlaskForm
from wtforms import SelectField, SelectMultipleField, SubmitField, TextAreaField
from wtforms.validators import DataRequired, Length, Optional

from app.models import Equipo, Hospital, Oficina, Servicio, TipoActa


class ActaForm(FlaskForm):
    """Form used to generate acta documents."""

    tipo = SelectField(
        "Tipo de acta",
        choices=[(t.value, t.name.title()) for t in TipoActa],
        validators=[DataRequired()],
    )
    hospital_id = SelectField("Hospital", coerce=int, validators=[DataRequired()])
    servicio_id = SelectField("Servicio", coerce=int, validators=[Optional()])
    oficina_id = SelectField("Oficina", coerce=int, validators=[Optional()])
    equipos = SelectMultipleField("Equipos", coerce=int, validators=[DataRequired()])
    observaciones = TextAreaField("Observaciones", validators=[Optional(), Length(max=500)])
    submit = SubmitField("Generar acta")

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.hospital_id.choices = [(h.id, h.nombre) for h in Hospital.query.order_by(Hospital.nombre)]
        self.servicio_id.choices = [(0, "- Seleccione -")] + [
            (s.id, f"{s.hospital.nombre} / {s.nombre}") for s in Servicio.query.order_by(Servicio.nombre)
        ]
        self.oficina_id.choices = [(0, "- Seleccione -")] + [
            (o.id, f"{o.hospital.nombre} / {o.nombre}") for o in Oficina.query.order_by(Oficina.nombre)
        ]
        self.equipos.choices = [
            (e.id, f"{e.codigo or e.descripcion or e.id}") for e in Equipo.query.order_by(Equipo.descripcion)
        ]


__all__ = ["ActaForm"]
