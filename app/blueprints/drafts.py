from flask import Blueprint, render_template, request, redirect, url_for, flash

from flask_login import login_required, current_user

drafts_bp = Blueprint("drafts", __name__)


@drafts_bp.route("/")
@login_required
def index():
    """Lista svih DOI draft-ova."""
    # TODO: Implementirati sa DOIDraft modelom
    return render_template("drafts/index.html", title="DOI Draft-ovi")


@drafts_bp.route("/create/<int:publication_id>", methods=["GET", "POST"])
@login_required
def create(publication_id):
    """Kreiranje novog DOI draft-a za publikaciju."""
    if request.method == "POST":
        # TODO: Implementirati kreiranje draft-a kada bude DOIDraft model
        flash("Kreiranje DOI draft-a nije još implementirano.", "info")
        return redirect(url_for("drafts.index"))

    return render_template("drafts/create.html", title="Novi DOI draft")


@drafts_bp.route("/<int:draft_id>")
@login_required
def detail(draft_id):
    """Detalji o DOI draft-u."""
    # TODO: Implementirati sa DOIDraft modelom
    return render_template("drafts/detail.html", title=f"DOI Draft #{draft_id}")


@drafts_bp.route("/<int:draft_id>/edit", methods=["GET", "POST"])
@login_required
def edit(draft_id):
    """Uređivanje DOI draft-a."""
    if request.method == "POST":
        # TODO: Implementirati uređivanje kada bude DOIDraft model
        flash("Uređivanje DOI draft-a nije još implementirano.", "info")
        return redirect(url_for("drafts.detail", draft_id=draft_id))

    return render_template("drafts/edit.html", title=f"Uredi DOI draft #{draft_id}")


@drafts_bp.route("/<int:draft_id>/generate-xml")
@login_required
def generate_xml(draft_id):
    """Generisanje Crossref XML fajla za DOI draft."""
    # TODO: Implementirati XML generisanje sa CrossrefXMLGenerator servisom
    flash("XML generisanje nije još implementirano.", "info")
    return redirect(url_for("drafts.detail", draft_id=draft_id))
