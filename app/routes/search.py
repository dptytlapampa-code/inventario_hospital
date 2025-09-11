from __future__ import annotations

from typing import Any, Iterable

from flask import Blueprint, render_template, request

from app.extensions import db
from app.models.equipo import Equipo
from app.models.insumo import Insumo
from app.models.usuario import Usuario
from app.models.user import USERS
from app.services import search_service

search_bp = Blueprint("search", __name__, url_prefix="/search")


def _combined_dataset() -> list[dict[str, Any]]:
    """Return a combined list of equipos, insumos and usuarios.

    The function tries to query the database for each model.  If the database
    is not configured (as in lightweight test environments) it falls back to
    the in-memory ``USERS`` dataset for usuarios and leaves other collections
    empty.  Each item includes a ``tipo`` field describing its origin.
    """

    dataset: list[dict[str, Any]] = []

    try:
        for equipo in db.session.query(Equipo).all():  # type: ignore[attr-defined]
            dataset.append(
                {
                    "tipo": "Equipo",
                    "nombre": equipo.descripcion or "",
                    "numero_serie": equipo.numero_serie or "",
                }
            )
    except Exception:  # pragma: no cover - database not available
        pass

    try:
        for insumo in db.session.query(Insumo).all():  # type: ignore[attr-defined]
            dataset.append(
                {
                    "tipo": "Insumo",
                    "nombre": insumo.nombre,
                    "numero_serie": insumo.numero_serie or "",
                }
            )
    except Exception:  # pragma: no cover - database not available
        pass

    try:
        for usuario in db.session.query(Usuario).all():  # type: ignore[attr-defined]
            dataset.append(
                {
                    "tipo": "Usuario",
                    "nombre": usuario.nombre,
                    "email": usuario.email,
                }
            )
    except Exception:  # pragma: no cover - fall back to in-memory users
        for usuario in USERS.values():
            dataset.append({"tipo": "Usuario", "nombre": usuario.username})

    return dataset


def paginate(items: Iterable[Any], page: int, per_page: int) -> list[Any]:
    """Return a slice of ``items`` for the given page.

    Pagination is implemented using simple list slicing and therefore works
    with any iterable once it is materialised into a list.
    """

    start = (page - 1) * per_page
    end = start + per_page
    return list(items)[start:end]


@search_bp.route("/", methods=["GET"])
def search() -> str:
    """Render search results for the given query.

    The view aggregates data from multiple sources and uses the generic
    :func:`search_service.global_search` helper for matching.  Results are
    paginated with a fixed page size of ten items.
    """

    query = request.args.get("q", "")
    page = request.args.get("page", type=int, default=1)
    dataset = _combined_dataset()
    results = search_service.global_search(query, dataset) if query else []

    per_page = 10
    paginated = paginate(results, page, per_page)
    has_prev = page > 1
    has_next = page * per_page < len(results)

    return render_template(
        "search/results.html",
        query=query,
        results=paginated,
        page=page,
        has_prev=has_prev,
        has_next=has_next,
    )
