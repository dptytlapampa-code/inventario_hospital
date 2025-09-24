"""Favicon generation helpers."""
from __future__ import annotations

from base64 import b64decode
from pathlib import Path

from . import ensure_static_asset

# Embedded 16x16 favicon (ICO) encoded in base64 so we can avoid committing a
# binary blob to the repository while still serving a proper ``favicon.ico``.
_FAVICON_B64 = (
    "AAABAAEAEBAAAAEAIABoBAAAFgAAACgAAAAQAAAAIAAAAAEAIAAAAAAAAAQAAAAA"
    "AAAAAAAAAAAAAAAAAAD9bg3//W4N//1uDf/9bg3//W4N//1uDf/9bg3//W4N//1u"
    "Df/9bg3//W4N//1uDf/9bg3//W4N//1uDf/9bg3//W4N//1uDf/9bg3//W4N//1u"
    "Df/9bg3//W4N//1uDf/9bg3//W4N//1uDf/9bg3//W4N//1uDf/9bg3//W4N//1u"
    "Df/9bg3//W4N//1uDf/9bg3//W4N//1uDf/9bg3//W4N//1uDf/9bg3//W4N//1u"
    "Df/9bg3//W4N//1uDf/9bg3//W4N//1uDf/9bg3//W4N//1uDf/9bg3//W4N//1u"
    "Df/9bg3//W4N//1uDf/9bg3//W4N//1uDf/9bg3//W4N//1uDf/9bg3//W4N//1u"
    "Df/9bg3//W4N//1uDf/9bg3//W4N//1uDf/9bg3//W4N//1uDf/9bg3//W4N//1u"
    "Df/9bg3//W4N//1uDf/9bg3//W4N//1uDf/9bg3//W4N//1uDf/9bg3//W4N//1u"
    "Df/9bg3//W4N//1uDf/9bg3//W4N//1uDf/9bg3//W4N//1uDf/9bg3//W4N//1u"
    "Df/9bg3//W4N//1uDf/9bg3//W4N//1uDf/9bg3//W4N//1uDf/9bg3//W4N//1u"
    "Df/9bg3//W4N//1uDf/9bg3//W4N//1uDf/9bg3//W4N//1uDf/9bg3//W4N//1u"
    "Df/9bg3//W4N//1uDf/9bg3//W4N//1uDf/9bg3//W4N//1uDf/9bg3//W4N//1u"
    "Df/9bg3//W4N//1uDf/9bg3//W4N//1uDf/9bg3//W4N//1uDf/9bg3//W4N//1u"
    "Df/9bg3//W4N//1uDf/9bg3//W4N//1uDf/9bg3//W4N//1uDf/9bg3//W4N//1u"
    "Df/9bg3//W4N//1uDf/9bg3//W4N//1uDf/9bg3//W4N//1uDf/9bg3//W4N//1u"
    "Df/9bg3//W4N//1uDf/9bg3//W4N//1uDf/9bg3//W4N//1uDf/9bg3//W4N//1u"
    "Df/9bg3//W4N//1uDf/9bg3//W4N//1uDf/9bg3//W4N//1uDf/9bg3//W4N//1u"
    "Df/9bg3//W4N//1uDf/9bg3//W4N//1uDf/9bg3//W4N//1uDf/9bg3//W4N//1u"
    "Df/9bg3//W4N//1uDf/9bg3//W4N//1uDf/9bg3//W4N//1uDf/9bg3//W4N//1u"
    "Df/9bg3//W4N//1uDf/9bg3//W4N//1uDf/9bg3//W4N//1uDf/9bg3//W4N//1u"
    "Df/9bg3//W4N//1uDf/9bg3//W4N//1uDf/9bg3//W4N//1uDf/9bg3//W4N//1u"
    "Df/9bg3//W4N//1uDf/9bg3//W4N//1uDf/9bg3/AAAAAAAAAAAAAAAAAAAAAAAA"
    "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA=="
)


def ensure_favicon(static_folder: str | Path) -> Path:
    """Make sure ``favicon.ico`` exists under ``static_folder``.

    The helper can be called multiple times without rewriting the file and
    returns the resulting :class:`~pathlib.Path` for convenience.
    """

    static_path = Path(static_folder)
    target = static_path / "favicon.ico"
    data = b64decode(_FAVICON_B64)
    return ensure_static_asset(target, data)


__all__ = ["ensure_favicon"]
