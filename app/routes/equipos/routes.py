from flask import Blueprint, render_template

equipos_bp = Blueprint("equipos", __name__, url_prefix="/equipos")

@equipos_bp.route("/")
def index():
    return render_template("equipos/index.html")
