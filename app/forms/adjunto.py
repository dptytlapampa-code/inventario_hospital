"""Forms to manage equipment attachments."""
from __future__ import annotations

from flask_wtf import FlaskForm
from flask_wtf.file import FileAllowed, FileField, FileRequired
from wtforms import SelectField, SubmitField, TextAreaField
from wtforms.validators import DataRequired, Length, Optional

from app.models import Equipo, TipoAdjunto


class AdjuntoForm(FlaskForm):
    """Upload an attachment for an equipment."""

    equipo_id = SelectField("Equipo", coerce=int, validators=[DataRequired()])
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

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.equipo_id.choices = [
            (e.id, f"{e.codigo or e.descripcion or e.id}") for e in Equipo.query.order_by(Equipo.descripcion)
        ]


__all__ = ["AdjuntoForm"]
