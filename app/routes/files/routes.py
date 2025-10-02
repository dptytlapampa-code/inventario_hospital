"""Serve and manage evidence files."""
from __future__ import annotations

from pathlib import Path

from flask import (
    Blueprint,
    abort,
    flash,
    g,
    redirect,
    request,
    send_file,
    url_for,
)
from flask_login import current_user, login_required
from sqlalchemy.orm import selectinload

from app.extensions import db
from app.forms.equipo import EquipoAdjuntoDeleteForm
from app.models import EquipoAdjunto, Modulo
from app.security import permissions_required, require_hospital_access
from app.services.audit_service import log_action
from app.services.file_service import (
    generate_image_thumbnail,
    purge_file_variants,
    resolve_storage_path,
    thumbnail_path,
)


files_bp = Blueprint("files", __name__, url_prefix="/files")


def _ensure_allowed(adjunto: EquipoAdjunto) -> None:
    equipo = adjunto.equipo
    allowed = getattr(g, "allowed_hospitals", set())
    if allowed and equipo and equipo.hospital_id not in allowed:
        abort(404)


def _load_adjunto(file_id: int) -> EquipoAdjunto:
    adjunto = (
        EquipoAdjunto.query.options(selectinload(EquipoAdjunto.equipo))
        .filter_by(id=file_id)
        .first()
    )
    if not adjunto:
        abort(404)
    _ensure_allowed(adjunto)
    return adjunto


def _resolve_or_404(adjunto: EquipoAdjunto) -> Path:
    try:
        stored_path = resolve_storage_path(adjunto.filepath)
    except FileNotFoundError:  # pragma: no cover - defensive
        abort(404)
    if not stored_path.exists():
        abort(404)
    return stored_path


def _fallback_target(adjunto: EquipoAdjunto) -> str:
    target = request.args.get("next") or request.referrer
    if not target and adjunto.equipo:
        target = url_for("equipos.detalle", equipo_id=adjunto.equipo_id)
    return target or url_for("equipos.listar")


@files_bp.route("/view/<int:file_id>")
@login_required
@permissions_required("inventario:read")
@require_hospital_access(Modulo.INVENTARIO)
def view_file(file_id: int):
    adjunto = _load_adjunto(file_id)
    stored_path = _resolve_or_404(adjunto)
    return send_file(stored_path, as_attachment=False, download_name=adjunto.filename)


@files_bp.route("/download/<int:file_id>")
@login_required
@permissions_required("inventario:read")
@require_hospital_access(Modulo.INVENTARIO)
def download_file(file_id: int):
    adjunto = _load_adjunto(file_id)
    stored_path = _resolve_or_404(adjunto)
    return send_file(stored_path, as_attachment=True, download_name=adjunto.filename)


@files_bp.route("/thumb/<int:file_id>")
@login_required
@permissions_required("inventario:read")
@require_hospital_access(Modulo.INVENTARIO)
def thumbnail(file_id: int):
    adjunto = _load_adjunto(file_id)
    if not (adjunto.mime_type or "").startswith("image/"):
        abort(404)
    original = _resolve_or_404(adjunto)
    thumb_path = thumbnail_path(original)
    if thumb_path.exists():
        return send_file(thumb_path, as_attachment=False, download_name=thumb_path.name)

    generated = generate_image_thumbnail(original)
    if generated is None:
        return send_file(original, as_attachment=False, download_name=adjunto.filename)

    thumb_path = generated
    if not thumb_path.exists():
        return send_file(original, as_attachment=False, download_name=adjunto.filename)

    return send_file(thumb_path, as_attachment=False, download_name=thumb_path.name)


@files_bp.route("/delete/<int:file_id>", methods=["POST"])
@login_required
@permissions_required("inventario:write")
@require_hospital_access(Modulo.INVENTARIO)
def delete_file(file_id: int):
    form = EquipoAdjuntoDeleteForm()
    if not form.validate_on_submit():
        flash("No se pudo validar la solicitud.", "danger")
        adjunto = _load_adjunto(file_id)
        return redirect(_fallback_target(adjunto))

    adjunto = _load_adjunto(file_id)
    equipo = adjunto.equipo

    try:
        stored_path = _resolve_or_404(adjunto)
    except Exception:  # pragma: no cover - handled by removing file
        stored_path = None

    thumb = thumbnail_path(stored_path) if stored_path else None
    purge_file_variants(path for path in [stored_path, thumb] if path)
    if stored_path:
        parent = stored_path.parent
        if parent.exists() and not any(parent.iterdir()):
            parent.rmdir()

    redirect_target = _fallback_target(adjunto)

    db.session.delete(adjunto)
    if equipo:
        equipo.registrar_evento(
            current_user,
            "Adjunto",
            f"Archivo {adjunto.filename} eliminado",
        )
    db.session.commit()
    log_action(
        usuario_id=current_user.id,
        accion="eliminar_adjunto",
        modulo="inventario",
        tabla="equipos_adjuntos",
        registro_id=adjunto.id,
    )
    flash("Adjunto eliminado correctamente.", "success")
    return redirect(redirect_target)


__all__ = ["files_bp"]
