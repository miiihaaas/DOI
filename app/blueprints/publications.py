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
from app.utils.pagination import paginate_query

# Blueprint creation
publications_bp = Blueprint('publications', __name__, template_folder='templates')


@publications_bp.route('/')
@login_required
def index():
    """Main publications page with navigation help."""
    return render_template('publications/index.html')


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
    
    # Build query
    query = Publication.query.filter_by(member_id=member_id, is_active=True)
    
    if publication_type_filter:
        query = query.filter_by(publication_type=publication_type_filter)
    
    # Apply pagination
    publications = paginate_query(query, page=page, per_page=10)
    
    # Get publication counts by type for statistics
    type_counts = {}
    for pub_type in PublicationType:
        count = Publication.query.filter_by(
            member_id=member_id, 
            publication_type=pub_type,
            is_active=True
        ).count()
        type_counts[pub_type.value] = count
    
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
            # Extract form data based on publication type
            pub_type = form.publication_type.data
            
            # Base data
            publication_data = {
                'publication_type': pub_type,
                'title': form.title.data,
                'subtitle': form.subtitle.data,
                'language_code': form.language_code.data
            }
            
            # Add type-specific data
            if pub_type == 'journal':
                publication_data.update({
                    'journal_abbreviated_title': form.journal_abbreviated_title.data,
                    'journal_issn': form.journal_issn.data,
                    'journal_electronic_issn': form.journal_electronic_issn.data,
                    'journal_coden': form.journal_coden.data
                })
                
            elif pub_type == 'book_series':
                publication_data.update({
                    'series_title': form.series_title.data,
                    'series_subtitle': form.series_subtitle.data,
                    'series_issn': form.series_issn.data,
                    'series_electronic_issn': form.series_electronic_issn.data,
                    'series_coden': form.series_coden.data,
                    'series_number': form.series_number.data
                })
                
            elif pub_type == 'book_set':
                publication_data.update({
                    'set_title': form.set_title.data,
                    'set_subtitle': form.set_subtitle.data,
                    'set_isbn': form.set_isbn.data,
                    'set_electronic_isbn': form.set_electronic_isbn.data,
                    'set_part_number': form.set_part_number.data
                })
                
            elif pub_type == 'book':
                publication_data.update({
                    'book_type': form.book_type.data,
                    'edition_number': form.edition_number.data,
                    'isbn': form.isbn.data,
                    'electronic_isbn': form.electronic_isbn.data,
                    'noisbn_reason': form.noisbn_reason.data
                })
            
            # Create publication using model method
            publication = Publication.create_publication(
                member_id=member_id,
                **publication_data
            )
            
            flash(f'Publication template "{publication.title}" created successfully!', 'success')
            return redirect(url_for('publications.detail', publication_id=publication.id))
            
        except ValueError as e:
            flash(f'Validation error: {str(e)}', 'error')
        except Exception as e:
            flash(f'An error occurred: {str(e)}', 'error')
            db.session.rollback()
    
    return render_template(
        'publications/form.html',
        form=form,
        member=member,
        action='Create',
        submit_text='Create Publication Template'
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
    
    publication = Publication.query.get_or_404(publication_id)
    
    # Verify access - publication must belong to member of sponsor
    if publication.member.sponsor_id != sponsor.id:
        flash('Nemate dozvolu da pristupite ovoj publikaciji.', 'error')
        return redirect(url_for('main.dashboard'))
    
    # Get draft count (placeholder - will be implemented when DOIDraft model exists)
    draft_count = 0  # TODO: Replace with actual DOIDraft count query
    
    # Get workflow type for display
    workflow_info = {
        'supports_multiple_drafts': publication.supports_multiple_drafts(),
        'is_single_draft_type': publication.is_single_draft_type(),
        'relationship_type': '1:N (Multiple Drafts)' if publication.supports_multiple_drafts() else '1:1 (Single Draft)'
    }
    
    return render_template(
        'publications/detail.html',
        publication=publication,
        draft_count=draft_count,
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
        action='Edit',
        submit_text='Update Publication Template'
    )


@publications_bp.route('/<int:publication_id>/toggle-status', methods=['POST'])
@login_required
def toggle_status(publication_id):
    """Toggle publication active status (soft delete)."""
    # Get the singleton sponsor
    sponsor = Sponsor.get_instance()
    if not sponsor:
        return jsonify({'error': 'Sponsor nije konfigurisan'}), 500
    
    publication = Publication.query.get_or_404(publication_id)
    
    # Verify access
    if publication.member.sponsor_id != sponsor.id:
        return jsonify({'error': 'Permission denied'}), 403
    
    try:
        if publication.is_active:
            publication.deactivate()
            message = f'Publication template "{publication.title}" deactivated.'
            status = 'deactivated'
        else:
            publication.activate()
            message = f'Publication template "{publication.title}" activated.'
            status = 'activated'
        
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
