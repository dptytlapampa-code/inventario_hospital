"""Blueprint managing equipment inventory."""
from __future__ import annotations

from datetime import date, datetime, time
from pathlib import Path
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
    url_for,
)
from flask_login import current_user, login_required
from sqlalchemy import func, or_
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import selectinload
from werkzeug.utils import secure_filename

from app.extensions import db
from app.forms.equipo import (
    EquipoActaFiltroForm,
    EquipoAdjuntoForm,
    EquipoFiltroForm,
    EquipoForm,
    EquipoHistorialFiltroForm,
    TipoEquipoDeleteForm,
    TipoEquipoCreateForm,
    TipoEquipoUpdateForm,
)
from app.models import (
    Acta,
    ActaItem,
    Equipo,
    EquipoAdjunto,
    EquipoHistorial,
    EquipoInsumo,
    EstadoEquipo,
    Hospital,
    InsumoMovimiento,
    InsumoSerie,
    Modulo,
    MovimientoTipo,
    Oficina,
    SerieEstado,
    Servicio,
    TipoActa,
    TipoEquipo,
)
from app.security import permissions_required, require_hospital_access, require_roles
from app.services.audit_service import log_action
from app.services.equipo_service import generate_internal_serial
from app.services.file_service import equipment_upload_dir, generate_image_thumbnail
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

    query = Equipo.query.options(selectinload(Equipo.tipo)).order_by(Equipo.created_at.desc())
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
        hospital = Hospital.query.get(form.hospital_id.data)
        if not hospital:
            flash("El hospital seleccionado no existe.", "danger")
            form.hospital_id.errors.append("Seleccione un hospital válido")
            return render_template("equipos/crear.html", form=form, titulo="Nuevo equipo"), 400

        servicio = None
        if form.servicio_id.data:
            servicio = Servicio.query.get(form.servicio_id.data)
            if not servicio or servicio.hospital_id != hospital.id:
                flash(
                    "El servicio seleccionado no pertenece al hospital indicado.",
                    "danger",
                )
                form.servicio_id.errors.append("Seleccione un servicio válido")
                return render_template("equipos/crear.html", form=form, titulo="Nuevo equipo"), 400

        oficina = None
        if form.oficina_id.data:
            oficina = Oficina.query.get(form.oficina_id.data)
            if not oficina or oficina.hospital_id != hospital.id:
                flash("La oficina seleccionada no existe.", "danger")
                form.oficina_id.errors.append("Seleccione una oficina válida")
                return render_template("equipos/crear.html", form=form, titulo="Nuevo equipo"), 400
            if servicio and oficina.servicio_id != servicio.id:
                flash(
                    "La oficina seleccionada no pertenece al servicio indicado.",
                    "danger",
                )
                form.oficina_id.errors.append("Seleccione una oficina válida")
                return render_template("equipos/crear.html", form=form, titulo="Nuevo equipo"), 400

        numero_serie = (
            generate_internal_serial(db.session)
            if form.sin_numero_serie.data
            else (form.numero_serie.data or "").strip()
        )

        equipo = Equipo(
            codigo=form.codigo.data or None,
            tipo_id=form.tipo.data,
            estado=form.estado.data,
            descripcion=form.descripcion.data or None,
            marca=form.marca.data or None,
            modelo=form.modelo.data or None,
            numero_serie=numero_serie,
            sin_numero_serie=bool(form.sin_numero_serie.data),
            hospital_id=hospital.id,
            servicio_id=servicio.id if servicio else None,
            oficina_id=oficina.id if oficina else None,
            responsable=form.responsable.data or None,
            fecha_ingreso=form.fecha_ingreso.data,
            fecha_instalacion=form.fecha_instalacion.data,
            garantia_hasta=form.garantia_hasta.data,
            observaciones=form.observaciones.data or None,
            es_nuevo=bool(form.es_nuevo.data),
            expediente=form.expediente.data or None,
            anio_expediente=form.anio_expediente.data or None,
            orden_compra=form.orden_compra.data or None,
            tipo_adquisicion=form.tipo_adquisicion.data or None,
        )
        detalle_alta = "Alta de equipo nuevo" if form.es_nuevo.data else "Alta de equipo usado"
        equipo.registrar_evento(current_user, "Alta", detalle_alta)
        db.session.add(equipo)
        db.session.commit()
        log_action(
            usuario_id=current_user.id,
            accion="crear",
            modulo="inventario",
            tabla="equipos",
            registro_id=equipo.id,
        )
        flash("Equipo creado correctamente", "success")
        return redirect(url_for("equipos.listar"))

    return render_template("equipos/crear.html", form=form, titulo="Nuevo equipo")


@equipos_bp.route("/<int:equipo_id>/editar", methods=["GET", "POST"])
@login_required
@permissions_required("inventario:write")
@require_hospital_access(Modulo.INVENTARIO)
def editar(equipo_id: int):
    equipo = Equipo.query.options(selectinload(Equipo.tipo)).get_or_404(equipo_id)
    form = EquipoForm(obj=equipo)
    if request.method == "GET":
        form.sin_numero_serie.data = equipo.sin_numero_serie

    if form.validate_on_submit():
        hospital = Hospital.query.get(form.hospital_id.data)
        if not hospital:
            flash("El hospital seleccionado no existe.", "danger")
            form.hospital_id.errors.append("Seleccione un hospital válido")
            return render_template("equipos/editar.html", form=form, titulo="Editar equipo", equipo=equipo), 400

        servicio = None
        if form.servicio_id.data:
            servicio = Servicio.query.get(form.servicio_id.data)
            if not servicio or servicio.hospital_id != hospital.id:
                flash(
                    "El servicio seleccionado no pertenece al hospital indicado.",
                    "danger",
                )
                form.servicio_id.errors.append("Seleccione un servicio válido")
                return render_template("equipos/editar.html", form=form, titulo="Editar equipo", equipo=equipo), 400

        oficina = None
        if form.oficina_id.data:
            oficina = Oficina.query.get(form.oficina_id.data)
            if not oficina or oficina.hospital_id != hospital.id:
                flash("La oficina seleccionada no existe.", "danger")
                form.oficina_id.errors.append("Seleccione una oficina válida")
                return render_template("equipos/editar.html", form=form, titulo="Editar equipo", equipo=equipo), 400
            if servicio and oficina.servicio_id != servicio.id:
                flash(
                    "La oficina seleccionada no pertenece al servicio indicado.",
                    "danger",
                )
                form.oficina_id.errors.append("Seleccione una oficina válida")
                return render_template("equipos/editar.html", form=form, titulo="Editar equipo", equipo=equipo), 400

        numero_serie = (
            generate_internal_serial(db.session)
            if form.sin_numero_serie.data
            else (form.numero_serie.data or "").strip()
        )

        equipo.codigo = form.codigo.data or None
        equipo.tipo_id = form.tipo.data
        equipo.estado = form.estado.data
        equipo.descripcion = form.descripcion.data or None
        equipo.marca = form.marca.data or None
        equipo.modelo = form.modelo.data or None
        equipo.numero_serie = numero_serie
        equipo.sin_numero_serie = bool(form.sin_numero_serie.data)
        equipo.hospital_id = hospital.id
        equipo.servicio_id = servicio.id if servicio else None
        equipo.oficina_id = oficina.id if oficina else None
        equipo.responsable = form.responsable.data or None
        equipo.fecha_ingreso = form.fecha_ingreso.data
        equipo.fecha_instalacion = form.fecha_instalacion.data
        equipo.garantia_hasta = form.garantia_hasta.data
        equipo.observaciones = form.observaciones.data or None
        equipo.es_nuevo = bool(form.es_nuevo.data)
        equipo.expediente = form.expediente.data or None
        equipo.anio_expediente = form.anio_expediente.data or None
        equipo.orden_compra = form.orden_compra.data or None
        equipo.tipo_adquisicion = form.tipo_adquisicion.data or None
        equipo.modified_by = current_user.id

        detalle_alta = "Actualización de equipo nuevo" if form.es_nuevo.data else "Actualización de equipo"
        equipo.registrar_evento(current_user, "Actualización", detalle_alta)
        db.session.commit()
        log_action(
            usuario_id=current_user.id,
            accion="editar",
            modulo="inventario",
            tabla="equipos",
            registro_id=equipo.id,
        )
        flash("Equipo actualizado", "success")
        return redirect(url_for("equipos.detalle", equipo_id=equipo.id))

    return render_template("equipos/editar.html", form=form, titulo="Editar equipo", equipo=equipo)
@equipos_bp.route("/<int:equipo_id>")
@login_required
@permissions_required("inventario:read")
@require_hospital_access(Modulo.INVENTARIO)
def detalle(equipo_id: int):
    equipo = (
        Equipo.query.options(
            selectinload(Equipo.tipo),
            selectinload(Equipo.insumos_asociados)
            .selectinload(EquipoInsumo.serie)
            .selectinload(InsumoSerie.insumo),
            selectinload(Equipo.insumos_asociados).selectinload(EquipoInsumo.insumo),
            selectinload(Equipo.insumos_asociados).selectinload(EquipoInsumo.asociado_por),
        )
        .get_or_404(equipo_id)
    )

    form_adjuntos = EquipoAdjuntoForm()
    per_page = current_app.config.get("DEFAULT_PAGE_SIZE", 25)

    insumos_page = request.args.get("insumos_page", type=int, default=1)
    insumos_query = (
        EquipoInsumo.query.options(
            selectinload(EquipoInsumo.insumo),
            selectinload(EquipoInsumo.serie).selectinload(InsumoSerie.insumo),
            selectinload(EquipoInsumo.asociado_por),
        )
        .filter(
            EquipoInsumo.equipo_id == equipo.id,
            EquipoInsumo.fecha_desasociacion.is_(None),
        )
        .order_by(EquipoInsumo.fecha_asociacion.desc())
    )
    insumos_pagination = insumos_query.paginate(
        page=insumos_page, per_page=per_page, error_out=False
    )

    historial_page = request.args.get("historial_page", type=int, default=1)
    historial_query = (
        EquipoHistorial.query.options(selectinload(EquipoHistorial.usuario))
        .filter(EquipoHistorial.equipo_id == equipo.id)
        .order_by(EquipoHistorial.fecha.desc())
    )
    historial_pagination = historial_query.paginate(
        page=historial_page, per_page=per_page, error_out=False
    )

    actas_page = request.args.get("actas_page", type=int, default=1)
    actas_query = (
        Acta.query.join(Acta.items)
        .filter(ActaItem.equipo_id == equipo.id)
        .order_by(Acta.fecha.desc())
        .distinct()
    )
    actas_pagination = actas_query.paginate(
        page=actas_page, per_page=per_page, error_out=False
    )

    evidencias_page = request.args.get("evidencias_page", type=int, default=1)
    evidencias_query = (
        EquipoAdjunto.query.filter(EquipoAdjunto.equipo_id == equipo.id)
        .order_by(EquipoAdjunto.created_at.desc(), EquipoAdjunto.id.desc())
    )
    evidencias_pagination = evidencias_query.paginate(
        page=evidencias_page, per_page=per_page, error_out=False
    )

    return render_template(
        "equipos/detalle.html",
        equipo=equipo,
        insumos_pagination=insumos_pagination,
        historial_pagination=historial_pagination,
        actas_pagination=actas_pagination,
        evidencias_pagination=evidencias_pagination,
        adjunto_form=form_adjuntos,
        tipos_acta=list(TipoActa),
        max_upload_size=current_app.config.get("EQUIPOS_MAX_FILE_SIZE", 10 * 1024 * 1024),
    )


@equipos_bp.post("/<int:equipo_id>/insumos/asociar")
@login_required
@permissions_required("inventario:write")
@require_hospital_access(Modulo.INVENTARIO)
def asociar_insumo(equipo_id: int):
    equipo = Equipo.query.get_or_404(equipo_id)
    payload = request.get_json(silent=True) or {}
    nro_serie = (payload.get("nro_serie") or "").strip()
    if not nro_serie:
        return jsonify({"ok": False, "message": "Debe indicar número de serie"}), 400

    serie = InsumoSerie.query.filter_by(nro_serie=nro_serie).first()
    if not serie:
        return jsonify({"ok": False, "message": "No existe un insumo con ese número de serie"}), 404

    if serie.estado != SerieEstado.LIBRE or serie.equipo_id is not None:
        return jsonify({"ok": False, "message": "La serie ya está asignada"}), 409

    insumo = serie.insumo
    if not insumo:
        return jsonify({"ok": False, "message": "El insumo asociado no es válido"}), 409

    if insumo.stock <= 0:
        return jsonify({"ok": False, "message": "Sin stock disponible de este insumo"}), 409

    existente = (
        EquipoInsumo.query.filter_by(insumo_serie_id=serie.id, fecha_desasociacion=None)
        .order_by(EquipoInsumo.fecha_asociacion.desc())
        .first()
    )
    if existente:
        return jsonify({"ok": False, "message": "La serie ya está asignada"}), 409

    serie.estado = SerieEstado.ASIGNADO
    serie.equipo_id = equipo.id
    insumo.ajustar_stock(-1)

    asignacion = EquipoInsumo(
        equipo=equipo,
        insumo=insumo,
        serie=serie,
        asociado_por=current_user if getattr(current_user, "is_authenticated", False) else None,
    )
    movimiento = InsumoMovimiento(
        insumo=insumo,
        usuario=current_user if getattr(current_user, "is_authenticated", False) else None,
        equipo_id=equipo.id,
        tipo=MovimientoTipo.EGRESO,
        cantidad=1,
        motivo="Asignación a equipo",
    )
    db.session.add(asignacion)
    db.session.add(movimiento)
    equipo.registrar_evento(
        current_user,
        "Asociación de insumo",
        f"{insumo.nombre} · {serie.nro_serie}",
    )
    db.session.flush()
    db.session.commit()

    respuesta = {
        "ok": True,
        "message": "Insumo asociado",
        "asociacion": {
            "id": asignacion.id,
            "insumo": {"id": insumo.id, "nombre": insumo.nombre},
            "serie": {"id": serie.id, "nro_serie": serie.nro_serie},
            "fecha_asociacion": asignacion.fecha_asociacion.isoformat()
            if asignacion.fecha_asociacion
            else None,
            "asociado_por": asignacion.asociado_por.nombre if asignacion.asociado_por else None,
        },
    }
    return jsonify(respuesta), 201


@equipos_bp.post("/<int:equipo_id>/insumos/quitar")
@login_required
@permissions_required("inventario:write")
@require_hospital_access(Modulo.INVENTARIO)
def quitar_insumo(equipo_id: int):
    equipo = Equipo.query.get_or_404(equipo_id)
    payload = request.get_json(silent=True) or {}
    serie_id = payload.get("insumo_serie_id")
    if not serie_id:
        return jsonify({"ok": False, "message": "Debe indicar insumo_serie_id"}), 400

    try:
        serie_id_int = int(serie_id)
    except (TypeError, ValueError):
        return jsonify({"ok": False, "message": "Identificador de serie inválido"}), 400

    serie = (
        InsumoSerie.query.filter_by(id=serie_id_int, equipo_id=equipo.id)
        .options(selectinload(InsumoSerie.insumo))
        .first()
    )
    if not serie:
        return jsonify({"ok": False, "message": "La serie no está asociada a este equipo"}), 404

    asignacion = (
        EquipoInsumo.query.filter_by(
            equipo_id=equipo.id, insumo_serie_id=serie.id, fecha_desasociacion=None
        )
        .order_by(EquipoInsumo.fecha_asociacion.desc())
        .first()
    )
    if not asignacion:
        return jsonify({"ok": False, "message": "No se encontró la asociación activa"}), 404

    insumo = serie.insumo
    serie.estado = SerieEstado.LIBRE
    serie.equipo_id = None
    insumo.ajustar_stock(1)
    asignacion.fecha_desasociacion = func.now()

    movimiento = InsumoMovimiento(
        insumo=insumo,
        usuario=current_user if getattr(current_user, "is_authenticated", False) else None,
        equipo_id=equipo.id,
        tipo=MovimientoTipo.INGRESO,
        cantidad=1,
        motivo="Desasociación de equipo",
    )
    db.session.add(movimiento)
    equipo.registrar_evento(
        current_user,
        "Desasociación de insumo",
        f"{insumo.nombre} · {serie.nro_serie}",
    )
    db.session.commit()

    return jsonify(
        {
            "ok": True,
            "message": "Insumo removido",
            "serie_id": serie.id,
            "nro_serie": serie.nro_serie,
        }
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
    directory = equipment_upload_dir(equipo.id)
    storage_path = directory / unique_name
    file.save(storage_path)

    if (file.mimetype or "").startswith("image/"):
        generate_image_thumbnail(storage_path)

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


@equipos_bp.route("/tipos", methods=["GET", "POST"])
@login_required
@require_roles("admin", "superadmin")
def gestionar_tipos():
    """Allow superadministrators to create and maintain equipment types."""

    create_form = TipoEquipoCreateForm(prefix="nuevo")
    if create_form.validate_on_submit():
        nuevo = TipoEquipo(
            nombre=(create_form.nombre.data or "").strip(),
            descripcion=(create_form.descripcion.data or "").strip() or None,
            activo=bool(create_form.activo.data),
        )
        db.session.add(nuevo)
        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            create_form.nombre.errors.append("Ya existe un tipo con ese nombre")
        else:
            flash("Tipo de equipo agregado", "success")
            return redirect(url_for("equipos.gestionar_tipos"))

    tipos = (
        TipoEquipo.query.order_by(TipoEquipo.activo.desc(), TipoEquipo.nombre.asc())
        .all()
    )
    tipo_ids = [tipo.id for tipo in tipos]
    equipos_por_tipo: dict[int, int] = {}
    if tipo_ids:
        resultados = (
            db.session.query(Equipo.tipo_id, func.count(Equipo.id))
            .filter(Equipo.tipo_id.in_(tipo_ids))
            .group_by(Equipo.tipo_id)
            .all()
        )
        equipos_por_tipo = {tipo_id: total for tipo_id, total in resultados}

    update_forms = []
    for tipo in tipos:
        form = TipoEquipoUpdateForm(prefix=f"tipo-{tipo.id}")
        form.tipo_id.data = str(tipo.id)
        form.nombre.data = tipo.nombre
        form.descripcion.data = tipo.descripcion
        form.activo.data = tipo.activo
        delete_form = TipoEquipoDeleteForm(prefix=f"delete-{tipo.id}")
        delete_form.tipo_id.data = str(tipo.id)
        has_equipos = equipos_por_tipo.get(tipo.id, 0) > 0
        update_forms.append((tipo, form, delete_form, has_equipos))

    return render_template(
        "equipos/tipos.html",
        create_form=create_form,
        update_forms=update_forms,
        tipos=tipos,
    )


@equipos_bp.route("/tipos/<int:tipo_id>", methods=["POST"])
@login_required
@require_roles("admin", "superadmin")
def actualizar_tipo(tipo_id: int):
    """Persist updates to an equipment type."""

    tipo = TipoEquipo.query.get_or_404(tipo_id)
    form = TipoEquipoUpdateForm(prefix=f"tipo-{tipo_id}")
    if not form.validate_on_submit():
        for errors in form.errors.values():
            for message in errors:
                flash(message, "danger")
        return redirect(url_for("equipos.gestionar_tipos"))

    try:
        submitted_id = int(form.tipo_id.data)
    except (TypeError, ValueError):
        flash("Identificador inválido", "danger")
        return redirect(url_for("equipos.gestionar_tipos"))

    if submitted_id != tipo_id:
        flash("El identificador enviado no coincide", "danger")
        return redirect(url_for("equipos.gestionar_tipos"))

    tipo.nombre = (form.nombre.data or "").strip()
    tipo.descripcion = (form.descripcion.data or "").strip() or None
    tipo.activo = bool(form.activo.data)
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        flash("Ya existe un tipo con ese nombre", "danger")
    else:
        flash("Tipo de equipo actualizado", "success")
    return redirect(url_for("equipos.gestionar_tipos"))


@equipos_bp.route("/tipos/<int:tipo_id>/eliminar", methods=["POST"])
@login_required
@require_roles("admin", "superadmin")
def eliminar_tipo(tipo_id: int):
    """Remove an equipment type when it has no associated equipment."""

    tipo = TipoEquipo.query.get_or_404(tipo_id)
    form = TipoEquipoDeleteForm(prefix=f"delete-{tipo_id}")
    if not form.validate_on_submit():
        for errors in form.errors.values():
            for message in errors:
                flash(message, "danger")
        return redirect(url_for("equipos.gestionar_tipos"))

    try:
        submitted_id = int(form.tipo_id.data)
    except (TypeError, ValueError):
        flash("Identificador inválido", "danger")
        return redirect(url_for("equipos.gestionar_tipos"))

    if submitted_id != tipo_id:
        flash("El identificador enviado no coincide", "danger")
        return redirect(url_for("equipos.gestionar_tipos"))

    asociado = Equipo.query.filter(Equipo.tipo_id == tipo_id).first()
    if asociado is not None:
        flash("No se puede eliminar el tipo porque tiene equipos asociados", "danger")
        return redirect(url_for("equipos.gestionar_tipos"))

    db.session.delete(tipo)
    db.session.commit()
    flash("Tipo de equipo eliminado", "success")
    return redirect(url_for("equipos.gestionar_tipos"))
