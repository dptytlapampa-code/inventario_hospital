"""QR code generation helpers."""

from __future__ import annotations

from io import BytesIO

try:  # pragma: no cover - optional dependency
    import qrcode  # type: ignore
except Exception:  # pragma: no cover - qrcode not installed
    qrcode = None  # type: ignore


def create_qr(data: str) -> bytes:
    """Return a PNG image containing a QR code for ``data``.

    If the :mod:`qrcode` package is not installed the UTF-8 encoded text is
    returned instead so the caller always receives ``bytes``.
    """

    if qrcode is None:
        return data.encode("utf-8")

    img = qrcode.make(data)
    buffer = BytesIO()
    img.save(buffer, format="PNG")
    return buffer.getvalue()
