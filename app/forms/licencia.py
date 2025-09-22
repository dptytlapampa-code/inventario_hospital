"""Forms used in the license workflow."""
from __future__ import annotations

from datetime import date

from flask_wtf import FlaskForm
from wtforms import BooleanField, DateField, SelectField, SubmitField, TextAreaField
from wtforms.validators import DataRequired, Length, Optional, ValidationError

from app.models import TipoLicencia, Usuario


class LicenciaForm(FlaskForm):
    """Form to request a new license."""

    tipo = SelectField(
        "Tipo de licencia",
        choices=[(t.value, t.name.title()) for t in TipoLicencia],
        validators=[DataRequired()],
    )
    fecha_inicio = DateField("Fecha de inicio", validators=[DataRequired()])
    fecha_fin = DateField("Fecha de fin", validators=[DataRequired()])
    motivo = TextAreaField("Motivo", validators=[DataRequired(), Length(max=500)])
    comentario = TextAreaField("Comentario", validators=[Optional(), Length(max=500)])
    requires_replacement = BooleanField("Requiere reemplazo")
    reemplazo_id = SelectField("Reemplazo", coerce=int, validators=[Optional()])
    submit = SubmitField("Enviar solicitud")

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.reemplazo_id.choices = [(0, "Sin reemplazo")] + [
            (u.id, u.nombre) for u in Usuario.query.order_by(Usuario.nombre)
        ]

    def validate_fecha_fin(self, field):
        if self.fecha_inicio.data and field.data and field.data < self.fecha_inicio.data:
            raise ValidationError("La fecha de fin debe ser posterior a la fecha de inicio")

    def validate_reemplazo_id(self, field):
        if self.requires_replacement.data and field.data == 0:
            raise ValidationError("Debe seleccionar un reemplazo")


class AprobarRechazarForm(FlaskForm):
    """Form to approve or reject a license."""

    accion = SelectField(
        "Acción",
        choices=[("aprobar", "Aprobar"), ("rechazar", "Rechazar")],
        validators=[DataRequired()],
    )
    comentario = TextAreaField("Comentario", validators=[Optional(), Length(max=500)])
    submit = SubmitField("Confirmar")


class CalendarioFiltroForm(FlaskForm):
    """Filter for license calendar."""

    mes = DateField("Mes", default=date.today, validators=[Optional()])
    submit = SubmitField("Filtrar")


__all__ = ["LicenciaForm", "AprobarRechazarForm", "CalendarioFiltroForm"]
