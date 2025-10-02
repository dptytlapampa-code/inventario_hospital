"""Forms for equipment management."""
from __future__ import annotations

from datetime import date

from flask_wtf import FlaskForm
from flask_wtf.file import FileAllowed, FileField, FileRequired
from sqlalchemy import func
from wtforms import (
    BooleanField,
    DateField,
    HiddenField,
    IntegerField,
    SelectField,
    StringField,
    SubmitField,
    TextAreaField,
)
from wtforms.validators import DataRequired, Length, Optional, ValidationError

from app.models import (
    EstadoEquipo,
    Hospital,
    Oficina,
    Servicio,
    TipoActa,
    TipoEquipo,
)


class EquipoForm(FlaskForm):
    """Create or edit an equipment entry."""

    codigo = StringField("Código patrimonial", validators=[Optional(), Length(max=50)])
    tipo = SelectField("Tipo", choices=[], validators=[DataRequired()], coerce=int)
    estado = SelectField("Estado", choices=[], validators=[DataRequired()])
    descripcion = TextAreaField("Descripción", validators=[Optional(), Length(max=500)])
    marca = StringField("Marca", validators=[Optional(), Length(max=100)])
    modelo = StringField("Modelo", validators=[Optional(), Length(max=100)])
    numero_serie = StringField("Número de serie", validators=[Optional(), Length(max=120)])
    hospital_id = IntegerField(
        "Hospital", validators=[DataRequired(message="Seleccione una opción válida")]
    )
    servicio_id = IntegerField("Servicio", validators=[Optional()])
    oficina_id = IntegerField("Oficina", validators=[Optional()])
    responsable = StringField("Responsable", validators=[Optional(), Length(max=120)])
    fecha_ingreso = DateField("Fecha de ingreso", validators=[Optional()], default=None)
    fecha_instalacion = DateField("Fecha de instalación", validators=[Optional()], default=None)
    garantia_hasta = DateField("Garantía hasta", validators=[Optional()], default=None)
    observaciones = TextAreaField("Observaciones", validators=[Optional(), Length(max=1000)])
    sin_numero_serie = BooleanField("Sin número de serie visible", default=False)
    es_nuevo = BooleanField("Equipo nuevo", default=False)
    expediente = StringField("Expediente", validators=[Optional(), Length(max=120)])
    anio_expediente = IntegerField(
        "Año del expediente",
        validators=[Optional()],
        render_kw={"min": 1900, "max": 2100},
    )
    orden_compra = StringField("Orden de compra", validators=[Optional(), Length(max=120)])
    tipo_adquisicion = SelectField(
        "Tipo de adquisición",
        choices=[
            ("", "Seleccione una opción"),
            ("licitacion", "Licitación"),
            ("compra", "Compra"),
            ("donacion", "Donación"),
            ("otro", "Otro"),
        ],
        validators=[Optional()],
        coerce=str,
    )
    submit = SubmitField("Guardar")

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._populate_tipo_choices()
        if isinstance(self.tipo.data, TipoEquipo):
            self.tipo.data = self.tipo.data.id
        self._initial_tipo_id = self.tipo.data if isinstance(self.tipo.data, int) else None
        self.estado.choices = [(estado.value, estado.name.replace("_", " ").title()) for estado in EstadoEquipo]

    def _populate_tipo_choices(self) -> None:
        tipos = (
            TipoEquipo.query.order_by(TipoEquipo.nombre).all()
            if TipoEquipo is not None
            else []
        )
        active_choices = [(tipo.id, tipo.nombre) for tipo in tipos if tipo.activo]
        selected = self.tipo.data
        if selected and isinstance(selected, str) and selected.isdigit():
            selected = int(selected)
        if selected and selected not in {choice[0] for choice in active_choices}:
            current = next((tipo for tipo in tipos if tipo.id == selected), None)
            if current:
                active_choices.append((current.id, f"{current.nombre} (inactivo)"))
        self.tipo.choices = active_choices
        self.tipo.render_kw = {} if active_choices else {"disabled": "disabled"}

    def validate(self, extra_validators=None):  # type: ignore[override]
        if not super().validate(extra_validators=extra_validators):
            return False
        if not self.tipo.choices:
            self.tipo.errors.append(
                "No hay tipos de equipo activos disponibles. Pida a un superadministrador que los configure."
            )
            return False
        tipo = TipoEquipo.query.get(self.tipo.data)
        if not tipo:
            self.tipo.errors.append("Seleccione un tipo válido")
            return False
        if not tipo.activo and self._initial_tipo_id != tipo.id:
            self.tipo.errors.append("Seleccione un tipo activo")
            return False
        numero_serie = (self.numero_serie.data or "").strip()
        if not self.sin_numero_serie.data and not numero_serie:
            self.numero_serie.errors.append(
                "Ingrese un número de serie o marque 'Sin número de serie visible'"
            )
            return False
        if self.fecha_ingreso.data and self.fecha_ingreso.data > date.today():
            self.fecha_ingreso.errors.append("La fecha de ingreso no puede ser futura")
            return False
        if (
            self.fecha_instalacion.data
            and self.fecha_ingreso.data
            and self.fecha_instalacion.data < self.fecha_ingreso.data
        ):
            self.fecha_instalacion.errors.append("La instalación no puede ser anterior al ingreso")
            return False
        if self.es_nuevo.data:
            if not self.tipo_adquisicion.data:
                self.tipo_adquisicion.errors.append("Seleccione el tipo de adquisición")
                return False
            if not (self.expediente.data or self.orden_compra.data):
                self.expediente.errors.append(
                    "Ingrese el expediente u orden de compra utilizada en el alta"
                )
                self.orden_compra.errors.append(
                    "Ingrese el expediente u orden de compra utilizada en el alta"
                )
                return False
            if self.anio_expediente.data and not (1900 <= self.anio_expediente.data <= date.today().year + 1):
                self.anio_expediente.errors.append("Ingrese un año válido")
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


class EquipoAdjuntoForm(FlaskForm):
    """Upload form for equipment attachments."""

    archivo = FileField(
        "Archivo",
        validators=[
            FileRequired(message="Seleccione un archivo"),
            FileAllowed({"pdf", "jpg", "jpeg", "png"}, "Formatos permitidos: PDF o imagen"),
        ],
    )
    submit = SubmitField("Subir archivo")


class EquipoAdjuntoDeleteForm(FlaskForm):
    """Simple CSRF protected form to remove an attachment."""

    submit = SubmitField("Eliminar")


class EquipoHistorialFiltroForm(FlaskForm):
    """Filter historical entries for an equipment."""

    accion = StringField("Acción", validators=[Optional(), Length(max=120)])
    fecha_desde = DateField("Desde", validators=[Optional()])
    fecha_hasta = DateField("Hasta", validators=[Optional()])
    submit = SubmitField("Filtrar")

    def validate(self, extra_validators=None):  # type: ignore[override]
        if not super().validate(extra_validators=extra_validators):
            return False
        if (
            self.fecha_desde.data
            and self.fecha_hasta.data
            and self.fecha_desde.data > self.fecha_hasta.data
        ):
            self.fecha_hasta.errors.append("La fecha hasta debe ser posterior a la fecha desde")
            return False
        return True


class EquipoActaFiltroForm(FlaskForm):
    """Filter actas associated with an equipment."""

    tipo = SelectField("Tipo", coerce=str, validators=[Optional()])
    fecha_desde = DateField("Desde", validators=[Optional()])
    fecha_hasta = DateField("Hasta", validators=[Optional()])
    submit = SubmitField("Filtrar")

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.tipo.choices = [("", "Todos")] + [
            (tipo.value, tipo.name.replace("_", " ").title()) for tipo in TipoActa
        ]

    def validate(self, extra_validators=None):  # type: ignore[override]
        if not super().validate(extra_validators=extra_validators):
            return False
        if (
            self.fecha_desde.data
            and self.fecha_hasta.data
            and self.fecha_desde.data > self.fecha_hasta.data
        ):
            self.fecha_hasta.errors.append("La fecha hasta debe ser posterior a la fecha desde")
            return False
        return True


class TipoEquipoCreateForm(FlaskForm):
    """Form used by administrators to create new equipment types."""

    nombre = StringField("Nombre", validators=[DataRequired(), Length(max=160)])
    descripcion = TextAreaField("Descripción", validators=[Optional(), Length(max=500)])
    activo = BooleanField("Activo", default=True)
    submit = SubmitField("Agregar tipo")

    def validate(self, extra_validators=None):  # type: ignore[override]
        is_valid = super().validate(extra_validators=extra_validators)
        self._deduplicate_errors()
        return is_valid

    @staticmethod
    def _normalized(value: str | None) -> str:
        return (value or "").strip().lower()

    def validate_nombre(self, field: StringField) -> None:  # type: ignore[override]
        existing = (
            TipoEquipo.query.filter(func.lower(TipoEquipo.nombre) == self._normalized(field.data))
            .first()
        )
        if existing:
            raise ValidationError("Ya existe un tipo con ese nombre")

    def _deduplicate_errors(self) -> None:
        for field in self._fields.values():
            if getattr(field, "errors", None):
                seen: set[str] = set()
                deduped: list[str] = []
                for error in field.errors:
                    if error not in seen:
                        seen.add(error)
                        deduped.append(error)
                field.errors[:] = deduped


class TipoEquipoUpdateForm(FlaskForm):
    """Form to rename or toggle availability of existing types."""

    tipo_id = HiddenField(validators=[DataRequired()])
    nombre = StringField("Nombre", validators=[DataRequired(), Length(max=160)])
    descripcion = TextAreaField("Descripción", validators=[Optional(), Length(max=500)])
    activo = BooleanField("Activo")
    submit = SubmitField("Guardar cambios")

    def validate(self, extra_validators=None):  # type: ignore[override]
        is_valid = super().validate(extra_validators=extra_validators)
        self._deduplicate_errors()
        return is_valid

    @staticmethod
    def _normalized(value: str | None) -> str:
        return (value or "").strip().lower()

    def validate_nombre(self, field: StringField) -> None:  # type: ignore[override]
        try:
            current_id = int(self.tipo_id.data)
        except (TypeError, ValueError) as exc:
            raise ValidationError("Identificador inválido") from exc
        existing = (
            TipoEquipo.query.filter(func.lower(TipoEquipo.nombre) == self._normalized(field.data))
            .filter(TipoEquipo.id != current_id)
            .first()
        )
        if existing:
            raise ValidationError("Ya existe un tipo con ese nombre")

    def _deduplicate_errors(self) -> None:
        for field in self._fields.values():
            if getattr(field, "errors", None):
                seen: set[str] = set()
                deduped: list[str] = []
                for error in field.errors:
                    if error not in seen:
                        seen.add(error)
                        deduped.append(error)
                field.errors[:] = deduped

__all__ = [
    "EquipoForm",
    "EquipoFiltroForm",
    "EquipoAdjuntoForm",
    "EquipoAdjuntoDeleteForm",
    "EquipoHistorialFiltroForm",
    "EquipoActaFiltroForm",
    "TipoEquipoCreateForm",
    "TipoEquipoUpdateForm",
]
