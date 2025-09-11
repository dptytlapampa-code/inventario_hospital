from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired

class AuthForm(FlaskForm):
    """Formulario de ejemplo para autenticación."""
    name = StringField("Nombre", validators=[DataRequired()])
    submit = SubmitField("Enviar")
