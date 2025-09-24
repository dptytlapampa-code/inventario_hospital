"""Application factory for the Inventario Hospital system."""
from __future__ import annotations

from pathlib import Path

from flask import Flask, render_template

from config import Config
from app.extensions import configure_logging, init_extensions, login_manager
from app.utils import build_select_attrs, render_input_field


def create_app(config_class: type[Config] | Config = Config) -> Flask:
    """Create and configure a fully featured Flask application."""

    app = Flask(__name__, instance_relative_config=False)
    if isinstance(config_class, type):
        app.config.from_object(config_class)
    else:
        app.config.from_object(config_class)

    upload_root = Path(app.config["UPLOAD_FOLDER"])
    upload_root.mkdir(parents=True, exist_ok=True)
    for key, folder in {
        "ADJUNTOS_UPLOAD_FOLDER": upload_root / app.config.get("ADJUNTOS_SUBFOLDER", "adjuntos"),
        "DOCSCAN_UPLOAD_FOLDER": upload_root / app.config.get("DOCSCAN_SUBFOLDER", "docscan"),
    }.items():
        folder.mkdir(parents=True, exist_ok=True)
        app.config[key] = str(folder)

    configure_logging(app)
    init_extensions(app)

    app.jinja_env.globals.setdefault("render_input_field", render_input_field)
    app.jinja_env.globals.setdefault("build_select_attrs", build_select_attrs)

    from app.models.usuario import Usuario  # imported lazily to avoid circular imports

    @login_manager.user_loader
    def load_user(user_id: str) -> Usuario | None:  # type: ignore[override]
        if not user_id:
            return None
        try:
            return Usuario.query.get(int(user_id))
        except (ValueError, TypeError):  # pragma: no cover - defensive
            return None

    from app.routes.actas import actas_bp
    from app.routes.adjuntos import adjuntos_bp
    from app.routes.auth import auth_bp
    from app.routes.docscan import docscan_bp
    from app.routes.equipos import equipos_bp
    from app.routes.insumos import insumos_bp
    from app.routes.licencias.routes import licencias_bp
    from app.routes.main import main_bp
    from app.routes.permisos import permisos_bp
    from app.routes.search import search_bp
    from app.routes.ubicaciones import ubicaciones_bp

    for blueprint in (
        auth_bp,
        main_bp,
        equipos_bp,
        insumos_bp,
        ubicaciones_bp,
        adjuntos_bp,
        docscan_bp,
        permisos_bp,
        actas_bp,
        search_bp,
        licencias_bp,
    ):
        app.register_blueprint(blueprint)

    app.add_url_rule("/", endpoint="index", view_func=app.view_functions["main.index"])

    @app.errorhandler(404)
    def not_found(error):  # type: ignore[override]
        return render_template("errors/404.html"), 404

    return app


__all__ = ["create_app"]
