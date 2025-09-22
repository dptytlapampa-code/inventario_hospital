"""Tests for acta PDF generation."""
from __future__ import annotations

from app.models import Acta
from app.services.pdf_service import build_acta_pdf


def test_build_acta_pdf_creates_file(app, data, tmp_path):
    acta_id = data["acta"].id

    with app.app_context():
        acta = Acta.query.get(acta_id)
        assert acta is not None
        output_dir = tmp_path / "actas"
        pdf_path = build_acta_pdf(acta, output_dir)

    assert pdf_path.exists()
    assert pdf_path.suffix == ".pdf"
    stored_path = pdf_path.as_posix()
    assert stored_path.startswith(str(tmp_path.as_posix()))
