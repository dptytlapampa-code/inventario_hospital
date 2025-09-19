"""Formularios para documentos escaneados."""

from __future__ import annotations

from flask_wtf import FlaskForm
from wtforms import SelectField, StringField, SubmitField
from wtforms.validators import DataRequired, Length

from app.models.docscan import TipoDocscan


class DocscanForm(FlaskForm):
    """Formulario simple para subir documentos digitalizados."""

    titulo = StringField("Título", validators=[DataRequired(), Length(max=120)])
    equipo_id = SelectField("Equipo", coerce=int, validators=[DataRequired()])
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
            (tipo.value, tipo.name.title()) for tipo in TipoDocscan
        ]
