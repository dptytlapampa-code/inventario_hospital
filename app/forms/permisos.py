from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired

class PermisosForm(FlaskForm):
    """Formulario de ejemplo para permisos."""
    nombre = StringField("Nombre", validators=[DataRequired()])
    submit = SubmitField("Guardar")
