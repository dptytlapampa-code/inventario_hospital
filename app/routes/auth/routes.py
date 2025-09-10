from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import login_required, login_user, logout_user

from app.forms.login import LoginForm
from app.models.user import USERNAME_TABLE


auth_bp = Blueprint("auth", __name__, url_prefix="/auth")


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = USERNAME_TABLE.get(form.username.data)
        if user and user.check_password(form.password.data):
            login_user(user)
            next_page = request.args.get("next") or url_for("index")
            return redirect(next_page)
        flash("Usuario o contraseña inválidos", "error")
    return render_template("auth/login.html", form=form)


@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("auth.login"))
