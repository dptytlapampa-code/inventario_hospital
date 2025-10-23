"""Forms for scanned notes module."""
from __future__ import annotations

from flask_wtf import FlaskForm
from flask_wtf.file import FileAllowed, FileField, FileRequired
from wtforms import DateField, SelectField, StringField, SubmitField, TextAreaField
from wtforms.validators import DataRequired, Length, Optional

from app.models import Hospital, Oficina, Servicio, TipoDocscan
from app.utils.forms import preload_model_choice


class DocscanForm(FlaskForm):
    """Upload scanned documentation."""

    titulo = StringField("Título", validators=[DataRequired(), Length(max=150)])
    tipo = SelectField(
        "Tipo",
        choices=[(t.value, t.name.title()) for t in TipoDocscan],
        validators=[DataRequired()],
    )
    hospital_id = SelectField(
        "Hospital",
        coerce=lambda value: int(value) if value else None,
        validators=[Optional()],
        validate_choice=False,
        render_kw={"data-placeholder": "Sin hospital asignado"},
    )
    servicio_id = SelectField(
        "Servicio",
        coerce=lambda value: int(value) if value else None,
        validators=[Optional()],
        validate_choice=False,
        render_kw={"data-placeholder": "Sin servicio"},
    )
    oficina_id = SelectField(
        "Oficina",
        coerce=lambda value: int(value) if value else None,
        validators=[Optional()],
        validate_choice=False,
        render_kw={"data-placeholder": "Sin oficina"},
    )
    _date_render = {"placeholder": "dd/mm/aaaa", "data-date-format": "d/m/Y", "autocomplete": "off"}
    fecha_documento = DateField(
        "Fecha del documento",
        validators=[Optional()],
        format="%d/%m/%Y",
        render_kw=_date_render,
    )
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
        self._preload_hospital()
        self._preload_servicio()
        self._preload_oficina()

    def _preload_hospital(self) -> None:
        preload_model_choice(self.hospital_id, Hospital, lambda hospital: hospital.nombre)

    def _preload_servicio(self) -> None:
        preload_model_choice(
            self.servicio_id,
            Servicio,
            lambda servicio: f"{servicio.hospital.nombre} · {servicio.nombre}",
        )

    def _preload_oficina(self) -> None:
        preload_model_choice(
            self.oficina_id,
            Oficina,
            lambda oficina: f"{oficina.hospital.nombre} · {oficina.nombre}",
        )


__all__ = ["DocscanForm"]
