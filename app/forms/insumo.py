"""Forms for managing consumables."""
from __future__ import annotations

from flask_wtf import FlaskForm
from wtforms import DecimalField, IntegerField, SelectField, SelectMultipleField, StringField, SubmitField, TextAreaField
from wtforms.validators import DataRequired, Length, NumberRange, Optional

from app.models import Equipo, MovimientoTipo


class InsumoForm(FlaskForm):
    """Create or edit an insumo."""

    nombre = StringField("Nombre", validators=[DataRequired(), Length(max=120)])
    numero_serie = StringField("Número de serie", validators=[Optional(), Length(max=100)])
    descripcion = TextAreaField("Descripción", validators=[Optional(), Length(max=500)])
    unidad_medida = StringField("Unidad de medida", validators=[Optional(), Length(max=20)])
    stock = IntegerField("Stock", validators=[DataRequired(), NumberRange(min=0)])
    stock_minimo = IntegerField("Stock mínimo", validators=[Optional(), NumberRange(min=0)])
    costo_unitario = DecimalField(
        "Costo unitario",
        validators=[Optional(), NumberRange(min=0)],
        places=2,
    )
    equipos = SelectMultipleField("Equipos asociados", coerce=int, validators=[Optional()])
    submit = SubmitField("Guardar")

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.equipos.choices = [
            (e.id, f"{e.codigo or e.descripcion or e.id}") for e in Equipo.query.order_by(Equipo.descripcion)
        ]


class MovimientoForm(FlaskForm):
    """Register stock movements."""

    tipo = SelectField(
        "Tipo de movimiento",
        choices=[(MovimientoTipo.INGRESO.value, "Ingreso"), (MovimientoTipo.EGRESO.value, "Egreso")],
        validators=[DataRequired()],
    )
    cantidad = IntegerField("Cantidad", validators=[DataRequired(), NumberRange(min=1)])
    equipo_id = SelectField("Equipo relacionado", coerce=int, validators=[Optional()])
    motivo = StringField("Motivo", validators=[Optional(), Length(max=255)])
    observaciones = TextAreaField("Observaciones", validators=[Optional(), Length(max=500)])
    submit = SubmitField("Registrar movimiento")

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.equipo_id.choices = [(0, "N/A")] + [
            (e.id, f"{e.codigo or e.descripcion or e.id}") for e in Equipo.query.order_by(Equipo.descripcion)
        ]


__all__ = ["InsumoForm", "MovimientoForm"]
