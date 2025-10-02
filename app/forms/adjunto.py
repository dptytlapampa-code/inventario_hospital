"""Forms to manage equipment attachments."""
from __future__ import annotations

from flask_wtf import FlaskForm
from flask_wtf.file import FileAllowed, FileField, FileRequired
from wtforms import SelectField, SubmitField, TextAreaField
from wtforms.validators import DataRequired, Length, Optional, ValidationError

from app.forms.fields import HiddenIntegerField
from app.models import Equipo, TipoAdjunto


class AdjuntoForm(FlaskForm):
    """Upload an attachment for an equipment."""

    equipo_id = HiddenIntegerField("Equipo", validators=[DataRequired()])
    tipo = SelectField(
        "Tipo de documento",
        choices=[(t.value, t.name.replace("_", " ").title()) for t in TipoAdjunto],
        validators=[DataRequired()],
    )
    descripcion = TextAreaField("Descripción", validators=[Optional(), Length(max=500)])
    archivo = FileField(
        "Archivo",
        validators=[
            FileRequired("Debe seleccionar un archivo"),
            FileAllowed({"pdf", "jpg", "jpeg", "png"}, "Formatos permitidos: PDF/JPG/PNG"),
        ],
    )
    submit = SubmitField("Subir")

    def validate_equipo_id(self, field: HiddenIntegerField) -> None:  # type: ignore[override]
        if field.data is None:
            raise ValidationError("Seleccione un equipo válido")
        exists = Equipo.query.get(field.data)
        if not exists:
            raise ValidationError("El equipo seleccionado no existe")


__all__ = ["AdjuntoForm"]
