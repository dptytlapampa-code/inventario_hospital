from flask import Blueprint, render_template

permisos_bp = Blueprint("permisos", __name__, url_prefix="/permisos")

@permisos_bp.route("/")
def index():
    return render_template("permisos/index.html")
