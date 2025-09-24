"""WSGI entry point for running the Flask application."""

from __future__ import annotations

import os

from app import create_app


app = create_app()


if __name__ == "__main__":  # pragma: no cover - manual execution helper
    host = os.getenv("FLASK_RUN_HOST", "127.0.0.1")
    port = int(os.getenv("FLASK_RUN_PORT", "5000"))
    app.run(host=host, port=port)
