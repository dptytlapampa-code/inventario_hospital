"""Blueprint managing equipment inventory."""
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
    send_file,
    url_for,
)
from flask_login import current_user, login_required
from sqlalchemy import or_
from werkzeug.utils import secure_filename

from app.extensions import db
from app.forms.equipo import EquipoAdjuntoForm, EquipoFiltroForm, EquipoForm
from app.models import Equipo, EquipoAdjunto, EstadoEquipo, Modulo
from app.security import permissions_required, require_hospital_access
from app.services.audit_service import log_action
from app.services.equipo_service import generate_internal_serial


equipos_bp = Blueprint("equipos", __name__, url_prefix="/equipos")


def _paginar(query, page: int, per_page: int):
    return query.paginate(page=page, per_page=per_page, error_out=False)


@equipos_bp.route("/")
@login_required
@permissions_required("inventario:read")
@require_hospital_access(Modulo.INVENTARIO)
def listar():
    form = EquipoFiltroForm(request.args)
    page = request.args.get("page", type=int, default=1)
    per_page = current_app.config.get("DEFAULT_PAGE_SIZE", 20)

    query = Equipo.query.order_by(Equipo.created_at.desc())
    allowed = getattr(g, "allowed_hospitals", set())
    if allowed:
        query = query.filter(Equipo.hospital_id.in_(allowed))
    if form.hospital_id.data and form.hospital_id.data != 0:
        query = query.filter(Equipo.hospital_id == form.hospital_id.data)
    if form.estado.data:
        query = query.filter(Equipo.estado == form.estado.data)
    if form.buscar.data:
        like = f"%{form.buscar.data}%"
        query = query.filter(
            or_(
                Equipo.descripcion.ilike(like),
                Equipo.codigo.ilike(like),
                Equipo.numero_serie.ilike(like),
            )
        )

    pagination = _paginar(query, page, per_page)
    return render_template(
        "equipos/listar.html",
        form=form,
        equipos=pagination.items,
        pagination=pagination,
    )
@equipos_bp.route("/crear", methods=["GET", "POST"])
@login_required
@permissions_required("inventario:write")
@require_hospital_access(Modulo.INVENTARIO)
def crear():
    form = EquipoForm()
    if form.validate_on_submit():
        numero_serie = (form.numero_serie.data or "").strip() or None
        if form.sin_numero_serie.data:
            numero_serie = generate_internal_serial(db.session)
        equipo = Equipo(
            codigo=form.codigo.data or None,
            tipo=form.tipo.data,
            estado=form.estado.data,
            descripcion=form.descripcion.data or None,
            marca=form.marca.data or None,
            modelo=form.modelo.data or None,
            numero_serie=numero_serie,
            sin_numero_serie=bool(form.sin_numero_serie.data),
            hospital_id=form.hospital_id.data,
            servicio_id=form.servicio_id.data or None,
            oficina_id=form.oficina_id.data or None,
            responsable=form.responsable.data or None,
            fecha_compra=form.fecha_compra.data,
            fecha_instalacion=form.fecha_instalacion.data,
            garantia_hasta=form.garantia_hasta.data,
            observaciones=form.observaciones.data or None,
        )
        equipo.registrar_evento(current_user, "Alta", "Creación de equipo")
        db.session.add(equipo)
        db.session.commit()
        log_action(usuario_id=current_user.id, accion="crear", modulo="inventario", tabla="equipos", registro_id=equipo.id)
        flash("Equipo creado correctamente", "success")
        return redirect(url_for("equipos.listar"))
    return render_template("equipos/formulario.html", form=form, titulo="Nuevo equipo")


@equipos_bp.route("/<int:equipo_id>/editar", methods=["GET", "POST"])
@login_required
@permissions_required("inventario:write")
@require_hospital_access(Modulo.INVENTARIO)
def editar(equipo_id: int):
    equipo = Equipo.query.get_or_404(equipo_id)
    form = EquipoForm(obj=equipo)
    if request.method == "GET":
        form.sin_numero_serie.data = equipo.sin_numero_serie
    if form.validate_on_submit():
        numero_serie = (form.numero_serie.data or "").strip() or None
        if form.sin_numero_serie.data:
            numero_serie = generate_internal_serial(db.session)
        equipo.codigo = form.codigo.data or None
        equipo.tipo = form.tipo.data
        equipo.estado = form.estado.data
        equipo.descripcion = form.descripcion.data or None
        equipo.marca = form.marca.data or None
        equipo.modelo = form.modelo.data or None
        equipo.numero_serie = numero_serie
        equipo.sin_numero_serie = bool(form.sin_numero_serie.data)
        equipo.hospital_id = form.hospital_id.data
        equipo.servicio_id = form.servicio_id.data or None
        equipo.oficina_id = form.oficina_id.data or None
        equipo.responsable = form.responsable.data or None
        equipo.fecha_compra = form.fecha_compra.data
        equipo.fecha_instalacion = form.fecha_instalacion.data
        equipo.garantia_hasta = form.garantia_hasta.data
        equipo.observaciones = form.observaciones.data or None
        equipo.registrar_evento(current_user, "Actualización", "Edición de equipo")
        db.session.commit()
        log_action(usuario_id=current_user.id, accion="editar", modulo="inventario", tabla="equipos", registro_id=equipo.id)
        flash("Equipo actualizado", "success")
        return redirect(url_for("equipos.detalle", equipo_id=equipo.id))
    return render_template("equipos/formulario.html", form=form, titulo="Editar equipo", equipo=equipo)


@equipos_bp.route("/<int:equipo_id>")
@login_required
@permissions_required("inventario:read")
@require_hospital_access(Modulo.INVENTARIO)
def detalle(equipo_id: int):
    equipo = Equipo.query.get_or_404(equipo_id)
    form_adjuntos = EquipoAdjuntoForm()
    return render_template(
        "equipos/detalle.html",
        equipo=equipo,
        historial=equipo.historial[-10:],
        actas=[item.acta for item in equipo.acta_items],
        adjuntos=equipo.adjuntos,
        archivos=sorted(
            equipo.archivos,
            key=lambda item: item.created_at or item.id,
            reverse=True,
        ),
        insumos=equipo.insumos,
        adjunto_form=form_adjuntos,
    )


def _ensure_upload_size(file_storage) -> bool:
    file_storage.stream.seek(0, 2)
    size = file_storage.stream.tell()
    file_storage.stream.seek(0)
    max_size = 10 * 1024 * 1024
    return size <= max_size


def _equipment_upload_dir(equipo_id: int) -> Path:
    base = Path(current_app.config["EQUIPOS_UPLOAD_FOLDER"])
    base.mkdir(parents=True, exist_ok=True)
    target = base / str(equipo_id)
    target.mkdir(parents=True, exist_ok=True)
    return target


@equipos_bp.route("/<int:equipo_id>/adjuntos/subir", methods=["POST"])
@login_required
@permissions_required("inventario:write")
@require_hospital_access(Modulo.INVENTARIO)
def subir_adjunto(equipo_id: int):
    equipo = Equipo.query.get_or_404(equipo_id)
    form = EquipoAdjuntoForm()
    if not form.validate_on_submit():
        for field, errors in form.errors.items():
            for error in errors:
                flash(error, "danger")
        return redirect(url_for("equipos.detalle", equipo_id=equipo.id))

    file = form.archivo.data
    if not _ensure_upload_size(file):
        flash("El archivo supera el tamaño máximo permitido (10 MB).", "danger")
        return redirect(url_for("equipos.detalle", equipo_id=equipo.id))

    original_name = secure_filename(file.filename or "archivo")
    extension = Path(original_name).suffix.lower()
    unique_name = f"{uuid4().hex}{extension}"
    directory = _equipment_upload_dir(equipo.id)
    storage_path = directory / unique_name
    file.save(storage_path)

    adjunto = EquipoAdjunto(
        equipo_id=equipo.id,
        filename=original_name,
        filepath=str(storage_path),
        mime_type=file.mimetype or "application/octet-stream",
        uploaded_by_id=current_user.id,
    )
    db.session.add(adjunto)
    equipo.registrar_evento(current_user, "Adjunto", f"Archivo {original_name} cargado")
    db.session.commit()
    log_action(
        usuario_id=current_user.id,
        accion="subir_adjunto",
        modulo="inventario",
        tabla="equipos_adjuntos",
        registro_id=adjunto.id,
    )
    flash("Archivo adjuntado correctamente.", "success")
    return redirect(url_for("equipos.detalle", equipo_id=equipo.id))


def _resolve_storage_path(adjunto: EquipoAdjunto) -> Path:
    configured = Path(current_app.config["EQUIPOS_UPLOAD_FOLDER"]).resolve()
    stored = Path(adjunto.filepath)
    if not stored.is_absolute():
        stored = configured / stored
    stored = stored.resolve()
    if configured not in stored.parents and stored != configured:
        raise FileNotFoundError("Ubicación fuera del directorio permitido")
    return stored


@equipos_bp.route("/<int:equipo_id>/adjuntos/<int:adjunto_id>/descargar")
@login_required
@permissions_required("inventario:read")
@require_hospital_access(Modulo.INVENTARIO)
def descargar_adjunto(equipo_id: int, adjunto_id: int):
    adjunto = EquipoAdjunto.query.get_or_404(adjunto_id)
    if adjunto.equipo_id != equipo_id:
        abort(404)
    try:
        stored_path = _resolve_storage_path(adjunto)
    except FileNotFoundError:
        flash("El archivo del adjunto no está disponible.", "warning")
        return redirect(url_for("equipos.detalle", equipo_id=equipo_id))
    if not stored_path.exists():
        flash("El archivo del adjunto no está disponible.", "warning")
        return redirect(url_for("equipos.detalle", equipo_id=equipo_id))
    inline = request.args.get("preview") == "1"
    return send_file(
        stored_path,
        as_attachment=not inline,
        download_name=adjunto.filename,
    )


@equipos_bp.route("/<int:equipo_id>/adjuntos/<int:adjunto_id>/eliminar", methods=["POST"])
@login_required
@permissions_required("inventario:write")
@require_hospital_access(Modulo.INVENTARIO)
def eliminar_adjunto(equipo_id: int, adjunto_id: int):
    adjunto = EquipoAdjunto.query.get_or_404(adjunto_id)
    if adjunto.equipo_id != equipo_id:
        abort(404)
    try:
        stored_path = _resolve_storage_path(adjunto)
    except FileNotFoundError:
        stored_path = None
    if stored_path and stored_path.exists():
        stored_path.unlink(missing_ok=True)
        parent = stored_path.parent
        if parent != stored_path and parent.exists() and not any(parent.iterdir()):
            parent.rmdir()
    equipo = Equipo.query.get(equipo_id)
    db.session.delete(adjunto)
    if equipo:
        equipo.registrar_evento(current_user, "Adjunto", f"Archivo {adjunto.filename} eliminado")
    db.session.commit()
    log_action(
        usuario_id=current_user.id,
        accion="eliminar_adjunto",
        modulo="inventario",
        tabla="equipos_adjuntos",
        registro_id=adjunto.id,
    )
    flash("Adjunto eliminado correctamente.", "success")
    return redirect(url_for("equipos.detalle", equipo_id=equipo_id))
