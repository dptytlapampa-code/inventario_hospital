"""Asynchronous search endpoints for select widgets."""
from __future__ import annotations

from flask import jsonify, request
from flask_login import login_required
from sqlalchemy import asc

from app.models import Insumo, Oficina, Servicio

from . import api_bp

DEFAULT_PAGE_SIZE = 20
MAX_PAGE_SIZE = 50


def _sanitize_query_param() -> str:
    query = request.args.get("q", "").strip()
    return query[:80]


def _get_page_size() -> int:
    page_size = request.args.get("per_page", type=int, default=DEFAULT_PAGE_SIZE)
    return max(1, min(page_size, MAX_PAGE_SIZE))


@api_bp.route("/servicios/search")
@login_required
def search_servicios():
    query_value = _sanitize_query_param()
    page = request.args.get("page", type=int, default=1)
    per_page = _get_page_size()

    search = Servicio.query.join(Servicio.hospital).order_by(asc(Servicio.nombre))
    if query_value:
        like = f"%{query_value}%"
        search = search.filter(Servicio.nombre.ilike(like))

    pagination = search.paginate(page=page, per_page=per_page, error_out=False)
    results = [
        {
            "id": servicio.id,
            "text": f"{servicio.hospital.nombre} · {servicio.nombre}",
        }
        for servicio in pagination.items
    ]
    return jsonify({"results": results, "next": pagination.has_next})


@api_bp.route("/oficinas/search")
@login_required
def search_oficinas():
    servicio_id = request.args.get("servicio_id", type=int)
    if not servicio_id:
        return (
            jsonify({"results": [], "next": False, "message": "Seleccione un servicio para filtrar oficinas"}),
            400,
        )

    query_value = _sanitize_query_param()
    page = request.args.get("page", type=int, default=1)
    per_page = _get_page_size()

    search = Oficina.query.join(Oficina.hospital).filter(Oficina.servicio_id == servicio_id).order_by(asc(Oficina.nombre))
    if query_value:
        like = f"%{query_value}%"
        search = search.filter(Oficina.nombre.ilike(like))

    pagination = search.paginate(page=page, per_page=per_page, error_out=False)
    results = [
        {
            "id": oficina.id,
            "text": f"{oficina.hospital.nombre} · {oficina.nombre}",
        }
        for oficina in pagination.items
    ]
    return jsonify({"results": results, "next": pagination.has_next})


@api_bp.route("/insumos/search")
@login_required
def search_insumos():
    query_value = _sanitize_query_param()
    page = request.args.get("page", type=int, default=1)
    per_page = _get_page_size()

    search = Insumo.query.order_by(asc(Insumo.nombre))
    if query_value:
        like = f"%{query_value}%"
        search = search.filter(Insumo.nombre.ilike(like))

    pagination = search.paginate(page=page, per_page=per_page, error_out=False)
    results = [
        {
            "id": insumo.id,
            "text": insumo.nombre,
        }
        for insumo in pagination.items
    ]
    return jsonify({"results": results, "next": pagination.has_next})
