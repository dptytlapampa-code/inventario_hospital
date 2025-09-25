"""API blueprint exposing lightweight search endpoints."""
from __future__ import annotations

from flask import Blueprint

api_bp = Blueprint("api", __name__, url_prefix="/api")

from . import dashboard, licencias, search, users  # noqa: E402  pylint: disable=wrong-import-position

__all__ = ["api_bp"]
