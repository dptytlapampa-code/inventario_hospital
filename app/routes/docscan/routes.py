"""Vistas de documentos escaneados."""

from __future__ import annotations

from typing import Dict, List, Optional

from app.forms.docscan import DocscanForm
from app.routes._compat import Blueprint, flash, login_required, redirect, render_template, url_for

DOCSCAN_ITEMS: List[Dict[str, object]] = [
    {
        "id": 1,
        "titulo": "Acta de entrega",
        "equipo_id": 1,
        "tipo": "acta",
    },
    {
        "id": 2,
        "titulo": "Contrato de mantenimiento",
        "equipo_id": 2,
        "tipo": "contrato",
    },
]


def _get_docscan(doc_id: int) -> Optional[Dict[str, object]]:
    return next((item for item in DOCSCAN_ITEMS if item["id"] == doc_id), None)


docscan_bp = Blueprint("docscan", __name__, url_prefix="/docscan")


@docscan_bp.route("/")
@login_required
def listar() -> str:
    return render_template("docscan/listar.html", documentos=DOCSCAN_ITEMS)


@docscan_bp.route("/subir", methods=["GET", "POST"])
@login_required
def subir() -> str:
    form = DocscanForm()
    if form.validate_on_submit():  # pragma: no cover - requiere contexto Flask real
        new_id = max((int(item["id"]) for item in DOCSCAN_ITEMS), default=0) + 1
        DOCSCAN_ITEMS.append(
            {
                "id": new_id,
                "titulo": form.titulo.data,
                "equipo_id": form.equipo_id.data,
                "tipo": form.tipo.data,
            }
        )
        flash("Documento digitalizado cargado", "success")
        return redirect(url_for("docscan.listar"))
    return render_template("docscan/formulario.html", form=form, titulo="Nuevo documento")


@docscan_bp.route("/<int:doc_id>")
@login_required
def detalle(doc_id: int) -> str:
    documento = _get_docscan(doc_id)
    return render_template("docscan/detalle.html", documento=documento)
