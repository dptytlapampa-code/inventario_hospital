"""Restore the Superadmin password to the configured default value."""

from __future__ import annotations

import logging
from typing import Final

from flask import current_app

from app import create_app, db
from app.models import Usuario
from config import Config
from seeds.demo_seed import ensure_superadmin

LOGGER = logging.getLogger(__name__)
DEFAULT_USERNAME: Final[str] = "admin"


def _resolve_password() -> str:
    """Return the configured default password used for bootstrap accounts."""

    password = current_app.config.get("DEFAULT_PASSWORD")
    if password:
        return password

    return Config.DEFAULT_PASSWORD


def main() -> None:
    """Reset the Superadmin password, creating the account when necessary."""

    app = create_app()
    with app.app_context():
        password = _resolve_password()
        usuario: Usuario = ensure_superadmin(
            db.session,
            username=DEFAULT_USERNAME,
            password=password,
        )
        db.session.commit()

        LOGGER.info(
            "Password del usuario %s restaurada al valor por defecto.",
            usuario.username,
        )
        print(
            "La contraseña del usuario 'admin' se actualizó correctamente."
            f" Nuevo password: {password}"
        )


if __name__ == "__main__":
    main()
