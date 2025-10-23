"""Forms for assigning permissions to roles."""
from __future__ import annotations

from flask_wtf import FlaskForm
from wtforms import BooleanField, SelectField, SubmitField
from wtforms.validators import DataRequired

from app.models import Hospital, Modulo, Rol


class PermisoForm(FlaskForm):
    rol_id = SelectField("Rol", coerce=int, validators=[DataRequired()])
    modulo = SelectField(
        "Módulo",
        choices=[(m.value, m.name.title()) for m in Modulo],
        validators=[DataRequired()],
    )
    hospital_id = SelectField(
        "Hospital",
        coerce=int,
        validators=[DataRequired()],
        validate_choice=False,
        render_kw={"data-placeholder": "Seleccione un hospital"},
    )
    can_read = BooleanField("Puede leer", default=True)
    can_write = BooleanField("Puede editar")
    allow_export = BooleanField("Puede exportar")
    submit = SubmitField("Guardar")

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.rol_id.choices = [(r.id, r.nombre) for r in Rol.query.order_by(Rol.nombre)]
        self.hospital_id.choices = [(0, "Todos los hospitales")]
        hospital_id = self.hospital_id.data or (self.hospital_id.raw_data[0] if self.hospital_id.raw_data else None)
        try:
            hospital_id_int = int(hospital_id) if hospital_id not in (None, "", 0) else None
        except (TypeError, ValueError):
            hospital_id_int = None
        if hospital_id_int:
            hospital = Hospital.query.get(hospital_id_int)
            if hospital:
                self.hospital_id.choices.append((hospital.id, hospital.nombre))


__all__ = ["PermisoForm"]
