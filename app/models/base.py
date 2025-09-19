"""Declarative base linked to the Flask-SQLAlchemy extension."""
from __future__ import annotations

from app.extensions import db


class Base(db.Model):
    """Base class for SQLAlchemy models bound to the shared metadata."""

    __abstract__ = True


__all__ = ["Base"]
