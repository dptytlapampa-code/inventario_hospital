"""Forms for managing hospital hierarchy."""
from __future__ import annotations

from flask_wtf import FlaskForm
from wtforms import IntegerField, SelectField, StringField, SubmitField, TextAreaField
from wtforms.validators import DataRequired, Length, NumberRange, Optional

from app.models import Hospital, Servicio


class HospitalForm(FlaskForm):
    nombre = StringField("Nombre", validators=[DataRequired(), Length(max=120)])
    codigo = StringField("Código", validators=[Optional(), Length(max=20)])
    localidad = StringField("Localidad", validators=[Optional(), Length(max=120)])
    direccion = StringField("Dirección", validators=[Optional(), Length(max=255)])
    telefono = StringField("Teléfono", validators=[Optional(), Length(max=50)])
    nivel_complejidad = IntegerField(
        "Nivel de complejidad",
        validators=[Optional(), NumberRange(min=1, max=10)],
        description="Ingrese un valor entre 1 y 10",
    )
    submit = SubmitField("Guardar")


class ServicioForm(FlaskForm):
    nombre = StringField("Nombre del servicio", validators=[DataRequired(), Length(max=120)])
    descripcion = TextAreaField("Descripción", validators=[Optional(), Length(max=255)])
    hospital_id = SelectField("Hospital", coerce=int, validators=[DataRequired()])
    submit = SubmitField("Guardar")

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.hospital_id.choices = [(h.id, h.nombre) for h in Hospital.query.order_by(Hospital.nombre)]


class OficinaForm(FlaskForm):
    nombre = StringField("Nombre de la oficina", validators=[DataRequired(), Length(max=120)])
    piso = StringField("Piso", validators=[Optional(), Length(max=20)])
    servicio_id = SelectField("Servicio", coerce=int, validators=[DataRequired()])
    submit = SubmitField("Guardar")

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.servicio_id.choices = [
            (s.id, f"{s.hospital.nombre} / {s.nombre}") for s in Servicio.query.order_by(Servicio.nombre)
        ]


__all__ = ["HospitalForm", "ServicioForm", "OficinaForm"]
