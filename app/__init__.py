"""Application factory for the Inventario Hospital system."""
from __future__ import annotations

from typing import Any, Callable

from flask import Flask

from config import Config
from app.extensions import csrf, db, login_manager, migrate
from app.models.user import USERNAME_TABLE


def _init_extension(extension: Any, app: Flask, *args: Any) -> None:
    """Safely call ``init_app`` on an extension if available."""

    init_app: Callable[..., Any] | None = getattr(extension, "init_app", None)
    if callable(init_app):
        init_app(app, *args)


def create_app(config_class: type[Config] | Config = Config) -> Flask:
    """Create and configure a fully featured Flask application."""

    app = Flask(__name__)

    if isinstance(config_class, type):
        app.config.from_object(config_class)
    else:
        app.config.from_object(config_class)

    _init_extension(db, app)

    if hasattr(migrate, "init_app") and callable(getattr(migrate, "init_app")):
        migrate.init_app(app, db)  # type: ignore[call-arg]
    else:
        _init_extension(migrate, app, db)

    _init_extension(login_manager, app)
    if hasattr(login_manager, "login_view"):
        login_manager.login_view = "auth.login"

    _init_extension(csrf, app)

    user_loader = getattr(login_manager, "user_loader", None)
    if callable(user_loader):

        @login_manager.user_loader  # type: ignore[misc]
        def load_user(username: str):  # pragma: no cover - flask-login handles errors
            return USERNAME_TABLE.get(username)

    else:  # pragma: no cover - fallback for minimal stubs during tests

        def load_user(username: str):
            return USERNAME_TABLE.get(username)

        setattr(login_manager, "user_callback", load_user)
        setattr(login_manager, "_user_callback", load_user)

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

    if "main.index" in app.view_functions:
        app.add_url_rule(
            "/",
            endpoint="index",
            view_func=app.view_functions["main.index"],
        )

    return app


__all__ = ["create_app"]
