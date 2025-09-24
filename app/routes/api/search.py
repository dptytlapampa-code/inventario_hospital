"""Asynchronous search endpoints for select widgets."""
from __future__ import annotations

from flask import jsonify, request
from flask_login import login_required
from sqlalchemy import asc, or_

from app.models import Hospital, Insumo, Oficina, Servicio

from . import api_bp

DEFAULT_PAGE_SIZE = 20
MAX_PAGE_SIZE = 50
LOOKUP_PAGE_SIZE = 100


def _sanitize_query_param() -> str:
    query = request.args.get("q", "").strip()
    return query[:80]


def _get_page_size() -> int:
    page_size = request.args.get("per_page", type=int, default=DEFAULT_PAGE_SIZE)
    return max(1, min(page_size, MAX_PAGE_SIZE))


def _format_hospital_label(hospital: Hospital) -> str:
    locality = getattr(hospital, "localidad", None) or getattr(hospital, "direccion", None)
    return f"{hospital.nombre} - {locality}" if locality else hospital.nombre


def _paginate(query, page: int, per_page: int):
    offset = max(page - 1, 0) * per_page
    items = query.limit(per_page + 1).offset(offset).all()
    has_next = len(items) > per_page
    if has_next:
        items = items[:-1]
    return items, has_next


@api_bp.route("/search/hospitales")
@login_required
def search_hospitales():
    query_value = _sanitize_query_param()
    page = request.args.get("page", type=int, default=1)

    lookup = Hospital.query.order_by(asc(Hospital.nombre))
    if query_value and query_value != "...":
        like = f"%{query_value}%"
        conditions = [Hospital.nombre.ilike(like)]
        localidad_column = getattr(Hospital, "localidad", None)
        if localidad_column is not None:
            conditions.append(localidad_column.ilike(like))
        direccion_column = getattr(Hospital, "direccion", None)
        if direccion_column is not None and direccion_column not in conditions:
            conditions.append(direccion_column.ilike(like))
        lookup = lookup.filter(or_(*conditions))
    items, has_next = _paginate(lookup, page, LOOKUP_PAGE_SIZE)
    results = [
        {
            "id": hospital.id,
            "text": _format_hospital_label(hospital),
        }
        for hospital in items
    ]
    return jsonify({"results": results, "next": has_next})


@api_bp.route("/search/servicios")
@login_required
def search_servicios_lookup():
    hospital_id = request.args.get("hospital_id", type=int)
    if not hospital_id:
        return (
            jsonify({"results": [], "next": False, "message": "Seleccione un hospital"}),
            400,
        )

    query_value = _sanitize_query_param()
    page = request.args.get("page", type=int, default=1)

    lookup = Servicio.query.filter(Servicio.hospital_id == hospital_id).order_by(asc(Servicio.nombre))
    if query_value and query_value != "...":
        like = f"%{query_value}%"
        lookup = lookup.filter(Servicio.nombre.ilike(like))

    items, has_next = _paginate(lookup, page, LOOKUP_PAGE_SIZE)
    results = [
        {
            "id": servicio.id,
            "text": servicio.nombre,
        }
        for servicio in items
    ]
    return jsonify({"results": results, "next": has_next})


@api_bp.route("/search/oficinas")
@login_required
def search_oficinas_lookup():
    hospital_id = request.args.get("hospital_id", type=int)
    if not hospital_id:
        return (
            jsonify({"results": [], "next": False, "message": "Seleccione un hospital"}),
            400,
        )
    servicio_id = request.args.get("servicio_id", type=int)

    query_value = _sanitize_query_param()
    page = request.args.get("page", type=int, default=1)

    lookup = Oficina.query.filter(Oficina.hospital_id == hospital_id).order_by(asc(Oficina.nombre))
    if servicio_id:
        lookup = lookup.filter(Oficina.servicio_id == servicio_id)
    if query_value and query_value != "...":
        like = f"%{query_value}%"
        lookup = lookup.filter(Oficina.nombre.ilike(like))

    items, has_next = _paginate(lookup, page, LOOKUP_PAGE_SIZE)
    results = [
        {
            "id": oficina.id,
            "text": oficina.nombre,
        }
        for oficina in items
    ]
    return jsonify({"results": results, "next": has_next})


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
