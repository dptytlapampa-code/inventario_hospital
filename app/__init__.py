from __future__ import annotations

from flask import Flask, request, redirect, session

from app.models.user import USERNAME_TABLE
from licencias import usuario_con_licencia_activa


def create_app() -> Flask:
    """Create and configure the Flask application."""
    app = Flask(__name__)
    app.config.from_object("config.Config")

    @app.route("/auth/login", methods=["GET", "POST"])
    def login() -> tuple[str, int] | str:
        """Simple login route used in tests.

        It validates the provided credentials against the in-memory user table
        and stores the user identifier in the session when authentication is
        successful. Users with an approved license are denied access as defined
        in ``licencias.usuario_con_licencia_activa``.
        """
        if request.method == "POST":
            username = request.form.get("username")
            password = request.form.get("password", "")
            user = USERNAME_TABLE.get(username)
            if user and user.check_password(password):
                if usuario_con_licencia_activa(user.id):
                    # License active: deny login with 200 OK as tests expect
                    return "", 200
                session["user_id"] = user.id
                return redirect("/")
            return "", 200
        return "", 200

    @app.route("/licencias/listar")
    def listar_licencias() -> tuple[str, int] | str:
        """Protected route that requires a logged in user."""
        if not session.get("user_id"):
            return redirect("/auth/login")
        return "", 200

    return app


__all__ = ["create_app"]
