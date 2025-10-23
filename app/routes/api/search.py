"""Asynchronous search endpoints for select widgets."""
from __future__ import annotations

import json

from flask import current_app, jsonify, request
from flask_login import current_user, login_required
from sqlalchemy import asc, or_

from app.models import Equipo, Hospital, Insumo, Oficina, Servicio, TipoEquipo
from app.services.equipo_service import format_equipo_option

from . import api_bp

DEFAULT_PAGE_SIZE = 20
LOOKUP_PAGE_SIZE = 20
MAX_PAGE_SIZE = 50
EQUIPO_PAGE_SIZE = 20


def _sanitize_query_param() -> str:
    query = request.args.get("q", "").strip()
    if query == "...":
        return ""
    return query[:80]


def _get_page_size(default: int = DEFAULT_PAGE_SIZE) -> int:
    page_size = request.args.get("per_page", type=int, default=default)
    return max(1, min(page_size, MAX_PAGE_SIZE))


def _format_hospital_label(hospital: Hospital) -> str:
    locality = getattr(hospital, "localidad", None) or getattr(hospital, "direccion", None)
    return f"{hospital.nombre} - {locality}" if locality else hospital.nombre


def _build_paginated_response(pagination, formatter):
    items = []
    for entry in pagination.items:
        formatted = formatter(entry)
        if isinstance(formatted, dict):
            if "text" not in formatted and "label" in formatted:
                formatted = {**formatted, "text": formatted["label"]}
            elif "label" not in formatted and "text" in formatted:
                formatted = {**formatted, "label": formatted["text"]}
        items.append(formatted)
    return jsonify(
        {
            "items": items,
            "page": pagination.page,
            "pages": pagination.pages,
            "total": pagination.total,
        }
    )


def _log_missing_dependency(endpoint: str, **extra) -> None:
    payload = {"endpoint": endpoint, "status": 400, **extra}
    current_app.logger.warning(json.dumps(payload, ensure_ascii=False))


@api_bp.route("/search/hospitales")
@login_required
def search_hospitales():
    query_value = _sanitize_query_param()
    page = request.args.get("page", type=int, default=1)
    per_page = _get_page_size()

    lookup = Hospital.query.order_by(asc(Hospital.nombre))
    if query_value:
        like = f"%{query_value}%"
        conditions = [Hospital.nombre.ilike(like)]
        localidad_column = getattr(Hospital, "localidad", None)
        if localidad_column is not None:
            conditions.append(localidad_column.ilike(like))
        direccion_column = getattr(Hospital, "direccion", None)
        if direccion_column is not None and direccion_column not in conditions:
            conditions.append(direccion_column.ilike(like))
        lookup = lookup.filter(or_(*conditions))
    pagination = lookup.paginate(page=page, per_page=per_page, error_out=False)
    return _build_paginated_response(
        pagination,
        lambda hospital: {"id": hospital.id, "label": _format_hospital_label(hospital)},
    )


@api_bp.route("/search_servicios")
@api_bp.route("/search/servicios")
@login_required
def search_servicios_lookup():
    hospital_id = request.args.get("hospital_id", type=int)
    if not hospital_id:
        _log_missing_dependency(
            "api.search_servicios_lookup", message="hospital_id es requerido"
        )
        return (
            jsonify(
                {
                    "items": [],
                    "page": 1,
                    "pages": 0,
                    "total": 0,
                    "message": "Seleccione un hospital",
                }
            ),
            400,
        )

    query_value = _sanitize_query_param()
    page = request.args.get("page", type=int, default=1)
    per_page = _get_page_size(LOOKUP_PAGE_SIZE)

    lookup = (
        Servicio.query.filter(Servicio.hospital_id == hospital_id)
        .order_by(asc(Servicio.nombre))
    )
    if query_value:
        like = f"%{query_value}%"
        lookup = lookup.filter(Servicio.nombre.ilike(like))

    pagination = lookup.paginate(page=page, per_page=per_page, error_out=False)
    return _build_paginated_response(
        pagination, lambda servicio: {"id": servicio.id, "label": servicio.nombre}
    )


@api_bp.route("/search_oficinas")
@api_bp.route("/search/oficinas")
@login_required
def search_oficinas_lookup():
    hospital_id = request.args.get("hospital_id", type=int)
    if not hospital_id:
        _log_missing_dependency(
            "api.search_oficinas_lookup", message="hospital_id es requerido"
        )
        return (
            jsonify(
                {
                    "items": [],
                    "page": 1,
                    "pages": 0,
                    "total": 0,
                    "message": "Seleccione un hospital",
                }
            ),
            400,
        )
    servicio_id = request.args.get("servicio_id", type=int)
    if not servicio_id:
        _log_missing_dependency(
            "api.search_oficinas_lookup", message="servicio_id es requerido"
        )
        return (
            jsonify(
                {
                    "items": [],
                    "page": 1,
                    "pages": 0,
                    "total": 0,
                    "message": "Seleccione un servicio",
                }
            ),
            400,
        )

    query_value = _sanitize_query_param()
    page = request.args.get("page", type=int, default=1)
    per_page = _get_page_size(LOOKUP_PAGE_SIZE)

    lookup = (
        Oficina.query.filter(Oficina.hospital_id == hospital_id)
        .order_by(asc(Oficina.nombre))
    )
    lookup = lookup.filter(Oficina.servicio_id == servicio_id)
    if query_value:
        like = f"%{query_value}%"
        lookup = lookup.filter(Oficina.nombre.ilike(like))

    pagination = lookup.paginate(page=page, per_page=per_page, error_out=False)
    return _build_paginated_response(
        pagination,
        lambda oficina: {"id": oficina.id, "label": oficina.nombre},
    )


@api_bp.route("/equipos/search")
@login_required
def search_equipos():
    query_value = _sanitize_query_param()
    page = request.args.get("page", type=int, default=1)
    per_page = _get_page_size(EQUIPO_PAGE_SIZE)

    search = (
        Equipo.query.join(Equipo.tipo)
        .filter(TipoEquipo.activo.is_(True))
        .order_by(asc(TipoEquipo.nombre), asc(Equipo.marca), asc(Equipo.modelo))
    )

    allowed = current_user.allowed_hospital_ids()
    if allowed:
        search = search.filter(Equipo.hospital_id.in_(allowed))

    hospital_id = request.args.get("hospital_id", type=int)
    if hospital_id:
        search = search.filter(Equipo.hospital_id == hospital_id)

    servicio_id = request.args.get("servicio_id", type=int)
    if servicio_id:
        search = search.filter(Equipo.servicio_id == servicio_id)

    oficina_id = request.args.get("oficina_id", type=int)
    if oficina_id:
        search = search.filter(Equipo.oficina_id == oficina_id)

    if query_value:
        like = f"%{query_value}%"
        filters = [
            TipoEquipo.nombre.ilike(like),
            Equipo.descripcion.ilike(like),
            Equipo.marca.ilike(like),
            Equipo.modelo.ilike(like),
            Equipo.numero_serie.ilike(like),
        ]
        codigo_column = getattr(Equipo, "codigo", None)
        if codigo_column is not None:
            filters.append(codigo_column.ilike(like))
        patrimonial_column = getattr(Equipo, "bien_patrimonial", None)
        if patrimonial_column is not None:
            filters.append(patrimonial_column.ilike(like))
        search = search.filter(or_(*filters))

    pagination = search.paginate(page=page, per_page=per_page, error_out=False)
    items = [format_equipo_option(equipo) for equipo in pagination.items]
    return jsonify({"results": items, "pagination": {"more": pagination.has_next}})


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
    return _build_paginated_response(
        pagination,
        lambda servicio: {
            "id": servicio.id,
            "label": f"{servicio.hospital.nombre} · {servicio.nombre}",
        },
    )


@api_bp.route("/oficinas/search")
@login_required
def search_oficinas():
    servicio_id = request.args.get("servicio_id", type=int)
    if not servicio_id:
        _log_missing_dependency(
            "api.search_oficinas", message="servicio_id es requerido"
        )
        return (
            jsonify(
                {
                    "items": [],
                    "page": 1,
                    "pages": 0,
                    "total": 0,
                    "message": "Seleccione un servicio para filtrar oficinas",
                }
            ),
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
    return _build_paginated_response(
        pagination,
        lambda oficina: {
            "id": oficina.id,
            "label": f"{oficina.hospital.nombre} · {oficina.nombre}",
        },
    )


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
    return _build_paginated_response(
        pagination, lambda insumo: {"id": insumo.id, "label": insumo.nombre}
    )
