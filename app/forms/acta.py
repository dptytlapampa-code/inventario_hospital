from __future__ import annotations

from flask_wtf import FlaskForm
from wtforms import SelectField, SelectMultipleField, SubmitField
from wtforms.validators import DataRequired

from app.models.acta import TipoActa


class ActaForm(FlaskForm):
    """Formulario para generar un acta."""

    tipo = SelectField(
        "Tipo",
        choices=[(t.value, t.name.title()) for t in TipoActa],
        validators=[DataRequired()],
    )
    equipos = SelectMultipleField(
        "Equipos",
        validators=[DataRequired()],
        coerce=int,
    )
    submit = SubmitField("Generar")
