"""Application factory for the Inventario Hospital system."""
from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import Any

import click
from alembic.script import ScriptDirectory
from flask import Flask, current_app, render_template
from flask.cli import with_appcontext
from flask_migrate import CommandError, merge as migrate_merge, upgrade as migrate_upgrade
from sqlalchemy import select
from sqlalchemy.orm import joinedload

from config import Config
from app.assets import ensure_favicon
from app.extensions import configure_logging, db, init_extensions, login_manager
from app.security.rbac import has_role
from app.utils import (
    build_select_attrs,
    humanize_bytes,
    normalize_enum_value,
    render_input_field,
)


def _combine_dicts(
    value: Mapping[str, Any] | None, other: Mapping[str, Any] | None
) -> dict[str, Any]:
    """Return a new dict with the contents of ``value`` and ``other``.

    The filter mirrors Jinja's ``combine`` filter from newer versions, keeping
    the original dictionaries untouched and letting keys from ``other``
    override those in ``value`` when they overlap.
    """

    combined: dict[str, Any] = {}
    for mapping in (value, other):
        if not mapping:
            continue
        try:
            combined.update(mapping)
        except (TypeError, ValueError):
            combined.update(dict(mapping))
    return combined


def _get_alembic_heads() -> list[str]:
    """Return the list of revision heads known to Alembic."""

    migrate_config = current_app.extensions.get("migrate")
    if not migrate_config:
        raise click.ClickException("Flask-Migrate no está configurado en la aplicación actual.")

    alembic_config = migrate_config.migrate.get_config(directory=migrate_config.directory)
    script = ScriptDirectory.from_config(alembic_config)
    return script.get_heads()


def _register_cli(app: Flask) -> None:
    """Register custom Flask CLI commands used by the project."""

    @app.cli.command("dbsafe-upgrade")
    @with_appcontext
    def dbsafe_upgrade_command() -> None:
        """Upgrade the database after merging stray Alembic heads if needed."""

        try:
            heads = _get_alembic_heads()
            if len(heads) > 1:
                revisions = " ".join(heads)
                click.secho(
                    f"Se detectaron {len(heads)} heads de Alembic. Realizando merge automático...",
                    fg="yellow",
                )
                migrate_merge(revisions=revisions, message="auto merge heads")
            migrate_upgrade()
        except CommandError as exc:  # pragma: no cover - CLI wrapper
            raise click.ClickException(str(exc)) from exc

        click.secho("Migraciones aplicadas correctamente.", fg="green")

    @app.cli.command("seed")
    @with_appcontext
    def seed_command() -> None:
        """Populate the database with deterministic seed data."""

        from seeds.seed import run_seed

        run_seed(current_app)


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
        "EQUIPOS_UPLOAD_FOLDER": upload_root / app.config.get("EQUIPOS_SUBFOLDER", "equipos"),
    }.items():
        folder.mkdir(parents=True, exist_ok=True)
        app.config[key] = str(folder)

    configure_logging(app)
    init_extensions(app)

    app.jinja_env.globals.setdefault("render_input_field", render_input_field)
    app.jinja_env.globals.setdefault("build_select_attrs", build_select_attrs)
    app.jinja_env.globals.setdefault("normalize_enum_value", normalize_enum_value)
    app.jinja_env.globals.setdefault("humanize_bytes", humanize_bytes)
    app.jinja_env.globals.setdefault("has_role", has_role)
    app.jinja_env.filters.setdefault("enum_value", normalize_enum_value)
    app.jinja_env.filters.setdefault("humanize_bytes", humanize_bytes)
    app.jinja_env.filters.setdefault("combine", _combine_dicts)

    from app.models.usuario import Usuario  # imported lazily to avoid circular imports

    @login_manager.user_loader
    def load_user(user_id: str) -> Usuario | None:  # type: ignore[override]
        if not user_id:
            return None
        try:
            user_pk = int(user_id)
        except (ValueError, TypeError):  # pragma: no cover - defensive
            return None
        stmt = (
            select(Usuario)
            .options(joinedload(Usuario.rol))
            .where(Usuario.id == user_pk)
        )
        return db.session.execute(stmt).scalar_one_or_none()

    from app.routes.actas import actas_bp
    from app.routes.adjuntos import adjuntos_bp
    from app.routes.api import api_bp
    from app.routes.auth import auth_bp
    from app.routes.auditoria import auditoria_bp
    from app.routes.docscan import docscan_bp
    from app.routes.equipos import equipos_bp
    from app.routes.insumos import insumos_bp
    from app.routes.licencias.routes import licencias_bp
    from app.routes.main import main_bp
    from app.routes.permisos import permisos_bp
    from app.routes.search import search_bp
    from app.routes.search_api import search_api_bp
    from app.routes.usuarios import usuarios_bp
    from app.routes.ubicaciones import ubicaciones_bp
    from app.routes.ubicaciones_api import ubicaciones_api_bp

    for blueprint in (
        auth_bp,
        main_bp,
        equipos_bp,
        insumos_bp,
        ubicaciones_bp,
        adjuntos_bp,
        docscan_bp,
        permisos_bp,
        auditoria_bp,
        actas_bp,
        search_bp,
        licencias_bp,
        api_bp,
        search_api_bp,
        ubicaciones_api_bp,
        usuarios_bp,
    ):
        app.register_blueprint(blueprint)

    app.add_url_rule("/", endpoint="index", view_func=app.view_functions["main.index"])

    # Materialise the favicon lazily so we avoid storing binary blobs in the
    # repository while still serving ``/static/favicon.ico`` and preventing the
    # browser from issuing 404 requests for the asset.
    ensure_favicon(app.static_folder)

    _register_cli(app)

    @app.errorhandler(401)
    def unauthorized(error):  # type: ignore[override]
        return render_template("errors/401.html"), 401

    @app.errorhandler(403)
    def forbidden(error):  # type: ignore[override]
        return render_template("errors/403.html"), 403

    @app.errorhandler(404)
    def not_found(error):  # type: ignore[override]
        return render_template("errors/404.html"), 404

    return app


__all__ = ["create_app"]
