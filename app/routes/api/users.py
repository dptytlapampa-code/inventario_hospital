"""Lightweight user helper endpoints."""
from __future__ import annotations

from flask import jsonify, request
from flask_login import login_required

from app.models import Usuario

from . import api_bp


@api_bp.get("/users/check")
@login_required
def users_check():
    """Return duplicate flags for username and DNI fields."""

    username = (request.args.get("username", "") or "").strip()
    dni = (request.args.get("dni", "") or "").strip()
    exclude_id = request.args.get("exclude_id", type=int)

    exists_username = False
    exists_dni = False

    if username:
        query = Usuario.query.filter(Usuario.username == username)
        if exclude_id:
            query = query.filter(Usuario.id != exclude_id)
        exists_username = query.first() is not None

    if dni:
        query = Usuario.query.filter(Usuario.dni == dni)
        if exclude_id:
            query = query.filter(Usuario.id != exclude_id)
        exists_dni = query.first() is not None

    return jsonify({
        "exists_username": exists_username,
        "exists_dni": exists_dni,
    })


__all__ = ["users_check"]
