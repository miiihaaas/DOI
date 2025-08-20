from flask import Blueprint, render_template, request, redirect, url_for, flash

from flask_login import login_required

publications_bp = Blueprint("publications", __name__)


@publications_bp.route("/")
@login_required
def index():
    """Lista svih publikacija."""
    # TODO: Implementirati sa Publication modelom
    return render_template("publications/index.html", title="Publikacije")


@publications_bp.route("/create", methods=["GET", "POST"])
@login_required
def create():
    """Kreiranje nove publikacije."""
    if request.method == "POST":
        # TODO: Implementirati kreiranje publikacije kada bude Publication model
        flash("Kreiranje publikacije nije još implementirano.", "info")
        return redirect(url_for("publications.index"))

    return render_template("publications/create.html", title="Nova publikacija")


@publications_bp.route("/<int:publication_id>")
@login_required
def detail(publication_id):
    """Detalji o publikaciji."""
    # TODO: Implementirati sa Publication modelom
    return render_template(
        "publications/detail.html", title=f"Publikacija #{publication_id}"
    )


@publications_bp.route("/<int:publication_id>/edit", methods=["GET", "POST"])
@login_required
def edit(publication_id):
    """Uređivanje publikacije."""
    if request.method == "POST":
        # TODO: Implementirati uređivanje kada bude Publication model
        flash("Uređivanje publikacije nije još implementirano.", "info")
        return redirect(url_for("publications.detail", publication_id=publication_id))

    return render_template(
        "publications/edit.html", title=f"Uredi publikaciju #{publication_id}"
    )
