from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired

class DocscanForm(FlaskForm):
    """Formulario de ejemplo para documentos escaneados."""
    titulo = StringField("Título", validators=[DataRequired()])
    submit = SubmitField("Guardar")
