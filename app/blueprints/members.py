from flask import Blueprint, render_template, request, redirect, url_for, flash, abort, jsonify
from flask_login import login_required, current_user
from sqlalchemy import or_
from app import db
from app.models.member import Member
from app.models.publication import Publication
from app.models.sponsor import Sponsor
from app.services.member_service import MemberService
from app.forms.member_forms import MemberCreateForm, MemberEditForm, MemberSearchForm
from app.utils.pagination import paginate_query

members_bp = Blueprint("members", __name__, template_folder='templates')


@members_bp.route("/")
@login_required
def index():
    """Lista svih član organizacije sa search i pagination."""
    page = request.args.get('page', 1, type=int)
    per_page = 10
    search = request.args.get('search', '')
    status = request.args.get('status', 'all')  # all, active, inactive
    
    search_form = MemberSearchForm()
    
    # Get the singleton sponsor
    sponsor = Sponsor.get_instance()
    if not sponsor:
        flash("Nema konfigurisan sponsor. Kontaktirajte administratora.", "error")
        return redirect(url_for('main.index'))
    
    # Get members for current sponsor with search and filtering
    members_data = MemberService.get_members_for_sponsor(
        sponsor_id=sponsor.id,
        page=page,
        per_page=per_page,
        search=search,
        status=status
    )
    
    # Get statistics
    stats = MemberService.get_member_statistics(sponsor.id)
    
    return render_template(
        "members/list.html", 
        title="Članovi",
        members_pagination=members_data,
        search_form=search_form,
        search=search,
        status=status,
        stats=stats
    )


@members_bp.route("/create", methods=["GET", "POST"])
@login_required
def create():
    """Kreiranje novog člana."""
    form = MemberCreateForm()
    
    if form.validate_on_submit():
        try:
            # Get the singleton sponsor
            sponsor = Sponsor.get_instance()
            if not sponsor:
                flash("Nema konfigurisan sponsor. Kontaktirajte administratora.", "error")
                return redirect(url_for('members.index'))
                
            member = MemberService.create_member(
                sponsor_id=sponsor.id,
                form_data=form.data
            )
            flash(f"Član '{member.name}' je uspešno kreiran.", "success")
            return redirect(url_for("members.detail", member_id=member.id))
        except ValueError as e:
            flash(f"Greška pri kreiranju člana: {str(e)}", "error")
        except Exception as e:
            flash("Došlo je do greške pri kreiranju člana. Molimo pokušajte ponovo.", "error")
            db.session.rollback()

    return render_template("members/form.html", title="Novi član", form=form, mode="create")


@members_bp.route("/<int:member_id>")
@login_required
def detail(member_id):
    """Detalji o članu sa statistikama."""
    # Get the singleton sponsor
    sponsor = Sponsor.get_instance()
    if not sponsor:
        abort(404)
        
    member = MemberService.get_member_by_id(member_id, sponsor.id)
    if not member:
        abort(404)
    
    # Get member statistics through DashboardService
    from app.services.dashboard_service import DashboardService
    member_stats = DashboardService.get_member_detail_statistics(member_id)
    
    return render_template(
        "members/detail.html", 
        title=f"Član: {member.name}",
        member=member,
        member_stats=member_stats
    )


@members_bp.route("/<int:member_id>/edit", methods=["GET", "POST"])
@login_required
def edit(member_id):
    """Uređivanje člana."""
    # Get the singleton sponsor
    sponsor = Sponsor.get_instance()
    if not sponsor:
        abort(404)
        
    member = MemberService.get_member_by_id(member_id, sponsor.id)
    if not member:
        abort(404)
    
    form = MemberEditForm(obj=member)
    
    if form.validate_on_submit():
        try:
            updated_member = MemberService.update_member(
                member_id=member.id,
                sponsor_id=sponsor.id,
                form_data=form.data
            )
            flash(f"Član '{updated_member.name}' je uspešno ažuriran.", "success")
            return redirect(url_for("members.detail", member_id=updated_member.id))
        except ValueError as e:
            flash(f"Greška pri ažuriranju člana: {str(e)}", "error")
        except Exception as e:
            flash("Došlo je do greške pri ažuriranju člana. Molimo pokušajte ponovo.", "error")
            db.session.rollback()

    return render_template(
        "members/form.html", 
        title=f"Uredi član: {member.name}",
        form=form,
        member=member,
        mode="edit"
    )


@members_bp.route("/<int:member_id>/toggle-status", methods=["POST"])
@login_required
def toggle_status(member_id):
    """Toggle member active/inactive status (soft delete)."""
    try:
        # Get the singleton sponsor
        sponsor = Sponsor.get_instance()
        if not sponsor:
            flash("Nema konfigurisan sponsor. Kontaktirajte administratora.", "error")
            return redirect(url_for('members.index'))
            
        member = MemberService.toggle_member_status(
            member_id=member_id,
            sponsor_id=sponsor.id
        )
        
        status_text = "aktiviran" if member.is_active else "deaktiviran"
        flash(f"Član '{member.name}' je uspešno {status_text}.", "success")
        
        return redirect(url_for("members.detail", member_id=member.id))
    except ValueError as e:
        flash(f"Greška: {str(e)}", "error")
        return redirect(url_for("members.index"))
    except Exception as e:
        flash("Došlo je do greške pri menjanju statusa člana.", "error")
        return redirect(url_for("members.index"))


@members_bp.route("/search", methods=["GET"])
@login_required
def search():
    """AJAX endpoint za search članova u realnom vremenu."""
    search_term = request.args.get('q', '')
    page = request.args.get('page', 1, type=int)
    per_page = 5  # Fewer results for AJAX
    
    if not search_term or len(search_term) < 2:
        return jsonify({'members': [], 'has_more': False})
    
    try:
        # Get the singleton sponsor
        sponsor = Sponsor.get_instance()
        if not sponsor:
            return jsonify({'error': 'Nema konfigurisan sponsor.'}), 500
            
        members_data = MemberService.search_members(
            sponsor_id=sponsor.id,
            search_term=search_term,
            page=page,
            per_page=per_page
        )
        
        members_list = []
        for member in members_data.items:
            members_list.append({
                'id': member.id,
                'name': member.name,
                'institution': member.institution,
                'contact_email': member.contact_email,
                'is_active': member.is_active
            })
        
        return jsonify({
            'members': members_list,
            'has_more': members_data.has_next,
            'total': members_data.total
        })
    
    except Exception as e:
        return jsonify({'error': 'Došlo je do greške pri pretraživanju.'}), 500