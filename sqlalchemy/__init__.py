"""Minimal SQLAlchemy stubs for tests.

This module provides just enough structure for the application code to run
without installing the real SQLAlchemy dependency. It is *not* a replacement
for the actual library.
"""

class String:
    def __init__(self, *args, **kwargs) -> None:
        pass


class Boolean:
    def __init__(self, *args, **kwargs) -> None:
        pass


class DateTime:
    def __init__(self, *args, **kwargs) -> None:
        pass


class Enum:
    def __init__(self, enum, name: str | None = None) -> None:
        self.enum = enum
        self.name = name


class ForeignKey:
    def __init__(self, target, *args, **kwargs) -> None:
        self.target = target


class Index:
    def __init__(self, name: str, *columns) -> None:
        self.name = name
        self.columns = columns


class Integer:
    def __init__(self, *args, **kwargs) -> None:
        pass


class _Func:
    def now(self):  # pragma: no cover - simple stub
        return None


func = _Func()

__all__ = [
    "String",
    "Boolean",
    "DateTime",
    "Enum",
    "ForeignKey",
    "Index",
    "Integer",
    "func",
]
