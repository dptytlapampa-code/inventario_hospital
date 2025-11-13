"""Centralised configuration for the Inventario Hospital Flask app."""
from __future__ import annotations

import logging
import os
from datetime import timedelta
from pathlib import Path

from dotenv import load_dotenv

LOGGER = logging.getLogger(__name__)

BASE_DIR = Path(__file__).resolve().parent
ENV_PATH = BASE_DIR / ".env"
if ENV_PATH.exists():
    load_dotenv(ENV_PATH)


def _resolve_sqlite_path(filename: str) -> str:
    instance_dir = BASE_DIR / "instance"
    instance_dir.mkdir(exist_ok=True)
    return f"sqlite:///{(instance_dir / filename).resolve()}"


def _database_uri_from_env() -> str:
    """Determine the SQLAlchemy database URI honouring environment overrides."""

    explicit = os.getenv("SQLALCHEMY_DATABASE_URI") or os.getenv("DATABASE_URL")
    if explicit:
        return explicit

    db_host = os.getenv("DB_HOST") or os.getenv("POSTGRES_HOST")
    if db_host:
        db_user = os.getenv("DB_USER", os.getenv("POSTGRES_USER", "postgres"))
        db_password = os.getenv(
            "DB_PASSWORD", os.getenv("POSTGRES_PASSWORD", "postgres")
        )
        db_name = os.getenv("DB_NAME", os.getenv("POSTGRES_DB", "inventario"))
        db_port = os.getenv("DB_PORT", os.getenv("POSTGRES_PORT", "5432"))
        return f"postgresql+psycopg2://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"

    flask_env = os.getenv("FLASK_ENV", "").lower()
    app_env = os.getenv("APP_ENV", "").lower()
    env = os.getenv("ENV", "").lower()
    if flask_env in {"testing", "test"} or os.getenv("PYTEST_CURRENT_TEST"):
        return "sqlite:///:memory:"

    if app_env == "production" or env == "production" or flask_env == "production":
        LOGGER.warning(
            "Entorno de producción sin base configurada explícitamente; usando SQLite de emergencia."
        )

    return _resolve_sqlite_path("inventario.db")


def _bool_env(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.lower() in {"1", "true", "t", "yes", "y"}


def _upload_root() -> str:
    path = BASE_DIR / "uploads"
    path.mkdir(exist_ok=True)
    return str(path)


class Config:
    """Base configuration shared by all environments."""

    SECRET_KEY: str = os.getenv("SECRET_KEY", "change-me")
    SQLALCHEMY_DATABASE_URI: str = _database_uri_from_env()
    SQLALCHEMY_TRACK_MODIFICATIONS: bool = False
    SQLALCHEMY_ENGINE_OPTIONS = {"pool_pre_ping": True}

    AUTO_SEED_ON_START: bool = _bool_env("AUTO_SEED_ON_START")
    DEMO_SEED_VERBOSE: bool = _bool_env("DEMO_SEED_VERBOSE")

    SESSION_COOKIE_SECURE: bool = _bool_env("SESSION_COOKIE_SECURE")
    REMEMBER_COOKIE_DURATION = timedelta(days=30)

    UPLOAD_FOLDER: str = os.getenv("UPLOAD_FOLDER", _upload_root())
    ADJUNTOS_SUBFOLDER: str = os.getenv("ADJUNTOS_SUBFOLDER", "adjuntos")
    DOCSCAN_SUBFOLDER: str = os.getenv("DOCSCAN_SUBFOLDER", "docscan")
    EQUIPOS_SUBFOLDER: str = os.getenv("EQUIPOS_SUBFOLDER", "equipos")
    EQUIPOS_MAX_FILE_SIZE: int = int(os.getenv("EQUIPOS_MAX_FILE_SIZE", 10 * 1024 * 1024))
    MAX_CONTENT_LENGTH: int = int(os.getenv("MAX_CONTENT_LENGTH", 16 * 1024 * 1024))
    ALLOWED_EXTENSIONS: set[str] = set(
        filter(None, os.getenv("ALLOWED_EXTENSIONS", "pdf,jpg,jpeg,png").split(","))
    )

    SECURITY_PASSWORD_SALT: str = os.getenv("SECURITY_PASSWORD_SALT", "inventory-salt")

    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOG_FILE: str | None = os.getenv("LOG_FILE")

    DEFAULT_PAGE_SIZE: int = int(os.getenv("DEFAULT_PAGE_SIZE", 25))
    DASHBOARD_CACHE_TIMEOUT: int = int(os.getenv("DASHBOARD_CACHE_TIMEOUT", 300))

    WEASYPRINT_BASE_URL: str = os.getenv("WEASYPRINT_BASE_URL", str(BASE_DIR))


class TestingConfig(Config):
    TESTING = True
    WTF_CSRF_ENABLED = False
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    SERVER_NAME = "localhost"


class DevelopmentConfig(Config):
    DEBUG = True


class ProductionConfig(Config):
    SESSION_COOKIE_SECURE = True
    REMEMBER_COOKIE_DURATION = timedelta(days=7)
    PREFERRED_URL_SCHEME = "https"
    LOG_LEVEL = os.getenv("LOG_LEVEL", "WARNING")
