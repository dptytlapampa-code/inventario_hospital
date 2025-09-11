"""WSGI entry point for running the Flask application."""

from app import create_app


app = create_app()


if __name__ == "__main__":  # pragma: no cover - manual execution helper
    app.run()
