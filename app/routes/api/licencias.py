"""API endpoints to expose license information."""
from __future__ import annotations

from datetime import date

import json
import time

from flask import Response, abort, current_app, jsonify, request, stream_with_context
from flask_login import current_user, login_required
from sqlalchemy.orm import joinedload

from app.models import EstadoLicencia, Licencia, TipoLicencia

from . import api_bp


def _parse_enum(value: str | None, enum_cls):
    if not value:
        return None
    try:
        return enum_cls(value)
    except ValueError as exc:  # pragma: no cover - defensive
        abort(400, description=str(exc))


def _parse_date(value: str | None) -> date | None:
    if not value:
        return None
    try:
        return date.fromisoformat(value)
    except ValueError:  # pragma: no cover - defensive
        abort(400, description="Formato de fecha inválido. Use AAAA-MM-DD.")


def _serialize(licencia: Licencia) -> dict[str, object]:
    return {
        "id": licencia.id,
        "tipo": licencia.tipo.value,
        "estado": licencia.estado.value,
        "fecha_inicio": licencia.fecha_inicio.isoformat(),
        "fecha_fin": licencia.fecha_fin.isoformat(),
        "motivo": licencia.motivo,
        "motivo_rechazo": licencia.motivo_rechazo,
        "hospital": licencia.hospital.nombre if licencia.hospital else None,
        "usuario": licencia.usuario.nombre if licencia.usuario else None,
        "decidido_por": licencia.decisor.nombre if licencia.decisor else None,
        "decidido_en": licencia.decidido_en.isoformat() if licencia.decidido_en else None,
    }


def _stream_query(user) -> list[Licencia]:
    query = Licencia.query.options(
        joinedload(Licencia.usuario),
        joinedload(Licencia.hospital),
        joinedload(Licencia.decisor),
    ).order_by(Licencia.created_at.desc())
    if not user.has_role("superadmin"):
        query = query.filter(Licencia.user_id == user.id)
    return query.all()


@api_bp.get("/licencias/mias")
@login_required
def api_mis_licencias():
    """Return the current user's license requests in JSON format."""

    query = Licencia.query.filter(Licencia.user_id == current_user.id)

    estado = _parse_enum(request.args.get("estado"), EstadoLicencia)
    tipo = _parse_enum(request.args.get("tipo"), TipoLicencia)
    fecha_desde = _parse_date(request.args.get("desde"))
    fecha_hasta = _parse_date(request.args.get("hasta"))

    if estado:
        query = query.filter(Licencia.estado == estado)
    if tipo:
        query = query.filter(Licencia.tipo == tipo)
    if fecha_desde:
        query = query.filter(Licencia.fecha_fin >= fecha_desde)
    if fecha_hasta:
        query = query.filter(Licencia.fecha_inicio <= fecha_hasta)

    licencias = query.order_by(Licencia.created_at.desc()).all()
    return jsonify({"licencias": [_serialize(licencia) for licencia in licencias]})


@api_bp.get("/licencias/admin")
@login_required
def api_licencias_admin():
    """Expose the admin view of licenses for superadmin users."""

    if not current_user.has_role("superadmin"):
        abort(403)

    query = Licencia.query

    estado = _parse_enum(request.args.get("estado"), EstadoLicencia)
    tipo = _parse_enum(request.args.get("tipo"), TipoLicencia)
    usuario_id = request.args.get("usuario_id", type=int)
    hospital_id = request.args.get("hospital_id", type=int)
    fecha_desde = _parse_date(request.args.get("desde"))
    fecha_hasta = _parse_date(request.args.get("hasta"))

    if estado:
        query = query.filter(Licencia.estado == estado)
    if tipo:
        query = query.filter(Licencia.tipo == tipo)
    if usuario_id:
        query = query.filter(Licencia.user_id == usuario_id)
    if hospital_id:
        query = query.filter(Licencia.hospital_id == hospital_id)
    if fecha_desde:
        query = query.filter(Licencia.fecha_fin >= fecha_desde)
    if fecha_hasta:
        query = query.filter(Licencia.fecha_inicio <= fecha_hasta)

    licencias = query.order_by(Licencia.created_at.desc()).all()
    return jsonify({"licencias": [_serialize(licencia) for licencia in licencias]})


@api_bp.get("/licencias/stream")
@login_required
def api_licencias_stream() -> Response:
    """Stream license updates for the current user via SSE."""

    user = current_user._get_current_object()
    interval = current_app.config.get("LICENSES_STREAM_INTERVAL", 30)
    retry = current_app.config.get("LICENSES_STREAM_RETRY", interval * 1000)

    @stream_with_context
    def generate():
        yield f"retry: {int(retry)}\n\n"
        while True:
            licencias = _stream_query(user)
            payload = {
                "scope": "admin" if user.has_role("superadmin") else "mine",
                "licencias": [_serialize(licencia) for licencia in licencias],
            }
            yield f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"
            time.sleep(max(30, int(interval)))

    response = Response(generate(), mimetype="text/event-stream")
    response.headers["Cache-Control"] = "no-cache"
    return response
