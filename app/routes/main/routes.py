"""Vistas base y panel principal del sistema."""

from __future__ import annotations

from datetime import date

from app.routes._compat import Blueprint, render_template

main_bp = Blueprint("main", __name__)


@main_bp.route("/")
def index() -> str:
    """Pantalla de bienvenida con métricas rápidas."""

    stats = {
        "equipos": 128,
        "insumos": 342,
        "hospitales": 6,
        "permisos": 24,
    }
    notices = [
        {"titulo": "Inventario actualizado", "fecha": date.today()},
        {"titulo": "Nueva política de adjuntos", "fecha": date.today()},
    ]
    return render_template("main/index.html", stats=stats, notices=notices)


@main_bp.route("/dashboard")
def dashboard() -> str:
    """Vista de tablero con datos de Chart.js."""

    chart_data = {
        "labels": ["Equipos", "Insumos", "Adjuntos", "Docscan"],
        "values": [128, 342, 58, 17],
    }
    return render_template("main/dashboard.html", chart_data=chart_data)
