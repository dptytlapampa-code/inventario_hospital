"""Forms for equipment management."""
from __future__ import annotations

from datetime import date

from flask_wtf import FlaskForm
from wtforms import (
    DateField,
    SelectField,
    SelectMultipleField,
    StringField,
    SubmitField,
    TextAreaField,
)
from wtforms.validators import DataRequired, Length, Optional

from app.models import EstadoEquipo, Hospital, Insumo, Oficina, Servicio, TipoEquipo


class EquipoForm(FlaskForm):
    """Create or edit an equipment entry."""

    codigo = StringField("Código patrimonial", validators=[Optional(), Length(max=50)])
    tipo = SelectField("Tipo", choices=[], validators=[DataRequired()])
    estado = SelectField("Estado", choices=[], validators=[DataRequired()])
    descripcion = TextAreaField("Descripción", validators=[Optional(), Length(max=500)])
    marca = StringField("Marca", validators=[Optional(), Length(max=100)])
    modelo = StringField("Modelo", validators=[Optional(), Length(max=100)])
    numero_serie = StringField("Número de serie", validators=[Optional(), Length(max=120)])
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
    responsable = StringField("Responsable", validators=[Optional(), Length(max=120)])
    fecha_compra = DateField("Fecha de compra", validators=[Optional()], default=None)
    fecha_instalacion = DateField("Fecha de instalación", validators=[Optional()], default=None)
    garantia_hasta = DateField("Garantía hasta", validators=[Optional()], default=None)
    observaciones = TextAreaField("Observaciones", validators=[Optional(), Length(max=1000)])
    insumos = SelectMultipleField(
        "Insumos asociados",
        coerce=int,
        validators=[Optional()],
        validate_choice=False,
        render_kw={"data-placeholder": "Buscar insumos"},
    )
    submit = SubmitField("Guardar")

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.tipo.choices = [(tipo.value, tipo.name.replace("_", " ").title()) for tipo in TipoEquipo]
        self.estado.choices = [(estado.value, estado.name.replace("_", " ").title()) for estado in EstadoEquipo]
        self.hospital_id.choices = [
            (h.id, h.nombre) for h in Hospital.query.order_by(Hospital.nombre)
        ]
        self.hospital_id.choices.insert(0, (0, "- Seleccione -"))

        self._preload_selected_servicio()
        self._preload_selected_oficina()
        self._preload_selected_insumos()

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

    def _preload_selected_insumos(self) -> None:
        data = self.insumos.data or self.insumos.raw_data or []
        if not data:
            self.insumos.choices = []
            return
        if not isinstance(data, (list, tuple)):
            data = [data]
        ids = []
        for value in data:
            try:
                ids.append(int(value))
            except (TypeError, ValueError):  # pragma: no cover - defensive
                continue
        if not ids:
            self.insumos.choices = []
            return
        insumos = Insumo.query.filter(Insumo.id.in_(ids)).order_by(Insumo.nombre).all()
        self.insumos.choices = [(insumo.id, insumo.nombre) for insumo in insumos]

    def validate(self, extra_validators=None):  # type: ignore[override]
        if not super().validate(extra_validators=extra_validators):
            return False
        if self.hospital_id.data == 0:
            self.hospital_id.errors.append("Debe seleccionar un hospital")
            return False
        if self.fecha_compra.data and self.fecha_compra.data > date.today():
            self.fecha_compra.errors.append("La fecha de compra no puede ser futura")
            return False
        if (
            self.fecha_instalacion.data
            and self.fecha_compra.data
            and self.fecha_instalacion.data < self.fecha_compra.data
        ):
            self.fecha_instalacion.errors.append("La instalación no puede ser anterior a la compra")
            return False
        return True


class EquipoFiltroForm(FlaskForm):
    """Filter form for equipment listing."""

    buscar = StringField("Buscar", validators=[Optional(), Length(max=120)])
    hospital_id = SelectField("Hospital", coerce=int, validators=[Optional()])
    estado = SelectField("Estado", coerce=str, validators=[Optional()])
    submit = SubmitField("Filtrar")

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.hospital_id.choices = [(0, "Todos")] + [
            (h.id, h.nombre) for h in Hospital.query.order_by(Hospital.nombre)
        ]
        self.estado.choices = [("", "Todos")] + [
            (estado.value, estado.name.replace("_", " ").title()) for estado in EstadoEquipo
        ]


__all__ = ["EquipoForm", "EquipoFiltroForm"]
