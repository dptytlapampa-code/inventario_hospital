"""Forms for managing consumables."""
from __future__ import annotations

from flask_wtf import FlaskForm
from wtforms import (
    BooleanField,
    DecimalField,
    IntegerField,
    SelectField,
    StringField,
    SubmitField,
    TextAreaField,
)
from wtforms.validators import DataRequired, Length, NumberRange, Optional, ValidationError

from app.forms.fields import HiddenIntegerField
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
    submit = SubmitField("Guardar")


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


class InsumoSeriesForm(FlaskForm):
    """Agregar números de serie a un insumo."""

    series = TextAreaField(
        "Números de serie",
        validators=[DataRequired()],
        description="Ingrese uno por línea o separados por comas.",
    )
    ajustar_stock = BooleanField(
        "Sumar la cantidad de series creadas al stock actual",
        default=False,
    )
    submit = SubmitField("Agregar series")

    _parsed_series: list[str] | None = None

    def parsed_series(self) -> list[str]:
        """Return sanitized serial numbers removing blanks."""

        if self._parsed_series is None:
            raw_value = self.series.data or ""
            candidates = raw_value.replace(",", "\n").splitlines()
            parsed: list[str] = []
            for item in candidates:
                value = item.strip()
                if value:
                    parsed.append(value)
            self._parsed_series = parsed
        return self._parsed_series

    def validate_series(self, field: TextAreaField) -> None:  # type: ignore[override]
        valores = self.parsed_series()
        if not valores:
            raise ValidationError("Debe ingresar al menos un número de serie")
        if len(valores) > 200:
            raise ValidationError("No se pueden cargar más de 200 series a la vez")

        vistos: set[str] = set()
        duplicados: set[str] = set()
        for numero in valores:
            if numero in vistos:
                duplicados.add(numero)
            vistos.add(numero)
        if duplicados:
            duplicados_txt = ", ".join(sorted(duplicados))
            raise ValidationError(
                f"Los números de serie no pueden repetirse: {duplicados_txt}"
            )


__all__ = ["InsumoForm", "MovimientoForm", "InsumoSeriesForm"]
