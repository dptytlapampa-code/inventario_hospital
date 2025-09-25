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

    role = (getattr(user, "role", None) or "").lower()
    if role == "superadmin":
        return "todos"

    allowed = set()
    if hasattr(user, "allowed_hospital_ids"):
        allowed.update(user.allowed_hospital_ids(None))

    if getattr(user, "hospital_id", None):
        allowed.add(int(user.hospital_id))

    return _normalize_ids(allowed)


__all__ = ["get_user_hospital_scope", "ScopeValue"]
