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
        self.blueprints: Dict[str, Any] = {}

    def test_client(self) -> SimpleClient:
        return SimpleClient(self)

    def register_blueprint(self, blueprint: Any) -> None:
        """Store blueprints so tests can introspect registrations."""

        name = getattr(blueprint, "name", repr(blueprint))
        self.blueprints[name] = blueprint


def create_app() -> SimpleApp:
    """Factory returning an instance of :class:`SimpleApp`."""

    app = SimpleApp()

    try:  # pragma: no cover - blueprints may rely on optional deps
        from app.routes.actas import actas_bp
        from app.routes.adjuntos import adjuntos_bp
        from app.routes.docscan import docscan_bp
        from app.routes.equipos import equipos_bp
        from app.routes.insumos import insumos_bp
        from app.routes.main import main_bp
        from app.routes.permisos import permisos_bp
        from app.routes.search import search_bp
        from app.routes.ubicaciones import ubicaciones_bp
    except ModuleNotFoundError:
        return app

    for blueprint in (
        main_bp,
        equipos_bp,
        insumos_bp,
        ubicaciones_bp,
        adjuntos_bp,
        docscan_bp,
        permisos_bp,
        actas_bp,
        search_bp,
    ):
        app.register_blueprint(blueprint)

    return app


__all__ = ["create_app"]
