"""API endpoints serving dashboard metrics."""
from __future__ import annotations

from flask import jsonify
from flask_login import login_required

from app.services.dashboard_service import collect_dashboard_metrics

from . import api_bp


@api_bp.route("/dashboard/metrics")
@login_required
def dashboard_metrics():
    """Return aggregated metrics for the realtime dashboard."""

    payload = collect_dashboard_metrics()
    return jsonify(payload)


__all__ = ["dashboard_metrics"]
