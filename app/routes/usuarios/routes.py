"""Gestión de usuarios del sistema."""
from __future__ import annotations

import secrets

from flask import (
    Blueprint,
    abort,
    current_app,
    flash,
    redirect,
    render_template,
    request,
    url_for,
)
from flask_login import current_user, login_required
from sqlalchemy import asc, or_

from app.extensions import db
from app.forms.usuario import UsuarioForm
from app.models import Rol, Usuario
from app.security import require_roles
from app.services.audit_service import log_action

usuarios_bp = Blueprint("usuarios", __name__, url_prefix="/usuarios")


def _paginate(query, page: int, per_page: int):
    return query.paginate(page=page, per_page=per_page, error_out=False)


@usuarios_bp.route("/")
@login_required
@require_roles("admin", "superadmin")
def listar():
    buscar = request.args.get("q", "").strip()
    page = request.args.get("page", type=int, default=1)
    per_page = current_app.config.get("DEFAULT_PAGE_SIZE", 20)

    query = Usuario.query.order_by(asc(Usuario.nombre))
    if buscar:
        like = f"%{buscar}%"
        query = query.filter(
            or_(
                Usuario.nombre.ilike(like),
                Usuario.apellido.ilike(like),
                Usuario.email.ilike(like),
                Usuario.username.ilike(like),
            )
        )

    pagination = _paginate(query, page, per_page)
    return render_template(
        "usuarios/listar.html",
        usuarios=pagination.items,
        pagination=pagination,
        buscar=buscar,
    )


@usuarios_bp.route("/crear", methods=["GET", "POST"])
@login_required
@require_roles("admin", "superadmin")
def crear():
    form = UsuarioForm()
    if form.validate_on_submit():
        usuario = Usuario(
            nombre=form.nombre.data.strip(),
            apellido=(form.apellido.data or "").strip() or None,
            email=form.email.data.strip().lower(),
            dni=form.dni.data.strip(),
            username=form.username.data.strip(),
            rol_id=form.rol_id.data,
            activo=form.activo.data,
        )
        usuario.set_password(form.password.data)
        db.session.add(usuario)
        db.session.commit()
        flash("Usuario creado correctamente", "success")
        log_action(usuario_id=current_user.id, accion="crear", modulo="usuarios", tabla="usuarios", registro_id=usuario.id)
        return redirect(url_for("usuarios.listar"))
    return render_template("usuarios/formulario.html", form=form, titulo="Nuevo usuario", usuario=None)


@usuarios_bp.route("/<int:usuario_id>/editar", methods=["GET", "POST"])
@login_required
@require_roles("admin", "superadmin")
def editar(usuario_id: int):
    usuario = Usuario.query.get_or_404(usuario_id)
    form = UsuarioForm(usuario=usuario, obj=usuario)
    if form.validate_on_submit():
        usuario.nombre = form.nombre.data.strip()
        usuario.apellido = (form.apellido.data or "").strip() or None
        usuario.email = form.email.data.strip().lower()
        usuario.dni = form.dni.data.strip()
        usuario.username = form.username.data.strip()
        usuario.rol_id = form.rol_id.data
        usuario.activo = form.activo.data
        if form.password.data:
            usuario.set_password(form.password.data)
        db.session.commit()
        flash("Usuario actualizado", "success")
        log_action(usuario_id=current_user.id, accion="editar", modulo="usuarios", tabla="usuarios", registro_id=usuario.id)
        return redirect(url_for("usuarios.listar"))
    return render_template("usuarios/formulario.html", form=form, titulo="Editar usuario", usuario=usuario)


@usuarios_bp.route("/<int:usuario_id>/reset_password", methods=["POST"])
@login_required
@require_roles("superadmin")
def reset_password(usuario_id: int):
    usuario = Usuario.query.get_or_404(usuario_id)
    new_password = secrets.token_urlsafe(8)
    usuario.set_password(new_password)
    db.session.commit()
    flash(f"Contraseña restablecida: {new_password}", "info")
    log_action(usuario_id=current_user.id, accion="reset_password", modulo="usuarios", tabla="usuarios", registro_id=usuario.id)
    return redirect(url_for("usuarios.editar", usuario_id=usuario.id))


@usuarios_bp.route("/<int:usuario_id>/<string:accion>", methods=["POST"])
@login_required
@require_roles("admin", "superadmin")
def cambiar_estado(usuario_id: int, accion: str):
    if accion not in {"activar", "desactivar"}:
        abort(404)
    usuario = Usuario.query.get_or_404(usuario_id)
    if usuario.id == current_user.id:
        flash("No puede cambiar su propio estado", "warning")
        return redirect(url_for("usuarios.listar"))
    if usuario.role == "superadmin" and current_user.role != "superadmin":
        flash("Solo un superadministrador puede modificar este usuario", "warning")
        return redirect(url_for("usuarios.listar"))

    usuario.activo = accion == "activar"
    db.session.commit()
    flash(
        "Usuario activado" if usuario.activo else "Usuario desactivado",
        "success" if usuario.activo else "warning",
    )
    log_action(
        usuario_id=current_user.id,
        accion=accion,
        modulo="usuarios",
        tabla="usuarios",
        registro_id=usuario.id,
    )
    return redirect(url_for("usuarios.listar"))


@usuarios_bp.route("/asignacion")
@login_required
@require_roles("admin", "superadmin")
def asignacion():
    roles = Rol.query.order_by(Rol.nombre).all()
    return render_template(
        "usuarios/asignacion.html",
        roles=roles,
        usuario=None,
    )
