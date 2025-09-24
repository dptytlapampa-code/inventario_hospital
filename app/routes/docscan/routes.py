"""Routes for scanned documentation module."""
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
from app.forms.docscan import DocscanForm
from app.models import Docscan, Modulo
from app.security import permissions_required, require_hospital_access
from app.services.audit_service import log_action
from sqlalchemy import or_


docscan_bp = Blueprint("docscan", __name__, url_prefix="/docscan")

def _docscan_dir() -> Path:
    base = Path(current_app.config["DOCSCAN_UPLOAD_FOLDER"])
    base.mkdir(parents=True, exist_ok=True)
    return base


@docscan_bp.route("/")
@login_required
@permissions_required("docscan:read")
@require_hospital_access(Modulo.DOCSCAN)
def listar():
    page = request.args.get("page", type=int, default=1)
    per_page = current_app.config.get("DEFAULT_PAGE_SIZE", 20)
    buscar = request.args.get("q", "")

    query = Docscan.query.order_by(Docscan.uploaded_at.desc())
    allowed = getattr(g, "allowed_hospitals", set())
    if allowed:
        query = query.filter(Docscan.hospital_id.in_(allowed))
    if buscar:
        like = f"%{buscar}%"
        query = query.filter(
            or_(Docscan.titulo.ilike(like), Docscan.comentario.ilike(like))
        )

    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    return render_template(
        "docscan/listar.html",
        documentos=pagination.items,
        pagination=pagination,
        buscar=buscar,
    )


@docscan_bp.route("/subir", methods=["GET", "POST"])
@login_required
@permissions_required("docscan:write")
@require_hospital_access(Modulo.DOCSCAN)
def subir():
    form = DocscanForm()
    if form.validate_on_submit():
        file = form.archivo.data
        original_name = secure_filename(file.filename)
        unique_name = f"{uuid4().hex}_{original_name}"
        path = _docscan_dir() / unique_name
        file.save(path)
        doc = Docscan(
            titulo=form.titulo.data,
            tipo=form.tipo.data,
            filename=original_name,
            path=path.as_posix(),
            fecha_documento=form.fecha_documento.data,
            comentario=form.comentario.data or None,
            usuario=current_user,
            hospital_id=form.hospital_id.data or None,
            servicio_id=form.servicio_id.data or None,
            oficina_id=form.oficina_id.data or None,
        )
        db.session.add(doc)
        db.session.commit()
        log_action(usuario_id=current_user.id, accion="subir", modulo="docscan", tabla="docscan", registro_id=doc.id)
        flash("Documento cargado", "success")
        return redirect(url_for("docscan.listar"))
    return render_template("docscan/formulario.html", form=form, titulo="Nuevo documento")


@docscan_bp.route("/<int:doc_id>")
@login_required
@permissions_required("docscan:read")
@require_hospital_access(Modulo.DOCSCAN)
def detalle(doc_id: int):
    documento = Docscan.query.get_or_404(doc_id)
    return render_template("docscan/detalle.html", documento=documento)


@docscan_bp.route("/<int:doc_id>/descargar")
@login_required
@permissions_required("docscan:read")
@require_hospital_access(Modulo.DOCSCAN)
def descargar(doc_id: int):
    documento = Docscan.query.get_or_404(doc_id)
    storage_dir = Path(current_app.config["DOCSCAN_UPLOAD_FOLDER"])
    upload_root = Path(current_app.config["UPLOAD_FOLDER"]).resolve()

    stored_path = Path(documento.path) if documento.path else None
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
            "Archivo de docscan %s no encontrado en %s", documento.id, documento.path
        )
        flash("El archivo solicitado no está disponible.", "warning")
        abort(404)

    try:
        selected_path.relative_to(upload_root)
    except ValueError:
        current_app.logger.warning(
            "Ruta de docscan %s fuera del directorio permitido: %s", documento.id, selected_path
        )
        flash("El archivo solicitado no está disponible.", "warning")
        abort(404)

    return send_from_directory(
        selected_path.parent, selected_path.name, as_attachment=True, download_name=documento.filename
    )
