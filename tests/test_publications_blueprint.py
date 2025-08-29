"""
Tests for Publications Blueprint - routes and view testing.
"""

import pytest
from flask import url_for
from app import db
from app.models.publication import Publication, PublicationType
from app.models.member import Member
from app.models.sponsor import Sponsor


class TestPublicationsBlueprintBasic:
    """Test basic blueprint functionality."""
    
    def test_publications_index_requires_authentication(self, client):
        """Test that publications index requires login."""
        response = client.get('/publications/')
        assert response.status_code == 302
        assert '/auth/login' in response.location
    
    def test_publications_index_authenticated(self, client, auth_user):
        """Test publications index with authenticated user."""
        with client.session_transaction() as sess:
            sess['_user_id'] = str(auth_user.id)
        
        response = client.get('/publications/')
        assert response.status_code == 200
        assert 'Publikacije' in response.data.decode('utf-8')
    
    def test_publications_index_shows_all_publications(self, client, auth_user, test_member, test_journal_publication, test_book_publication):
        """Test that index page shows all publications."""
        with client.session_transaction() as sess:
            sess['_user_id'] = str(auth_user.id)
        
        response = client.get('/publications/')
        assert response.status_code == 200
        response_text = response.data.decode('utf-8')
        
        # Should show both publications
        assert test_journal_publication.title in response_text
        assert test_book_publication.title in response_text
        
        # Should show create form
        assert 'Kreiranje nove publikacije' in response_text
        assert 'Izaberite člana:' in response_text
        
        # Should show member names in select
        assert test_member.name in response_text
    
    def test_publications_index_type_filter(self, client, auth_user, test_journal_publication, test_book_publication):
        """Test type filtering on index page."""
        with client.session_transaction() as sess:
            sess['_user_id'] = str(auth_user.id)
        
        # Test journal filter
        response = client.get('/publications/?type=journal')
        assert response.status_code == 200
        response_text = response.data.decode('utf-8')
        
        assert test_journal_publication.title in response_text
        # Book should not be shown when filtering by journal
        assert test_book_publication.title not in response_text


class TestPublicationsListByMember:
    """Test member-specific publication listing."""
    
    def test_list_by_member_requires_auth(self, client, test_member):
        """Test that listing requires authentication."""
        response = client.get(f'/publications/member/{test_member.id}')
        assert response.status_code == 302
        assert '/auth/login' in response.location
    
    def test_list_by_member_authenticated(self, client, auth_user, test_member):
        """Test listing publications for member."""
        with client.session_transaction() as sess:
            sess['_user_id'] = str(auth_user.id)
        
        response = client.get(f'/publications/member/{test_member.id}')
        assert response.status_code == 200
        assert test_member.name.encode() in response.data
        assert b'Lista publikacija' in response.data
    
    def test_list_by_member_with_publications(self, client, auth_user, test_member, test_journal_publication):
        """Test listing member with publications."""
        with client.session_transaction() as sess:
            sess['_user_id'] = str(auth_user.id)
        
        response = client.get(f'/publications/member/{test_member.id}')
        assert response.status_code == 200
        assert test_journal_publication.title.encode() in response.data
        assert 'Časopis' in response.data.decode('utf-8')  # Journal type badge
    
    def test_list_by_member_with_type_filter(self, client, auth_user, test_member, test_journal_publication):
        """Test filtering publications by type."""
        with client.session_transaction() as sess:
            sess['_user_id'] = str(auth_user.id)
        
        response = client.get(f'/publications/member/{test_member.id}?type=journal')
        assert response.status_code == 200
        assert test_journal_publication.title.encode() in response.data
        
        # Test with non-existing type filter
        response = client.get(f'/publications/member/{test_member.id}?type=book')
        assert response.status_code == 200
        assert b'Nema publikacija' in response.data
    
    def test_list_by_member_pagination(self, client, auth_user, test_member):
        """Test pagination functionality."""
        # Create multiple publications
        publications = []
        for i in range(15):  # More than default page size (10)
            pub = Publication.create_publication(
                member_id=test_member.id,
                publication_type='journal',
                title=f'Test Journal {i}',
                language_code='en',
                journal_issn=f'1234-567{i % 10}'
            )
            publications.append(pub)
        
        with client.session_transaction() as sess:
            sess['_user_id'] = str(auth_user.id)
        
        # Test first page
        response = client.get(f'/publications/member/{test_member.id}')
        assert response.status_code == 200
        assert b'Test Journal 14' in response.data  # Latest first
        
        # Test second page
        response = client.get(f'/publications/member/{test_member.id}?page=2')
        assert response.status_code == 200
        assert b'Test Journal 4' in response.data


class TestPublicationCreate:
    """Test publication creation functionality."""
    
    def test_create_get_requires_auth(self, client, test_member):
        """Test that create form requires authentication."""
        response = client.get(f'/publications/member/{test_member.id}/create')
        assert response.status_code == 302
        assert '/auth/login' in response.location
    
    def test_create_get_form(self, client, auth_user, test_member):
        """Test displaying create form."""
        with client.session_transaction() as sess:
            sess['_user_id'] = str(auth_user.id)
        
        response = client.get(f'/publications/member/{test_member.id}/create')
        assert response.status_code == 200
        assert b'Nova publikaciju' in response.data
        assert b'publication_type' in response.data
    
    def test_create_post_journal(self, client, auth_user, test_member):
        """Test creating a journal publication."""
        with client.session_transaction() as sess:
            sess['_user_id'] = str(auth_user.id)
        
        form_data = {
            'publication_type': 'journal',
            'title': 'Test Journal Creation',
            'subtitle': 'Test Subtitle',
            'language_code': 'en',
            'journal_abbreviated_title': 'Test J.',
            'journal_issn': '1234-5678',
            'journal_electronic_issn': '1234-5679',
            'journal_coden': 'TESTJX',
            'csrf_token': 'test_token'  # You may need to handle CSRF differently
        }
        
        response = client.post(
            f'/publications/member/{test_member.id}/create',
            data=form_data,
            follow_redirects=False
        )
        
        # Should redirect to detail page on success
        assert response.status_code == 302
        
        # Verify publication was created
        publication = Publication.query.filter_by(
            member_id=test_member.id,
            title='Test Journal Creation'
        ).first()
        assert publication is not None
        assert publication.publication_type == PublicationType.journal
        assert publication.journal_issn == '1234-5678'
    
    def test_create_post_book_series(self, client, auth_user, test_member):
        """Test creating a book series publication."""
        with client.session_transaction() as sess:
            sess['_user_id'] = str(auth_user.id)
        
        form_data = {
            'publication_type': 'book_series',
            'title': 'Test Series',
            'language_code': 'en',
            'series_title': 'Academic Book Series',
            'series_issn': '9876-5432',
            'csrf_token': 'test_token'
        }
        
        response = client.post(
            f'/publications/member/{test_member.id}/create',
            data=form_data,
            follow_redirects=False
        )
        
        assert response.status_code == 302
        
        publication = Publication.query.filter_by(
            member_id=test_member.id,
            title='Test Series'
        ).first()
        assert publication is not None
        assert publication.publication_type == PublicationType.book_series
        assert publication.series_title == 'Academic Book Series'


class TestPublicationDetail:
    """Test publication detail view."""
    
    def test_detail_requires_auth(self, client, test_journal_publication):
        """Test that detail view requires authentication."""
        response = client.get(f'/publications/{test_journal_publication.id}')
        assert response.status_code == 302
        assert '/auth/login' in response.location
    
    def test_detail_view(self, client, auth_user, test_journal_publication):
        """Test publication detail view."""
        with client.session_transaction() as sess:
            sess['_user_id'] = str(auth_user.id)
        
        response = client.get(f'/publications/{test_journal_publication.id}')
        assert response.status_code == 200
        assert test_journal_publication.title.encode() in response.data
        assert 'Podaci o časopisu' in response.data.decode('utf-8')
        assert b'Workflow informacije' in response.data
        assert b'Istorija aktivnosti' in response.data
    
    def test_detail_workflow_info(self, client, auth_user, test_journal_publication, test_book_publication):
        """Test workflow information display."""
        with client.session_transaction() as sess:
            sess['_user_id'] = str(auth_user.id)
        
        # Test journal (multiple drafts)
        response = client.get(f'/publications/{test_journal_publication.id}')
        assert response.status_code == 200
        assert b'1:N (Multiple Drafts)' in response.data
        assert 'Više draft-ova' in response.data.decode('utf-8')
        
        # Test book (single draft)
        response = client.get(f'/publications/{test_book_publication.id}')
        assert response.status_code == 200
        assert b'1:1 (Single Draft)' in response.data
        assert b'Jedinstven draft' in response.data


class TestPublicationEdit:
    """Test publication editing functionality."""
    
    def test_edit_get_form(self, client, auth_user, test_journal_publication):
        """Test displaying edit form."""
        with client.session_transaction() as sess:
            sess['_user_id'] = str(auth_user.id)
        
        response = client.get(f'/publications/{test_journal_publication.id}/edit')
        assert response.status_code == 200
        assert b'Izmeni publikaciju' in response.data
        assert test_journal_publication.title.encode() in response.data
    
    def test_edit_post_update(self, client, auth_user, test_journal_publication):
        """Test updating publication."""
        original_title = test_journal_publication.title
        
        with client.session_transaction() as sess:
            sess['_user_id'] = str(auth_user.id)
        
        form_data = {
            'publication_type': 'journal',
            'title': 'Updated Journal Title',
            'subtitle': test_journal_publication.subtitle or '',
            'language_code': test_journal_publication.language_code,
            'journal_abbreviated_title': 'Updated J.',
            'journal_issn': '9999-8888',
            'csrf_token': 'test_token'
        }
        
        response = client.post(
            f'/publications/{test_journal_publication.id}/edit',
            data=form_data,
            follow_redirects=False
        )
        
        assert response.status_code == 302
        
        # Verify update
        updated_publication = db.session.get(Publication, test_journal_publication.id)
        assert updated_publication.title == 'Updated Journal Title'
        assert updated_publication.journal_issn == '9999-8888'
        assert updated_publication.title != original_title


class TestPublicationToggleStatus:
    """Test publication status toggle functionality."""
    
    def test_toggle_status_requires_auth(self, client, test_journal_publication):
        """Test that toggle status requires authentication."""
        response = client.post(f'/publications/{test_journal_publication.id}/toggle-status')
        assert response.status_code == 302
        assert '/auth/login' in response.location
    
    def test_toggle_status_json(self, client, auth_user, test_journal_publication):
        """Test toggling publication status via JSON request."""
        with client.session_transaction() as sess:
            sess['_user_id'] = str(auth_user.id)
        
        # Test deactivation
        assert test_journal_publication.is_active == True
        
        response = client.post(
            f'/publications/{test_journal_publication.id}/toggle-status',
            content_type='application/json'
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] == True
        assert data['status'] == 'deactivated'
        
        # Verify database change
        updated_publication = db.session.get(Publication, test_journal_publication.id)
        assert updated_publication.is_active == False


class TestAjaxFiltering:
    """Test AJAX filtering endpoint."""
    
    def test_ajax_filter_requires_auth(self, client, test_member):
        """Test that AJAX endpoint requires authentication."""
        response = client.get(f'/publications/api/member/{test_member.id}/filter')
        assert response.status_code == 302
        assert '/auth/login' in response.location
    
    def test_ajax_filter_basic(self, client, auth_user, test_member, test_journal_publication):
        """Test basic AJAX filtering."""
        with client.session_transaction() as sess:
            sess['_user_id'] = str(auth_user.id)
        
        response = client.get(f'/publications/api/member/{test_member.id}/filter')
        assert response.status_code == 200
        
        data = response.get_json()
        assert data['success'] == True
        assert 'publications_html' in data
        assert 'stats_html' in data
        assert 'pagination' in data
    
    def test_ajax_filter_by_type(self, client, auth_user, test_member, test_journal_publication):
        """Test AJAX filtering by publication type."""
        with client.session_transaction() as sess:
            sess['_user_id'] = str(auth_user.id)
        
        response = client.get(f'/publications/api/member/{test_member.id}/filter?type=journal')
        assert response.status_code == 200
        
        data = response.get_json()
        assert data['success'] == True
        assert test_journal_publication.title in data['publications_html']
    
    def test_ajax_filter_pagination(self, client, auth_user, test_member):
        """Test AJAX filtering with pagination."""
        # Create multiple publications
        for i in range(15):
            Publication.create_publication(
                member_id=test_member.id,
                publication_type='journal',
                title=f'AJAX Test Journal {i}',
                language_code='en',
                journal_issn=f'1111-222{i % 10}'
            )
        
        with client.session_transaction() as sess:
            sess['_user_id'] = str(auth_user.id)
        
        response = client.get(f'/publications/api/member/{test_member.id}/filter?page=2')
        assert response.status_code == 200
        
        data = response.get_json()
        assert data['success'] == True
        assert data['pagination']['page'] == 2
        assert data['pagination']['pages'] >= 2