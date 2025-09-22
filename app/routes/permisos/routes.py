"""Routes to manage role permissions."""
from __future__ import annotations

from flask import Blueprint, current_app, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required
from sqlalchemy import or_

from app.extensions import db
from app.forms.permisos import PermisoForm
from app.models import Hospital, Modulo, Permiso, Rol
from app.security import permissions_required
from app.services.audit_service import log_action

permisos_bp = Blueprint("permisos", __name__, url_prefix="/permisos")


def _require_superadmin():
    if not current_user.has_role("Superadmin"):
        flash("Solo el Superadmin puede modificar permisos", "warning")
        return False
    return True


@permisos_bp.route("/")
@login_required
@permissions_required("auditoria:read")
def listar():
    page = request.args.get("page", type=int, default=1)
    per_page = current_app.config.get("DEFAULT_PAGE_SIZE", 20)
    buscar = request.args.get("q", "")

    query = Permiso.query.order_by(Permiso.rol_id, Permiso.modulo)
    if buscar:
        like = f"%{buscar}%"
        query = query.filter(
            or_(
                Permiso.modulo.ilike(like),
                Permiso.rol.has(Rol.nombre.ilike(like)),
                Permiso.hospital.has(Hospital.nombre.ilike(like)),
            )
        )
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    return render_template(
        "permisos/listar.html",
        permisos=pagination.items,
        pagination=pagination,
        buscar=buscar,
    )


@permisos_bp.route("/crear", methods=["GET", "POST"])
@login_required
@permissions_required("auditoria:write")
def crear():
    if not _require_superadmin():
        return redirect(url_for("permisos.listar"))
    form = PermisoForm()
    if form.validate_on_submit():
        permiso = Permiso(
            rol_id=form.rol_id.data,
            modulo=Modulo(form.modulo.data),
            hospital_id=form.hospital_id.data or None,
            can_read=form.can_read.data,
            can_write=form.can_write.data,
            allow_export=form.allow_export.data,
        )
        db.session.add(permiso)
        db.session.commit()
        log_action(usuario_id=current_user.id, accion="crear", modulo="permisos", tabla="permisos", registro_id=permiso.id)
        flash("Permiso creado", "success")
        return redirect(url_for("permisos.listar"))
    return render_template("permisos/formulario.html", form=form, titulo="Nuevo permiso")


@permisos_bp.route("/<int:permiso_id>/editar", methods=["GET", "POST"])
@login_required
@permissions_required("auditoria:write")
def editar(permiso_id: int):
    if not _require_superadmin():
        return redirect(url_for("permisos.listar"))
    permiso = Permiso.query.get_or_404(permiso_id)
    form = PermisoForm(obj=permiso)
    if form.validate_on_submit():
        permiso.rol_id = form.rol_id.data
        permiso.modulo = Modulo(form.modulo.data)
        permiso.hospital_id = form.hospital_id.data or None
        permiso.can_read = form.can_read.data
        permiso.can_write = form.can_write.data
        permiso.allow_export = form.allow_export.data
        db.session.commit()
        log_action(usuario_id=current_user.id, accion="editar", modulo="permisos", tabla="permisos", registro_id=permiso.id)
        flash("Permiso actualizado", "success")
        return redirect(url_for("permisos.listar"))
    return render_template("permisos/formulario.html", form=form, titulo="Editar permiso", permiso=permiso)
