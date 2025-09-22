"""Forms for scanned notes module."""
from __future__ import annotations

from flask_wtf import FlaskForm
from flask_wtf.file import FileAllowed, FileField, FileRequired
from wtforms import DateField, SelectField, StringField, SubmitField, TextAreaField
from wtforms.validators import DataRequired, Length, Optional

from app.models import Hospital, Oficina, Servicio, TipoDocscan


class DocscanForm(FlaskForm):
    """Upload scanned documentation."""

    titulo = StringField("Título", validators=[DataRequired(), Length(max=150)])
    tipo = SelectField(
        "Tipo",
        choices=[(t.value, t.name.title()) for t in TipoDocscan],
        validators=[DataRequired()],
    )
    hospital_id = SelectField("Hospital", coerce=int, validators=[Optional()])
    servicio_id = SelectField("Servicio", coerce=int, validators=[Optional()])
    oficina_id = SelectField("Oficina", coerce=int, validators=[Optional()])
    fecha_documento = DateField("Fecha del documento", validators=[Optional()])
    comentario = TextAreaField("Comentario", validators=[Optional(), Length(max=500)])
    archivo = FileField(
        "Archivo",
        validators=[
            FileRequired("Debe seleccionar un archivo"),
            FileAllowed({"pdf", "jpg", "jpeg", "png"}, "Formatos permitidos: PDF/JPG/PNG"),
        ],
    )
    submit = SubmitField("Subir documento")

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.hospital_id.choices = [(0, "N/A")] + [
            (h.id, h.nombre) for h in Hospital.query.order_by(Hospital.nombre)
        ]
        self.servicio_id.choices = [(0, "N/A")] + [
            (s.id, f"{s.hospital.nombre} / {s.nombre}") for s in Servicio.query.order_by(Servicio.nombre)
        ]
        self.oficina_id.choices = [(0, "N/A")] + [
            (o.id, f"{o.hospital.nombre} / {o.nombre}") for o in Oficina.query.order_by(Oficina.nombre)
        ]


__all__ = ["DocscanForm"]
