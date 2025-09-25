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
    hospital_busqueda = StringField("Hospital", validators=[DataRequired(), Length(max=160)])
    hospital_id = HiddenField()
    servicio_busqueda = StringField("Servicio", validators=[Optional(), Length(max=160)])
    servicio_id = HiddenField()
    oficina_busqueda = StringField("Oficina", validators=[Optional(), Length(max=160)])
    oficina_id = HiddenField()
    responsable = StringField("Responsable", validators=[Optional(), Length(max=120)])
    fecha_compra = DateField("Fecha de compra", validators=[Optional()], default=None)
    fecha_instalacion = DateField("Fecha de instalación", validators=[Optional()], default=None)
    garantia_hasta = DateField("Garantía hasta", validators=[Optional()], default=None)
    observaciones = TextAreaField("Observaciones", validators=[Optional(), Length(max=1000)])
    sin_numero_serie = BooleanField("Sin número de serie visible", default=False)
    submit = SubmitField("Guardar")

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._populate_tipo_choices()
        if isinstance(self.tipo.data, TipoEquipo):
            self.tipo.data = self.tipo.data.id
        self._initial_tipo_id = self.tipo.data if isinstance(self.tipo.data, int) else None
        self.estado.choices = [(estado.value, estado.name.replace("_", " ").title()) for estado in EstadoEquipo]
        self._populate_lookup_defaults()

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

    # pylint: disable=too-many-return-statements
    def _populate_lookup_defaults(self) -> None:
        if self.hospital_id.data:
            try:
                hospital_id = int(self.hospital_id.data)
            except (TypeError, ValueError):
                hospital_id = None
            if hospital_id:
                hospital = Hospital.query.get(hospital_id)
                if hospital:
                    self.hospital_busqueda.data = self._format_hospital_label(hospital)
        if self.servicio_id.data:
            try:
                servicio_id = int(self.servicio_id.data)
            except (TypeError, ValueError):
                servicio_id = None
            if servicio_id:
                servicio = Servicio.query.get(servicio_id)
                if servicio:
                    self.servicio_busqueda.data = servicio.nombre
        if self.oficina_id.data:
            try:
                oficina_id = int(self.oficina_id.data)
            except (TypeError, ValueError):
                oficina_id = None
            if oficina_id:
                oficina = Oficina.query.get(oficina_id)
                if oficina:
                    self.oficina_busqueda.data = oficina.nombre

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
        if not self._validate_lookup(
            self.hospital_busqueda,
            self.hospital_id,
            Hospital,
            required=True,
            label_getter=self._format_hospital_label,
        ):
            return False
        if not self._validate_lookup(self.servicio_busqueda, self.servicio_id, Servicio, required=False):
            return False
        if not self._validate_lookup(self.oficina_busqueda, self.oficina_id, Oficina, required=False):
            return False

        if self.servicio_id.data:
            servicio = Servicio.query.get(self.servicio_id.data)
            if not servicio or servicio.hospital_id != self.hospital_id.data:
                self.servicio_busqueda.errors.append("Seleccione una opción válida")
                return False
        if self.oficina_id.data:
            oficina = Oficina.query.get(self.oficina_id.data)
            if not oficina or oficina.hospital_id != self.hospital_id.data:
                self.oficina_busqueda.errors.append("Seleccione una opción válida")
                return False
            if self.servicio_id.data and oficina.servicio_id and oficina.servicio_id != self.servicio_id.data:
                self.oficina_busqueda.errors.append("Seleccione una opción válida")
                return False
        numero_serie = (self.numero_serie.data or "").strip()
        if not self.sin_numero_serie.data and not numero_serie:
            self.numero_serie.errors.append(
                "Ingrese un número de serie o marque 'Sin número de serie visible'"
            )
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

    @staticmethod
    def _validate_lookup(text_field, hidden_field, model, required: bool, label_getter=None) -> bool:
        text = (text_field.data or "").strip() if text_field is not None else ""
        hidden_value = hidden_field.data if hidden_field is not None else None

        if not text and not hidden_value:
            if required:
                text_field.errors.append("Seleccione una opción válida")
                return False
            hidden_field.data = None
            return True

        if required and not hidden_value:
            text_field.errors.append("Seleccione una opción válida")
            return False
        if hidden_value in (None, ""):
            if text:
                text_field.errors.append("Seleccione una opción válida")
                return False
            text_field.data = ""
            hidden_field.data = None
            return True
        try:
            identifier = int(hidden_value)
        except (TypeError, ValueError):
            text_field.errors.append("Seleccione una opción válida")
            return False
        instance = model.query.get(identifier)
        if not instance:
            text_field.errors.append("Seleccione una opción válida")
            return False
        hidden_field.data = identifier
        if text_field is not None:
            if label_getter is not None:
                text_field.data = label_getter(instance)
            else:
                text_field.data = getattr(instance, "nombre", str(instance))
        return True

    @staticmethod
    def _format_hospital_label(hospital: Hospital) -> str:
        localidad = getattr(hospital, "localidad", None) or getattr(hospital, "direccion", None)
        return f"{hospital.nombre} - {localidad}" if localidad else hospital.nombre


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
    """Form used by superadmins to create new equipment types."""

    nombre = StringField("Nombre", validators=[DataRequired(), Length(max=160)])
    submit = SubmitField("Agregar tipo")

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


class TipoEquipoUpdateForm(FlaskForm):
    """Form to rename or toggle availability of existing types."""

    tipo_id = HiddenField(validators=[DataRequired()])
    nombre = StringField("Nombre", validators=[DataRequired(), Length(max=160)])
    activo = BooleanField("Activo")
    submit = SubmitField("Guardar cambios")

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
