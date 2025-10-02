"""Forms for acta generation."""
from __future__ import annotations

from flask_wtf import FlaskForm
from wtforms import SelectField, SubmitField, TextAreaField
from wtforms.validators import DataRequired, Length, Optional, ValidationError

from app.forms.fields import CSVIntegerListField
from app.models import Equipo, Hospital, Oficina, Servicio, TipoActa


class ActaForm(FlaskForm):
    """Form used to generate acta documents."""

    tipo = SelectField(
        "Tipo de acta",
        choices=[(t.value, t.name.title()) for t in TipoActa],
        validators=[DataRequired()],
    )
    hospital_id = SelectField("Hospital", coerce=int, validators=[DataRequired()])
    servicio_id = SelectField(
        "Servicio",
        coerce=int,
        validators=[Optional()],
        validate_choice=False,
        render_kw={"data-placeholder": "Escriba para buscar un servicio"},
    )
    oficina_id = SelectField(
        "Oficina",
        coerce=int,
        validators=[Optional()],
        validate_choice=False,
        render_kw={"data-placeholder": "Seleccione un servicio para buscar oficinas"},
    )
    equipos = CSVIntegerListField("Equipos", validators=[DataRequired()])
    observaciones = TextAreaField("Observaciones", validators=[Optional(), Length(max=500)])
    submit = SubmitField("Generar acta")

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.hospital_id.choices = [(h.id, h.nombre) for h in Hospital.query.order_by(Hospital.nombre)]
        self._preload_selected_servicio()
        self._preload_selected_oficina()
        if not self.equipos.data:
            self.equipos.data = []

    def _preload_selected_servicio(self) -> None:
        value = self.servicio_id.data or (self.servicio_id.raw_data[0] if self.servicio_id.raw_data else None)
        if not value:
            self.servicio_id.choices = []
            return
        try:
            servicio_id = int(value)
        except (TypeError, ValueError):
            self.servicio_id.choices = []
            return
        servicio = Servicio.query.get(servicio_id)
        if servicio:
            label = f"{servicio.hospital.nombre} · {servicio.nombre}"
            self.servicio_id.choices = [(servicio.id, label)]
        else:
            self.servicio_id.choices = []

    def _preload_selected_oficina(self) -> None:
        value = self.oficina_id.data or (self.oficina_id.raw_data[0] if self.oficina_id.raw_data else None)
        if not value:
            self.oficina_id.choices = []
            return
        try:
            oficina_id = int(value)
        except (TypeError, ValueError):
            self.oficina_id.choices = []
            return
        oficina = Oficina.query.get(oficina_id)
        if oficina:
            label = f"{oficina.hospital.nombre} · {oficina.nombre}"
            self.oficina_id.choices = [(oficina.id, label)]
        else:
            self.oficina_id.choices = []

    def validate_equipos(self, field: CSVIntegerListField) -> None:  # type: ignore[override]
        if not field.data:
            raise ValidationError("Seleccione al menos un equipo")
        existentes = Equipo.query.filter(Equipo.id.in_(field.data)).all()
        encontrados = {equipo.id for equipo in existentes}
        faltantes = [str(eid) for eid in field.data if eid not in encontrados]
        if faltantes:
            raise ValidationError("Algunos equipos seleccionados no existen")


__all__ = ["ActaForm"]
