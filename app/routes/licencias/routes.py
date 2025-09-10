from flask import Blueprint, render_template, redirect, url_for, flash, request

from app.forms.licencia import LicenciaForm, AprobarRechazarForm


licencias_bp = Blueprint("licencias", __name__, url_prefix="/licencias")


# Simple in-memory storage for demo purposes
SOLICITUDES = []


def _get_solicitud(licencia_id: int):
    for solicitud in SOLICITUDES:
        if solicitud["id"] == licencia_id:
            return solicitud
    return None


@licencias_bp.route("/solicitar", methods=["GET", "POST"])
def solicitar():
    form = LicenciaForm()
    if form.validate_on_submit():
        solicitud = {
            "id": len(SOLICITUDES) + 1,
            "empleado": form.empleado.data,
            "fecha_inicio": form.fecha_inicio.data,
            "fecha_fin": form.fecha_fin.data,
            "motivo": form.motivo.data,
            "estado": "pendiente",
        }
        SOLICITUDES.append(solicitud)
        flash("Solicitud registrada", "success")
        return redirect(url_for("licencias.listar"))
    return render_template("licencias/solicitar.html", form=form)


@licencias_bp.route("/listar")
def listar():
    return render_template("licencias/listar.html", solicitudes=SOLICITUDES)


@licencias_bp.route("/<int:licencia_id>/aprobar_rechazar", methods=["GET", "POST"])
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
def calendario():
    return render_template("licencias/calendario.html", solicitudes=SOLICITUDES)


@licencias_bp.route("/<int:licencia_id>/detalle")
def detalle(licencia_id: int):
    solicitud = _get_solicitud(licencia_id)
    if not solicitud:
        flash("Solicitud no encontrada", "error")
        return redirect(url_for("licencias.listar"))
    return render_template("licencias/detalle.html", solicitud=solicitud)
