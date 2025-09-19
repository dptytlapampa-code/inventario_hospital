"""WSGI entry point for running the Flask application."""

from app import create_app, create_flask_app


try:  # pragma: no cover - depends on optional Flask installation
    app = create_flask_app()
except RuntimeError:  # Fall back to the lightweight stub used in tests
    app = create_app()


if __name__ == "__main__":  # pragma: no cover - manual execution helper
    app.run()
