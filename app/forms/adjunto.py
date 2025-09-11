from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired

class AdjuntoForm(FlaskForm):
    """Formulario de ejemplo para adjuntos."""
    nombre = StringField("Nombre", validators=[DataRequired()])
    submit = SubmitField("Guardar")
