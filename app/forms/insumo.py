"""Forms for managing consumables."""
from __future__ import annotations

from flask_wtf import FlaskForm
from wtforms import DecimalField, IntegerField, SelectField, StringField, SubmitField, TextAreaField
from wtforms.validators import DataRequired, Length, NumberRange, Optional, ValidationError

from app.forms.fields import CSVIntegerListField, HiddenIntegerField
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
    equipos = CSVIntegerListField("Equipos asociados", validators=[Optional()])
    submit = SubmitField("Guardar")

    def validate_equipos(self, field: CSVIntegerListField) -> None:  # type: ignore[override]
        if not field.data:
            return
        existentes = Equipo.query.filter(Equipo.id.in_(field.data)).all()
        encontrados = {equipo.id for equipo in existentes}
        faltantes = [str(eid) for eid in field.data if eid not in encontrados]
        if faltantes:
            raise ValidationError("Algunos equipos seleccionados no existen")


class MovimientoForm(FlaskForm):
    """Register stock movements."""

    tipo = SelectField(
        "Tipo de movimiento",
        choices=[(MovimientoTipo.INGRESO.value, "Ingreso"), (MovimientoTipo.EGRESO.value, "Egreso")],
        validators=[DataRequired()],
    )
    cantidad = IntegerField("Cantidad", validators=[DataRequired(), NumberRange(min=1)])
    equipo_id = HiddenIntegerField("Equipo relacionado", validators=[Optional()])
    motivo = StringField("Motivo", validators=[Optional(), Length(max=255)])
    observaciones = TextAreaField("Observaciones", validators=[Optional(), Length(max=500)])
    submit = SubmitField("Registrar movimiento")

    def validate_equipo_id(self, field: HiddenIntegerField) -> None:  # type: ignore[override]
        if field.data in (None, 0):
            field.data = None
            return
        equipo = Equipo.query.get(field.data)
        if not equipo:
            raise ValidationError("Seleccione un equipo válido")


__all__ = ["InsumoForm", "MovimientoForm"]
