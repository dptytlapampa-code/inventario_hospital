from __future__ import annotations

from collections import defaultdict
from typing import Dict, List

try:  # pragma: no cover - fallbacks for environments without Flask
    from flask import Blueprint, flash, redirect, render_template, url_for
    from flask_login import login_required
except ModuleNotFoundError:  # pragma: no cover - simple stubs for testing
    class Blueprint:  # type: ignore
        def __init__(self, *args, **kwargs) -> None:
            pass

        def route(self, *args, **kwargs):
            def decorator(func):
                return func

            return decorator

    def flash(*args, **kwargs):  # type: ignore
        return None

    def redirect(location):  # type: ignore
        return location

    def render_template(template_name: str, **context):  # type: ignore
        return template_name

    def url_for(endpoint: str, **values):  # type: ignore
        return endpoint

    def login_required(func):  # type: ignore
        return func

from app.forms.acta import ActaForm
from app.models.acta import Acta, ActaItem, TipoActa
from app.models.adjunto import Adjunto, TipoAdjunto
from app.services.pdf_service import create_pdf

actas_bp = Blueprint("actas", __name__, url_prefix="/actas")

# Simple in-memory storage for demo purposes
ACTAS: Dict[int, Acta] = {}
ACTA_PDFS: Dict[int, bytes] = {}
ADJUNTOS: Dict[int, List[Adjunto]] = defaultdict(list)


@actas_bp.route("/crear", methods=["GET", "POST"])
@login_required
def crear():
    form = ActaForm()
    # Choices de equipos de ejemplo
    if not form.equipos.choices:
        form.equipos.choices = [(1, "Equipo 1"), (2, "Equipo 2"), (3, "Equipo 3")]
    if form.validate_on_submit():
        acta_id = max(ACTAS.keys(), default=0) + 1
        acta = Acta(tipo=TipoActa(form.tipo.data))
        acta.items = [ActaItem(equipo_id=e) for e in form.equipos.data]
        ACTAS[acta_id] = acta
        pdf_bytes = create_pdf(f"Acta {acta_id}")
        ACTA_PDFS[acta_id] = pdf_bytes
        for equipo_id in form.equipos.data:
            adjunto = Adjunto(
                equipo_id=equipo_id,
                filename=f"acta_{acta_id}.pdf",
                tipo=TipoAdjunto.ACTA,
            )
            ADJUNTOS[equipo_id].append(adjunto)
        flash("Acta creada", "success")
        return redirect(url_for("actas.listar"))
    return render_template("actas/crear.html", form=form)


@actas_bp.route("/listar")
@login_required
def listar():
    return render_template("actas/listar.html", actas=ACTAS.items())


@actas_bp.route("/<int:acta_id>/descargar")
@login_required
def descargar(acta_id: int):
    if acta_id not in ACTAS:
        flash("Acta no encontrada", "error")
        return redirect(url_for("actas.listar"))
    return render_template("actas/descargar.html", acta_id=acta_id)


@actas_bp.route("/<int:acta_id>/pdf")
@login_required
def pdf(acta_id: int):
    pdf_bytes = ACTA_PDFS.get(acta_id)
    if not pdf_bytes:
        flash("Acta no encontrada", "error")
        return redirect(url_for("actas.listar"))
    headers = {
        "Content-Type": "application/pdf",
        "Content-Disposition": f"attachment; filename=acta_{acta_id}.pdf",
    }
    return pdf_bytes, 200, headers
