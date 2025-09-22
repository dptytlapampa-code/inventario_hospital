"""Centralised Flask extension instances."""
from __future__ import annotations

import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Any

from flask_login import LoginManager
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import CSRFProtect


try:  # pragma: no cover - runtime dependency handling
    from flask_bcrypt import Bcrypt  # type: ignore
except ModuleNotFoundError:  # pragma: no cover - fallback for offline envs
    from app.passwords import PasswordHasher as Bcrypt


db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
csrf = CSRFProtect()
bcrypt = Bcrypt()


def init_extensions(app: Any) -> None:
    """Initialise extensions with the given Flask ``app``."""

    db.init_app(app)
    migrate.init_app(app, db)
    csrf.init_app(app)
    bcrypt.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = "auth.login"


def configure_logging(app: Any) -> None:
    """Configure application logging according to app config."""

    level = getattr(logging, str(app.config.get("LOG_LEVEL", "INFO")).upper(), logging.INFO)
    logging.basicConfig(level=level)

    log_file = app.config.get("LOG_FILE")
    if log_file:
        handler = RotatingFileHandler(Path(log_file), maxBytes=1_048_576, backupCount=5)
        handler.setLevel(level)
        handler.setFormatter(
            logging.Formatter(
                "%(asctime)s [%(levelname)s] %(name)s - %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S",
            )
        )
        app.logger.addHandler(handler)


__all__ = ["db", "migrate", "login_manager", "csrf", "bcrypt", "init_extensions", "configure_logging"]
