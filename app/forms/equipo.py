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
    servicio_id = SelectField("Servicio", coerce=int, validators=[Optional()])
    oficina_id = SelectField("Oficina", coerce=int, validators=[Optional()])
    responsable = StringField("Responsable", validators=[Optional(), Length(max=120)])
    fecha_compra = DateField("Fecha de compra", validators=[Optional()], default=None)
    fecha_instalacion = DateField("Fecha de instalación", validators=[Optional()], default=None)
    garantia_hasta = DateField("Garantía hasta", validators=[Optional()], default=None)
    observaciones = TextAreaField("Observaciones", validators=[Optional(), Length(max=1000)])
    insumos = SelectMultipleField("Insumos asociados", coerce=int, validators=[Optional()])
    submit = SubmitField("Guardar")

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.tipo.choices = [(tipo.value, tipo.name.replace("_", " ").title()) for tipo in TipoEquipo]
        self.estado.choices = [(estado.value, estado.name.replace("_", " ").title()) for estado in EstadoEquipo]
        self.hospital_id.choices = [(h.id, h.nombre) for h in Hospital.query.order_by(Hospital.nombre)]
        self.hospital_id.choices.insert(0, (0, "- Seleccione -"))
        self.servicio_id.choices = [(0, "- Seleccione -")] + [
            (s.id, f"{s.hospital.nombre} / {s.nombre}") for s in Servicio.query.order_by(Servicio.nombre)
        ]
        self.oficina_id.choices = [(0, "- Seleccione -")] + [
            (o.id, f"{o.hospital.nombre} / {o.nombre}") for o in Oficina.query.order_by(Oficina.nombre)
        ]
        self.insumos.choices = [(i.id, i.nombre) for i in Insumo.query.order_by(Insumo.nombre)]

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
