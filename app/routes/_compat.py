"""Compat helpers for environments without Flask installed.

This module mirrors the minimal subset of Flask/Flask-Login APIs used by the
blueprint stubs in the test environment.  When Flask is available the real
objects are imported; otherwise lightweight fallbacks are provided so the
modules remain importable during unit tests.
"""

from __future__ import annotations

from typing import Any, Callable

try:  # pragma: no cover - executed only when Flask is installed
    from flask import Blueprint, flash, redirect, render_template, request, url_for
    from flask_login import login_required
except ModuleNotFoundError:  # pragma: no cover - simple shims for tests
    class Blueprint:  # type: ignore
        """Very small stand-in for :class:`flask.Blueprint`."""

        def __init__(self, name: str, import_name: str, url_prefix: str | None = None):
            self.name = name
            self.import_name = import_name
            self.url_prefix = url_prefix
            self.routes: list[tuple[str, dict[str, Any], Callable[..., Any]]] = []

        def route(self, rule: str, **options: Any) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
            def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
                self.routes.append((rule, options, func))
                return func

            return decorator

    def flash(message: str, category: str = "message") -> dict[str, str]:  # type: ignore
        return {"message": message, "category": category}

    def redirect(location: str) -> str:  # type: ignore
        return location

    def render_template(template_name: str, **context: Any) -> str:  # type: ignore
        return template_name

    def url_for(endpoint: str, **values: Any) -> str:  # type: ignore
        return endpoint

    def login_required(func: Callable[..., Any]) -> Callable[..., Any]:  # type: ignore
        return func

    class _Request:
        args: dict[str, Any] = {}
        form: dict[str, Any] = {}

    request = _Request()  # type: ignore

__all__ = ["Blueprint", "flash", "redirect", "render_template", "request", "url_for", "login_required"]
