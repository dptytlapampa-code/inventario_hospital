"""Utilities to generate PDF documents using WeasyPrint."""
from __future__ import annotations
"""Utilities to generate PDF documents using WeasyPrint."""

from pathlib import Path
from typing import Any

from flask import current_app, render_template
from sqlalchemy.orm import object_session, selectinload

try:  # pragma: no cover - optional dependency
    from weasyprint import HTML
except Exception:  # pragma: no cover
    HTML = None  # type: ignore


def render_pdf(template: str, context: dict[str, Any], output_path: Path) -> Path:
    """Render ``template`` with ``context`` to ``output_path``."""

    html = render_template(template, **context)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    if HTML is None:
        output_path.write_text(html, encoding="utf-8")
        return output_path

    base_url = current_app.config.get("WEASYPRINT_BASE_URL")
    HTML(string=html, base_url=base_url).write_pdf(str(output_path))
    return output_path



def _load_acta(acta):
    """Ensure ``acta`` is attached to a session with eager relationships."""

    from app.models import Acta, ActaItem  # imported lazily to avoid circular imports

    session = object_session(acta)
    if session is not None:
        return acta

    refreshed = (
        Acta.query.options(
            selectinload(Acta.items).selectinload(ActaItem.equipo),
            selectinload(Acta.hospital),
            selectinload(Acta.servicio),
            selectinload(Acta.oficina),
            selectinload(Acta.usuario),
        )
        .filter_by(id=acta.id)
        .first()
    )
    return refreshed or acta


def build_acta_pdf(acta, output_dir: Path) -> Path:
    """Generate the PDF for an acta and return the file path."""

    acta = _load_acta(acta)
    filename = f"acta_{acta.id}.pdf"
    output_path = output_dir / filename
    context = {"acta": acta}
    return render_pdf("actas/pdf.html", context, output_path)


__all__ = ["render_pdf", "build_acta_pdf"]
