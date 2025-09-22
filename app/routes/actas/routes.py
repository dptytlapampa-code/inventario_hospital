"""Blueprint for acta creation and download."""
from __future__ import annotations

from pathlib import Path

from flask import (
    Blueprint,
    current_app,
    flash,
    g,
    redirect,
    render_template,
    request,
    send_file,
    url_for,
)
from flask_login import current_user, login_required

from sqlalchemy import or_

from app.extensions import db
from app.forms.acta import ActaForm
from app.models import Acta, ActaItem, Modulo
from app.security import permissions_required, require_hospital_access
from app.services.audit_service import log_action
from app.services.pdf_service import build_acta_pdf

actas_bp = Blueprint("actas", __name__, url_prefix="/actas")


def _acta_output_dir() -> Path:
    uploads = Path(current_app.config.get("UPLOAD_FOLDER", "uploads")) / "actas"
    uploads.mkdir(parents=True, exist_ok=True)
    return uploads


@actas_bp.route("/")
@login_required
@permissions_required("actas:read")
@require_hospital_access(Modulo.ACTAS)
def listar():
    page = request.args.get("page", type=int, default=1)
    per_page = current_app.config.get("DEFAULT_PAGE_SIZE", 20)
    buscar = request.args.get("q", "")

    query = Acta.query.order_by(Acta.fecha.desc())
    allowed = getattr(g, "allowed_hospitals", set())
    if allowed:
        query = query.filter(Acta.hospital_id.in_(allowed))
    elif not current_user.has_role("Superadmin"):
        query = query.filter(Acta.usuario_id == current_user.id)
    if buscar:
        like = f"%{buscar}%"
        query = query.filter(
            or_(Acta.observaciones.ilike(like), Acta.numero.ilike(like))
        )

    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    return render_template(
        "actas/listar.html",
        actas=pagination.items,
        pagination=pagination,
        buscar=buscar,
    )


@actas_bp.route("/crear", methods=["GET", "POST"])
@login_required
@permissions_required("actas:write")
@require_hospital_access(Modulo.ACTAS)
def crear():
    form = ActaForm()
    if form.validate_on_submit():
        acta = Acta(
            tipo=form.tipo.data,
            hospital_id=form.hospital_id.data,
            servicio_id=form.servicio_id.data or None,
            oficina_id=form.oficina_id.data or None,
            usuario=current_user,
            observaciones=form.observaciones.data or None,
        )
        for equipo_id in form.equipos.data:
            item = ActaItem(equipo_id=equipo_id)
            acta.items.append(item)
        db.session.add(acta)
        db.session.flush()
        pdf_path = build_acta_pdf(acta, _acta_output_dir())
        acta.pdf_path = pdf_path.as_posix()
        for item in acta.items:
            if item.equipo:
                item.equipo.registrar_evento(
                    current_user,
                    f"Acta {acta.tipo.value.title()}",
                    f"Acta #{acta.id}",
                )
        db.session.commit()
        log_action(usuario_id=current_user.id, accion="crear", modulo="actas", tabla="actas", registro_id=acta.id)
        flash("Acta generada correctamente", "success")
        return redirect(url_for("actas.detalle", acta_id=acta.id))
    return render_template("actas/crear.html", form=form)


@actas_bp.route("/<int:acta_id>")
@login_required
@permissions_required("actas:read")
@require_hospital_access(Modulo.ACTAS)
def detalle(acta_id: int):
    acta = Acta.query.get_or_404(acta_id)
    return render_template("actas/descargar.html", acta=acta)


@actas_bp.route("/<int:acta_id>/pdf")
@login_required
@permissions_required("actas:read")
@require_hospital_access(Modulo.ACTAS)
def descargar_pdf(acta_id: int):
    acta = Acta.query.get_or_404(acta_id)
    if not acta.pdf_path:
        flash("Acta sin PDF generado", "warning")
        return redirect(url_for("actas.detalle", acta_id=acta.id))
    file_path = Path(acta.pdf_path)
    return send_file(file_path, as_attachment=True, download_name=file_path.name)
