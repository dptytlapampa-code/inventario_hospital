"""Blueprint exposing audit trail with advanced filters."""
from __future__ import annotations

from datetime import datetime

from flask import Blueprint, render_template, request
from flask_login import current_user, login_required

from app.models import Auditoria, Hospital, Usuario
from app.security import require_roles
from app.utils.search import apply_text_search, paginate_query


auditoria_bp = Blueprint("auditoria", __name__, url_prefix="/auditorias")


@auditoria_bp.route("/")
@login_required
@require_roles("admin", "superadmin")
def index():
    q = (request.args.get("q", "") or "").strip()
    usuario_id = request.args.get("usuario_id", type=int)
    hospital_id = request.args.get("hospital_id", type=int)
    modulo = (request.args.get("modulo") or "").strip() or None
    accion = (request.args.get("accion") or "").strip() or None
    fecha_desde = request.args.get("desde")
    fecha_hasta = request.args.get("hasta")

    def parse_date(value: str | None):
        if not value:
            return None
        try:
            return datetime.fromisoformat(value)
        except ValueError:
            return None

    desde_dt = parse_date(fecha_desde)
    hasta_dt = parse_date(fecha_hasta)

    query = Auditoria.query.outerjoin(Auditoria.usuario).outerjoin(Auditoria.hospital)
    allowed_hospitals = current_user.allowed_hospital_ids()
    if allowed_hospitals:
        query = query.filter(
            Auditoria.hospital_id.is_(None) | Auditoria.hospital_id.in_(allowed_hospitals)
        )

    if usuario_id:
        query = query.filter(Auditoria.usuario_id == usuario_id)
    if hospital_id:
        query = query.filter(Auditoria.hospital_id == hospital_id)
    if modulo:
        query = query.filter(Auditoria.modulo == modulo)
    if accion:
        query = query.filter(Auditoria.accion == accion)

    if desde_dt:
        query = query.filter(Auditoria.created_at >= desde_dt)
    if hasta_dt:
        query = query.filter(Auditoria.created_at <= hasta_dt)

    if q:
        query = apply_text_search(
            query,
            (Auditoria.descripcion, Auditoria.modulo, Auditoria.accion, Auditoria.entidad),
            q,
        )

    page = request.args.get("page", type=int, default=1)
    per_page = request.args.get("per_page", type=int, default=20)
    pagination = paginate_query(
        query.order_by(Auditoria.created_at.desc()), page=page, per_page=per_page
    )

    usuarios = Usuario.query.order_by(Usuario.nombre).all()
    selected_hospital = Hospital.query.get(hospital_id) if hospital_id else None

    return render_template(
        "auditoria/index.html",
        pagination=pagination,
        filtros={
            "q": q,
            "usuario_id": usuario_id,
            "hospital_id": hospital_id,
            "modulo": modulo,
            "accion": accion,
            "desde": fecha_desde,
            "hasta": fecha_hasta,
        },
        usuarios=usuarios,
        selected_hospital=selected_hospital,
    )


__all__ = ["auditoria_bp"]
