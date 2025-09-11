from flask import Blueprint, render_template

adjuntos_bp = Blueprint("adjuntos", __name__, url_prefix="/adjuntos")

@adjuntos_bp.route("/")
def index():
    return render_template("adjuntos/index.html")
