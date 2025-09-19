"""Formularios relacionados con adjuntos."""

from __future__ import annotations

from flask_wtf import FlaskForm
from wtforms import SelectField, StringField, SubmitField
from wtforms.validators import DataRequired, Length

from app.models.adjunto import TipoAdjunto


class AdjuntoForm(FlaskForm):
    """Formulario mínimo para subir adjuntos."""

    equipo_id = SelectField("Equipo", coerce=int, validators=[DataRequired()])
    filename = StringField("Nombre del archivo", validators=[DataRequired(), Length(max=255)])
    tipo = SelectField("Tipo", choices=[], validators=[DataRequired()])
    submit = SubmitField("Guardar")

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        if not self.equipo_id.choices:
            self.equipo_id.choices = [
                (1, "Impresora HP"),
                (2, "Switch Cisco"),
                (3, "Notebook Dell"),
            ]
        self.tipo.choices = [
            (tipo.value, tipo.name.replace("_", " ").title()) for tipo in TipoAdjunto
        ]
