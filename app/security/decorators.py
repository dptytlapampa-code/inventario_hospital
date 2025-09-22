"""Decorators enforcing role and permission checks."""
from __future__ import annotations

from functools import wraps
from typing import Callable

from flask import abort, g
from flask_login import current_user

from app.models import Modulo


def roles_required(*roles: str) -> Callable:
    """Ensure the current user has one of the provided ``roles``."""

    def decorator(view: Callable) -> Callable:
        @wraps(view)
        def wrapped(*args, **kwargs):
            if not current_user.is_authenticated:
                abort(401)
            if not current_user.has_role(*roles):
                abort(403)
            return view(*args, **kwargs)

        return wrapped

    return decorator


def permissions_required(*permissions: str) -> Callable:
    """Ensure the user has all permissions in ``module:action`` form."""

    def decorator(view: Callable) -> Callable:
        @wraps(view)
        def wrapped(*args, **kwargs):
            if not current_user.is_authenticated:
                abort(401)
            missing = [perm for perm in permissions if not current_user.has_permission(perm)]
            if missing:
                abort(403)
            return view(*args, **kwargs)

        return wrapped

    return decorator


def require_hospital_access(modulo: Modulo | str) -> Callable:
    """Limit the view to hospitals the user can access for ``modulo``."""

    modulo_value = modulo.value if isinstance(modulo, Modulo) else modulo

    def decorator(view: Callable) -> Callable:
        @wraps(view)
        def wrapped(*args, **kwargs):
            if not current_user.is_authenticated:
                abort(401)
            allowed = current_user.allowed_hospital_ids(modulo_value)
            g.allowed_hospitals = allowed
            if not allowed and current_user.rol and current_user.rol.nombre.lower() != "superadmin":
                abort(403)
            return view(*args, **kwargs)

        return wrapped

    return decorator


__all__ = ["roles_required", "permissions_required", "require_hospital_access"]
