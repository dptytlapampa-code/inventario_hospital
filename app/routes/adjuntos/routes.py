"""Routes to manage equipment attachments."""
from __future__ import annotations

from pathlib import Path
from uuid import uuid4

from flask import (
    Blueprint,
    abort,
    current_app,
    flash,
    g,
    redirect,
    render_template,
    request,
    send_from_directory,
    url_for,
)
from flask_login import current_user, login_required
from werkzeug.utils import secure_filename

from app.extensions import db
from app.forms.adjunto import AdjuntoForm
from app.models import Adjunto, Equipo, Modulo
from app.security import permissions_required, require_hospital_access
from app.services.audit_service import log_action
from app.services.equipo_service import equipment_options_for_ids
from sqlalchemy import or_

adjuntos_bp = Blueprint("adjuntos", __name__, url_prefix="/adjuntos")

def _adjunto_dir() -> Path:
    base = Path(current_app.config["ADJUNTOS_UPLOAD_FOLDER"])
    base.mkdir(parents=True, exist_ok=True)
    return base


@adjuntos_bp.route("/")
@login_required
@permissions_required("adjuntos:read")
@require_hospital_access(Modulo.ADJUNTOS)
def listar():
    page = request.args.get("page", type=int, default=1)
    per_page = current_app.config.get("DEFAULT_PAGE_SIZE", 20)
    buscar = request.args.get("q", "")

    query = Adjunto.query.join(Adjunto.equipo).order_by(Adjunto.uploaded_at.desc())
    allowed = getattr(g, "allowed_hospitals", set())
    if allowed:
        query = query.filter(Equipo.hospital_id.in_(allowed))
    if buscar:
        like = f"%{buscar}%"
        query = query.filter(
            or_(
                Adjunto.filename.ilike(like),
                Adjunto.descripcion.ilike(like),
                Equipo.codigo.ilike(like),
                Equipo.descripcion.ilike(like),
            )
        )
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    return render_template(
        "adjuntos/listar.html",
        adjuntos=pagination.items,
        pagination=pagination,
        buscar=buscar,
    )


@adjuntos_bp.route("/subir", methods=["GET", "POST"])
@login_required
@permissions_required("adjuntos:write")
@require_hospital_access(Modulo.ADJUNTOS)
def subir():
    form = AdjuntoForm()
    if form.validate_on_submit():
        file = form.archivo.data
        original_name = secure_filename(file.filename)
        unique_name = f"{uuid4().hex}_{original_name}"
        path = _adjunto_dir() / unique_name
        file.save(path)

        adjunto = Adjunto(
            equipo_id=form.equipo_id.data,
            filename=original_name,
            path=path.as_posix(),
            tipo=form.tipo.data,
            descripcion=form.descripcion.data or None,
            uploaded_by=current_user,
        )
        db.session.add(adjunto)
        db.session.commit()
        log_action(usuario_id=current_user.id, accion="subir", modulo="adjuntos", tabla="adjuntos", registro_id=adjunto.id)
        flash("Adjunto subido correctamente", "success")
        return redirect(url_for("adjuntos.listar"))
    return render_template(
        "adjuntos/formulario.html",
        form=form,
        titulo="Nuevo adjunto",
        equipo_options=equipment_options_for_ids([form.equipo_id.data]),
    )


@adjuntos_bp.route("/<int:adjunto_id>")
@login_required
@permissions_required("adjuntos:read")
@require_hospital_access(Modulo.ADJUNTOS)
def detalle(adjunto_id: int):
    adjunto = Adjunto.query.get_or_404(adjunto_id)
    return render_template("adjuntos/detalle.html", adjunto=adjunto)


@adjuntos_bp.route("/<int:adjunto_id>/descargar")
@login_required
@permissions_required("adjuntos:read")
@require_hospital_access(Modulo.ADJUNTOS)
def descargar(adjunto_id: int):
    adjunto = Adjunto.query.get_or_404(adjunto_id)
    storage_dir = Path(current_app.config["ADJUNTOS_UPLOAD_FOLDER"])
    upload_root = Path(current_app.config["UPLOAD_FOLDER"]).resolve()

    stored_path = Path(adjunto.path) if adjunto.path else None
    candidates: list[Path] = []
    if stored_path and stored_path.name:
        candidates.append(storage_dir / stored_path.name)
    if stored_path:
        if stored_path.is_absolute():
            candidates.append(stored_path)
        else:
            candidates.append(Path(current_app.root_path).parent / stored_path)

    selected_path: Path | None = None
    for candidate in candidates:
        if candidate.exists():
            selected_path = candidate.resolve()
            break

    if not selected_path:
        current_app.logger.warning(
            "Archivo de adjunto %s no encontrado en %s", adjunto.id, adjunto.path
        )
        flash("El archivo del adjunto no está disponible.", "warning")
        abort(404)

    try:
        selected_path.relative_to(upload_root)
    except ValueError:
        current_app.logger.warning(
            "Ruta de adjunto %s fuera del directorio permitido: %s", adjunto.id, selected_path
        )
        flash("El archivo del adjunto no está disponible.", "warning")
        abort(404)

    return send_from_directory(
        selected_path.parent, selected_path.name, as_attachment=True, download_name=adjunto.filename
    )
