"""Minimal application stubs used solely for testing without Flask."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Any, Optional

from app.models.user import USERNAME_TABLE
from licencias import usuario_con_licencia_activa


@dataclass
class Response:
    status_code: int
    headers: Dict[str, str] = field(default_factory=dict)


class SimpleClient:
    def __init__(self, app: SimpleApp) -> None:
        self.app = app

    def post(self, path: str, data: Optional[Dict[str, Any]] = None, follow_redirects: bool = False) -> Response:
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
    def __init__(self) -> None:
        self.config: Dict[str, Any] = {}
        self.logged_in = False

    def test_client(self) -> SimpleClient:
        return SimpleClient(self)


def create_app() -> SimpleApp:
    return SimpleApp()


__all__ = ["create_app"]
