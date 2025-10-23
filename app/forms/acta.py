"""Forms for acta generation."""
from __future__ import annotations

from flask_wtf import FlaskForm
from wtforms import SelectField, SubmitField, TextAreaField
from wtforms.validators import DataRequired, Length, Optional, ValidationError

from app.forms.fields import CSVIntegerListField
from app.models import Equipo, Hospital, Oficina, Servicio, TipoActa
from app.utils.forms import preload_model_choice


class ActaForm(FlaskForm):
    """Form used to generate acta documents."""

    tipo = SelectField(
        "Tipo de acta",
        choices=[(t.value, t.name.title()) for t in TipoActa],
        validators=[DataRequired()],
    )
    hospital_id = SelectField(
        "Hospital",
        coerce=int,
        validators=[DataRequired()],
        validate_choice=False,
        render_kw={"data-placeholder": "Seleccione un hospital"},
    )
    servicio_id = SelectField(
        "Servicio",
        coerce=lambda value: int(value) if value else None,
        validators=[Optional()],
        validate_choice=False,
        render_kw={"data-placeholder": "Escriba para buscar un servicio"},
    )
    oficina_id = SelectField(
        "Oficina",
        coerce=lambda value: int(value) if value else None,
        validators=[Optional()],
        validate_choice=False,
        render_kw={"data-placeholder": "Seleccione un servicio para buscar oficinas"},
    )
    equipos = CSVIntegerListField("Equipos", validators=[DataRequired()])
    observaciones = TextAreaField("Observaciones", validators=[Optional(), Length(max=500)])
    submit = SubmitField("Generar acta")

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._preload_selected_hospital()
        self._preload_selected_servicio()
        self._preload_selected_oficina()
        if not self.equipos.data:
            self.equipos.data = []

    def _preload_selected_hospital(self) -> None:
        preload_model_choice(self.hospital_id, Hospital, lambda hospital: hospital.nombre)

    def _preload_selected_servicio(self) -> None:
        preload_model_choice(
            self.servicio_id,
            Servicio,
            lambda servicio: f"{servicio.hospital.nombre} · {servicio.nombre}",
        )

    def _preload_selected_oficina(self) -> None:
        preload_model_choice(
            self.oficina_id,
            Oficina,
            lambda oficina: f"{oficina.hospital.nombre} · {oficina.nombre}",
        )

    def validate_equipos(self, field: CSVIntegerListField) -> None:  # type: ignore[override]
        if not field.data:
            raise ValidationError("Seleccione al menos un equipo")
        existentes = Equipo.query.filter(Equipo.id.in_(field.data)).all()
        encontrados = {equipo.id for equipo in existentes}
        faltantes = [str(eid) for eid in field.data if eid not in encontrados]
        if faltantes:
            raise ValidationError("Algunos equipos seleccionados no existen")


__all__ = ["ActaForm"]
