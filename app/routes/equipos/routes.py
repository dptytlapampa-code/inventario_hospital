"""Blueprint managing equipment inventory."""
from __future__ import annotations

from flask import Blueprint, current_app, flash, g, redirect, render_template, request, url_for
from flask_login import current_user, login_required
from sqlalchemy import or_

from app.extensions import db
from app.forms.equipo import EquipoFiltroForm, EquipoForm
from app.models import Equipo, EstadoEquipo, Insumo, Modulo
from app.security import permissions_required, require_hospital_access
from app.services.audit_service import log_action


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


def _asignar_insumos(equipo: Equipo, insumo_ids: list[int]) -> None:
    equipo.insumos.clear()
    if insumo_ids:
        insumos = Insumo.query.filter(Insumo.id.in_(insumo_ids)).all()
        equipo.insumos.extend(insumos)


@equipos_bp.route("/crear", methods=["GET", "POST"])
@login_required
@permissions_required("inventario:write")
@require_hospital_access(Modulo.INVENTARIO)
def crear():
    form = EquipoForm()
    if form.validate_on_submit():
        equipo = Equipo(
            codigo=form.codigo.data or None,
            tipo=form.tipo.data,
            estado=form.estado.data,
            descripcion=form.descripcion.data or None,
            marca=form.marca.data or None,
            modelo=form.modelo.data or None,
            numero_serie=form.numero_serie.data or None,
            hospital_id=form.hospital_id.data,
            servicio_id=form.servicio_id.data or None,
            oficina_id=form.oficina_id.data or None,
            responsable=form.responsable.data or None,
            fecha_compra=form.fecha_compra.data,
            fecha_instalacion=form.fecha_instalacion.data,
            garantia_hasta=form.garantia_hasta.data,
            observaciones=form.observaciones.data or None,
        )
        _asignar_insumos(equipo, [int(i) for i in form.insumos.data])
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
        form.insumos.data = [insumo.id for insumo in equipo.insumos]
        form._preload_selected_insumos()
    if form.validate_on_submit():
        equipo.codigo = form.codigo.data or None
        equipo.tipo = form.tipo.data
        equipo.estado = form.estado.data
        equipo.descripcion = form.descripcion.data or None
        equipo.marca = form.marca.data or None
        equipo.modelo = form.modelo.data or None
        equipo.numero_serie = form.numero_serie.data or None
        equipo.hospital_id = form.hospital_id.data
        equipo.servicio_id = form.servicio_id.data or None
        equipo.oficina_id = form.oficina_id.data or None
        equipo.responsable = form.responsable.data or None
        equipo.fecha_compra = form.fecha_compra.data
        equipo.fecha_instalacion = form.fecha_instalacion.data
        equipo.garantia_hasta = form.garantia_hasta.data
        equipo.observaciones = form.observaciones.data or None
        _asignar_insumos(equipo, [int(i) for i in form.insumos.data])
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
    return render_template(
        "equipos/detalle.html",
        equipo=equipo,
        historial=equipo.historial[-10:],
        actas=[item.acta for item in equipo.acta_items],
        adjuntos=equipo.adjuntos,
        insumos=equipo.insumos,
    )
