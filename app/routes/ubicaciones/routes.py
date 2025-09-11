from flask import Blueprint, render_template

ubicaciones_bp = Blueprint("ubicaciones", __name__, url_prefix="/ubicaciones")

@ubicaciones_bp.route("/")
def index():
    return render_template("ubicaciones/index.html")
