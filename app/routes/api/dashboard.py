"""API endpoints serving dashboard metrics."""
from __future__ import annotations

import json
import time
from typing import Iterator

from flask import Response, current_app, jsonify, stream_with_context
from flask_login import current_user, login_required
from sqlalchemy import select
from sqlalchemy.orm import joinedload

from app.extensions import db
from app.models import Usuario
from app.services.dashboard_service import collect_dashboard_metrics

from . import api_bp


@api_bp.route("/dashboard/metrics")
@login_required
def dashboard_metrics():
    """Return aggregated metrics for the realtime dashboard."""

    payload = collect_dashboard_metrics(current_user)
    return jsonify(payload)


@api_bp.route("/dashboard/stream")
@login_required
def dashboard_stream() -> Response:
    """Stream dashboard updates using Server Sent Events."""

    try:
        user_id = int(current_user.get_id())
    except (TypeError, ValueError):
        user_id = None
    interval = current_app.config.get("DASHBOARD_STREAM_INTERVAL", 30)
    retry = current_app.config.get("DASHBOARD_STREAM_RETRY", interval * 1000)

    @stream_with_context
    def generate() -> Iterator[str]:
        yield f"retry: {retry}\n\n"
        while True:
            if user_id is None:
                break
            stmt = (
                select(Usuario)
                .options(joinedload(Usuario.rol))
                .where(Usuario.id == user_id)
            )
            user = db.session.execute(stmt).scalar_one_or_none()
            if user is None:
                break
            payload = collect_dashboard_metrics(user)
            yield f"data: {json.dumps(payload)}\n\n"
            time.sleep(max(1, int(interval)))

    return Response(generate(), mimetype="text/event-stream")


__all__ = ["dashboard_metrics", "dashboard_stream"]
