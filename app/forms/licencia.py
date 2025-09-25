"""Forms used in the license workflow."""
from __future__ import annotations

from datetime import date

from flask_wtf import FlaskForm
from wtforms import DateField, SelectField, SubmitField, TextAreaField
from wtforms.validators import DataRequired, Length, Optional, ValidationError

from app.models import TipoLicencia


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
    submit = SubmitField("Enviar solicitud")

    def validate_fecha_fin(self, field):
        if self.fecha_inicio.data and field.data and field.data < self.fecha_inicio.data:
            raise ValidationError("La fecha de fin debe ser posterior a la fecha de inicio")


class AprobarRechazarForm(FlaskForm):
    """Form to approve or reject a license."""

    accion = SelectField(
        "Acción",
        choices=[("aprobar", "Aprobar"), ("rechazar", "Rechazar")],
        validators=[DataRequired()],
    )
    submit = SubmitField("Confirmar")


class CalendarioFiltroForm(FlaskForm):
    """Filter for license calendar."""

    mes = DateField("Mes", default=date.today, validators=[Optional()])
    submit = SubmitField("Filtrar")


__all__ = ["LicenciaForm", "AprobarRechazarForm", "CalendarioFiltroForm"]
