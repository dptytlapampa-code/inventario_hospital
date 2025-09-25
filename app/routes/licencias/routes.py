"""License management views."""
from __future__ import annotations

from calendar import monthrange
from datetime import date

from flask import Blueprint, current_app, flash, g, redirect, render_template, request, url_for
from flask_login import current_user, login_required
from sqlalchemy import or_

from app.forms.licencia import AprobarRechazarForm, CalendarioFiltroForm, LicenciaForm
from app.models import EstadoLicencia, Licencia, Modulo, TipoLicencia, Usuario
from app.security import permissions_required, require_hospital_access
from app.services.audit_service import log_action
from app.services.licencia_service import (
    aprobar_licencia,
    cancelar_licencia,
    crear_licencia,
    enviar_licencia,
    rechazar_licencia,
)


licencias_bp = Blueprint("licencias", __name__, url_prefix="/licencias")


@licencias_bp.route("/solicitar", methods=["GET", "POST"])
@login_required
@permissions_required("licencias:write")
@require_hospital_access(Modulo.LICENCIAS)
def solicitar():
    if current_user.role == "superadmin":
        flash("El superadministrador no puede solicitar licencias.", "warning")
        return render_template("errors/403.html"), 403

    form = LicenciaForm()
    if form.validate_on_submit():
        licencia = crear_licencia(
            usuario=current_user,
            hospital_id=current_user.hospital_id,
            tipo=TipoLicencia(form.tipo.data),
            fecha_inicio=form.fecha_inicio.data,
            fecha_fin=form.fecha_fin.data,
            motivo=form.motivo.data,
        )
        enviar_licencia(licencia)
        flash("Solicitud enviada", "success")
        log_action(usuario_id=current_user.id, accion="solicitar", modulo="licencias", tabla="licencias", registro_id=licencia.id)
        return redirect(url_for("licencias.listar"))
    return render_template("licencias/solicitar.html", form=form)


@licencias_bp.route("/listar")
@login_required
@permissions_required("licencias:read")
@require_hospital_access(Modulo.LICENCIAS)
def listar():
    estado = request.args.get("estado")
    buscar = request.args.get("q", "")
    page = request.args.get("page", type=int, default=1)
    per_page = current_app.config.get("DEFAULT_PAGE_SIZE", 20)

    query = Licencia.query.order_by(Licencia.created_at.desc())
    allowed = getattr(g, "allowed_hospitals", set())
    if allowed:
        query = query.filter(Licencia.hospital_id.in_(allowed))
    elif current_user.role != "superadmin":
        query = query.filter(Licencia.user_id == current_user.id)

    if estado:
        try:
            estado_enum = EstadoLicencia(estado)
        except ValueError:
            flash("Estado de licencia desconocido", "warning")
        else:
            query = query.filter(Licencia.estado == estado_enum)

    if buscar:
        like = f"%{buscar}%"
        query = query.join(Licencia.usuario).filter(
            or_(Usuario.nombre.ilike(like), Usuario.email.ilike(like))
        )

    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    return render_template(
        "licencias/listar.html",
        licencias=pagination.items,
        pagination=pagination,
        estado=estado,
        buscar=buscar,
        estados=EstadoLicencia,
    )


@licencias_bp.route("/<int:licencia_id>/detalle")
@login_required
@permissions_required("licencias:read")
@require_hospital_access(Modulo.LICENCIAS)
def detalle(licencia_id: int):
    licencia = Licencia.query.get_or_404(licencia_id)
    return render_template("licencias/detalle.html", licencia=licencia)


@licencias_bp.route("/<int:licencia_id>/aprobar", methods=["GET", "POST"])
@login_required
@permissions_required("licencias:write")
@require_hospital_access(Modulo.LICENCIAS)
def aprobar_rechazar(licencia_id: int):
    licencia = Licencia.query.get_or_404(licencia_id)
    form = AprobarRechazarForm()
    if licencia.estado != EstadoLicencia.SOLICITADA:
        flash("Solo se pueden gestionar licencias solicitadas.", "warning")
        return redirect(url_for("licencias.detalle", licencia_id=licencia.id))
    if form.validate_on_submit():
        try:
            if form.accion.data == "aprobar":
                aprobar_licencia(licencia, current_user)
                flash("Licencia aprobada", "success")
            else:
                rechazar_licencia(licencia, current_user)
                flash("Licencia rechazada", "info")
        except ValueError as exc:
            current_app.logger.warning(
                "No se pudo %s la licencia %s: %s", form.accion.data, licencia.id, exc
            )
            flash(str(exc), "warning")
        else:
            log_action(
                usuario_id=current_user.id,
                accion=form.accion.data,
                modulo="licencias",
                tabla="licencias",
                registro_id=licencia.id,
            )
            return redirect(url_for("licencias.detalle", licencia_id=licencia.id))
    return render_template("licencias/aprobar_rechazar.html", form=form, licencia=licencia)


@licencias_bp.route("/<int:licencia_id>/cancelar", methods=["POST"])
@login_required
@permissions_required("licencias:write")
@require_hospital_access(Modulo.LICENCIAS)
def cancelar(licencia_id: int):
    licencia = Licencia.query.get_or_404(licencia_id)
    cancelar_licencia(licencia, current_user)
    flash("Licencia cancelada", "warning")
    log_action(usuario_id=current_user.id, accion="cancelar", modulo="licencias", tabla="licencias", registro_id=licencia.id)
    return redirect(url_for("licencias.listar"))


@licencias_bp.route("/calendario", methods=["GET", "POST"])
@login_required
@permissions_required("licencias:read")
@require_hospital_access(Modulo.LICENCIAS)
def calendario():
    form = CalendarioFiltroForm(request.args)
    query = Licencia.query.filter(Licencia.estado == EstadoLicencia.APROBADA)
    allowed = getattr(g, "allowed_hospitals", set())
    if allowed:
        query = query.filter(Licencia.hospital_id.in_(allowed))
    elif current_user.role != "superadmin":
        query = query.filter(Licencia.user_id == current_user.id)

    if form.validate() and form.mes.data:
        inicio_mes = form.mes.data.replace(day=1)
        _, last_day = monthrange(inicio_mes.year, inicio_mes.month)
        fin_mes = inicio_mes.replace(day=last_day)
        query = query.filter(
            Licencia.fecha_inicio <= fin_mes, Licencia.fecha_fin >= inicio_mes
        )

    licencias = query.order_by(Licencia.fecha_inicio).all()
    eventos = [
        {
            "title": licencia.usuario.nombre,
            "start": licencia.fecha_inicio.isoformat(),
            "end": licencia.fecha_fin.isoformat(),
            "estado": licencia.estado.value,
        }
        for licencia in licencias
    ]
    return render_template("licencias/calendario.html", form=form, eventos=eventos)
