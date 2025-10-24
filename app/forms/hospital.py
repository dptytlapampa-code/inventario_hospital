"""Forms for managing institution hierarchy."""
from __future__ import annotations

from flask_wtf import FlaskForm
from wtforms import SelectField, StringField, SubmitField, TextAreaField
from wtforms.validators import DataRequired, Length, Optional, ValidationError

from app.models import Hospital, Servicio
from app.utils.forms import preload_model_choice


class HospitalForm(FlaskForm):
    nombre = StringField("Nombre", validators=[DataRequired(), Length(max=255)])
    tipo_institucion = SelectField(
        "Tipo de institución",
        choices=[("Hospital", "Hospital")],
        default="Hospital",
        validators=[DataRequired()],
    )
    codigo = StringField("Código", validators=[Optional(), Length(max=50)])
    localidad = StringField("Localidad", validators=[DataRequired(), Length(max=120)])
    provincia = StringField(
        "Provincia",
        validators=[DataRequired(), Length(max=120)],
        default="La Pampa",
    )
    zona_sanitaria = StringField("Zona sanitaria", validators=[Optional(), Length(max=120)])
    direccion = StringField("Dirección", validators=[Optional(), Length(max=255)])
    estado = SelectField(
        "Estado",
        choices=[("Activa", "Activa"), ("Inactiva", "Inactiva")],
        default="Activa",
        validators=[DataRequired()],
    )
    submit = SubmitField("Guardar")


class ServicioForm(FlaskForm):
    nombre = StringField("Nombre del servicio", validators=[DataRequired(), Length(max=120)])
    descripcion = TextAreaField("Descripción", validators=[Optional(), Length(max=255)])
    hospital_id = SelectField(
        "Institución",
        coerce=int,
        validators=[DataRequired()],
        validate_choice=False,
        render_kw={"data-placeholder": "Seleccione una institución"},
    )
    submit = SubmitField("Guardar")

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        preload_model_choice(self.hospital_id, Hospital, lambda hospital: hospital.nombre)


class OficinaForm(FlaskForm):
    nombre = StringField("Nombre de la oficina", validators=[DataRequired(), Length(max=120)])
    piso = StringField("Piso", validators=[Optional(), Length(max=20)])
    hospital_id = SelectField(
        "Institución",
        coerce=int,
        validators=[DataRequired()],
        validate_choice=False,
        render_kw={"data-placeholder": "Seleccione una institución"},
    )
    servicio_id = SelectField(
        "Servicio",
        coerce=int,
        validators=[DataRequired()],
        validate_choice=False,
        render_kw={"data-placeholder": "Seleccione un servicio"},
    )
    submit = SubmitField("Guardar")

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        preload_model_choice(self.hospital_id, Hospital, lambda hospital: hospital.nombre)
        preload_model_choice(
            self.servicio_id,
            Servicio,
            lambda servicio: f"{servicio.hospital.nombre} · {servicio.nombre}",
        )

    def validate_servicio_id(self, field: SelectField) -> None:  # type: ignore[override]
        if not field.data:
            raise ValidationError("Seleccione un servicio")

        servicio = Servicio.query.get(field.data)
        if not servicio:
            raise ValidationError("Seleccione un servicio válido")

        hospital_id = self.hospital_id.data
        if hospital_id and servicio.hospital_id != hospital_id:
            raise ValidationError(
                "Seleccione un servicio perteneciente a la institución indicada"
            )


__all__ = ["HospitalForm", "ServicioForm", "OficinaForm"]
