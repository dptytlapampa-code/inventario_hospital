from flask import Blueprint, render_template

docscan_bp = Blueprint("docscan", __name__, url_prefix="/docscan")

@docscan_bp.route("/")
def index():
    return render_template("docscan/index.html")
