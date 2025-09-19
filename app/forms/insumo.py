"""Formularios de insumos."""

from __future__ import annotations

from flask_wtf import FlaskForm
from wtforms import IntegerField, SelectMultipleField, StringField, SubmitField
from wtforms.validators import DataRequired, Length, NumberRange, Optional as OptionalValidator


class InsumoForm(FlaskForm):
    """Formulario básico para gestionar insumos."""

    nombre = StringField("Nombre", validators=[DataRequired(), Length(max=100)])
    numero_serie = StringField(
        "Número de serie", validators=[OptionalValidator(), Length(max=100)]
    )
    stock = IntegerField("Stock", validators=[DataRequired(), NumberRange(min=0)])
    equipos = SelectMultipleField("Equipos asociados", coerce=int)
    submit = SubmitField("Guardar")

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        if not self.equipos.choices:
            self.equipos.choices = [
                (1, "Impresora HP"),
                (2, "Switch Cisco"),
                (3, "Notebook Dell"),
            ]
