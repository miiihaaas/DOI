from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user
from app import db, limiter
from app.models.user import User
from app.models.sponsor import Sponsor

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/login", methods=["GET", "POST"])
@limiter.limit("5 per minute")
def login():
    """Prijava korisnika."""
    # Redirect if already logged in
    if current_user.is_authenticated:
        return redirect(url_for("main.dashboard"))
    
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        
        # Validate input
        if not email or not password:
            flash("Email i lozinka su obavezni.", "error")
            return render_template("auth/login.html", title="Prijava")
        
        # Find user by email
        user = User.get_by_email(email)
        
        if user and user.check_password(password):
            # Successful login
            login_user(user)
            user.update_last_login()
            
            flash(f"Dobrodošli, {user.full_name}!", "success")
            
            # Redirect to next page or dashboard
            next_page = request.args.get('next')
            if next_page:
                return redirect(next_page)
            return redirect(url_for("main.dashboard"))
        else:
            # Failed login
            flash("Neispravni podaci za prijavu.", "error")
    
    return render_template("auth/login.html", title="Prijava")


@auth_bp.route("/logout", methods=["POST"])
@login_required
def logout():
    """Odjava korisnika."""
    user_name = current_user.full_name
    logout_user()
    flash(f"Uspešno ste se odjavili, {user_name}.", "success")
    return redirect(url_for("auth.login"))


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    """Registracija novog korisnika."""
    if request.method == "POST":
        # TODO: Implementirati registraciju kada bude User model
        flash("Registracija nije još implementirana.", "info")
        return redirect(url_for("auth.login"))

    return render_template("auth/register.html", title="Registracija")
