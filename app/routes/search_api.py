"""REST API for live search lookups."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Iterable

from flask import Blueprint, abort, jsonify, request
from flask_login import current_user, login_required

from app.models import Hospital, HospitalUsuarioRol, Rol, Usuario
from app.services.audit_service import log_action
from app.utils.search import apply_text_search, paginate_query

search_api_bp = Blueprint("search_api", __name__, url_prefix="/api/search")


@dataclass
class SearchResource:
    model: type
    columns: tuple
    formatter: Callable[[object], dict]
    hospital_field: object | None = None
    extra_filters: Callable[[object], object] | None = None


def _sanitize_page() -> tuple[int, int]:
    page = request.args.get("page", type=int, default=1)
    per_page = request.args.get("per_page", type=int, default=20)
    per_page = max(1, min(per_page, 50))
    return page, per_page


def _apply_hospital_scope(query, field):
    hospital_id = request.args.get("hospital_id", type=int)
    if hospital_id:
        return query.filter(field == hospital_id)

    if not current_user.is_authenticated:
        return query

    allowed = current_user.allowed_hospital_ids()
    if not allowed:
        return query
    return query.filter(field.in_(allowed))


def _configure_resources() -> dict[str, SearchResource]:
    return {
        "usuarios": SearchResource(
            model=Usuario,
            columns=(Usuario.nombre, Usuario.apellido, Usuario.username, Usuario.email),
            formatter=lambda usuario: {
                "id": usuario.id,
                "label": f"{usuario.nombre} {usuario.apellido or ''}".strip(),
                "extra": {
                    "email": usuario.email,
                    "rol": usuario.rol.nombre if usuario.rol else None,
                },
            },
        ),
        "hospitales": SearchResource(
            model=Hospital,
            columns=(Hospital.nombre, Hospital.direccion, Hospital.codigo),
            formatter=lambda hospital: {
                "id": hospital.id,
                "label": hospital.nombre,
                "extra": {"direccion": hospital.direccion},
            },
        ),
        "roles": SearchResource(
            model=Rol,
            columns=(Rol.nombre,),
            formatter=lambda rol: {
                "id": rol.id,
                "label": rol.nombre,
            },
        ),
    }


@search_api_bp.get("/<resource>")
@login_required
def live_search(resource: str):
    resources = _configure_resources()
    config = resources.get(resource)
    if not config:
        abort(404)

    query_value = (request.args.get("q", "") or "").strip()

    query = config.model.query
    if config.hospital_field is not None:
        query = _apply_hospital_scope(query, config.hospital_field)

    query = apply_text_search(query, config.columns, query_value)
    if config.extra_filters:
        query = config.extra_filters(query)

    page, per_page = _sanitize_page()
    pagination = paginate_query(query, page=page, per_page=per_page)
    items = [config.formatter(item) for item in pagination.items]
    return jsonify(
        {
            "items": items,
            "page": pagination.page,
            "pages": pagination.pages,
            "total": pagination.total,
        }
    )


@search_api_bp.get("/usuarios/<int:usuario_id>/hospitales")
@login_required
def get_usuario_hospitales(usuario_id: int):
    if not current_user.has_role("admin", "superadmin"):
        abort(403)
    usuario = Usuario.query.get_or_404(usuario_id)
    assignments = [
        {
            "hospital_id": rel.hospital_id,
            "hospital": rel.hospital.nombre,
            "rol_id": rel.rol_id,
            "rol": rel.rol.nombre,
        }
        for rel in usuario.hospitales_roles
    ]
    return jsonify({"items": assignments})


@search_api_bp.post("/usuarios/<int:usuario_id>/hospitales/bulk")
@login_required
def bulk_update_usuario_hospitales(usuario_id: int):
    if not current_user.has_role("admin", "superadmin"):
        abort(403)

    usuario = Usuario.query.get_or_404(usuario_id)
    payload = request.get_json(silent=True) or {}
    desired_assignments: Iterable[dict] = payload.get("add", [])
    desired_map: dict[int, int] = {}
    for item in desired_assignments:
        try:
            hospital_id = int(item.get("hospital_id"))
        except (TypeError, ValueError):
            continue
        try:
            rol_id = int(item.get("rol_id")) if item.get("rol_id") is not None else None
        except (TypeError, ValueError):
            rol_id = None
        if rol_id is None:
            continue
        desired_map[hospital_id] = rol_id

    existing = {rel.hospital_id: rel for rel in usuario.hospitales_roles}

    for hospital_id, relation in list(existing.items()):
        if hospital_id not in desired_map:
            usuario.hospitales_roles.remove(relation)

    for hospital_id, rol_id in desired_map.items():
        relation = existing.get(hospital_id)
        if relation:
            relation.rol_id = rol_id
        else:
            usuario.hospitales_roles.append(
                HospitalUsuarioRol(hospital_id=hospital_id, rol_id=rol_id)
            )

    from app.extensions import db

    db.session.add(usuario)
    db.session.commit()

    log_action(
        usuario_id=current_user.id,
        accion="asignar_hospitales",
        modulo="usuarios",
        entidad="Usuario",
        entidad_id=usuario.id,
        descripcion="Actualización masiva de asignaciones de hospitales",
        cambios={"hospitales": list(desired_map.keys())},
    )

    assignments = [
        {
            "hospital_id": rel.hospital_id,
            "hospital": rel.hospital.nombre,
            "rol_id": rel.rol_id,
            "rol": rel.rol.nombre,
        }
        for rel in usuario.hospitales_roles
    ]
    return jsonify({"items": assignments})


__all__ = ["search_api_bp"]
