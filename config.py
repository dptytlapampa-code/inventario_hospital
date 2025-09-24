"""Application configuration module."""
from __future__ import annotations

import os
from datetime import timedelta
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")


def _default_upload_dir() -> str:
    uploads = BASE_DIR / "uploads"
    uploads.mkdir(exist_ok=True)
    return str(uploads)


class Config:
    """Base configuration for all environments."""

    SECRET_KEY: str = os.getenv("SECRET_KEY", "change-me")
    SQLALCHEMY_DATABASE_URI: str = os.getenv(
        "DATABASE_URL", f"sqlite:///{BASE_DIR / 'inventario.db'}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS: bool = False
    SQLALCHEMY_ENGINE_OPTIONS = {"pool_pre_ping": True}

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
