"""Blueprint for consumable management."""
from __future__ import annotations

from flask import Blueprint, current_app, flash, g, jsonify, redirect, render_template, request, url_for
from flask_login import current_user, login_required
from sqlalchemy import or_

from app.extensions import db
from app.forms.insumo import InsumoForm, MovimientoForm
from app.models import Equipo, Insumo, InsumoSerie, MovimientoTipo, Modulo, SerieEstado
from app.security import permissions_required, require_hospital_access
from app.services import insumo_service
from app.services.audit_service import log_action
from app.services.equipo_service import equipment_options_for_ids

insumos_bp = Blueprint("insumos", __name__, url_prefix="/insumos")


def _paginar(query, page, per_page):
    return query.paginate(page=page, per_page=per_page, error_out=False)


@insumos_bp.route("/")
@login_required
@permissions_required("insumos:read")
@require_hospital_access(Modulo.INSUMOS)
def listar():
    page = request.args.get("page", type=int, default=1)
    per_page = current_app.config.get("DEFAULT_PAGE_SIZE", 20)
    buscar = request.args.get("q", "")
    criticos = request.args.get("criticos", type=int)

    query = Insumo.query.order_by(Insumo.nombre)
    allowed = getattr(g, "allowed_hospitals", set())
    if allowed:
        query = (
            query.outerjoin(Insumo.equipos)
            .filter(or_(Equipo.hospital_id.in_(allowed), Equipo.id.is_(None)))
            .distinct()
        )
    if buscar:
        like = f"%{buscar}%"
        query = query.filter(
            or_(
                Insumo.nombre.ilike(like),
                Insumo.numero_serie.ilike(like),
                Insumo.descripcion.ilike(like),
            )
        )

    if criticos:
        query = query.filter(
            Insumo.stock_minimo > 0,
            Insumo.stock <= Insumo.stock_minimo,
        )

    pagination = _paginar(query, page, per_page)
    return render_template(
        "insumos/listar.html",
        insumos=pagination.items,
        pagination=pagination,
        buscar=buscar,
        criticos=bool(criticos),
    )


@insumos_bp.route("/crear", methods=["GET", "POST"])
@login_required
@permissions_required("insumos:write")
@require_hospital_access(Modulo.INSUMOS)
def crear():
    form = InsumoForm()
    if form.validate_on_submit():
        insumo = Insumo(
            nombre=form.nombre.data,
            numero_serie=form.numero_serie.data or None,
            descripcion=form.descripcion.data or None,
            unidad_medida=form.unidad_medida.data or None,
            stock=form.stock.data,
            stock_minimo=form.stock_minimo.data or 0,
            costo_unitario=form.costo_unitario.data,
        )
        db.session.add(insumo)
        db.session.flush()
        db.session.commit()
        flash("Insumo creado", "success")
        log_action(usuario_id=current_user.id, accion="crear", modulo="insumos", tabla="insumos", registro_id=insumo.id)
        return redirect(url_for("insumos.listar"))
    return render_template(
        "insumos/formulario.html",
        form=form,
        titulo="Nuevo insumo",
    )


@insumos_bp.route("/<int:insumo_id>/editar", methods=["GET", "POST"])
@login_required
@permissions_required("insumos:write")
@require_hospital_access(Modulo.INSUMOS)
def editar(insumo_id: int):
    insumo = Insumo.query.get_or_404(insumo_id)
    form = InsumoForm(obj=insumo)
    if form.validate_on_submit():
        insumo.nombre = form.nombre.data
        insumo.numero_serie = form.numero_serie.data or None
        insumo.descripcion = form.descripcion.data or None
        insumo.unidad_medida = form.unidad_medida.data or None
        insumo.stock = form.stock.data
        insumo.stock_minimo = form.stock_minimo.data or 0
        insumo.costo_unitario = form.costo_unitario.data
        db.session.commit()
        log_action(usuario_id=current_user.id, accion="editar", modulo="insumos", tabla="insumos", registro_id=insumo.id)
        flash("Insumo actualizado", "success")
        return redirect(url_for("insumos.detalle", insumo_id=insumo.id))
    return render_template(
        "insumos/formulario.html",
        form=form,
        titulo="Editar insumo",
        insumo=insumo,
    )


@insumos_bp.get("/series")
@login_required
@permissions_required("inventario:write")
def series_disponibles():
    query = (request.args.get("q") or "").strip()
    limit = request.args.get("limit", type=int) or 10
    limit = max(1, min(limit, 20))

    base_query = (
        InsumoSerie.query.join(Insumo, Insumo.id == InsumoSerie.insumo_id)
        .filter(InsumoSerie.estado == SerieEstado.LIBRE)
        .order_by(InsumoSerie.nro_serie.asc())
    )
    if query:
        like = f"%{query}%"
        base_query = base_query.filter(
            or_(
                InsumoSerie.nro_serie.ilike(like),
                Insumo.nombre.ilike(like),
            )
        )

    series = base_query.limit(limit).all()
    items = [
        {
            "id": serie.nro_serie,
            "text": f"{serie.nro_serie} · {serie.insumo.nombre if serie.insumo else ''}".strip(),
            "serie_id": serie.id,
            "insumo_id": serie.insumo_id,
        }
        for serie in series
    ]
    return jsonify({"items": items})


@insumos_bp.route("/<int:insumo_id>")
@login_required
@permissions_required("insumos:read")
@require_hospital_access(Modulo.INSUMOS)
def detalle(insumo_id: int):
    insumo = Insumo.query.get_or_404(insumo_id)
    movimiento_form = MovimientoForm()
    return render_template(
        "insumos/detalle.html",
        insumo=insumo,
        movimientos=insumo.movimientos[-20:],
        movimiento_form=movimiento_form,
        movimiento_equipo_options=equipment_options_for_ids([
            movimiento_form.equipo_id.data
        ]),
    )


@insumos_bp.route("/<int:insumo_id>/movimiento", methods=["POST"])
@login_required
@permissions_required("insumos:write")
@require_hospital_access(Modulo.INSUMOS)
def registrar_movimiento(insumo_id: int):
    insumo = Insumo.query.get_or_404(insumo_id)
    form = MovimientoForm()
    if form.validate_on_submit():
        equipo_id = form.equipo_id.data or None
        movimiento = insumo_service.registrar_movimiento(
            insumo=insumo,
            tipo=MovimientoTipo(form.tipo.data),
            cantidad=form.cantidad.data,
            usuario=current_user,
            equipo_id=equipo_id,
            motivo=form.motivo.data,
            observaciones=form.observaciones.data,
        )
        log_action(
            usuario_id=current_user.id,
            accion="movimiento",
            modulo="insumos",
            tabla="insumo_movimientos",
            registro_id=movimiento.id,
        )
        flash("Movimiento registrado", "success")
    else:
        flash("No se pudo registrar el movimiento", "danger")
    return redirect(url_for("insumos.detalle", insumo_id=insumo.id))
