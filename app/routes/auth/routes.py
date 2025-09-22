"""Authentication blueprint."""
from __future__ import annotations

from datetime import datetime

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required, login_user, logout_user

from app.extensions import db
from app.forms.login import LoginForm
from app.models import Usuario
from app.services.audit_service import log_action
from app.services.licencia_service import usuario_con_licencia_activa


auth_bp = Blueprint("auth", __name__, url_prefix="/auth")


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("main.index"))

    form = LoginForm()
    if form.validate_on_submit():
        usuario = Usuario.query.filter_by(username=form.username.data).first()
        if not usuario or not usuario.check_password(form.password.data):
            flash("Usuario o contraseña inválidos", "danger")
        elif not usuario.activo:
            flash("El usuario se encuentra inactivo", "warning")
        elif usuario_con_licencia_activa(usuario.id):
            flash("Acceso denegado: licencia aprobada activa", "danger")
        else:
            login_user(usuario)
            usuario.ultimo_login = datetime.utcnow()
            db.session.commit()
            log_action(usuario_id=usuario.id, accion="login", modulo="auth")
            next_page = request.args.get("next")
            return redirect(next_page or url_for("main.index"))
    return render_template("auth/login.html", form=form)


@auth_bp.route("/logout")
@login_required
def logout():
    usuario_id = current_user.id
    logout_user()
    if usuario_id:
        log_action(usuario_id=usuario_id, accion="logout", modulo="auth")
    return redirect(url_for("auth.login"))


@auth_bp.before_app_request
def validar_licencia():
    if not current_user.is_authenticated:
        return None
    if usuario_con_licencia_activa(current_user.id):
        flash("Acceso denegado: licencia aprobada activa", "danger")
        logout_user()
        return redirect(url_for("auth.login"))
    return None
