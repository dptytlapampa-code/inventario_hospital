from flask import Flask, render_template
from flask_login import LoginManager

from app.routes.auth import auth_bp
from app.routes.licencias.routes import licencias_bp
from app.models.user import USERS

login_manager = LoginManager()
login_manager.login_view = "auth.login"


@login_manager.user_loader
def load_user(user_id: str):
    return USERS.get(int(user_id))


def create_app() -> Flask:
    app = Flask(__name__)
    app.config["SECRET_KEY"] = "dev-secret-key"

    login_manager.init_app(app)

    app.register_blueprint(auth_bp)
    app.register_blueprint(licencias_bp)

    @app.route("/")
    def index():
        return render_template("index.html")

    return app


__all__ = ["create_app", "login_manager"]
