from flask import Blueprint, flash, redirect, render_template, url_for
from flask_login import login_required

from app.forms.licencia import AprobarRechazarForm, LicenciaForm
from licencias import calcular_dias_habiles


licencias_bp = Blueprint("licencias", __name__, url_prefix="/licencias")


# Simple in-memory storage for demo purposes
SOLICITUDES = []


def _get_solicitud(licencia_id: int):
    for solicitud in SOLICITUDES:
        if solicitud["id"] == licencia_id:
            return solicitud
    return None


@licencias_bp.route("/solicitar", methods=["GET", "POST"])
@login_required
def solicitar():
    form = LicenciaForm()
    if form.validate_on_submit():
        solicitud = {
            "id": len(SOLICITUDES) + 1,
            "empleado": form.empleado.data,
            "fecha_inicio": form.fecha_inicio.data,
            "fecha_fin": form.fecha_fin.data,
            "motivo": form.motivo.data,
            "requiere_reemplazo": form.requiere_reemplazo.data,
            "reemplazo_id": form.reemplazo_id.data,
            "dias_habiles": calcular_dias_habiles(
                form.fecha_inicio.data, form.fecha_fin.data
            ),
            "estado": "pendiente",
        }
        SOLICITUDES.append(solicitud)
        flash("Solicitud registrada", "success")
        return redirect(url_for("licencias.listar"))
    return render_template("licencias/solicitar.html", form=form)


@licencias_bp.route("/listar")
@login_required
def listar():
    return render_template("licencias/listar.html", solicitudes=SOLICITUDES)


@licencias_bp.route("/<int:licencia_id>/aprobar_rechazar", methods=["GET", "POST"])
@login_required
def aprobar_rechazar(licencia_id: int):
    solicitud = _get_solicitud(licencia_id)
    if not solicitud:
        flash("Solicitud no encontrada", "error")
        return redirect(url_for("licencias.listar"))

    form = AprobarRechazarForm()
    if form.validate_on_submit():
        accion = form.accion.data
        solicitud["estado"] = "aprobada" if accion == "aprobar" else "rechazada"
        flash(f"Solicitud {accion}da", "success")
        return redirect(url_for("licencias.detalle", licencia_id=licencia_id))
    return render_template("licencias/aprobar_rechazar.html", form=form, solicitud=solicitud)


@licencias_bp.route("/calendario")
@login_required
def calendario():
    return render_template("licencias/calendario.html", solicitudes=SOLICITUDES)


@licencias_bp.route("/<int:licencia_id>/detalle")
@login_required
def detalle(licencia_id: int):
    solicitud = _get_solicitud(licencia_id)
    if not solicitud:
        flash("Solicitud no encontrada", "error")
        return redirect(url_for("licencias.listar"))
    return render_template("licencias/detalle.html", solicitud=solicitud)
