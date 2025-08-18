from flask import Blueprint, render_template, request, redirect, url_for, flash

# from flask_login import login_user, logout_user, login_required, current_user

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    """Prijava korisnika - implementirati sa User modelom."""
    if request.method == "POST":
        # TODO: Implementirati logiku prijave kada bude User model
        flash("Prijava nije još implementirana.", "info")
        return redirect(url_for("main.index"))

    return render_template("auth/login.html", title="Prijava")


@auth_bp.route("/logout")
def logout():
    """Odjava korisnika."""
    # TODO: Implementirati logout_user() kada bude User model
    flash("Uspešno ste se odjavili.", "success")
    return redirect(url_for("main.index"))


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    """Registracija novog korisnika."""
    if request.method == "POST":
        # TODO: Implementirati registraciju kada bude User model
        flash("Registracija nije još implementirana.", "info")
        return redirect(url_for("auth.login"))

    return render_template("auth/register.html", title="Registracija")
