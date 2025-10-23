"""Views for the licenses workflow."""
from __future__ import annotations

from datetime import date

from flask import Blueprint, abort, flash, jsonify, redirect, render_template, request, url_for
from flask_login import current_user, login_required
from sqlalchemy.orm import joinedload

from app.forms.licencia import (
    GestionLicenciasFiltroForm,
    LicenciaAccionForm,
    LicenciaForm,
    LicenciaRechazoForm,
    MisLicenciasFiltroForm,
)
from app.models import EstadoLicencia, Hospital, Licencia, TipoLicencia, Usuario
from app.services.audit_service import log_action
from app.services.licencia_service import (
    aprobar_licencia,
    cancelar_licencia,
    crear_licencia,
    enviar_licencia,
    rechazar_licencia,
)
from app.utils.forms import preload_model_choice

licencias_bp = Blueprint("licencias", __name__, url_prefix="/licencias")


def _require_role(*roles: str) -> None:
    if not current_user.has_role(*roles):
        abort(403)


def _estado_badge(estado: EstadoLicencia) -> str:
    return {
        EstadoLicencia.SOLICITADA: "secondary",
        EstadoLicencia.APROBADA: "success",
        EstadoLicencia.RECHAZADA: "danger",
        EstadoLicencia.CANCELADA: "warning",
    }.get(estado, "secondary")


@licencias_bp.route("/mias")
@login_required
def mias() -> str:
    """List the licenses belonging to the current user."""

    _require_role("admin", "tecnico")

    form = MisLicenciasFiltroForm(request.args, meta={"csrf": False})
    form.estado.choices = [("", "Todos")] + [
        (estado.value, estado.name.title()) for estado in EstadoLicencia
    ]
    form.tipo.choices = [("", "Todos")] + [
        (tipo.value, tipo.name.title()) for tipo in TipoLicencia
    ]

    form.validate()

    query = Licencia.query.filter(Licencia.user_id == current_user.id)

    if form.estado.data:
        try:
            estado = EstadoLicencia(form.estado.data)
        except ValueError:
            flash("Estado de licencia desconocido", "warning")
        else:
            query = query.filter(Licencia.estado == estado)

    if form.tipo.data:
        try:
            tipo = TipoLicencia(form.tipo.data)
        except ValueError:
            flash("Tipo de licencia desconocido", "warning")
        else:
            query = query.filter(Licencia.tipo == tipo)

    if form.fecha_desde.data:
        query = query.filter(Licencia.fecha_fin >= form.fecha_desde.data)
    if form.fecha_hasta.data:
        query = query.filter(Licencia.fecha_inicio <= form.fecha_hasta.data)

    page = request.args.get("page", type=int, default=1)
    per_page = request.args.get("per_page", type=int, default=10)
    pagination = (
        query.order_by(Licencia.created_at.desc())
        .options(joinedload(Licencia.hospital), joinedload(Licencia.decisor))
        .paginate(page=page, per_page=per_page, error_out=False)
    )

    cancel_form = LicenciaAccionForm()

    return render_template(
        "licencias/mias.html",
        form=form,
        pagination=pagination,
        badge_for=_estado_badge,
        cancel_form=cancel_form,
        EstadoLicencia=EstadoLicencia,
    )


@licencias_bp.route("/nueva", methods=["GET", "POST"])
@login_required
def nueva() -> str:
    """Display the license request form for technicians and admins."""

    _require_role("admin", "tecnico")

    form = LicenciaForm()

    if request.method == "GET" and current_user.hospital_id:
        form.hospital_id.data = current_user.hospital_id
        preload_model_choice(form.hospital_id, Hospital, lambda hospital: hospital.nombre)

    if form.validate_on_submit():
        hospital_id = form.hospital_id.data or None
        licencia = crear_licencia(
            usuario=current_user,
            hospital_id=hospital_id,
            tipo=TipoLicencia(form.tipo.data),
            fecha_inicio=form.fecha_inicio.data,
            fecha_fin=form.fecha_fin.data,
            motivo=form.motivo.data.strip(),
        )

        overlapping = (
            Licencia.query.filter(Licencia.user_id == current_user.id)
            .filter(Licencia.id != licencia.id)
            .filter(Licencia.estado != EstadoLicencia.CANCELADA)
            .filter(Licencia.fecha_inicio <= form.fecha_fin.data)
            .filter(Licencia.fecha_fin >= form.fecha_inicio.data)
            .all()
        )
        if overlapping:
            flash(
                "La solicitud se superpone con otras licencias registradas.",
                "warning",
            )

        enviar_licencia(licencia)
        flash("Solicitud de licencia enviada", "success")
        log_action(
            usuario_id=current_user.id,
            accion="solicitar",
            modulo="licencias",
            tabla="licencias",
            registro_id=licencia.id,
        )
        return redirect(url_for("licencias.mias"))

    return render_template("licencias/nueva.html", form=form)


@licencias_bp.route("/gestion")
@login_required
def gestion() -> str:
    """Superadmin management dashboard for license requests."""

    _require_role("superadmin")

    form = GestionLicenciasFiltroForm(request.args, meta={"csrf": False})
    form.estado.choices = [("", "Todos")] + [
        (estado.value, estado.name.title()) for estado in EstadoLicencia
    ]

    usuarios = (
        Usuario.query.order_by(Usuario.nombre, Usuario.apellido)
        .with_entities(Usuario.id, Usuario.nombre, Usuario.apellido)
        .all()
    )
    form.usuario_id.choices = [("", "Todos los usuarios")] + [
        (
            str(usuario.id),
            f"{usuario.nombre} {usuario.apellido or ''}".strip(),
        )
        for usuario in usuarios
    ]

    preload_model_choice(form.hospital_id, Hospital, lambda hospital: hospital.nombre)

    form.validate()

    query = (
        Licencia.query.options(
            joinedload(Licencia.usuario),
            joinedload(Licencia.hospital),
            joinedload(Licencia.decisor),
        )
        .order_by(Licencia.created_at.desc())
    )

    if form.usuario_id.data:
        query = query.filter(Licencia.user_id == form.usuario_id.data)
    if form.hospital_id.data:
        query = query.filter(Licencia.hospital_id == form.hospital_id.data)
    if form.estado.data:
        try:
            estado = EstadoLicencia(form.estado.data)
        except ValueError:
            flash("Estado de licencia desconocido", "warning")
        else:
            query = query.filter(Licencia.estado == estado)
    if form.fecha_desde.data:
        query = query.filter(Licencia.fecha_fin >= form.fecha_desde.data)
    if form.fecha_hasta.data:
        query = query.filter(Licencia.fecha_inicio <= form.fecha_hasta.data)

    page = request.args.get("page", type=int, default=1)
    per_page = request.args.get("per_page", type=int, default=20)
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)

    aprobar_form = LicenciaAccionForm()
    cancelar_form = LicenciaAccionForm()
    rechazo_form = LicenciaRechazoForm()

    return render_template(
        "licencias/gestion.html",
        form=form,
        pagination=pagination,
        badge_for=_estado_badge,
        aprobar_form=aprobar_form,
        cancelar_form=cancelar_form,
        rechazo_form=rechazo_form,
        EstadoLicencia=EstadoLicencia,
    )


def _get_licencia_or_404(licencia_id: int) -> Licencia:
    licencia = Licencia.query.get_or_404(licencia_id)
    return licencia


@licencias_bp.post("/<int:licencia_id>/aprobar")
@login_required
def aprobar(licencia_id: int):
    _require_role("superadmin")
    form = LicenciaAccionForm()
    if not form.validate_on_submit():
        abort(400)

    licencia = _get_licencia_or_404(licencia_id)
    try:
        aprobar_licencia(licencia, current_user)
        flash("Licencia aprobada", "success")
        response = {"ok": True, "estado": licencia.estado.value}
    except ValueError as exc:  # pragma: no cover - defensive
        flash(str(exc), "warning")
        response = {"ok": False, "error": str(exc)}
    else:
        log_action(
            usuario_id=current_user.id,
            accion="aprobar",
            modulo="licencias",
            tabla="licencias",
            registro_id=licencia.id,
        )
    if request.accept_mimetypes.accept_json:
        status = 200 if response.get("ok") else 400
        response.update({"licencia_id": licencia.id})
        return jsonify(response), status
    return redirect(request.referrer or url_for("licencias.gestion"))


@licencias_bp.post("/<int:licencia_id>/rechazar")
@login_required
def rechazar(licencia_id: int):
    _require_role("superadmin")
    form = LicenciaRechazoForm()
    if not form.validate_on_submit():
        abort(400)

    licencia = _get_licencia_or_404(licencia_id)
    try:
        rechazar_licencia(licencia, current_user, form.motivo_rechazo.data)
        flash("Licencia rechazada", "info")
        response = {"ok": True, "estado": licencia.estado.value}
    except ValueError as exc:  # pragma: no cover - defensive
        flash(str(exc), "warning")
        response = {"ok": False, "error": str(exc)}
    else:
        log_action(
            usuario_id=current_user.id,
            accion="rechazar",
            modulo="licencias",
            tabla="licencias",
            registro_id=licencia.id,
        )
    if request.accept_mimetypes.accept_json:
        status = 200 if response.get("ok") else 400
        response.update({"licencia_id": licencia.id})
        return jsonify(response), status
    return redirect(request.referrer or url_for("licencias.gestion"))


@licencias_bp.post("/<int:licencia_id>/cancelar")
@login_required
def cancelar(licencia_id: int):
    licencia = _get_licencia_or_404(licencia_id)

    if current_user.has_role("superadmin"):
        actor = current_user
    elif current_user.id == licencia.user_id and licencia.estado == EstadoLicencia.SOLICITADA:
        actor = current_user
    else:
        abort(403)

    form = LicenciaAccionForm()
    if not form.validate_on_submit():
        abort(400)

    cancelar_licencia(licencia, actor)
    flash("Licencia cancelada", "warning")
    log_action(
        usuario_id=current_user.id,
        accion="cancelar",
        modulo="licencias",
        tabla="licencias",
        registro_id=licencia.id,
    )
    destino = "licencias.gestion" if current_user.has_role("superadmin") else "licencias.mias"
    return redirect(request.referrer or url_for(destino))
