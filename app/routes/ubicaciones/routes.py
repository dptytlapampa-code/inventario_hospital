"""Routes to manage hospitals, services and offices."""
from __future__ import annotations

from flask import Blueprint, current_app, flash, redirect, render_template, request, url_for
from flask_login import login_required
from sqlalchemy.orm import selectinload

from app.extensions import db
from app.forms.hospital import HospitalForm, OficinaForm, ServicioForm
from app.models import Hospital, Oficina, Servicio
from app.security import permissions_required
from app.services.audit_service import log_action

ubicaciones_bp = Blueprint("ubicaciones", __name__, url_prefix="/ubicaciones")


@ubicaciones_bp.route("/")
@login_required
@permissions_required("inventario:read")
def listar():
    page = request.args.get("page", type=int, default=1)
    per_page = current_app.config.get("DEFAULT_PAGE_SIZE", 20)
    buscar = request.args.get("q", "")

    query = Hospital.query.options(
        selectinload(Hospital.servicios).selectinload(Servicio.oficinas)
    ).order_by(Hospital.nombre)
    if buscar:
        like = f"%{buscar}%"
        query = query.filter(Hospital.nombre.ilike(like))

    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    return render_template(
        "ubicaciones/listar.html",
        hospitales=pagination.items,
        pagination=pagination,
        buscar=buscar,
    )


@ubicaciones_bp.route("/hospital/crear", methods=["GET", "POST"])
@login_required
@permissions_required("inventario:write")
def crear_hospital():
    form = HospitalForm()
    if form.validate_on_submit():
        hospital = Hospital(
            nombre=form.nombre.data,
            codigo=form.codigo.data or None,
            direccion=form.direccion.data or None,
            telefono=form.telefono.data or None,
        )
        db.session.add(hospital)
        db.session.commit()
        log_action(usuario_id=None, accion="crear", modulo="ubicaciones", tabla="hospitales", registro_id=hospital.id)
        flash("Hospital creado", "success")
        return redirect(url_for("ubicaciones.listar"))
    return render_template("ubicaciones/formulario.html", form=form, titulo="Nuevo hospital")


@ubicaciones_bp.route("/hospital/<int:hospital_id>/editar", methods=["GET", "POST"])
@login_required
@permissions_required("inventario:write")
def editar_hospital(hospital_id: int):
    hospital = Hospital.query.get_or_404(hospital_id)
    form = HospitalForm(obj=hospital)
    if form.validate_on_submit():
        hospital.nombre = form.nombre.data
        hospital.codigo = form.codigo.data or None
        hospital.direccion = form.direccion.data or None
        hospital.telefono = form.telefono.data or None
        db.session.commit()
        flash("Hospital actualizado", "success")
        return redirect(url_for("ubicaciones.listar"))
    return render_template("ubicaciones/formulario.html", form=form, titulo="Editar hospital", hospital=hospital)


@ubicaciones_bp.route("/servicio/crear", methods=["GET", "POST"])
@login_required
@permissions_required("inventario:write")
def crear_servicio():
    form = ServicioForm()
    if form.validate_on_submit():
        servicio = Servicio(
            nombre=form.nombre.data,
            descripcion=form.descripcion.data or None,
            hospital_id=form.hospital_id.data,
        )
        db.session.add(servicio)
        db.session.commit()
        flash("Servicio creado", "success")
        return redirect(url_for("ubicaciones.listar"))
    return render_template("ubicaciones/formulario.html", form=form, titulo="Nuevo servicio")


@ubicaciones_bp.route("/servicio/<int:servicio_id>/editar", methods=["GET", "POST"])
@login_required
@permissions_required("inventario:write")
def editar_servicio(servicio_id: int):
    servicio = Servicio.query.get_or_404(servicio_id)
    form = ServicioForm(obj=servicio)
    if form.validate_on_submit():
        servicio.nombre = form.nombre.data
        servicio.descripcion = form.descripcion.data or None
        servicio.hospital_id = form.hospital_id.data
        db.session.commit()
        flash("Servicio actualizado", "success")
        return redirect(url_for("ubicaciones.listar"))
    return render_template("ubicaciones/formulario.html", form=form, titulo="Editar servicio", servicio=servicio)


@ubicaciones_bp.route("/oficina/crear", methods=["GET", "POST"])
@login_required
@permissions_required("inventario:write")
def crear_oficina():
    form = OficinaForm()
    if form.validate_on_submit():
        servicio = Servicio.query.get(form.servicio_id.data)
        oficina = Oficina(
            nombre=form.nombre.data,
            piso=form.piso.data or None,
            servicio_id=form.servicio_id.data,
            hospital_id=servicio.hospital_id if servicio else None,
        )
        db.session.add(oficina)
        db.session.commit()
        flash("Oficina creada", "success")
        return redirect(url_for("ubicaciones.listar"))
    return render_template("ubicaciones/formulario.html", form=form, titulo="Nueva oficina")


@ubicaciones_bp.route("/oficina/<int:oficina_id>/editar", methods=["GET", "POST"])
@login_required
@permissions_required("inventario:write")
def editar_oficina(oficina_id: int):
    oficina = Oficina.query.get_or_404(oficina_id)
    form = OficinaForm(obj=oficina)
    if form.validate_on_submit():
        oficina.nombre = form.nombre.data
        oficina.piso = form.piso.data or None
        oficina.servicio_id = form.servicio_id.data
        servicio = Servicio.query.get(form.servicio_id.data)
        oficina.hospital_id = servicio.hospital_id if servicio else oficina.hospital_id
        db.session.commit()
        flash("Oficina actualizada", "success")
        return redirect(url_for("ubicaciones.listar"))
    return render_template("ubicaciones/formulario.html", form=form, titulo="Editar oficina", oficina=oficina)
