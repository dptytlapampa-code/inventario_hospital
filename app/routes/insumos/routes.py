from flask import Blueprint, render_template

insumos_bp = Blueprint("insumos", __name__, url_prefix="/insumos")

@insumos_bp.route("/")
def index():
    return render_template("insumos/index.html")
