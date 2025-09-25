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
    hospital_id = SelectField(
        "Hospital",
        coerce=int,
        validators=[Optional()],
        description="Opcional si la licencia está asociada a un hospital específico.",
    )
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


class MisLicenciasFiltroForm(FlaskForm):
    """Basic filters for the "mis licencias" listing."""

    estado = SelectField(
        "Estado",
        choices=[],
        validators=[Optional()],
        description="Filtrar por estado actual de la solicitud.",
    )
    tipo = SelectField(
        "Tipo",
        choices=[],
        validators=[Optional()],
        description="Filtrar por tipo de licencia.",
    )
    fecha_desde = DateField("Desde", validators=[Optional()])
    fecha_hasta = DateField("Hasta", validators=[Optional()])
    submit = SubmitField("Aplicar filtros")


class GestionLicenciasFiltroForm(FlaskForm):
    """Filters for the superadmin management board."""

    usuario_id = SelectField(
        "Usuario",
        coerce=lambda value: int(value) if value else None,
        choices=[],
        validators=[Optional()],
    )
    hospital_id = SelectField(
        "Hospital",
        coerce=lambda value: int(value) if value else None,
        choices=[],
        validators=[Optional()],
    )
    estado = SelectField("Estado", choices=[], validators=[Optional()])
    fecha_desde = DateField("Desde", validators=[Optional()])
    fecha_hasta = DateField("Hasta", validators=[Optional()])
    submit = SubmitField("Aplicar filtros")


class LicenciaAccionForm(FlaskForm):
    """Simple action form that only carries the CSRF token."""

    submit = SubmitField()


class LicenciaRechazoForm(FlaskForm):
    """Form used to capture an optional rejection reason."""

    motivo_rechazo = TextAreaField(
        "Motivo de rechazo",
        validators=[Optional(), Length(max=500)],
        description="Se enviará al solicitante junto con la notificación de rechazo.",
    )
    submit = SubmitField("Confirmar rechazo")


__all__ = [
    "LicenciaForm",
    "AprobarRechazarForm",
    "CalendarioFiltroForm",
    "MisLicenciasFiltroForm",
    "GestionLicenciasFiltroForm",
    "LicenciaAccionForm",
    "LicenciaRechazoForm",
]
