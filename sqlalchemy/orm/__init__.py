"""Minimal subset of :mod:`sqlalchemy.orm` for tests."""
from __future__ import annotations

from typing import Any, Generic, TypeVar

T = TypeVar("T")


class DeclarativeBase:
    """Placeholder base class for declarative models.

    It accepts keyword arguments on initialization and simply assigns them as
    attributes, emulating the behavior of SQLAlchemy's declarative base where
    columns can be set via the constructor.
    """

    def __init__(self, **kwargs: Any) -> None:  # pragma: no cover - trivial
        for key, value in kwargs.items():
            setattr(self, key, value)


class Mapped(Generic[T]):
    """Type marker used for mapped attributes."""


def mapped_column(*args, **kwargs) -> Any:  # pragma: no cover - simple stub
    return None


def relationship(*args, **kwargs) -> Any:  # pragma: no cover - simple stub
    return None


__all__ = ["DeclarativeBase", "Mapped", "mapped_column", "relationship"]
