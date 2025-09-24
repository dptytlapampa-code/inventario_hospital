"""Forms for user management."""
from __future__ import annotations

from flask_wtf import FlaskForm
from wtforms import BooleanField, PasswordField, SelectField, StringField, SubmitField, ValidationError
from wtforms.validators import DataRequired, Email, EqualTo, Length, Optional

from app.models import Rol, Usuario


class UsuarioForm(FlaskForm):
    """Form to create or edit usuarios."""

    nombre = StringField("Nombre", validators=[DataRequired(), Length(max=120)])
    apellido = StringField("Apellido", validators=[Optional(), Length(max=120)])
    email = StringField("Email", validators=[DataRequired(), Email(), Length(max=255)])
    username = StringField("Usuario", validators=[DataRequired(), Length(max=80)])
    rol_id = SelectField("Rol", coerce=int, validators=[DataRequired()])
    password = PasswordField("Contraseña", validators=[Optional(), Length(min=8, max=128)])
    confirm_password = PasswordField(
        "Confirmar contraseña",
        validators=[Optional(), EqualTo("password", message="Las contraseñas deben coincidir.")],
    )
    activo = BooleanField("Activo", default=True)
    submit = SubmitField("Guardar")

    def __init__(self, usuario: Usuario | None = None, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._usuario = usuario
        self.rol_id.choices = [
            (rol.id, rol.nombre.title()) for rol in Rol.query.order_by(Rol.nombre.asc())
        ]
        if usuario:
            self.activo.data = usuario.activo

    def validate_email(self, field):  # type: ignore[override]
        query = Usuario.query.filter(Usuario.email == field.data)
        if self._usuario:
            query = query.filter(Usuario.id != self._usuario.id)
        if query.first():
            raise ValidationError("Ya existe un usuario con este email")

    def validate_username(self, field):  # type: ignore[override]
        query = Usuario.query.filter(Usuario.username == field.data)
        if self._usuario:
            query = query.filter(Usuario.id != self._usuario.id)
        if query.first():
            raise ValidationError("El nombre de usuario ya está en uso")

    def validate(self, extra_validators=None):  # type: ignore[override]
        if not super().validate(extra_validators=extra_validators):
            return False
        if not self._usuario and not self.password.data:
            self.password.errors.append("Debe asignar una contraseña")
            return False
        return True


class PerfilForm(FlaskForm):
    """Allow an authenticated user to update their own profile."""

    nombre = StringField("Nombre", validators=[DataRequired(), Length(max=120)])
    apellido = StringField("Apellido", validators=[Optional(), Length(max=120)])
    email = StringField("Email", validators=[DataRequired(), Email(), Length(max=255)])
    telefono = StringField("Teléfono", validators=[Optional(), Length(max=50)])
    password = PasswordField("Nueva contraseña", validators=[Optional(), Length(min=8, max=128)])
    confirm_password = PasswordField(
        "Confirmar contraseña",
        validators=[Optional(), EqualTo("password", message="Las contraseñas deben coincidir.")],
    )
    submit = SubmitField("Guardar cambios")

    def __init__(self, usuario: Usuario, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._usuario = usuario

    def validate_email(self, field):  # type: ignore[override]
        query = Usuario.query.filter(Usuario.email == field.data)
        query = query.filter(Usuario.id != self._usuario.id)
        if query.first():
            raise ValidationError("Ya existe un usuario con este email")


__all__ = ["UsuarioForm", "PerfilForm"]
