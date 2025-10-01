"""Compatibility entrypoint to run the demo seed manually."""
from __future__ import annotations

from app import create_app, db
from seeds.demo_seed import load_demo_data


def main() -> None:
    """Execute the demo data loader inside the Flask application context."""

    app = create_app()
    with app.app_context():
        load_demo_data(db)
        db.session.commit()
        app.logger.info("Datos de demo cargados correctamente.")


if __name__ == "__main__":
    main()
