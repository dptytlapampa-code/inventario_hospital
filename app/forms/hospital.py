from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired

class HospitalForm(FlaskForm):
    """Formulario de ejemplo para hospitales."""
    name = StringField("Nombre", validators=[DataRequired()])
    submit = SubmitField("Guardar")
