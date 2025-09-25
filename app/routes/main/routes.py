"""Main blueprint containing dashboard views."""
from __future__ import annotations

from flask import Blueprint, abort, flash, jsonify, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from app.extensions import db
from app.forms.usuario import PerfilForm
from app.models.usuario import ThemePreference
from app.services.dashboard_service import collect_dashboard_metrics, collect_license_history

main_bp = Blueprint("main", __name__)


@main_bp.route("/")
@login_required
def index() -> str:
    metrics = collect_dashboard_metrics(current_user)
    licencias_chart = collect_license_history(current_user)
    return render_template("main/index.html", metrics=metrics, licencias_chart=licencias_chart)


@main_bp.route("/dashboard")
@login_required
def dashboard() -> str:
    metrics = collect_dashboard_metrics(current_user)
    licencias_chart = collect_license_history(current_user)

    role_template = {
        "superadmin": "main/dashboard_superadmin.html",
        "admin": "main/dashboard_admin.html",
        "tecnico": "main/dashboard_tecnico.html",
    }
    template = role_template.get((current_user.role or "").lower(), "main/dashboard_tecnico.html")

    return render_template(template, metrics=metrics, licencias_chart=licencias_chart)


@main_bp.route("/perfil", methods=["GET", "POST"])
@login_required
def perfil() -> str:
    form = PerfilForm(current_user, obj=current_user)
    if form.validate_on_submit():
        current_user.nombre = form.nombre.data.strip()
        current_user.apellido = (form.apellido.data or "").strip() or None
        current_user.email = form.email.data.strip().lower()
        current_user.telefono = (form.telefono.data or "").strip() or None
        if form.password.data:
            current_user.set_password(form.password.data)
        db.session.commit()
        flash("Perfil actualizado correctamente", "success")
        return redirect(url_for("main.perfil"))
    if request.method == "GET":
        form.nombre.data = current_user.nombre
        form.apellido.data = current_user.apellido
        form.email.data = current_user.email
        form.telefono.data = current_user.telefono
    return render_template("usuarios/perfil.html", form=form)


@main_bp.post("/preferencias/tema")
@login_required
def actualizar_tema() -> str:
    payload = request.get_json(silent=True) or {}
    theme = payload.get("theme")
    valid_values = {pref.value for pref in ThemePreference}
    if theme not in valid_values:
        abort(400, description="Preferencia de tema inválida")

    current_user.theme_pref = ThemePreference(theme)
    db.session.commit()
    return jsonify({"status": "ok", "theme": theme})
