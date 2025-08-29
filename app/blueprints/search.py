from flask import Blueprint, render_template, request, jsonify, redirect, url_for
from flask_login import login_required, current_user
from app.models.sponsor import Sponsor
from app.services.search_service import SearchService

search_bp = Blueprint('search', __name__, url_prefix='/search')


@search_bp.route('/')
@login_required
def search_index():
    """Glavna stranica za pretragu."""
    query = request.args.get('q', '').strip()
    entity_types = request.args.getlist('types')
    page = request.args.get('page', 1, type=int)
    
    # Dobij sponsor od singleton pattern
    sponsor = Sponsor.get_instance()
    if not sponsor:
        return redirect(url_for('main.index'))
    
    results = {}
    advanced_filters = SearchService.get_advanced_search_filters(sponsor.id)
    
    if query:
        # Izvršava pretragu
        results = SearchService.search_all(
            query=query,
            sponsor_id=sponsor.id,
            entity_types=entity_types if entity_types else None,
            page=page
        )
    
    return render_template('search/search_results.html',
                           query=query,
                           results=results,
                           entity_types=entity_types,
                           advanced_filters=advanced_filters,
                           title='Pretraga')


@search_bp.route('/api/suggestions')
@login_required
def search_suggestions():
    """API endpoint za autocomplete predloge."""
    query = request.args.get('q', '').strip()
    sponsor = Sponsor.get_instance()
    
    if not sponsor or not query or len(query) < 2:
        return jsonify([])
    
    suggestions = SearchService.get_search_suggestions(
        query=query,
        sponsor_id=sponsor.id,
        limit=8
    )
    
    return jsonify(suggestions)


@search_bp.route('/api/results')
@login_required
def search_api():
    """API endpoint za AJAX pretraživanje."""
    query = request.args.get('q', '').strip()
    entity_types = request.args.getlist('types')
    page = request.args.get('page', 1, type=int)
    
    sponsor = Sponsor.get_instance()
    if not sponsor:
        return jsonify({'error': 'Sponsor not found'}), 400
    
    if not query:
        return jsonify({
            'results': [],
            'total_results': 0,
            'members_count': 0,
            'publications_count': 0
        })
    
    results = SearchService.search_all(
        query=query,
        sponsor_id=sponsor.id,
        entity_types=entity_types if entity_types else None,
        page=page
    )
    
    return jsonify(results)


@search_bp.route('/members')
@login_required
def search_members():
    """Pretraživanje samo članova."""
    query = request.args.get('q', '').strip()
    page = request.args.get('page', 1, type=int)
    
    sponsor = Sponsor.get_instance()
    if not sponsor:
        return redirect(url_for('main.index'))
    
    results = {}
    if query:
        results = SearchService.search_all(
            query=query,
            sponsor_id=sponsor.id,
            entity_types=['member'],
            page=page
        )
    
    return render_template('search/search_results.html',
                           query=query,
                           results=results,
                           entity_types=['member'],
                           search_type='members',
                           title='Pretraga članova')


@search_bp.route('/publications')
@login_required
def search_publications():
    """Pretraživanje samo publikacija."""
    query = request.args.get('q', '').strip()
    page = request.args.get('page', 1, type=int)
    
    sponsor = Sponsor.get_instance()
    if not sponsor:
        return redirect(url_for('main.index'))
    
    results = {}
    if query:
        results = SearchService.search_all(
            query=query,
            sponsor_id=sponsor.id,
            entity_types=['publication'],
            page=page
        )
    
    return render_template('search/search_results.html',
                           query=query,
                           results=results,
                           entity_types=['publication'],
                           search_type='publications',
                           title='Pretraga publikacija')