"""Decorators enforcing role and permission checks."""
from __future__ import annotations

from functools import wraps
from typing import Callable

from flask import abort, current_app, flash, g
from flask_login import current_user

from app.models import Modulo
from app.extensions import login_manager


def _handle_unauthenticated():
    response = login_manager.unauthorized()
    if response is None:  # pragma: no cover - fallback when login view missing
        abort(401)
    return response


def roles_required(*roles: str) -> Callable:
    """Ensure the current user has one of the provided ``roles``."""

    def decorator(view: Callable) -> Callable:
        @wraps(view)
        def wrapped(*args, **kwargs):
            if not current_user.is_authenticated:
                return _handle_unauthenticated()
            if not current_user.has_role(*roles):
                current_app.logger.warning(
                    "Acceso denegado por rol. Usuario=%s, roles=%s, vista=%s",
                    getattr(current_user, "username", "anon"),
                    roles,
                    view.__name__,
                )
                flash("No tiene permisos para ver esta página.", "danger")
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
                return _handle_unauthenticated()
            missing = [perm for perm in permissions if not current_user.has_permission(perm)]
            if missing:
                current_app.logger.warning(
                    "Permiso insuficiente. Usuario=%s, permisos=%s, faltantes=%s, vista=%s",
                    getattr(current_user, "username", "anon"),
                    permissions,
                    missing,
                    view.__name__,
                )
                flash("No tiene permisos para ver esta página.", "danger")
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
                return _handle_unauthenticated()
            allowed = current_user.allowed_hospital_ids(modulo_value)
            g.allowed_hospitals = allowed
            if not allowed and current_user.rol and current_user.rol.nombre.lower() != "superadmin":
                current_app.logger.warning(
                    "Acceso denegado por hospital. Usuario=%s, modulo=%s",
                    getattr(current_user, "username", "anon"),
                    modulo_value,
                )
                flash("No tiene permisos para ver esta página.", "danger")
                abort(403)
            return view(*args, **kwargs)

        return wrapped

    return decorator


__all__ = ["roles_required", "permissions_required", "require_hospital_access"]
