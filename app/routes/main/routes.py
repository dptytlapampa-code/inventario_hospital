"""Main blueprint containing dashboard views."""
from __future__ import annotations

from datetime import date

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from app.extensions import db
from app.forms.usuario import PerfilForm
from app.models import Equipo, EstadoEquipo, EstadoLicencia, Hospital, Insumo, Licencia

main_bp = Blueprint("main", __name__)


@main_bp.route("/")
@login_required
def index() -> str:
    equipos_total = db.session.query(Equipo).count()
    insumos_total = db.session.query(Insumo).count()
    hospitales_total = db.session.query(Hospital).count()
    licencias_pendientes = (
        db.session.query(Licencia)
        .filter(Licencia.estado == EstadoLicencia.PENDIENTE)
        .count()
    )

    low_stock = (
        db.session.query(Insumo)
        .filter(Insumo.stock_minimo > 0)
        .filter(Insumo.stock <= Insumo.stock_minimo)
        .order_by(Insumo.nombre)
        .all()
    )

    notices = [
        {
            "titulo": "Licencias pendientes",
            "detalle": f"{licencias_pendientes} solicitudes esperan aprobación",
            "fecha": date.today(),
        }
    ]

    return render_template(
        "main/index.html",
        stats={
            "equipos": equipos_total,
            "insumos": insumos_total,
            "hospitales": hospitales_total,
            "licencias_pendientes": licencias_pendientes,
        },
        low_stock=low_stock,
        notices=notices,
    )


@main_bp.route("/dashboard")
@login_required
def dashboard() -> str:
    equipos_por_estado = (
        db.session.query(Equipo.estado, db.func.count(Equipo.id))
        .group_by(Equipo.estado)
        .all()
    )
    chart_data = {
        "labels": [estado.value.replace("_", " ").title() for estado, _ in equipos_por_estado],
        "values": [count for _, count in equipos_por_estado],
    }

    licencias_por_mes: dict[str, int] = {}
    for licencia in Licencia.query.filter(Licencia.estado == EstadoLicencia.APROBADA):
        key = licencia.fecha_inicio.strftime("%Y-%m")
        licencias_por_mes[key] = licencias_por_mes.get(key, 0) + 1
    labels = sorted(licencias_por_mes.keys())
    licencias_chart = {"labels": labels, "values": [licencias_por_mes[label] for label in labels]}

    return render_template("main/dashboard.html", chart_data=chart_data, licencias_chart=licencias_chart)


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
