"""Blueprint managing equipment inventory."""
from __future__ import annotations

from datetime import date, datetime, time
from pathlib import Path
from typing import Iterable
from uuid import uuid4

from flask import (
    Blueprint,
    abort,
    current_app,
    flash,
    g,
    jsonify,
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
from app.forms.equipo import (
    EquipoActaFiltroForm,
    EquipoAdjuntoDeleteForm,
    EquipoAdjuntoForm,
    EquipoFiltroForm,
    EquipoForm,
    EquipoHistorialFiltroForm,
)
from app.models import (
    Acta,
    ActaItem,
    Equipo,
    EquipoAdjunto,
    EquipoHistorial,
    EstadoEquipo,
    Modulo,
    TipoActa,
)
from app.security import permissions_required, require_hospital_access
from app.services.audit_service import log_action
from app.services.equipo_service import generate_internal_serial
from app.utils import normalize_enum_value


equipos_bp = Blueprint("equipos", __name__, url_prefix="/equipos")

MAX_REMOTE_PAGE_SIZE = 50


def _paginar(query, page: int, per_page: int):
    return query.paginate(page=page, per_page=per_page, error_out=False)


def _parse_limit(value: int | None, default: int = 10) -> int:
    if not value or value <= 0:
        return default
    return min(value, MAX_REMOTE_PAGE_SIZE)


def _parse_offset(value: int | None) -> int:
    if not value or value < 0:
        return 0
    return value


def _parse_iso_date(raw: str | None) -> date | None:
    if not raw:
        return None
    try:
        return datetime.strptime(raw, "%Y-%m-%d").date()
    except ValueError:
        return None


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
        if form.sin_numero_serie.data:
            numero_serie = generate_internal_serial(db.session)
        else:
            numero_serie = (form.numero_serie.data or "").strip()
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
        if form.sin_numero_serie.data:
            if not equipo.sin_numero_serie or not equipo.numero_serie:
                equipo.numero_serie = generate_internal_serial(db.session)
        else:
            equipo.numero_serie = (form.numero_serie.data or "").strip()
        equipo.codigo = form.codigo.data or None
        equipo.tipo = form.tipo.data
        equipo.estado = form.estado.data
        equipo.descripcion = form.descripcion.data or None
        equipo.marca = form.marca.data or None
        equipo.modelo = form.modelo.data or None
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
    delete_form = EquipoAdjuntoDeleteForm()

    historial_entries = sorted(
        equipo.historial,
        key=lambda item: item.fecha or datetime.min,
        reverse=True,
    )
    historial_recent = historial_entries[:3]

    acta_items: Iterable[ActaItem] = (
        entry for entry in equipo.acta_items if entry.acta is not None
    )
    actas_sorted = sorted(
        acta_items,
        key=lambda entry: entry.acta.fecha if entry.acta and entry.acta.fecha else datetime.min,
        reverse=True,
    )
    seen_actas: set[int] = set()
    actas_unique = []
    for entry in actas_sorted:
        acta = entry.acta
        if not acta or acta.id in seen_actas:
            continue
        seen_actas.add(acta.id)
        actas_unique.append(acta)
    actas_recent = actas_unique[:3]

    archivos = sorted(
        equipo.archivos,
        key=lambda item: item.created_at or item.id,
        reverse=True,
    )

    return render_template(
        "equipos/detalle.html",
        equipo=equipo,
        historial=historial_recent,
        historial_total=len(historial_entries),
        actas=actas_recent,
        actas_total=len(actas_unique),
        adjuntos=equipo.adjuntos,
        archivos=archivos,
        insumos=equipo.insumos,
        adjunto_form=form_adjuntos,
        delete_form=delete_form,
        tipos_acta=list(TipoActa),
        max_upload_size=current_app.config.get("EQUIPOS_MAX_FILE_SIZE", 10 * 1024 * 1024),
    )


@equipos_bp.route("/<int:equipo_id>/historial/datos")
@login_required
@permissions_required("inventario:read")
@require_hospital_access(Modulo.INVENTARIO)
def historial_datos(equipo_id: int):
    equipo = Equipo.query.get_or_404(equipo_id)

    limit = _parse_limit(request.args.get("limit", type=int), default=10)
    offset = _parse_offset(request.args.get("offset", type=int))
    tipo = (request.args.get("tipo", "") or "").strip()
    desde = _parse_iso_date(request.args.get("desde"))
    hasta = _parse_iso_date(request.args.get("hasta"))

    query = (
        EquipoHistorial.query.filter(EquipoHistorial.equipo_id == equipo.id)
        .order_by(EquipoHistorial.fecha.desc())
    )
    if tipo:
        like = f"%{tipo}%"
        query = query.filter(
            or_(
                EquipoHistorial.accion.ilike(like),
                EquipoHistorial.descripcion.ilike(like),
            )
        )
    if desde:
        query = query.filter(
            EquipoHistorial.fecha >= datetime.combine(desde, time.min)
        )
    if hasta:
        query = query.filter(
            EquipoHistorial.fecha <= datetime.combine(hasta, time.max)
        )

    total = query.count()
    registros = query.offset(offset).limit(limit).all()

    items = [
        {
            "id": registro.id,
            "accion": registro.accion,
            "descripcion": registro.descripcion,
            "fecha": registro.fecha.isoformat() if registro.fecha else None,
            "fecha_display": registro.fecha.strftime("%d/%m/%Y %H:%M")
            if registro.fecha
            else "",
            "usuario": registro.usuario.nombre if registro.usuario else None,
        }
        for registro in registros
    ]

    next_offset = offset + limit if offset + limit < total else None
    prev_offset = offset - limit if offset > 0 else None
    if prev_offset is not None and prev_offset < 0:
        prev_offset = 0

    return jsonify(
        {
            "items": items,
            "total": total,
            "limit": limit,
            "offset": offset,
            "next_offset": next_offset,
            "previous_offset": prev_offset,
        }
    )


@equipos_bp.route("/<int:equipo_id>/actas/datos")
@login_required
@permissions_required("inventario:read")
@require_hospital_access(Modulo.INVENTARIO)
def actas_datos(equipo_id: int):
    equipo = Equipo.query.get_or_404(equipo_id)

    limit = _parse_limit(request.args.get("limit", type=int), default=10)
    offset = _parse_offset(request.args.get("offset", type=int))
    tipo = (request.args.get("tipo") or "").strip()
    desde = _parse_iso_date(request.args.get("desde"))
    hasta = _parse_iso_date(request.args.get("hasta"))

    query = (
        Acta.query.join(Acta.items)
        .filter(ActaItem.equipo_id == equipo.id)
        .order_by(Acta.fecha.desc())
        .distinct()
    )

    if tipo:
        try:
            tipo_enum = TipoActa(tipo)
        except ValueError:
            tipo_enum = None
        if tipo_enum:
            query = query.filter(Acta.tipo == tipo_enum)

    if desde:
        query = query.filter(Acta.fecha >= datetime.combine(desde, time.min))
    if hasta:
        query = query.filter(Acta.fecha <= datetime.combine(hasta, time.max))

    total = query.count()
    actas = query.offset(offset).limit(limit).all()

    items = [
        {
            "id": acta.id,
            "tipo": acta.tipo.value if acta.tipo else None,
            "tipo_label": normalize_enum_value(acta.tipo) if acta.tipo else "",
            "fecha": acta.fecha.isoformat() if acta.fecha else None,
            "fecha_display": acta.fecha.strftime("%d/%m/%Y") if acta.fecha else "",
            "url": url_for("actas.detalle", acta_id=acta.id),
        }
        for acta in actas
    ]

    next_offset = offset + limit if offset + limit < total else None
    prev_offset = offset - limit if offset > 0 else None
    if prev_offset is not None and prev_offset < 0:
        prev_offset = 0

    return jsonify(
        {
            "items": items,
            "total": total,
            "limit": limit,
            "offset": offset,
            "next_offset": next_offset,
            "previous_offset": prev_offset,
        }
    )


def _max_upload_size() -> int:
    return int(current_app.config.get("EQUIPOS_MAX_FILE_SIZE", 10 * 1024 * 1024))


def _compute_file_size(file_storage) -> int:
    current_position = file_storage.stream.tell()
    file_storage.stream.seek(0, 2)
    size = file_storage.stream.tell()
    file_storage.stream.seek(current_position)
    return size


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
    file_size = _compute_file_size(file)
    max_size = _max_upload_size()
    if file_size > max_size:
        limit_mb = max_size / (1024 * 1024)
        flash(
            f"El archivo supera el tamaño máximo permitido ({limit_mb:.1f} MB).",
            "danger",
        )
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
        file_size=file_size,
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
    form = EquipoAdjuntoDeleteForm()
    if not form.validate_on_submit():
        flash("No se pudo validar la solicitud. Actualice la página e intente nuevamente.", "danger")
        return redirect(url_for("equipos.detalle", equipo_id=equipo_id))
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


@equipos_bp.route("/<int:equipo_id>/historial")
@login_required
@permissions_required("inventario:read")
@require_hospital_access(Modulo.INVENTARIO)
def historial_completo(equipo_id: int):
    equipo = Equipo.query.get_or_404(equipo_id)
    form = EquipoHistorialFiltroForm(request.args)

    query = (
        EquipoHistorial.query.filter(EquipoHistorial.equipo_id == equipo.id)
        .order_by(EquipoHistorial.fecha.desc())
    )

    if form.validate():
        if form.accion.data:
            like = f"%{form.accion.data.strip()}%"
            query = query.filter(
                or_(
                    EquipoHistorial.accion.ilike(like),
                    EquipoHistorial.descripcion.ilike(like),
                )
            )
        if form.fecha_desde.data:
            inicio = datetime.combine(form.fecha_desde.data, time.min)
            query = query.filter(EquipoHistorial.fecha >= inicio)
        if form.fecha_hasta.data:
            fin = datetime.combine(form.fecha_hasta.data, time.max)
            query = query.filter(EquipoHistorial.fecha <= fin)

    page = request.args.get("page", type=int, default=1)
    per_page = current_app.config.get("DEFAULT_PAGE_SIZE", 20)
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)

    return render_template(
        "equipos/historial.html",
        equipo=equipo,
        form=form,
        registros=pagination.items,
        pagination=pagination,
    )


@equipos_bp.route("/<int:equipo_id>/actas")
@login_required
@permissions_required("inventario:read")
@require_hospital_access(Modulo.INVENTARIO)
def actas_completas(equipo_id: int):
    equipo = Equipo.query.get_or_404(equipo_id)
    form = EquipoActaFiltroForm(request.args)

    query = (
        Acta.query.join(Acta.items)
        .filter(ActaItem.equipo_id == equipo.id)
        .order_by(Acta.fecha.desc())
        .distinct()
    )

    if form.validate():
        if form.tipo.data:
            query = query.filter(Acta.tipo == TipoActa(form.tipo.data))
        if form.fecha_desde.data:
            inicio = datetime.combine(form.fecha_desde.data, time.min)
            query = query.filter(Acta.fecha >= inicio)
        if form.fecha_hasta.data:
            fin = datetime.combine(form.fecha_hasta.data, time.max)
            query = query.filter(Acta.fecha <= fin)

    page = request.args.get("page", type=int, default=1)
    per_page = current_app.config.get("DEFAULT_PAGE_SIZE", 20)
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)

    return render_template(
        "equipos/actas.html",
        equipo=equipo,
        form=form,
        actas=pagination.items,
        pagination=pagination,
    )
