"""Helpers for computing hospital scope restrictions per user."""
from __future__ import annotations

from typing import Iterable

from flask_login import AnonymousUserMixin

from app.models import Usuario


ScopeValue = list[int] | str


def _normalize_ids(values: Iterable[int]) -> list[int]:
    return sorted({int(value) for value in values})


def get_user_hospital_scope(user: Usuario | AnonymousUserMixin | None) -> ScopeValue:
    """Return the hospital IDs a ``user`` can access or ``"todos"``."""

    if user is None or not getattr(user, "is_authenticated", False):
        return []

    rol = getattr(user, "rol", None)
    role_name = (getattr(rol, "nombre", None) or "").lower()
    if role_name == "superadmin":
        return "todos"

    allowed = set()
    allowed_method = getattr(user, "allowed_hospital_ids", None)
    if callable(allowed_method):
        allowed.update(int(value) for value in allowed_method(None))

    if getattr(user, "hospital_id", None):
        allowed.add(int(user.hospital_id))

    return _normalize_ids(allowed)


__all__ = ["get_user_hospital_scope", "ScopeValue"]
