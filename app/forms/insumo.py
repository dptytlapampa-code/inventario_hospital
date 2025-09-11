from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired

class InsumoForm(FlaskForm):
    """Formulario de ejemplo para insumos."""
    nombre = StringField("Nombre", validators=[DataRequired()])
    submit = SubmitField("Guardar")
