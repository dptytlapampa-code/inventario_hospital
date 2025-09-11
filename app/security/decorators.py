"""Reusable decorators enforcing role or permission requirements."""
from __future__ import annotations

from functools import wraps
from typing import Callable


def _has_all(values: set[str], required: tuple[str, ...]) -> bool:
    """Return ``True`` if all ``required`` values are present in ``values``."""
    return set(required).issubset(values)


def roles_required(*roles: str) -> Callable:
    """Allow access only to authenticated users with all ``roles``."""

    def decorator(view: Callable) -> Callable:
        @wraps(view)
        def wrapped(*args, **kwargs):
            from flask import abort  # imported lazily to avoid hard dependency
            from flask_login import current_user

            user_roles = set(getattr(current_user, "roles", []))
            if not current_user.is_authenticated or not _has_all(user_roles, roles):
                abort(403)
            return view(*args, **kwargs)

        return wrapped

    return decorator


def permissions_required(*permissions: str) -> Callable:
    """Allow access only to users that possess all ``permissions``."""

    def decorator(view: Callable) -> Callable:
        @wraps(view)
        def wrapped(*args, **kwargs):
            from flask import abort  # imported lazily
            from flask_login import current_user

            user_perms = set(getattr(current_user, "permissions", []))
            if not current_user.is_authenticated or not _has_all(user_perms, permissions):
                abort(403)
            return view(*args, **kwargs)

        return wrapped

    return decorator


__all__ = ["roles_required", "permissions_required"]
