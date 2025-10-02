"""Application configuration module.

This module centralises how environment variables are loaded and validated so
that the Flask app and ancillary scripts (CLI commands, seeds, runners) share
the same expectations.  The defaults favour a frictionless development
experience by automatically provisioning a SQLite database when no
``SQLALCHEMY_DATABASE_URI`` is provided, while keeping the ability to point to
PostgreSQL for staging and production deployments via the environment.
"""
from __future__ import annotations

import logging
import os
import sys
from datetime import timedelta
from pathlib import Path

from dotenv import load_dotenv

LOGGER = logging.getLogger(__name__)

BASE_DIR = Path(__file__).resolve().parent
# Cargar variables desde .env si está presente para que la configuración sea
# reproducible en entornos locales.
load_dotenv(BASE_DIR / ".env")


def _database_uri_from_env() -> str:
    """Resolve the SQLAlchemy database URI according to the environment."""

    uri = os.getenv("SQLALCHEMY_DATABASE_URI")
    if uri:
        return uri

    flask_env = os.getenv("FLASK_ENV", "").lower()

    if (
        flask_env in {"testing", "test"}
        or os.getenv("PYTEST_CURRENT_TEST")
        or "pytest" in sys.modules
    ):
        LOGGER.debug(
            "Defaulting SQLALCHEMY_DATABASE_URI to in-memory SQLite for the test suite."
        )
        return "sqlite:///:memory:"

    if flask_env == "development":
        LOGGER.info("Using default SQLite database for development.")
        return "sqlite:///inventario.db"

    if flask_env in {"production", "prod"} or os.getenv("ENV", "").lower() in {
        "production",
        "prod",
    } or os.getenv("APP_ENV", "").lower() in {"production", "prod"}:
        raise RuntimeError(
            "SQLALCHEMY_DATABASE_URI must be configured for production environments."
        )

    raise RuntimeError(
        "SQLALCHEMY_DATABASE_URI must be provided via the environment for this deployment."
    )


def _default_upload_dir() -> str:
    uploads = BASE_DIR / "uploads"
    uploads.mkdir(exist_ok=True)
    return str(uploads)


class Config:
    """Base configuration for all environments."""

    SECRET_KEY: str = os.getenv("SECRET_KEY", "change-me")
    SQLALCHEMY_DATABASE_URI: str = _database_uri_from_env()
    SQLALCHEMY_TRACK_MODIFICATIONS: bool = False
    SQLALCHEMY_ENGINE_OPTIONS = {"pool_pre_ping": True}
    AUTO_SEED_ON_START: bool = os.getenv("AUTO_SEED_ON_START", "0") in (
        "1",
        "true",
        "True",
    )
    DEMO_SEED_VERBOSE: bool = os.getenv("DEMO_SEED_VERBOSE", "0") in (
        "1",
        "true",
        "True",
    )

    SESSION_COOKIE_SECURE: bool = os.getenv("SESSION_COOKIE_SECURE", "false").lower() == "true"
    REMEMBER_COOKIE_DURATION = timedelta(days=30)

    UPLOAD_FOLDER: str = os.getenv("UPLOAD_FOLDER", _default_upload_dir())
    ADJUNTOS_SUBFOLDER: str = os.getenv("ADJUNTOS_SUBFOLDER", "adjuntos")
    DOCSCAN_SUBFOLDER: str = os.getenv("DOCSCAN_SUBFOLDER", "docscan")
    EQUIPOS_SUBFOLDER: str = os.getenv("EQUIPOS_SUBFOLDER", "equipos")
    EQUIPOS_MAX_FILE_SIZE: int = int(os.getenv("EQUIPOS_MAX_FILE_SIZE", 10 * 1024 * 1024))
    MAX_CONTENT_LENGTH: int = int(os.getenv("MAX_CONTENT_LENGTH", 16 * 1024 * 1024))
    ALLOWED_EXTENSIONS: set[str] = set(
        os.getenv("ALLOWED_EXTENSIONS", "pdf,jpg,jpeg,png").split(",")
    )

    SECURITY_PASSWORD_SALT: str = os.getenv("SECURITY_PASSWORD_SALT", "inventory-salt")

    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOG_FILE: str | None = os.getenv("LOG_FILE")

    DEFAULT_PAGE_SIZE: int = int(os.getenv("DEFAULT_PAGE_SIZE", 25))
    DASHBOARD_CACHE_TIMEOUT: int = int(os.getenv("DASHBOARD_CACHE_TIMEOUT", 300))

    WEASYPRINT_BASE_URL: str = os.getenv("WEASYPRINT_BASE_URL", str(BASE_DIR))


class TestingConfig(Config):
    """Configuration tailored for automated tests."""

    TESTING = True
    WTF_CSRF_ENABLED = False
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    SERVER_NAME = "localhost"


class DevelopmentConfig(Config):
    """Development configuration enabling debug helpers."""

    DEBUG = True


class ProductionConfig(Config):
    """Production hardened configuration."""

    SESSION_COOKIE_SECURE = True
    REMEMBER_COOKIE_DURATION = timedelta(days=7)
    PREFERRED_URL_SCHEME = "https"
    LOG_LEVEL = os.getenv("LOG_LEVEL", "WARNING")
