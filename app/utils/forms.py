"""Helper utilities for WTForms rendering in Jinja templates."""
from __future__ import annotations

from typing import Any

from markupsafe import Markup


def render_input_field(
    field: Any,
    classes: str,
    *,
    input_type: str | None = None,
    placeholder: str | None = None,
    min_value: Any | None = None,
    max_value: Any | None = None,
    step: Any | None = None,
    rows: int | None = None,
    extra_attrs: dict[str, Any] | None = None,
) -> Markup:
    """Render a WTForms field applying HTML attributes safely."""

    attrs: dict[str, Any] = {"class": classes}
    if input_type:
        attrs["type"] = input_type
    if placeholder:
        attrs["placeholder"] = placeholder
    if min_value is not None:
        attrs["min"] = min_value
    if max_value is not None:
        attrs["max"] = max_value
    if step is not None:
        attrs["step"] = step
    if rows is not None:
        attrs["rows"] = rows
    if extra_attrs:
        attrs.update(extra_attrs)

    return Markup(field(**attrs))


def build_select_attrs(
    field: Any,
    *,
    multiple: bool | None = None,
    size: int | None = None,
    extra_attrs: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Return a dictionary with normalized attributes for select fields."""

    attrs: dict[str, Any] = dict(extra_attrs or {})
    is_multiple_field = getattr(field, "type", "") in {
        "SelectMultipleField",
        "QuerySelectMultipleField",
    }
    if multiple is None:
        multiple_flag = is_multiple_field
    else:
        multiple_flag = multiple
    if multiple_flag:
        attrs["multiple"] = "multiple"
    if size:
        attrs["size"] = size
    return attrs


__all__ = ["render_input_field", "build_select_attrs"]
