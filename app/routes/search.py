"""Global search blueprint."""
from __future__ import annotations

from flask import Blueprint, render_template, request
from flask_login import login_required

from app.services.search_service import global_search

search_bp = Blueprint("search", __name__, url_prefix="/search")


@search_bp.route("/", methods=["GET"])
@login_required
def search() -> str:
    query = request.args.get("q", "")
    page = request.args.get("page", type=int, default=1)
    per_page = 10

    resultados = global_search(query)
    total = len(resultados)
    start = (page - 1) * per_page
    end = start + per_page
    paginated = resultados[start:end]

    return render_template(
        "search/results.html",
        query=query,
        results=paginated,
        page=page,
        has_prev=page > 1,
        has_next=end < total,
        total=total,
    )
