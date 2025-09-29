"""Audit service writing records to the database."""
from __future__ import annotations

from typing import Any

from flask import request

from app.extensions import db
from app.models import Auditoria


def log_action(
    *,
    usuario_id: int | None,
    accion: str,
    modulo: str | None = None,
    tabla: str | None = None,
    registro_id: int | None = None,
    datos: dict[str, Any] | None = None,
    hospital_id: int | None = None,
    descripcion: str | None = None,
    entidad: str | None = None,
    entidad_id: int | None = None,
    cambios: dict[str, Any] | None = None,
) -> Auditoria:
    """Persist an audit entry."""

    entry = Auditoria(
        usuario_id=usuario_id,
        accion=accion,
        modulo=modulo,
        hospital_id=hospital_id,
        entidad=entidad or tabla,
        entidad_id=entidad_id or registro_id,
        descripcion=descripcion,
        cambios=cambios or datos,
        ip_address=request.remote_addr if request else None,
    )
    db.session.add(entry)
    db.session.commit()
    return entry


def get_logs(limit: int = 100) -> list[Auditoria]:
    """Return the most recent audit entries."""

    return (
        Auditoria.query.order_by(Auditoria.created_at.desc()).limit(limit).all()
    )


__all__ = ["log_action", "get_logs"]
