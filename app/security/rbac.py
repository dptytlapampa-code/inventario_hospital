"""Lightweight role-based access helpers."""
from __future__ import annotations

from functools import wraps
from typing import Any, Callable, Iterable

from flask import redirect, render_template, request, url_for
from flask_login import current_user


ROLE_POWER: list[str] = ["visor", "tecnico", "admin", "superadmin"]


def _normalize_roles(roles: Iterable[str]) -> list[str]:
    return [role.lower() for role in roles]


def has_role(*roles: str) -> bool:
    """Return ``True`` when the authenticated user has one of ``roles``."""

    if not current_user.is_authenticated:
        return False
    if not roles:
        return False
    return (current_user.role or "") in _normalize_roles(roles)


def require_roles(*roles: str) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """Decorator enforcing that the user owns one of the accepted roles."""

    normalized = _normalize_roles(roles)

    def decorator(fn: Callable[..., Any]) -> Callable[..., Any]:
        @wraps(fn)
        def wrapped(*args: Any, **kwargs: Any):
            if not current_user.is_authenticated:
                return redirect(url_for("auth.login", next=request.path))
            if normalized and (current_user.role or "") not in normalized:
                return render_template("errors/403.html"), 403
            return fn(*args, **kwargs)

        return wrapped

    return decorator


__all__ = ["ROLE_POWER", "has_role", "require_roles"]
