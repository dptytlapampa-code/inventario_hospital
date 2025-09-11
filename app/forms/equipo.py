from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired

class EquipoForm(FlaskForm):
    """Formulario de ejemplo para equipos."""
    nombre = StringField("Nombre", validators=[DataRequired()])
    submit = SubmitField("Guardar")
