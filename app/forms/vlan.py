"""Forms to manage VLANs and their devices."""
from __future__ import annotations

from flask_wtf import FlaskForm
from wtforms import SelectField, StringField, SubmitField, TextAreaField
from wtforms.validators import DataRequired, IPAddress, Length, Optional, Regexp, ValidationError

from app.models import Hospital, Oficina, Servicio, Vlan, VlanDispositivo
from app.utils.forms import preload_model_choice


class VlanForm(FlaskForm):
    """Formulario para crear o editar una VLAN."""

    nombre = StringField("Nombre", validators=[DataRequired(), Length(max=120)])
    identificador = StringField(
        "Identificador", validators=[DataRequired(), Length(max=50)]
    )
    descripcion = TextAreaField("Descripción", validators=[Optional(), Length(max=255)])
    hospital_id = SelectField(
        "Hospital",
        coerce=int,
        validators=[DataRequired()],
        validate_choice=False,
        render_kw={"data-placeholder": "Seleccione un hospital"},
    )
    servicio_id = SelectField(
        "Servicio",
        coerce=lambda value: int(value) if value else 0,
        validators=[Optional()],
        validate_choice=False,
        render_kw={"data-placeholder": "Sin servicio asignado"},
    )
    oficina_id = SelectField(
        "Oficina",
        coerce=lambda value: int(value) if value else 0,
        validators=[Optional()],
        validate_choice=False,
        render_kw={"data-placeholder": "Sin oficina asignada"},
    )
    submit = SubmitField("Guardar")

    def __init__(self, vlan: Vlan | None = None, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._vlan = vlan
        self._assign_initial_data()
        self._preload_hospital()
        self._preload_servicio()
        self._preload_oficina()

    def _assign_initial_data(self) -> None:
        if not self._vlan:
            return
        if self.hospital_id.data is None:
            self.hospital_id.data = self._vlan.hospital_id
        if self.servicio_id.data is None and self._vlan.servicio_id:
            self.servicio_id.data = self._vlan.servicio_id
        if self.oficina_id.data is None and self._vlan.oficina_id:
            self.oficina_id.data = self._vlan.oficina_id

    def _preload_hospital(self) -> None:
        preload_model_choice(self.hospital_id, Hospital, lambda hospital: hospital.nombre)

    def _preload_servicio(self) -> None:
        self.servicio_id.choices = [(0, "Sin servicio asignado")]
        value = self.servicio_id.data or 0
        if value:
            servicio = Servicio.query.get(value)
            if servicio:
                self.servicio_id.choices.append((servicio.id, servicio.nombre))

    def _preload_oficina(self) -> None:
        self.oficina_id.choices = [(0, "Sin oficina asignada")]
        value = self.oficina_id.data or 0
        if value:
            oficina = Oficina.query.get(value)
            if oficina:
                self.oficina_id.choices.append((oficina.id, oficina.nombre))

    def validate_identificador(self, field):  # type: ignore[override]
        hospital_id = self.hospital_id.data
        query = Vlan.query.filter_by(
            hospital_id=hospital_id,
            identificador=field.data.strip(),
        )
        if self._vlan:
            query = query.filter(Vlan.id != self._vlan.id)
        if query.first():
            raise ValidationError(
                "Ya existe una VLAN con este identificador en el hospital seleccionado."
            )

    def validate(self, extra_validators=None):  # type: ignore[override]
        if not super().validate(extra_validators=extra_validators):
            return False
        hospital = Hospital.query.get(self.hospital_id.data)
        if not hospital:
            self.hospital_id.errors.append("Hospital inválido.")
            return False
        servicio_id = self.servicio_id.data or None
        oficina_id = self.oficina_id.data or None
        if servicio_id:
            servicio = Servicio.query.get(servicio_id)
            if not servicio or servicio.hospital_id != hospital.id:
                self.servicio_id.errors.append(
                    "El servicio no pertenece al hospital seleccionado."
                )
                return False
        if oficina_id:
            oficina = Oficina.query.get(oficina_id)
            if not oficina or oficina.hospital_id != hospital.id:
                self.oficina_id.errors.append(
                    "La oficina no pertenece al hospital seleccionado."
                )
                return False
            if servicio_id and oficina.servicio_id != servicio_id:
                self.oficina_id.errors.append(
                    "La oficina debe pertenecer al servicio elegido."
                )
                return False
        return True


class VlanDispositivoForm(FlaskForm):
    """Formulario para crear o editar un dispositivo en una VLAN."""

    nombre_equipo = StringField(
        "Nombre del equipamiento", validators=[DataRequired(), Length(max=150)]
    )
    host = StringField("Host", validators=[Optional(), Length(max=120)])
    direccion_ip = StringField(
        "Dirección IP",
        validators=[
            DataRequired(),
            Length(max=45),
            IPAddress(message="Ingrese una IP válida", ipv4=True, ipv6=True),
        ],
    )
    direccion_mac = StringField(
        "Dirección MAC",
        validators=[
            Optional(),
            Regexp(
                r"^(?:[0-9A-Fa-f]{2}([:-]?)){5}[0-9A-Fa-f]{2}$",
                message="Ingrese una dirección MAC válida.",
            ),
            Length(max=32),
        ],
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
        coerce=lambda value: int(value) if value else 0,
        validators=[Optional()],
        validate_choice=False,
        render_kw={"data-placeholder": "Sin servicio asignado"},
    )
    oficina_id = SelectField(
        "Oficina",
        coerce=lambda value: int(value) if value else 0,
        validators=[Optional()],
        validate_choice=False,
        render_kw={"data-placeholder": "Sin oficina asignada"},
    )
    vlan_id = SelectField("VLAN", coerce=int, validators=[DataRequired()])
    notas = TextAreaField("Notas", validators=[Optional(), Length(max=255)])
    submit = SubmitField("Guardar")

    def __init__(
        self,
        dispositivo: VlanDispositivo | None = None,
        *,
        vlan: Vlan | None = None,
        **kwargs,
    ) -> None:
        super().__init__(**kwargs)
        self._dispositivo = dispositivo
        self._vlan = vlan
        self._assign_initial_data()
        self._preload_hospital()
        self._preload_servicio()
        self._preload_oficina()
        self._load_vlan_choices(self.hospital_id.data)

    def _assign_initial_data(self) -> None:
        source = self._dispositivo or self._vlan
        if not source:
            return
        if self.hospital_id.data is None and getattr(source, "hospital_id", None):
            self.hospital_id.data = source.hospital_id
        if self.servicio_id.data is None and getattr(source, "servicio_id", None):
            self.servicio_id.data = getattr(source, "servicio_id") or 0
        if self.oficina_id.data is None and getattr(source, "oficina_id", None):
            self.oficina_id.data = getattr(source, "oficina_id") or 0
        if self._dispositivo and self.vlan_id.data is None:
            self.vlan_id.data = self._dispositivo.vlan_id
        elif self._vlan and self.vlan_id.data is None:
            self.vlan_id.data = self._vlan.id

    def _preload_hospital(self) -> None:
        preload_model_choice(self.hospital_id, Hospital, lambda hospital: hospital.nombre)

    def _preload_servicio(self) -> None:
        self.servicio_id.choices = [(0, "Sin servicio asignado")]
        value = self.servicio_id.data or 0
        if value:
            servicio = Servicio.query.get(value)
            if servicio:
                self.servicio_id.choices.append((servicio.id, servicio.nombre))

    def _preload_oficina(self) -> None:
        self.oficina_id.choices = [(0, "Sin oficina asignada")]
        value = self.oficina_id.data or 0
        if value:
            oficina = Oficina.query.get(value)
            if oficina:
                self.oficina_id.choices.append((oficina.id, oficina.nombre))

    def _load_vlan_choices(self, hospital_id: int | None) -> None:
        choices: list[tuple[int, str]] = []
        if hospital_id:
            vlans = (
                Vlan.query.filter_by(hospital_id=hospital_id)
                .order_by(Vlan.nombre.asc())
                .all()
            )
            choices = [(v.id, f"{v.nombre} ({v.identificador})") for v in vlans]
        self.vlan_id.choices = choices

    def validate_direccion_ip(self, field):  # type: ignore[override]
        query = VlanDispositivo.query.filter_by(direccion_ip=field.data.strip())
        if self._dispositivo:
            query = query.filter(VlanDispositivo.id != self._dispositivo.id)
        if query.first():
            raise ValidationError("La dirección IP ya está registrada en otro dispositivo.")

    def validate_vlan_id(self, field):  # type: ignore[override]
        vlan = Vlan.query.get(field.data)
        if not vlan:
            raise ValidationError("VLAN inválida.")
        if self.hospital_id.data and vlan.hospital_id != self.hospital_id.data:
            raise ValidationError("La VLAN seleccionada no pertenece al hospital elegido.")

    def validate(self, extra_validators=None):  # type: ignore[override]
        if not super().validate(extra_validators=extra_validators):
            return False
        hospital = Hospital.query.get(self.hospital_id.data)
        if not hospital:
            self.hospital_id.errors.append("Hospital inválido.")
            return False
        servicio_id = self.servicio_id.data or None
        oficina_id = self.oficina_id.data or None
        if servicio_id:
            servicio = Servicio.query.get(servicio_id)
            if not servicio or servicio.hospital_id != hospital.id:
                self.servicio_id.errors.append(
                    "El servicio no pertenece al hospital seleccionado."
                )
                return False
        if oficina_id:
            oficina = Oficina.query.get(oficina_id)
            if not oficina or oficina.hospital_id != hospital.id:
                self.oficina_id.errors.append(
                    "La oficina no pertenece al hospital seleccionado."
                )
                return False
            if servicio_id and oficina.servicio_id != servicio_id:
                self.oficina_id.errors.append(
                    "La oficina debe pertenecer al servicio elegido."
                )
                return False
        vlan = Vlan.query.get(self.vlan_id.data)
        if not vlan:
            self.vlan_id.errors.append("VLAN inválida.")
            return False
        if vlan.hospital_id != hospital.id:
            self.vlan_id.errors.append(
                "La VLAN seleccionada debe pertenecer al hospital elegido."
            )
            return False
        return True


__all__ = ["VlanForm", "VlanDispositivoForm"]
