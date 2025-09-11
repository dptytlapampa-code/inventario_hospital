from flask import Blueprint, render_template

actas_bp = Blueprint("actas", __name__, url_prefix="/actas")

@actas_bp.route("/")
def index():
    return render_template("actas/index.html")
