from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired

class ActaForm(FlaskForm):
    """Formulario de ejemplo para actas."""
    descripcion = StringField("Descripción", validators=[DataRequired()])
    submit = SubmitField("Guardar")
