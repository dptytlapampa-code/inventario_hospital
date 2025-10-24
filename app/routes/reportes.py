"""Vistas para la exportación de datos en Excel."""

from __future__ import annotations

from flask import Blueprint, abort, render_template, request, send_file
from flask_login import login_required

from app.models import Hospital
from app.security import require_roles
from app.services.reportes_service import generar_reporte_excel


reportes_bp = Blueprint("reportes", __name__, url_prefix="/reportes")


@reportes_bp.get("/exportar")
@login_required
@require_roles("superadmin")
def exportar() -> str:
    hospitales = Hospital.query.order_by(Hospital.nombre.asc()).all()
    selected_id = request.args.get("hospital_id", type=int)
    return render_template(
        "reportes/exportar.html",
        hospitales=hospitales,
        selected_id=selected_id,
    )


@reportes_bp.get("/exportar/descargar")
@login_required
@require_roles("superadmin")
def descargar():
    hospital_id = request.args.get("hospital_id", type=int)
    if hospital_id:
        hospital = Hospital.query.get(hospital_id)
        if not hospital:
            abort(404)
    stream, filename = generar_reporte_excel(hospital_id=hospital_id)
    return send_file(
        stream,
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        as_attachment=True,
        download_name=filename,
        max_age=0,
    )


__all__ = ["reportes_bp"]
