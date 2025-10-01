"""Custom Flask CLI commands for local development utilities."""
from __future__ import annotations

import click
from flask import Flask, current_app
from flask.cli import with_appcontext
from sqlalchemy import select
from sqlalchemy.orm import joinedload

from app.extensions import db


def register_commands(app: Flask) -> None:
    """Register the project's custom CLI commands."""

    @app.cli.group("seed")
    def seed_group() -> None:
        """Comandos de carga de datos iniciales."""

    @seed_group.command("demo")
    @with_appcontext
    def seed_demo_command() -> None:
        """Populate the database with demo data and default credentials."""

        from seeds.demo_seed import ensure_superadmin, load_demo_data

        ensure_superadmin(db.session)
        load_demo_data(db)
        db.session.commit()
        click.secho(
            "Seed de demo cargado. Usuario admin / 123456 disponible.", fg="green"
        )

    @app.cli.command("promote-superadmin")
    @click.option(
        "--username",
        "username",
        required=True,
        help="Nombre de usuario a promover al rol Superadmin.",
    )
    @with_appcontext
    def promote_superadmin_command(username: str) -> None:
        """Promote an existing user to the Superadmin role."""

        from seeds.demo_seed import ensure_superadmin, promote_to_superadmin

        superadmin_user = ensure_superadmin(db.session)
        promoted = promote_to_superadmin(
            db.session, username=username, role=superadmin_user.rol
        )
        if promoted is None:
            click.secho(
                f"Usuario '{username}' no encontrado. No se realizaron cambios.",
                fg="red",
            )
            db.session.commit()
            return

        current_app.logger.info(
            "Usuario %s promovido a Superadmin por CLI.", promoted.username
        )
        db.session.commit()
        click.secho(
            f"Usuario '{promoted.username}' ahora es Superadmin y está activo.",
            fg="green",
        )

    @app.cli.command("list-perms")
    @with_appcontext
    def list_permissions_command() -> None:
        """List the currently registered role permissions."""

        from app.models import Permiso

        stmt = (
            select(Permiso)
            .options(joinedload(Permiso.rol), joinedload(Permiso.hospital))
            .order_by(Permiso.rol_id, Permiso.modulo, Permiso.hospital_id)
        )
        permisos = db.session.execute(stmt).scalars().all()
        if not permisos:
            click.echo("No hay permisos registrados en la base de datos.")
            db.session.commit()
            return

        click.echo("Rol           | Módulo       | Ámbito       | Acciones")
        click.echo("-" * 60)
        for permiso in permisos:
            acciones: list[str] = []
            if permiso.can_read:
                acciones.append("read")
            if permiso.can_write:
                acciones.append("write")
            if permiso.allow_export:
                acciones.append("export")
            scope = permiso.hospital.nombre if permiso.hospital else "global"
            click.echo(
                f"{permiso.rol.nombre:<13} {permiso.modulo.value:<12} {scope:<12}"
                f" -> {', '.join(acciones) if acciones else 'sin acciones'}"
            )
        db.session.commit()


__all__ = ["register_commands"]
