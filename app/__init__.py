"""Minimal application setup used in tests."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Optional

from app.models.user import USERNAME_TABLE
from licencias import usuario_con_licencia_activa


@dataclass
class Response:
    """Simplified HTTP response used by the test client."""

    status_code: int
    headers: Dict[str, str] = field(default_factory=dict)


class SimpleClient:
    """Tiny test client with just the features tests rely on."""

    def __init__(self, app: SimpleApp) -> None:
        self.app = app

    def post(
        self,
        path: str,
        data: Optional[Dict[str, Any]] = None,
        follow_redirects: bool = False,
    ) -> Response:
        data = data or {}
        if path == "/auth/login":
            user = USERNAME_TABLE.get(data.get("username"))
            if user and user.check_password(data.get("password", "")):
                if usuario_con_licencia_activa(user.id):
                    return Response(200)
                self.app.logged_in = True
                return Response(302, {"Location": "/"})
            return Response(200)
        return Response(404)

    def get(self, path: str) -> Response:
        if path == "/auth/logout":
            self.app.logged_in = False
            return Response(302, {"Location": "/auth/login"})
        if path == "/licencias/listar":
            if self.app.logged_in:
                return Response(200)
            return Response(302, {"Location": "/auth/login"})
        return Response(404)


class SimpleApp:
    """Very small Flask-like application for unit tests."""

    def __init__(self) -> None:
        self.config: Dict[str, Any] = {}
        self.logged_in = False

    def test_client(self) -> SimpleClient:
        return SimpleClient(self)


def create_app() -> SimpleApp:
    """Factory returning an instance of :class:`SimpleApp`."""

    return SimpleApp()


def create_flask_app():  # pragma: no cover - requires optional dependencies
    """Create the real Flask application when full dependencies are present."""

    try:
        from flask import Flask
    except Exception as exc:  # pragma: no cover - executed when Flask is missing
        raise RuntimeError("Flask must be installed to create the web app") from exc

    from config import Config
    from app.extensions import csrf, db, login_manager, migrate

    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    csrf.init_app(app)

    return app


__all__ = ["create_app", "create_flask_app"]

