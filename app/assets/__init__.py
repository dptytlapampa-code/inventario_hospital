"""Static asset helpers for the Inventario Hospital application."""
from __future__ import annotations

from pathlib import Path

__all__ = ["ensure_favicon", "ensure_static_asset"]


def ensure_static_asset(target: Path, data: bytes) -> Path:
    """Write ``data`` to ``target`` if the file does not yet exist.

    The helper guarantees idempotency and creates any missing parent
    directories so assets can be materialised lazily during application
    start-up.  The resulting path is returned so callers can easily use it
    for logging or additional processing.
    """

    target.parent.mkdir(parents=True, exist_ok=True)
    if not target.exists():
        target.write_bytes(data)
    return target


from .favicon import ensure_favicon  # noqa: E402  (import after helper definition)
