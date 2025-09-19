"""Vistas de inventario de equipos."""

from __future__ import annotations

from typing import Dict, List, Optional

from app.forms.equipo import EquipoForm
from app.routes._compat import Blueprint, flash, login_required, redirect, render_template, url_for

EQUIPOS: List[Dict[str, object]] = [
    {
        "id": 1,
        "descripcion": "Impresora HP LaserJet",
        "tipo": "impresora",
        "estado": "operativo",
        "hospital_id": 1,
        "numero_serie": "HP123456",
    },
    {
        "id": 2,
        "descripcion": "Switch Cisco 24p",
        "tipo": "switch",
        "estado": "servicio_tecnico",
        "hospital_id": 2,
        "numero_serie": "CISCO9876",
    },
]


def _get_equipo(equipo_id: int) -> Optional[Dict[str, object]]:
    return next((equipo for equipo in EQUIPOS if equipo["id"] == equipo_id), None)


equipos_bp = Blueprint("equipos", __name__, url_prefix="/equipos")


@equipos_bp.route("/")
@login_required
def listar() -> str:
    """Listado sencillo de equipos registrados."""

    return render_template("equipos/listar.html", equipos=EQUIPOS)


@equipos_bp.route("/crear", methods=["GET", "POST"])
@login_required
def crear() -> str:
    """Formulario de alta de equipos."""

    form = EquipoForm()
    if form.validate_on_submit():  # pragma: no cover - requiere contexto Flask real
        new_id = max((int(equip["id"]) for equip in EQUIPOS), default=0) + 1
        EQUIPOS.append(
            {
                "id": new_id,
                "descripcion": form.descripcion.data,
                "tipo": form.tipo.data,
                "estado": form.estado.data,
                "hospital_id": form.hospital_id.data,
                "numero_serie": form.numero_serie.data,
            }
        )
        flash("Equipo creado correctamente", "success")
        return redirect(url_for("equipos.listar"))
    return render_template("equipos/formulario.html", form=form, titulo="Nuevo equipo")


@equipos_bp.route("/<int:equipo_id>/editar", methods=["GET", "POST"])
@login_required
def editar(equipo_id: int) -> str:
    """Edición básica de un equipo."""

    equipo = _get_equipo(equipo_id)
    form = EquipoForm(data=equipo)
    if form.validate_on_submit():  # pragma: no cover - requiere contexto Flask real
        if equipo is not None:
            equipo.update(
                {
                    "descripcion": form.descripcion.data,
                    "tipo": form.tipo.data,
                    "estado": form.estado.data,
                    "hospital_id": form.hospital_id.data,
                    "numero_serie": form.numero_serie.data,
                }
            )
            flash("Equipo actualizado", "success")
        return redirect(url_for("equipos.listar"))
    return render_template(
        "equipos/formulario.html",
        form=form,
        titulo="Editar equipo",
        equipo=equipo,
    )


@equipos_bp.route("/<int:equipo_id>")
@login_required
def detalle(equipo_id: int) -> str:
    """Vista de detalle simplificada."""

    equipo = _get_equipo(equipo_id)
    return render_template("equipos/detalle.html", equipo=equipo)
