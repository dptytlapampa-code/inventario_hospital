"""Blueprint para administrar ubicaciones y hospitales."""

from __future__ import annotations

from typing import Dict, List, Optional

from app.forms.hospital import HospitalForm
from app.routes._compat import Blueprint, flash, login_required, redirect, render_template, url_for

HOSPITALES: List[Dict[str, object]] = [
    {"id": 1, "nombre": "Hospital Central"},
    {"id": 2, "nombre": "Hospital Norte"},
    {"id": 3, "nombre": "Hospital Sur"},
]


def _get_hospital(hospital_id: int) -> Optional[Dict[str, object]]:
    return next((hospital for hospital in HOSPITALES if hospital["id"] == hospital_id), None)


ubicaciones_bp = Blueprint("ubicaciones", __name__, url_prefix="/ubicaciones")


@ubicaciones_bp.route("/")
@login_required
def listar() -> str:
    return render_template("ubicaciones/listar.html", hospitales=HOSPITALES)


@ubicaciones_bp.route("/crear", methods=["GET", "POST"])
@login_required
def crear() -> str:
    form = HospitalForm()
    if form.validate_on_submit():  # pragma: no cover - requiere contexto Flask real
        new_id = max((int(item["id"]) for item in HOSPITALES), default=0) + 1
        HOSPITALES.append({"id": new_id, "nombre": form.nombre.data})
        flash("Hospital agregado", "success")
        return redirect(url_for("ubicaciones.listar"))
    return render_template("ubicaciones/formulario.html", form=form, titulo="Nueva ubicación")


@ubicaciones_bp.route("/<int:hospital_id>/editar", methods=["GET", "POST"])
@login_required
def editar(hospital_id: int) -> str:
    hospital = _get_hospital(hospital_id)
    form = HospitalForm(data=hospital)
    if form.validate_on_submit():  # pragma: no cover - requiere contexto Flask real
        if hospital is not None:
            hospital.update({"nombre": form.nombre.data})
            flash("Hospital actualizado", "success")
        return redirect(url_for("ubicaciones.listar"))
    return render_template(
        "ubicaciones/formulario.html",
        form=form,
        titulo="Editar ubicación",
        hospital=hospital,
    )
