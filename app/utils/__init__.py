"""Utility helpers exposed to the Flask app."""

from __future__ import annotations

from math import log
from urllib.parse import urljoin, urlparse
from datetime import date, datetime

from flask import Request, current_app, request

from .forms import build_select_attrs, render_input_field


def humanize_bytes(size: int | None) -> str:
    """Return a human readable label for ``size`` measured in bytes."""

    if size is None or size < 0:
        return "—"
    if size == 0:
        return "0 B"
    units = ["B", "KB", "MB", "GB", "TB"]
    idx = min(int(log(size, 1024)), len(units) - 1)
    scaled = size / (1024 ** idx)
    if idx == 0:
        return f"{int(scaled)} {units[idx]}"
    return f"{scaled:.1f} {units[idx]}"


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


def format_spanish_date(value: object, include_time: bool | None = None) -> str:
    """Return ``value`` formatted as ``dd/mm/aaaa`` (optionally with time).

    ``include_time`` defaults to ``True`` when ``value`` is a :class:`datetime`
    instance and ``False`` otherwise. Strings in ISO format are parsed
    opportunistically to provide consistent output without raising errors.
    """

    if value in {None, "", "null"}:
        return "—"

    parsed_value: date | datetime | None
    parsed_value = None

    if isinstance(value, datetime):
        parsed_value = value
    elif isinstance(value, date):
        parsed_value = value
    elif isinstance(value, str):
        candidate = value.strip()
        if not candidate:
            return "—"
        try:
            parsed_value = datetime.fromisoformat(candidate.replace("Z", "+00:00"))
        except ValueError:
            try:
                parsed_value = datetime.strptime(candidate, "%d/%m/%Y")
            except ValueError:
                try:
                    current_app.logger.debug(
                        "No se pudo convertir la fecha '%s' al formato esperado.",
                        candidate,
                    )
                except RuntimeError:
                    pass
                return candidate

    if parsed_value is None:
        return "—"

    show_time = include_time
    if show_time is None:
        show_time = isinstance(parsed_value, datetime)

    if isinstance(parsed_value, datetime):
        if show_time:
            return parsed_value.strftime("%d/%m/%Y %H:%M")
        return parsed_value.strftime("%d/%m/%Y")

    return parsed_value.strftime("%d/%m/%Y")


__all__ = [
    "render_input_field",
    "build_select_attrs",
    "normalize_enum_value",
    "is_safe_redirect_target",
    "humanize_bytes",
    "format_spanish_date",
]
