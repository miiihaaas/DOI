from flask import Blueprint, render_template, request, redirect, url_for, flash

# from flask_login import login_required, current_user

members_bp = Blueprint("members", __name__)


@members_bp.route("/")
def index():
    """Lista svih članова organizacije."""
    # TODO: Implementirati sa Member modelom
    return render_template("members/index.html", title="Članovi")


@members_bp.route("/create", methods=["GET", "POST"])
def create():
    """Kreiranje novog člana."""
    if request.method == "POST":
        # TODO: Implementirati kreiranje člana kada bude Member model
        flash("Kreiranje člana nije još implementirano.", "info")
        return redirect(url_for("members.index"))

    return render_template("members/create.html", title="Novi član")


@members_bp.route("/<int:member_id>")
def detail(member_id):
    """Detalji o članu."""
    # TODO: Implementirati sa Member modelom
    return render_template("members/detail.html", title=f"Član #{member_id}")


@members_bp.route("/<int:member_id>/edit", methods=["GET", "POST"])
def edit(member_id):
    """Uređivanje člana."""
    if request.method == "POST":
        # TODO: Implementirati uređivanje kada bude Member model
        flash("Uređivanje člana nije još implementirano.", "info")
        return redirect(url_for("members.detail", member_id=member_id))

    return render_template("members/edit.html", title=f"Uredi član #{member_id}")
