from flask import Blueprint, render_template, request

main_bp = Blueprint("main", __name__)


@main_bp.route("/")
def index():
    """Glavna stranica aplikacije."""
    return render_template("index.html", title="DOI Management System")


@main_bp.route("/dashboard")
def dashboard():
    """Dashboard stranica - potrebna autentifikacija u budućnosti."""
    return render_template("dashboard.html", title="Dashboard")
