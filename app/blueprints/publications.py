"""
Publications Blueprint - handles publication template management with type-specific forms.
"""

from flask import Blueprint, request, render_template, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user

from app import db
from app.models.publication import Publication, PublicationType
from app.models.member import Member
from app.models.sponsor import Sponsor
from app.forms.publication_forms import UniversalPublicationForm
from app.services.publication_service import PublicationService

# Blueprint creation
publications_bp = Blueprint('publications', __name__, template_folder='templates')


@publications_bp.route('/')
@login_required
def index():
    """Main publications page with list of all publications and create functionality."""
    # Get the singleton sponsor
    sponsor = Sponsor.get_instance()
    if not sponsor:
        flash("Nema konfigurisan sponsor. Kontaktirajte administratora.", "error")
        return redirect(url_for('main.dashboard'))
    
    # Get filter parameters
    publication_type_filter = request.args.get('type', '')
    page = request.args.get('page', 1, type=int)
    
    # Get all publications across all members for this sponsor
    query = Publication.query.join(Member).filter(Member.sponsor_id == sponsor.id)
    
    # Apply type filter if provided
    if publication_type_filter:
        try:
            pub_type = PublicationType(publication_type_filter)
            query = query.filter(Publication.publication_type == pub_type)
        except ValueError:
            flash(f'Nepoznat tip publikacije: {publication_type_filter}', 'warning')
            publication_type_filter = ''
    
    # Order by creation date (newest first)
    query = query.order_by(Publication.created_at.desc())
    
    # Paginate results
    publications = query.paginate(
        page=page,
        per_page=20,
        error_out=False
    )
    
    # Get publication counts by type
    type_counts = {}
    total_count = 0
    for pub_type in PublicationType:
        count = Publication.query.join(Member).filter(
            Member.sponsor_id == sponsor.id,
            Publication.publication_type == pub_type
        ).count()
        type_counts[pub_type.value] = count
        total_count += count
    
    # Get all active members for the create form
    all_members = Member.get_by_sponsor(sponsor.id, active_only=True)
    
    return render_template(
        'publications/index.html',
        publications=publications,
        all_members=all_members,
        current_filter=publication_type_filter,
        total_count=total_count,
        type_counts=type_counts,
        publication_types=[(t.value, t.value.replace('_', ' ').title()) for t in PublicationType]
    )


@publications_bp.route('/member/<int:member_id>')
@login_required
def list_by_member(member_id):
    """List all publications for a specific member."""
    # Get the singleton sponsor
    sponsor = Sponsor.get_instance()
    if not sponsor:
        flash("Nema konfigurisan sponsor. Kontaktirajte administratora.", "error")
        return redirect(url_for('main.dashboard'))
    
    # Verify member belongs to sponsor
    member = Member.query.filter_by(
        id=member_id, 
        sponsor_id=sponsor.id
    ).first_or_404()
    
    # Get filter parameters
    publication_type_filter = request.args.get('type', '')
    page = request.args.get('page', 1, type=int)
    
    # Get publications using service
    publications = PublicationService.get_publications_for_member(
        member_id=member_id,
        page=page,
        per_page=10,
        publication_type_filter=publication_type_filter or None
    )
    
    # Get publication counts by type for statistics
    type_counts = PublicationService.get_publication_counts_by_type(member_id)
    
    return render_template(
        'publications/list.html',
        publications=publications,
        member=member,
        type_counts=type_counts,
        current_filter=publication_type_filter,
        publication_types=[(t.value, t.value.replace('_', ' ').title()) for t in PublicationType]
    )


@publications_bp.route('/member/<int:member_id>/create', methods=['GET', 'POST'])
@login_required
def create_for_member(member_id):
    """Create a new publication template for a member."""
    # Get the singleton sponsor
    sponsor = Sponsor.get_instance()
    if not sponsor:
        flash("Nema konfigurisan sponsor. Kontaktirajte administratora.", "error")
        return redirect(url_for('main.dashboard'))
    
    # Verify member belongs to sponsor
    member = Member.query.filter_by(
        id=member_id, 
        sponsor_id=sponsor.id
    ).first_or_404()
    
    form = UniversalPublicationForm()
    
    if form.validate_on_submit():
        try:
            # Extract all form data
            publication_data = PublicationService._extract_form_data(form)
            
            # Create publication using service
            publication = PublicationService.create_publication(
                member_id=member_id,
                publication_data=publication_data
            )
            
            flash(f'Publication template "{publication.title}" created successfully!', 'success')
            return redirect(url_for('publications.detail', publication_id=publication.id))
            
        except ValueError as e:
            flash(f'Validation error: {str(e)}', 'error')
        except Exception as e:
            flash(f'An error occurred: {str(e)}', 'error')
            db.session.rollback()
    else:
        # Debug: Show form validation errors only on POST
        if request.method == 'POST' and form.errors:
            for field, errors in form.errors.items():
                for error in errors:
                    flash(f'Field {field}: {error}', 'error')
    
    return render_template(
        'publications/form.html',
        form=form,
        member=member,
        action='Nova',
        submit_text='Kreiran template publikacije'
    )


@publications_bp.route('/<int:publication_id>')
@login_required
def detail(publication_id):
    """Show publication template details."""
    # Get the singleton sponsor
    sponsor = Sponsor.get_instance()
    if not sponsor:
        flash("Nema konfigurisan sponsor. Kontaktirajte administratora.", "error")
        return redirect(url_for('main.dashboard'))
    
    publication = PublicationService.get_publication_by_id(publication_id)
    if not publication:
        flash('Publikacija nije pronađena.', 'error')
        return redirect(url_for('main.dashboard'))
    
    # Verify access - publication must belong to member of sponsor
    if publication.member.sponsor_id != sponsor.id:
        flash('Nemate dozvolu da pristupite ovoj publikaciji.', 'error')
        return redirect(url_for('main.dashboard'))
    
    # Get detailed statistics through DashboardService
    from app.services.dashboard_service import DashboardService
    publication_stats = DashboardService.get_publication_detail_statistics(publication_id)
    
    # Get workflow type for display using service
    workflow_info = PublicationService.get_workflow_info(publication)
    
    return render_template(
        'publications/detail.html',
        publication=publication,
        publication_stats=publication_stats,
        draft_count=publication_stats['drafts']['total'],
        workflow_info=workflow_info
    )


@publications_bp.route('/<int:publication_id>/edit', methods=['GET', 'POST'])
@login_required
def edit(publication_id):
    """Edit publication template."""
    # Get the singleton sponsor
    sponsor = Sponsor.get_instance()
    if not sponsor:
        flash("Nema konfigurisan sponsor. Kontaktirajte administratora.", "error")
        return redirect(url_for('main.dashboard'))
    
    publication = Publication.query.get_or_404(publication_id)
    
    # Verify access
    if publication.member.sponsor_id != sponsor.id:
        flash('Nemate dozvolu da menjate ovu publikaciju.', 'error')
        return redirect(url_for('main.dashboard'))
    
    form = UniversalPublicationForm(obj=publication)
    
    if form.validate_on_submit():
        try:
            # Update base fields
            publication.publication_type = form.publication_type.data
            publication.title = form.title.data
            publication.subtitle = form.subtitle.data
            publication.language_code = form.language_code.data
            
            # Update type-specific fields based on new type
            pub_type = form.publication_type.data
            
            # Clear all type-specific fields first
            type_specific_fields = [
                'journal_abbreviated_title', 'journal_issn', 'journal_electronic_issn', 'journal_coden',
                'series_title', 'series_subtitle', 'series_issn', 'series_electronic_issn', 
                'series_coden', 'series_number',
                'set_title', 'set_subtitle', 'set_isbn', 'set_electronic_isbn', 'set_part_number',
                'book_type', 'edition_number', 'isbn', 'electronic_isbn', 'noisbn_reason'
            ]
            
            for field in type_specific_fields:
                setattr(publication, field, None)
            
            # Set new type-specific fields
            if pub_type == 'journal':
                publication.journal_abbreviated_title = form.journal_abbreviated_title.data
                publication.journal_issn = form.journal_issn.data
                publication.journal_electronic_issn = form.journal_electronic_issn.data
                publication.journal_coden = form.journal_coden.data
                
            elif pub_type == 'book_series':
                publication.series_title = form.series_title.data
                publication.series_subtitle = form.series_subtitle.data
                publication.series_issn = form.series_issn.data
                publication.series_electronic_issn = form.series_electronic_issn.data
                publication.series_coden = form.series_coden.data
                publication.series_number = form.series_number.data
                
            elif pub_type == 'book_set':
                publication.set_title = form.set_title.data
                publication.set_subtitle = form.set_subtitle.data
                publication.set_isbn = form.set_isbn.data
                publication.set_electronic_isbn = form.set_electronic_isbn.data
                publication.set_part_number = form.set_part_number.data
                
            elif pub_type == 'book':
                publication.book_type = form.book_type.data
                publication.edition_number = form.edition_number.data
                publication.isbn = form.isbn.data
                publication.electronic_isbn = form.electronic_isbn.data
                publication.noisbn_reason = form.noisbn_reason.data
            
            publication.save()
            
            flash(f'Publication template "{publication.title}" updated successfully!', 'success')
            return redirect(url_for('publications.detail', publication_id=publication.id))
            
        except Exception as e:
            flash(f'An error occurred: {str(e)}', 'error')
            db.session.rollback()
    
    return render_template(
        'publications/form.html',
        form=form,
        member=publication.member,
        publication=publication,
        action='Izmeni',
        submit_text='Ažuriraj template publikacije'
    )


@publications_bp.route('/<int:publication_id>/toggle-status', methods=['POST'])
@login_required
def toggle_status(publication_id):
    """Toggle publication active status (soft delete)."""
    # Get the singleton sponsor
    sponsor = Sponsor.get_instance()
    if not sponsor:
        return jsonify({'error': 'Sponsor nije konfigurisan'}), 500
    
    try:
        publication = PublicationService.get_publication_by_id(publication_id)
        if not publication:
            if request.content_type == 'application/json':
                return jsonify({'error': 'Publication not found'}), 404
            else:
                flash('Publikacija nije pronađena.', 'error')
                return redirect(url_for('publications.index'))
        
        # Verify access
        if publication.member.sponsor_id != sponsor.id:
            return jsonify({'error': 'Permission denied'}), 403
        
        # Toggle status using service
        publication, action = PublicationService.toggle_publication_status(publication_id)
        
        message = f'Publication template "{publication.title}" {action}.'
        status = action
        
        if request.content_type == 'application/json':
            return jsonify({
                'success': True,
                'message': message,
                'status': status,
                'is_active': publication.is_active
            })
        else:
            flash(message, 'success')
            return redirect(url_for('publications.detail', publication_id=publication_id))
            
    except Exception as e:
        if request.content_type == 'application/json':
            return jsonify({'error': str(e)}), 500
        else:
            flash(f'An error occurred: {str(e)}', 'error')
            return redirect(url_for('publications.detail', publication_id=publication_id))


@publications_bp.route('/api/member/<int:member_id>/filter')
@login_required
def filter_publications_ajax(member_id):
    """AJAX endpoint for filtering publications without page reload."""
    # Get the singleton sponsor
    sponsor = Sponsor.get_instance()
    if not sponsor:
        return jsonify({'error': 'Sponsor nije konfigurisan'}), 500
    
    # Verify member belongs to sponsor
    member = Member.query.filter_by(
        id=member_id, 
        sponsor_id=sponsor.id
    ).first_or_404()
    
    # Get filter parameters
    publication_type_filter = request.args.get('type', '')
    page = request.args.get('page', 1, type=int)
    
    # Get publications using service
    publications = PublicationService.get_publications_for_member(
        member_id=member_id,
        page=page,
        per_page=10,
        publication_type_filter=publication_type_filter or None
    )
    
    # Get publication counts by type for statistics
    type_counts = PublicationService.get_publication_counts_by_type(member_id)
    
    # Render only the publications table part
    publications_html = render_template(
        'publications/includes/publications-table.html',
        publications=publications,
        member=member,
        current_filter=publication_type_filter
    )
    
    # Render statistics cards
    stats_html = render_template(
        'publications/includes/statistics-cards.html',
        type_counts=type_counts
    )
    
    return jsonify({
        'success': True,
        'publications_html': publications_html,
        'stats_html': stats_html,
        'pagination': {
            'page': publications.page,
            'pages': publications.pages,
            'has_prev': publications.has_prev,
            'has_next': publications.has_next,
            'prev_num': publications.prev_num,
            'next_num': publications.next_num,
            'total': publications.total
        }
    })
