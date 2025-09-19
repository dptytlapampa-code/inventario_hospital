"""Formularios relacionados con equipos."""

from __future__ import annotations

from flask_wtf import FlaskForm
from wtforms import SelectField, StringField, SubmitField, TextAreaField
from wtforms.validators import DataRequired, Length

from app.models.equipo import EstadoEquipo, TipoEquipo


class EquipoForm(FlaskForm):
    """Formulario mínimo para crear/editar equipos."""

    tipo = SelectField("Tipo", choices=[], validators=[DataRequired()])
    estado = SelectField("Estado", choices=[], validators=[DataRequired()])
    descripcion = TextAreaField("Descripción", validators=[Length(max=255)])
    numero_serie = StringField("Número de serie", validators=[Length(max=100)])
    hospital_id = SelectField(
        "Hospital", choices=[], coerce=int, validators=[DataRequired()]
    )
    submit = SubmitField("Guardar")

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.tipo.choices = [
            (tipo.value, tipo.name.replace("_", " ").title()) for tipo in TipoEquipo
        ]
        self.estado.choices = [
            (estado.value, estado.name.replace("_", " ").title())
            for estado in EstadoEquipo
        ]
        if not self.hospital_id.choices:
            self.hospital_id.choices = [
                (1, "Hospital Central"),
                (2, "Hospital Norte"),
                (3, "Hospital Sur"),
            ]
