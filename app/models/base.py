"""Base model for SQLAlchemy models used in the application."""
from __future__ import annotations

from app.extensions import db


class Base(db.Model):
    """Base class for all ORM models."""

    __abstract__ = True


__all__ = ["Base"]
