"""Formularios para hospitales/ubicaciones."""

from __future__ import annotations

from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired, Length


class HospitalForm(FlaskForm):
    """Formulario minimalista para registrar hospitales."""

    nombre = StringField("Nombre", validators=[DataRequired(), Length(max=100)])
    submit = SubmitField("Guardar")
