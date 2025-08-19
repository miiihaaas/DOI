from flask import Blueprint, render_template, request
from flask_login import login_required

main_bp = Blueprint("main", __name__)


@main_bp.route("/")
def index():
    """Glavna stranica aplikacije."""
    return render_template("index.html", title="DOI Management System")


@main_bp.route("/dashboard")
@login_required
def dashboard():
    """Dashboard stranica - zaštićena autentifikacijom."""
    return render_template("dashboard.html", title="Dashboard")
