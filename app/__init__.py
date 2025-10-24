"""Application factory for the Inventario Hospital system."""
from __future__ import annotations

import os
import subprocess
import sys
from collections.abc import Mapping
from pathlib import Path
from typing import Any

import click
from alembic.script import ScriptDirectory
from flask import Flask, current_app, render_template
from flask.cli import with_appcontext
from flask_migrate import CommandError, upgrade as migrate_upgrade
from sqlalchemy import inspect, select
from sqlalchemy.orm import joinedload

from dotenv import load_dotenv

from config import Config
from app.assets import ensure_favicon
from app.extensions import configure_logging, db, init_extensions, login_manager
from app.security.rbac import has_role
from app.utils import (
    build_select_attrs,
    format_spanish_date,
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
        """Upgrade the database handling multiple Alembic heads safely."""

        try:
            heads = _get_alembic_heads()
            head_list = " ".join(heads)
            if len(heads) > 1:
                click.secho(
                    f"Se detectaron múltiples heads ({head_list}). Ejecutando 'flask db upgrade heads'...",
                    fg="yellow",
                )
                migrate_upgrade(revision="heads")
            else:
                migrate_upgrade()
        except CommandError as exc:  # pragma: no cover - CLI wrapper
            click.secho("Error al aplicar migraciones.", fg="red")
            click.secho("Tips: ejecutá 'flask db current', 'flask db heads' y 'flask db history' para más contexto.", fg="yellow")
            raise click.ClickException(str(exc)) from exc
        except Exception as exc:  # pragma: no cover - defensive guard
            click.secho("Fallo inesperado al aplicar migraciones.", fg="red")
            click.secho("Revisá la configuración de la base y el estado de Alembic.", fg="yellow")
            raise click.ClickException(str(exc)) from exc

        click.secho("Migraciones aplicadas correctamente.", fg="green")

    @app.cli.command("demo-seed")
    @click.option("--force", is_flag=True, help="Forzar seed aunque existan datos.")
    @with_appcontext
    def demo_seed_command(force: bool) -> None:
        """Carga datos de demo de forma idempotente."""

        from app.models import Usuario
        from seeds.demo_seed import load_demo_data

        if not force and db.session.query(Usuario).count() > 0:
            click.echo("Ya existen usuarios. Usa --force para resembrar (idempotente).")
            return
        load_demo_data(db)
        db.session.commit()
        click.echo("Datos de demo cargados.")


def create_app(config_class: type[Config] | Config = Config) -> Flask:
    """Create and configure a fully featured Flask application."""

    load_dotenv()
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

    with app.app_context():
        skip_auto_seed = os.getenv("AUTO_SEED_SKIP") == "1" or app.config.get("TESTING")
        is_prod = (
            app.config.get("ENV", "").lower() == "production"
            or app.config.get("FLASK_ENV") == "production"
        )
        if (
            not skip_auto_seed
            and app.config.get("AUTO_SEED_ON_START")
            and not is_prod
        ):
            insp = inspect(db.engine)
            if not insp.get_table_names():
                try:
                    migrations_dir = Path(app.root_path).parent / "migrations"
                    if migrations_dir.is_dir():
                        env = os.environ.copy()
                        env.setdefault("FLASK_APP", os.environ.get("FLASK_APP", "wsgi.py"))
                        env.setdefault("AUTO_SEED_SKIP", "1")
                        subprocess.run(
                            [sys.executable, "-m", "flask", "db", "upgrade"],
                            cwd=Path(app.root_path).parent,
                            check=True,
                            env=env,
                        )
                    else:
                        db.create_all()
                except Exception as exc:  # pragma: no cover - defensive branch
                    current_app.logger.warning(
                        "Auto-migrate fallback failed: %s. Trying create_all() for dev.",
                        exc,
                    )
                    db.create_all()

            try:
                from app.models import Usuario
                from seeds.demo_seed import load_demo_data

                if db.session.query(Usuario).count() == 0:
                    current_app.logger.info(
                        "Auto-seed: base sin usuarios, cargando datos demo…"
                    )
                    load_demo_data(db)
                    db.session.commit()
                    current_app.logger.info("Auto-seed: datos demo cargados.")
                elif app.config.get("DEMO_SEED_VERBOSE"):
                    current_app.logger.info(
                        "Auto-seed: ya hay datos, no se cargan demo."
                    )
            except Exception as exc:  # pragma: no cover - best effort guard
                current_app.logger.error(f"Auto-seed error: {exc}")
                db.session.rollback()

    app.jinja_env.globals.setdefault("render_input_field", render_input_field)
    app.jinja_env.globals.setdefault("build_select_attrs", build_select_attrs)
    app.jinja_env.globals.setdefault("normalize_enum_value", normalize_enum_value)
    app.jinja_env.globals.setdefault("humanize_bytes", humanize_bytes)
    app.jinja_env.globals.setdefault("has_role", has_role)
    app.jinja_env.filters.setdefault("enum_value", normalize_enum_value)
    app.jinja_env.filters.setdefault("humanize_bytes", humanize_bytes)
    app.jinja_env.filters.setdefault("combine", _combine_dicts)
    app.jinja_env.filters.setdefault("fecha", format_spanish_date)

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
    from app.routes.files import files_bp
    from app.routes.licencias.routes import licencias_bp
    from app.routes.main import main_bp
    from app.routes.permisos import permisos_bp
    from app.routes.search import search_bp
    from app.routes.search_api import search_api_bp
    from app.routes.reportes import reportes_bp
    from app.routes.usuarios import usuarios_bp
    from app.routes.vlans import vlans_bp
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
        files_bp,
        permisos_bp,
        auditoria_bp,
        actas_bp,
        search_bp,
        licencias_bp,
        api_bp,
        search_api_bp,
        ubicaciones_api_bp,
        reportes_bp,
        usuarios_bp,
        vlans_bp,
    ):
        app.register_blueprint(blueprint)

    app.add_url_rule("/", endpoint="index", view_func=app.view_functions["main.index"])

    # Materialise the favicon lazily so we avoid storing binary blobs in the
    # repository while still serving ``/static/favicon.ico`` and preventing the
    # browser from issuing 404 requests for the asset.
    ensure_favicon(app.static_folder)

    _register_cli(app)

    from app.cli import register_commands

    register_commands(app)

    @app.errorhandler(401)
    def unauthorized(error):  # type: ignore[override]
        return render_template("errors/401.html"), 401

    @app.errorhandler(403)
    def forbidden(error):  # type: ignore[override]
        return render_template("errors/403.html"), 403

    @app.errorhandler(404)
    def not_found(error):  # type: ignore[override]
        return render_template("errors/404.html"), 404

    from app.models import (
        Acta,
        ActaItem,
        Adjunto,
        Auditoria,
        Docscan,
        Equipo,
        EquipoAdjunto,
        EquipoHistorial,
        EstadoEquipo,
        Hospital,
        HospitalUsuarioRol,
        Insumo,
        InsumoMovimiento,
        InsumoSerie,
        Licencia,
        Modulo,
        MovimientoTipo,
        SerieEstado,
        Oficina,
        Permiso,
        Rol,
        Servicio,
        TipoActa,
        TipoAdjunto,
        TipoDocscan,
        TipoEquipo,
        TipoLicencia,
        Usuario,
        EquipoInsumo,
        EstadoLicencia,
        Vlan,
        VlanDispositivo,
    )

    _ = (
        Acta,
        ActaItem,
        Adjunto,
        Auditoria,
        Docscan,
        Equipo,
        EquipoAdjunto,
        EquipoHistorial,
        EstadoEquipo,
        Hospital,
        HospitalUsuarioRol,
        Insumo,
        InsumoMovimiento,
        InsumoSerie,
        Licencia,
        Modulo,
        MovimientoTipo,
        SerieEstado,
        Oficina,
        Permiso,
        Rol,
        Servicio,
        TipoActa,
        TipoAdjunto,
        TipoDocscan,
        TipoEquipo,
        TipoLicencia,
        Usuario,
        EquipoInsumo,
        EstadoLicencia,
        SerieEstado,
        Vlan,
        VlanDispositivo,
    )

    return app


__all__ = ["create_app"]
