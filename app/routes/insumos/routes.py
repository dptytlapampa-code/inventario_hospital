"""Vistas relacionadas con insumos."""

from __future__ import annotations

from typing import Dict, List, Optional

from app.forms.insumo import InsumoForm
from app.routes._compat import Blueprint, flash, login_required, redirect, render_template, url_for

INSUMOS: List[Dict[str, object]] = [
    {"id": 1, "nombre": "Cartucho Tóner", "stock": 15, "numero_serie": "TN-111"},
    {"id": 2, "nombre": "Cables HDMI", "stock": 40, "numero_serie": None},
]


def _get_insumo(insumo_id: int) -> Optional[Dict[str, object]]:
    return next((insumo for insumo in INSUMOS if insumo["id"] == insumo_id), None)


insumos_bp = Blueprint("insumos", __name__, url_prefix="/insumos")


@insumos_bp.route("/")
@login_required
def listar() -> str:
    """Inventario de insumos con stock."""

    return render_template("insumos/listar.html", insumos=INSUMOS)


@insumos_bp.route("/crear", methods=["GET", "POST"])
@login_required
def crear() -> str:
    form = InsumoForm()
    if form.validate_on_submit():  # pragma: no cover - requiere contexto Flask real
        new_id = max((int(item["id"]) for item in INSUMOS), default=0) + 1
        INSUMOS.append(
            {
                "id": new_id,
                "nombre": form.nombre.data,
                "stock": form.stock.data,
                "numero_serie": form.numero_serie.data,
                "equipos": form.equipos.data,
            }
        )
        flash("Insumo agregado", "success")
        return redirect(url_for("insumos.listar"))
    return render_template("insumos/formulario.html", form=form, titulo="Nuevo insumo")


@insumos_bp.route("/<int:insumo_id>/editar", methods=["GET", "POST"])
@login_required
def editar(insumo_id: int) -> str:
    insumo = _get_insumo(insumo_id)
    form = InsumoForm(data=insumo)
    if form.validate_on_submit():  # pragma: no cover - requiere contexto Flask real
        if insumo is not None:
            insumo.update(
                {
                    "nombre": form.nombre.data,
                    "stock": form.stock.data,
                    "numero_serie": form.numero_serie.data,
                    "equipos": form.equipos.data,
                }
            )
            flash("Insumo actualizado", "success")
        return redirect(url_for("insumos.listar"))
    return render_template(
        "insumos/formulario.html",
        form=form,
        titulo="Editar insumo",
        insumo=insumo,
    )


@insumos_bp.route("/<int:insumo_id>")
@login_required
def detalle(insumo_id: int) -> str:
    insumo = _get_insumo(insumo_id)
    return render_template("insumos/detalle.html", insumo=insumo)
