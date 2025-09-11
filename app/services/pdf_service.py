"""Utilities for creating PDF documents."""

from __future__ import annotations

from io import BytesIO

try:  # pragma: no cover - optional dependency
    from reportlab.pdfgen import canvas  # type: ignore
except Exception:  # pragma: no cover - if reportlab is missing
    canvas = None  # type: ignore


def create_pdf(text: str) -> bytes:
    """Create a simple PDF document from ``text``.

    The function attempts to use :mod:`reportlab` if available.  If the
    dependency is missing the plain text bytes are returned instead so the
    caller always receives a ``bytes`` object.
    """

    if canvas is None:
        return text.encode("utf-8")

    buffer = BytesIO()
    pdf = canvas.Canvas(buffer)
    pdf.drawString(72, 720, text)
    pdf.showPage()
    pdf.save()
    buffer.seek(0)
    return buffer.read()
