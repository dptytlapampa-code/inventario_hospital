"""Formularios de permisos por rol."""

from __future__ import annotations

from flask_wtf import FlaskForm
from wtforms import BooleanField, SelectField, SubmitField
from wtforms.validators import DataRequired, InputRequired

from app.models.permisos import Modulo


class PermisoForm(FlaskForm):
    """Formulario simple para administrar permisos de módulos."""

    rol_id = SelectField("Rol", coerce=int, validators=[InputRequired()])
    modulo = SelectField("Módulo", choices=[], validators=[DataRequired()])
    hospital_id = SelectField("Hospital", coerce=int, validators=[InputRequired()])
    can_read = BooleanField("Puede leer", default=True)
    can_write = BooleanField("Puede escribir")
    submit = SubmitField("Guardar")

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        if not self.rol_id.choices:
            self.rol_id.choices = [
                (1, "Administrador"),
                (2, "Operador"),
                (3, "Consulta"),
            ]
        self.modulo.choices = [
            (modulo.value, modulo.name.title()) for modulo in Modulo
        ]
        if not self.hospital_id.choices:
            self.hospital_id.choices = [
                (0, "Todos los hospitales"),
                (1, "Hospital Central"),
                (2, "Hospital Norte"),
                (3, "Hospital Sur"),
            ]
