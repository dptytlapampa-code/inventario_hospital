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
load_dotenv(BASE_DIR / ".env")


def _database_uri_from_env() -> str:
    """Return the configured SQLAlchemy database URI.

    The URI can be provided explicitly via ``SQLALCHEMY_DATABASE_URI``.  When
    omitted, the function selects sensible defaults depending on the execution
    context: in the test suite it relies on the in-memory SQLite engine, while
    in local development it creates ``inventario.db`` next to ``config.py``.
    Production deployments still require an explicit URI (typically pointing to
    PostgreSQL) to avoid accidentally persisting data to SQLite.
    """

    env_name = (
        os.getenv("FLASK_ENV")
        or os.getenv("ENV")
        or os.getenv("APP_ENV")
        or "production"
    ).lower()

    uri = os.getenv("SQLALCHEMY_DATABASE_URI")

    if uri:
        return uri

    if (
        env_name in {"test", "testing"}
        or os.getenv("PYTEST_CURRENT_TEST")
        or "pytest" in sys.modules
    ):
        LOGGER.debug(
            "Defaulting SQLALCHEMY_DATABASE_URI to in-memory SQLite for the test suite."
        )
        return "sqlite:///:memory:"

    flask_env = os.getenv("FLASK_ENV", "").lower()
    if env_name in {"production", "prod"} or flask_env == "production":
        raise RuntimeError(
            "SQLALCHEMY_DATABASE_URI must be configured for production environments."
        )

    sqlite_path = BASE_DIR / "inventario.db"
    LOGGER.info("Using SQLite database at %s", sqlite_path)
    return f"sqlite:///{sqlite_path}"


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

    DEFAULT_PAGE_SIZE: int = int(os.getenv("DEFAULT_PAGE_SIZE", 20))
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
