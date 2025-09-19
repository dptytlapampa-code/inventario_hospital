"""Vistas para administrar adjuntos de equipos."""

from __future__ import annotations

from typing import Dict, List, Optional

from app.forms.adjunto import AdjuntoForm
from app.routes._compat import Blueprint, flash, login_required, redirect, render_template, url_for

ADJUNTOS: List[Dict[str, object]] = [
    {
        "id": 1,
        "equipo_id": 1,
        "filename": "manual_impresora.pdf",
        "tipo": "manual",
    },
    {
        "id": 2,
        "equipo_id": 2,
        "filename": "garantia_switch.pdf",
        "tipo": "garantia",
    },
]


def _get_adjunto(adjunto_id: int) -> Optional[Dict[str, object]]:
    return next((adjunto for adjunto in ADJUNTOS if adjunto["id"] == adjunto_id), None)


adjuntos_bp = Blueprint("adjuntos", __name__, url_prefix="/adjuntos")


@adjuntos_bp.route("/")
@login_required
def listar() -> str:
    return render_template("adjuntos/listar.html", adjuntos=ADJUNTOS)


@adjuntos_bp.route("/subir", methods=["GET", "POST"])
@login_required
def subir() -> str:
    form = AdjuntoForm()
    if form.validate_on_submit():  # pragma: no cover - requiere contexto Flask real
        new_id = max((int(item["id"]) for item in ADJUNTOS), default=0) + 1
        ADJUNTOS.append(
            {
                "id": new_id,
                "equipo_id": form.equipo_id.data,
                "filename": form.filename.data,
                "tipo": form.tipo.data,
            }
        )
        flash("Adjunto cargado", "success")
        return redirect(url_for("adjuntos.listar"))
    return render_template("adjuntos/formulario.html", form=form, titulo="Nuevo adjunto")


@adjuntos_bp.route("/<int:adjunto_id>")
@login_required
def detalle(adjunto_id: int) -> str:
    adjunto = _get_adjunto(adjunto_id)
    return render_template("adjuntos/detalle.html", adjunto=adjunto)
