"""Helper utilities for WTForms rendering in Jinja templates."""
from __future__ import annotations

from typing import Any, Callable

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


def resolve_field_value(field: Any) -> Any:
    """Return the submitted value for a field, falling back to raw data."""

    value = getattr(field, "data", None)
    if value not in (None, "", ()):  # truthy or explicit zero values are returned as-is
        return value
    raw_data = getattr(field, "raw_data", None)
    if raw_data:
        candidate = raw_data[0]
        if candidate not in (None, ""):
            return candidate
    return None


def preload_model_choice(
    field: Any,
    model: Any,
    label_getter: Callable[[Any], str],
) -> None:
    """Populate a select field with the currently selected database option.

    The field is left without choices when there is no value or the record no
    longer exists. This allows asynchronous widgets such as Tom Select to load
    the available options on demand while still showing the persisted value
    when re-rendering a form.
    """

    value = resolve_field_value(field)
    if value in (None, "", 0):
        field.choices = []
        return

    try:
        record_id = int(value)
    except (TypeError, ValueError):
        field.choices = []
        return

    instance = model.query.get(record_id)
    if instance is None:
        field.choices = []
        return

    field.choices = [(instance.id, label_getter(instance))]


__all__ = [
    "render_input_field",
    "build_select_attrs",
    "resolve_field_value",
    "preload_model_choice",
]
