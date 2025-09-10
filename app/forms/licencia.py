from datetime import date

from flask_wtf import FlaskForm
from wtforms import StringField, DateField, TextAreaField, RadioField, SubmitField
from wtforms.validators import DataRequired, Length, ValidationError


class LicenciaForm(FlaskForm):
    empleado = StringField("Empleado", validators=[DataRequired(), Length(max=100)])
    fecha_inicio = DateField("Fecha de inicio", validators=[DataRequired()])
    fecha_fin = DateField("Fecha de fin", validators=[DataRequired()])
    motivo = TextAreaField("Motivo", validators=[DataRequired(), Length(max=255)])
    submit = SubmitField("Solicitar")

    def validate_fecha_fin(self, field):
        if self.fecha_inicio.data and field.data and field.data < self.fecha_inicio.data:
            raise ValidationError("La fecha de fin debe ser posterior a la fecha de inicio")


class AprobarRechazarForm(FlaskForm):
    accion = RadioField(
        "Acción",
        choices=[("aprobar", "Aprobar"), ("rechazar", "Rechazar")],
        validators=[DataRequired()],
    )
    comentario = TextAreaField("Comentario", validators=[Length(max=255)])
    submit = SubmitField("Enviar")
