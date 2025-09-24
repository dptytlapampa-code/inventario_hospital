"""Utility helpers exposed to the Flask app."""

from __future__ import annotations

from urllib.parse import urljoin, urlparse

from flask import Request, request

from .forms import build_select_attrs, render_input_field


def normalize_enum_value(value: object) -> str:
    """Return a displayable string for ``value`` from Enum or raw values."""

    if value is None:
        return ""

    candidate = getattr(value, "value", value)
    try:
        return str(candidate)
    except Exception:  # pragma: no cover - defensive fallback
        return ""


def is_safe_redirect_target(target: str | None, req: Request | None = None) -> bool:
    """Validate that ``target`` keeps the redirect inside the application."""

    if not target:
        return False

    active_request = req or request
    if active_request is None:  # pragma: no cover - requires request context
        return False

    base_url = active_request.host_url
    test_url = urljoin(base_url, target)
    base_parts = urlparse(base_url)
    target_parts = urlparse(test_url)
    return (
        target_parts.scheme in {"http", "https"}
        and base_parts.netloc == target_parts.netloc
    )


__all__ = [
    "render_input_field",
    "build_select_attrs",
    "normalize_enum_value",
    "is_safe_redirect_target",
]
