"""Vistas para gestionar permisos de acceso."""

from __future__ import annotations

from typing import Dict, List, Optional

from app.forms.permisos import PermisoForm
from app.routes._compat import Blueprint, flash, login_required, redirect, render_template, url_for

PERMISOS: List[Dict[str, object]] = [
    {
        "id": 1,
        "rol_id": 1,
        "rol": "Administrador",
        "modulo": "inventario",
        "hospital_id": 1,
        "hospital": "Hospital Central",
        "can_read": True,
        "can_write": True,
    },
    {
        "id": 2,
        "rol_id": 2,
        "rol": "Operador",
        "modulo": "insumos",
        "hospital_id": 2,
        "hospital": "Hospital Norte",
        "can_read": True,
        "can_write": False,
    },
]


def _get_permiso(permiso_id: int) -> Optional[Dict[str, object]]:
    return next((permiso for permiso in PERMISOS if permiso["id"] == permiso_id), None)


permisos_bp = Blueprint("permisos", __name__, url_prefix="/permisos")


@permisos_bp.route("/")
@login_required
def listar() -> str:
    return render_template("permisos/listar.html", permisos=PERMISOS)


@permisos_bp.route("/crear", methods=["GET", "POST"])
@login_required
def crear() -> str:
    form = PermisoForm()
    if form.validate_on_submit():  # pragma: no cover - requiere contexto Flask real
        new_id = max((int(item["id"]) for item in PERMISOS), default=0) + 1
        PERMISOS.append(
            {
                "id": new_id,
                "rol_id": form.rol_id.data,
                "rol": dict(form.rol_id.choices).get(form.rol_id.data, ""),
                "modulo": form.modulo.data,
                "hospital_id": form.hospital_id.data,
                "hospital": dict(form.hospital_id.choices).get(form.hospital_id.data, "Todos"),
                "can_read": form.can_read.data,
                "can_write": form.can_write.data,
            }
        )
        flash("Permiso creado", "success")
        return redirect(url_for("permisos.listar"))
    return render_template("permisos/formulario.html", form=form, titulo="Nuevo permiso")


@permisos_bp.route("/<int:permiso_id>/editar", methods=["GET", "POST"])
@login_required
def editar(permiso_id: int) -> str:
    permiso = _get_permiso(permiso_id)
    form = PermisoForm(data=permiso)
    if form.validate_on_submit():  # pragma: no cover - requiere contexto Flask real
        if permiso is not None:
            permiso.update(
                {
                    "rol_id": form.rol_id.data,
                    "rol": dict(form.rol_id.choices).get(form.rol_id.data, ""),
                    "modulo": form.modulo.data,
                    "hospital_id": form.hospital_id.data,
                    "hospital": dict(form.hospital_id.choices).get(form.hospital_id.data, "Todos"),
                    "can_read": form.can_read.data,
                    "can_write": form.can_write.data,
                }
            )
            flash("Permiso actualizado", "success")
        return redirect(url_for("permisos.listar"))
    return render_template(
        "permisos/formulario.html",
        form=form,
        titulo="Editar permiso",
        permiso=permiso,
    )
