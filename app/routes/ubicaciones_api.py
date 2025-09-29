"""JSON endpoints providing dependent location options."""
from __future__ import annotations

from flask import Blueprint, jsonify, request
from flask_login import login_required

from app.models import Oficina, Servicio

ubicaciones_api_bp = Blueprint(
    "ubicaciones_api", __name__, url_prefix="/api/ubicaciones"
)


@ubicaciones_api_bp.route("/servicios")
@login_required
def obtener_servicios() -> tuple[object, int] | object:
    """Return the services available for a given hospital."""

    hospital_id = request.args.get("hospital_id", type=int)
    if hospital_id is None:
        return jsonify({"error": "hospital_id requerido"}), 400

    servicios = (
        Servicio.query.filter_by(hospital_id=hospital_id)
        .order_by(Servicio.nombre.asc())
        .with_entities(Servicio.id, Servicio.nombre)
        .all()
    )
    payload = [
        {"id": servicio.id, "nombre": servicio.nombre}
        for servicio in servicios
    ]
    return jsonify(payload)


@ubicaciones_api_bp.route("/oficinas")
@login_required
def obtener_oficinas() -> tuple[object, int] | object:
    """Return the offices available for a given service."""

    servicio_id = request.args.get("servicio_id", type=int)
    if servicio_id is None:
        return jsonify({"error": "servicio_id requerido"}), 400

    oficinas = (
        Oficina.query.filter_by(servicio_id=servicio_id)
        .order_by(Oficina.nombre.asc())
        .with_entities(Oficina.id, Oficina.nombre)
        .all()
    )
    payload = [
        {"id": oficina.id, "nombre": oficina.nombre}
        for oficina in oficinas
    ]
    return jsonify(payload)


__all__ = ["ubicaciones_api_bp"]
