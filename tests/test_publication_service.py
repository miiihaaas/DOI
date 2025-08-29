"""
Tests for Publication Service - business logic testing.
"""

import pytest
from flask import Flask
from app.services.publication_service import PublicationService
from app.models.publication import Publication, PublicationType
from app.models.member import Member


class TestPublicationServiceBasic:
    """Test basic publication service functionality."""
    
    def test_get_publications_for_member(self, app, test_member, test_journal_publication):
        """Test getting publications for a member."""
        with app.app_context():
            publications = PublicationService.get_publications_for_member(test_member.id)
            
            assert publications is not None
            assert publications.total >= 1
            assert any(pub.id == test_journal_publication.id for pub in publications.items)
    
    def test_get_publications_with_type_filter(self, app, test_member, test_journal_publication):
        """Test getting publications with type filter."""
        with app.app_context():
            # Test with matching filter
            publications = PublicationService.get_publications_for_member(
                test_member.id, publication_type_filter='journal'
            )
            assert publications.total >= 1
            assert any(pub.id == test_journal_publication.id for pub in publications.items)
            
            # Test with non-matching filter
            publications = PublicationService.get_publications_for_member(
                test_member.id, publication_type_filter='book'
            )
            assert publications.total == 0
    
    def test_get_publications_pagination(self, app, test_member):
        """Test publication pagination."""
        with app.app_context():
            # Create multiple publications
            for i in range(15):
                Publication.create_publication(
                    member_id=test_member.id,
                    publication_type='journal',
                    title=f'Pagination Test Journal {i}',
                    language_code='en',
                    journal_issn=f'1111-{i:04d}'
                )
            
            # Test first page
            publications = PublicationService.get_publications_for_member(
                test_member.id, page=1, per_page=10
            )
            assert len(publications.items) == 10
            assert publications.has_next == True
            
            # Test second page
            publications = PublicationService.get_publications_for_member(
                test_member.id, page=2, per_page=10
            )
            assert len(publications.items) >= 5
            assert publications.has_prev == True


class TestPublicationCountsByType:
    """Test publication counts by type functionality."""
    
    def test_get_publication_counts_empty(self, app, test_member):
        """Test counts with no publications."""
        with app.app_context():
            counts = PublicationService.get_publication_counts_by_type(test_member.id)
            
            assert isinstance(counts, dict)
            assert counts['journal'] == 0
            assert counts['book_series'] == 0
            assert counts['book_set'] == 0
            assert counts['book'] == 0
    
    def test_get_publication_counts_with_data(self, app, test_member):
        """Test counts with actual publications."""
        with app.app_context():
            # Create publications of different types
            Publication.create_publication(
                member_id=test_member.id,
                publication_type='journal',
                title='Test Journal 1',
                language_code='en',
                journal_issn='1111-1111'
            )
            Publication.create_publication(
                member_id=test_member.id,
                publication_type='journal',
                title='Test Journal 2',
                language_code='en',
                journal_issn='1111-1112'
            )
            Publication.create_publication(
                member_id=test_member.id,
                publication_type='book',
                title='Test Book',
                language_code='en',
                book_type='monograph'
            )
            
            counts = PublicationService.get_publication_counts_by_type(test_member.id)
            
            assert counts['journal'] == 2
            assert counts['book'] == 1
            assert counts['book_series'] == 0
            assert counts['book_set'] == 0
    
    def test_counts_ignore_inactive_publications(self, app, test_member, test_journal_publication):
        """Test that counts ignore inactive publications."""
        with app.app_context():
            # Initially should have the publication
            counts = PublicationService.get_publication_counts_by_type(test_member.id)
            initial_journal_count = counts['journal']
            
            # Deactivate publication using service instead of model method to avoid session issues
            PublicationService.toggle_publication_status(test_journal_publication.id)
            
            # Counts should decrease
            counts = PublicationService.get_publication_counts_by_type(test_member.id)
            assert counts['journal'] == initial_journal_count - 1


class TestPublicationCreation:
    """Test publication creation service methods."""
    
    def test_create_journal_publication(self, app, test_member):
        """Test creating a journal publication."""
        with app.app_context():
            publication_data = {
                'publication_type': 'journal',
                'title': 'Service Test Journal',
                'subtitle': 'Test Subtitle',
                'language_code': 'en',
                'journal_abbreviated_title': 'Serv. Test J.',
                'journal_issn': '9999-8888',
                'journal_electronic_issn': '9999-8889',
                'journal_coden': 'STJRNL'
            }
            
            publication = PublicationService.create_publication(
                test_member.id, publication_data
            )
            
            assert publication is not None
            assert publication.title == 'Service Test Journal'
            assert publication.publication_type == PublicationType.journal
            assert publication.journal_issn == '9999-8888'
            assert publication.member_id == test_member.id
            assert publication.is_active == True
    
    def test_create_book_series_publication(self, app, test_member):
        """Test creating a book series publication."""
        with app.app_context():
            publication_data = {
                'publication_type': 'book_series',
                'title': 'Service Test Series',
                'language_code': 'sr',
                'series_title': 'Academic Book Series',
                'series_issn': '7777-6666',
                'series_number': 'Volume 1'
            }
            
            publication = PublicationService.create_publication(
                test_member.id, publication_data
            )
            
            assert publication is not None
            assert publication.title == 'Service Test Series'
            assert publication.publication_type == PublicationType.book_series
            assert publication.series_title == 'Academic Book Series'
            assert publication.series_issn == '7777-6666'
    
    def test_create_publication_validation_errors(self, app, test_member):
        """Test validation errors during creation."""
        with app.app_context():
            # Missing required fields
            publication_data = {
                'publication_type': 'journal'
                # Missing title
            }
            
            with pytest.raises(ValueError, match="Field 'title' is required"):
                PublicationService.create_publication(test_member.id, publication_data)
            
            # Invalid publication type
            publication_data = {
                'publication_type': 'invalid_type',
                'title': 'Test Publication'
            }
            
            with pytest.raises(ValueError, match="Invalid publication type"):
                PublicationService.create_publication(test_member.id, publication_data)
    
    def test_create_publication_type_specific_validation(self, app, test_member):
        """Test type-specific validation during creation."""
        with app.app_context():
            # Book series without series_title
            publication_data = {
                'publication_type': 'book_series',
                'title': 'Test Series',
                'language_code': 'en'
                # Missing series_title
            }
            
            with pytest.raises(ValueError, match="Series title is required"):
                PublicationService.create_publication(test_member.id, publication_data)
    
    def test_create_publication_invalid_member(self, app):
        """Test creation with invalid member ID."""
        with app.app_context():
            publication_data = {
                'publication_type': 'journal',
                'title': 'Test Journal',
                'language_code': 'en'
            }
            
            with pytest.raises(ValueError, match="Member with ID 99999 not found"):
                PublicationService.create_publication(99999, publication_data)


class TestPublicationUpdates:
    """Test publication update service methods."""
    
    def test_update_publication(self, app, test_journal_publication):
        """Test updating a publication."""
        with app.app_context():
            original_title = test_journal_publication.title
            
            publication_data = {
                'title': 'Updated Journal Title',
                'journal_issn': '5555-4444'
            }
            
            updated_publication = PublicationService.update_publication(
                test_journal_publication.id, publication_data
            )
            
            assert updated_publication.title == 'Updated Journal Title'
            assert updated_publication.journal_issn == '5555-4444'
            assert updated_publication.title != original_title
    
    def test_update_publication_type_change(self, app, test_journal_publication):
        """Test updating publication type (should clear type-specific fields)."""
        with app.app_context():
            original_issn = test_journal_publication.journal_issn
            
            publication_data = {
                'publication_type': 'book',
                'book_type': 'monograph'
            }
            
            updated_publication = PublicationService.update_publication(
                test_journal_publication.id, publication_data
            )
            
            assert updated_publication.publication_type == PublicationType.book
            assert updated_publication.book_type == 'monograph'
            # Old journal fields should be cleared
            assert updated_publication.journal_issn is None
    
    def test_update_publication_validation_error(self, app, test_journal_publication):
        """Test update validation errors."""
        with app.app_context():
            # Empty title should fail
            publication_data = {
                'title': ''
            }
            
            with pytest.raises(ValueError, match="Title is required"):
                PublicationService.update_publication(
                    test_journal_publication.id, publication_data
                )
    
    def test_update_nonexistent_publication(self, app):
        """Test updating non-existent publication."""
        with app.app_context():
            publication_data = {
                'title': 'Updated Title'
            }
            
            with pytest.raises(ValueError, match="Publication with ID 99999 not found"):
                PublicationService.update_publication(99999, publication_data)


class TestPublicationStatusToggle:
    """Test publication status toggle functionality."""
    
    def test_toggle_active_to_inactive(self, app, test_journal_publication):
        """Test toggling active publication to inactive."""
        with app.app_context():
            assert test_journal_publication.is_active == True
            
            publication, action = PublicationService.toggle_publication_status(
                test_journal_publication.id
            )
            
            assert action == 'deactivated'
            assert publication.is_active == False
    
    def test_toggle_inactive_to_active(self, app, test_journal_publication):
        """Test toggling inactive publication to active."""
        with app.app_context():
            # First deactivate using service to avoid session issues
            pub_after_deactivate, action1 = PublicationService.toggle_publication_status(test_journal_publication.id)
            assert pub_after_deactivate.is_active == False
            assert action1 == 'deactivated'
            
            # Now test toggling back to active
            publication, action = PublicationService.toggle_publication_status(
                test_journal_publication.id
            )
            
            assert action == 'activated'
            assert publication.is_active == True
    
    def test_toggle_status_nonexistent_publication(self, app):
        """Test toggling status of non-existent publication."""
        with app.app_context():
            with pytest.raises(ValueError, match="Publication with ID 99999 not found"):
                PublicationService.toggle_publication_status(99999)


class TestPublicationQueries:
    """Test publication query service methods."""
    
    def test_get_publication_by_id(self, app, test_journal_publication):
        """Test getting publication by ID."""
        with app.app_context():
            publication = PublicationService.get_publication_by_id(test_journal_publication.id)
            
            assert publication is not None
            assert publication.id == test_journal_publication.id
            assert publication.title == test_journal_publication.title
    
    def test_get_publication_by_invalid_id(self, app):
        """Test getting publication by invalid ID."""
        with app.app_context():
            publication = PublicationService.get_publication_by_id(99999)
            assert publication is None
    
    def test_search_publications(self, app, test_member):
        """Test searching publications by title."""
        with app.app_context():
            # Create publications with searchable titles
            Publication.create_publication(
                member_id=test_member.id,
                publication_type='journal',
                title='Searchable Journal Title',
                language_code='en',
                journal_issn='1111-1111'
            )
            Publication.create_publication(
                member_id=test_member.id,
                publication_type='book',
                title='Different Book Title',
                language_code='en',
                book_type='monograph'
            )
            
            # Search for "Searchable"
            results = PublicationService.search_publications(
                test_member.id, 'Searchable'
            )
            
            assert results.total == 1
            assert 'Searchable Journal Title' in [pub.title for pub in results.items]
            
            # Search for "Title" (should match both)
            results = PublicationService.search_publications(
                test_member.id, 'Title'
            )
            
            assert results.total == 2


class TestWorkflowInfo:
    """Test workflow information service methods."""
    
    def test_get_workflow_info_journal(self, app, test_journal_publication):
        """Test workflow info for journal (multiple drafts)."""
        with app.app_context():
            workflow_info = PublicationService.get_workflow_info(test_journal_publication)
            
            assert workflow_info['supports_multiple_drafts'] == True
            assert workflow_info['is_single_draft_type'] == False
            assert workflow_info['relationship_type'] == '1:N (Multiple Drafts)'
    
    def test_get_workflow_info_book(self, app, test_book_publication):
        """Test workflow info for book (single draft)."""
        with app.app_context():
            workflow_info = PublicationService.get_workflow_info(test_book_publication)
            
            assert workflow_info['supports_multiple_drafts'] == False
            assert workflow_info['is_single_draft_type'] == True
            assert workflow_info['relationship_type'] == '1:1 (Single Draft)'


class TestServiceIntegration:
    """Test service integration with other components."""
    
    def test_extract_form_data(self, app):
        """Test form data extraction utility method."""
        # This would typically be tested with a mock form object
        # For now, we'll test the concept that the method exists and can be called
        with app.app_context():
            # Note: This is testing the method exists and is callable
            # In real tests, you'd create a mock form object
            assert hasattr(PublicationService, '_extract_form_data')
    
    def test_clear_type_specific_fields(self, app, test_journal_publication):
        """Test clearing type-specific fields."""
        with app.app_context():
            original_issn = test_journal_publication.journal_issn
            assert original_issn is not None
            
            # Clear fields by changing type (this tests the private method indirectly)
            PublicationService._clear_type_specific_fields(test_journal_publication, 'book')
            
            assert test_journal_publication.journal_issn is None
            assert test_journal_publication.journal_abbreviated_title is None
    
    def test_validate_type_specific_fields(self, app):
        """Test type-specific field validation."""
        with app.app_context():
            # Valid book series data
            valid_data = {
                'publication_type': 'book_series',
                'series_title': 'Valid Series Title'
            }
            # Should not raise an exception
            PublicationService._validate_type_specific_fields(valid_data)
            
            # Invalid book series data (missing series_title)
            invalid_data = {
                'publication_type': 'book_series'
                # Missing series_title
            }
            
            with pytest.raises(ValueError, match="Series title is required"):
                PublicationService._validate_type_specific_fields(invalid_data)