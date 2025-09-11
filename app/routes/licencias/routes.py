from flask import Blueprint, render_template, redirect, url_for, flash
from flask_login import login_required

from app.forms.licencia import LicenciaForm, AprobarRechazarForm
from app.models import db
from app.models.licencia import Licencia


licencias_bp = Blueprint("licencias", __name__, url_prefix="/licencias")


def _get_solicitud(licencia_id: int) -> Licencia | None:
    """Return a licence by id or ``None`` if it does not exist."""
    return Licencia.query.get(licencia_id)


@licencias_bp.route("/solicitar", methods=["GET", "POST"])
@login_required
def solicitar():
    form = LicenciaForm()
    if form.validate_on_submit():
        licencia = Licencia(
            empleado=form.empleado.data,
            fecha_inicio=form.fecha_inicio.data,
            fecha_fin=form.fecha_fin.data,
            motivo=form.motivo.data,
        )
        db.session.add(licencia)
        db.session.commit()
        flash("Solicitud registrada", "success")
        return redirect(url_for("licencias.listar"))
    return render_template("licencias/solicitar.html", form=form)


@licencias_bp.route("/listar")
@login_required
def listar():
    solicitudes = Licencia.query.order_by(Licencia.id).all()
    return render_template("licencias/listar.html", solicitudes=solicitudes)


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
        solicitud.estado = "aprobada" if accion == "aprobar" else "rechazada"
        db.session.commit()
        flash(f"Solicitud {accion}da", "success")
        return redirect(url_for("licencias.detalle", licencia_id=licencia_id))
    return render_template("licencias/aprobar_rechazar.html", form=form, solicitud=solicitud)


@licencias_bp.route("/calendario")
@login_required
def calendario():
    solicitudes = Licencia.query.order_by(Licencia.fecha_inicio).all()
    return render_template("licencias/calendario.html", solicitudes=solicitudes)


@licencias_bp.route("/<int:licencia_id>/detalle")
@login_required
def detalle(licencia_id: int):
    solicitud = _get_solicitud(licencia_id)
    if not solicitud:
        flash("Solicitud no encontrada", "error")
        return redirect(url_for("licencias.listar"))
    return render_template("licencias/detalle.html", solicitud=solicitud)
