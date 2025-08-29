"""
Publication Service Layer - Business logic for publication template management.
"""

from typing import Optional, Dict, Any, List
from flask import current_app
from flask_sqlalchemy.pagination import Pagination

from app import db
from app.models.publication import Publication, PublicationType
from app.models.member import Member
from app.utils.pagination import paginate_query
from app.services.activity_logger import ActivityLogger


class PublicationService:
    """Service class for publication-related business operations."""

    @staticmethod
    def get_publications_for_member(
        member_id: int, 
        page: int = 1, 
        per_page: int = 10, 
        publication_type_filter: Optional[str] = None
    ) -> Pagination:
        """
        Get paginated publications for a specific member with optional type filtering.
        
        Args:
            member_id: ID of the member
            page: Page number for pagination
            per_page: Number of items per page
            publication_type_filter: Optional publication type filter
            
        Returns:
            Pagination object with publications
        """
        # Build base query
        query = Publication.query.filter_by(member_id=member_id, is_active=True)
        
        # Apply type filter if provided
        if publication_type_filter:
            query = query.filter_by(publication_type=publication_type_filter)
        
        # Order by creation date (newest first)
        query = query.order_by(Publication.created_at.desc())
        
        # Apply pagination
        return paginate_query(query, page=page, per_page=per_page)

    @staticmethod
    def get_publication_counts_by_type(member_id: int) -> Dict[str, int]:
        """
        Get publication counts grouped by type for a specific member.
        
        Args:
            member_id: ID of the member
            
        Returns:
            Dictionary with publication type as key and count as value
        """
        type_counts = {}
        for pub_type in PublicationType:
            count = Publication.query.filter_by(
                member_id=member_id, 
                publication_type=pub_type,
                is_active=True
            ).count()
            type_counts[pub_type.value] = count
        
        return type_counts

    @staticmethod
    def create_publication(member_id: int, publication_data: Dict[str, Any]) -> Publication:
        """
        Create a new publication template.
        
        Args:
            member_id: ID of the member who owns the publication
            publication_data: Dictionary containing publication data
            
        Returns:
            Created Publication instance
            
        Raises:
            ValueError: If validation fails
        """
        # Validate member exists
        member = db.session.get(Member, member_id)
        if not member:
            raise ValueError(f"Member with ID {member_id} not found")
        
        # Validate required fields
        required_fields = ['publication_type', 'title']
        for field in required_fields:
            if field not in publication_data or not publication_data[field]:
                raise ValueError(f"Field '{field}' is required")
        
        # Validate publication type
        pub_type = publication_data['publication_type']
        try:
            PublicationType(pub_type)
        except ValueError:
            raise ValueError(f"Invalid publication type: {pub_type}")
        
        # Type-specific validation
        PublicationService._validate_type_specific_fields(publication_data)
        
        # Create publication using model method
        publication = Publication.create_publication(
            member_id=member_id,
            **publication_data
        )
        
        # Log publication creation activity
        ActivityLogger.log_publication_action('create', publication)
        
        current_app.logger.info(
            f"Created publication '{publication.title}' (ID: {publication.id}) "
            f"for member {member.name} (ID: {member_id})"
        )
        
        return publication

    @staticmethod
    def update_publication(publication_id: int, publication_data: Dict[str, Any]) -> Publication:
        """
        Update an existing publication template.
        
        Args:
            publication_id: ID of the publication to update
            publication_data: Dictionary containing updated publication data
            
        Returns:
            Updated Publication instance
            
        Raises:
            ValueError: If validation fails or publication not found
        """
        publication = db.session.get(Publication, publication_id)
        if not publication:
            raise ValueError(f"Publication with ID {publication_id} not found")
        
        # Store old values for logging
        old_title = publication.title
        old_type = publication.publication_type.value
        
        # Track changes for activity logging
        changes = {}
        for field, new_value in publication_data.items():
            if hasattr(publication, field):
                current_value = getattr(publication, field)
                if field == 'publication_type' and hasattr(current_value, 'value'):
                    current_value = current_value.value
                if current_value != new_value:
                    changes[field] = new_value
        
        # Validate required fields
        if 'title' in publication_data and not publication_data['title']:
            raise ValueError("Title is required")
        
        # Validate publication type if being changed
        if 'publication_type' in publication_data:
            pub_type = publication_data['publication_type']
            try:
                PublicationType(pub_type)
            except ValueError:
                raise ValueError(f"Invalid publication type: {pub_type}")
        
        # Type-specific validation
        PublicationService._validate_type_specific_fields(publication_data)
        
        # Clear type-specific fields if type changed (do this before setting new values)
        if 'publication_type' in publication_data:
            new_type = publication_data['publication_type']
            if new_type != old_type:
                PublicationService._clear_type_specific_fields(publication, new_type)
        
        # Update fields (after clearing old type-specific fields)
        for field, value in publication_data.items():
            if hasattr(publication, field):
                setattr(publication, field, value)
        
        publication.save()
        
        # Log publication update activity (only if there were actual changes)
        if changes:
            ActivityLogger.log_publication_action('update', publication, changes=changes)
        
        current_app.logger.info(
            f"Updated publication '{publication.title}' (ID: {publication_id}) "
            f"for member {publication.member.name}"
        )
        
        return publication

    @staticmethod
    def toggle_publication_status(publication_id: int) -> tuple[Publication, str]:
        """
        Toggle active status of a publication (soft delete/restore).
        
        Args:
            publication_id: ID of the publication
            
        Returns:
            Tuple of (updated publication, action performed)
            
        Raises:
            ValueError: If publication not found
        """
        publication = db.session.get(Publication, publication_id)
        if not publication:
            raise ValueError(f"Publication with ID {publication_id} not found")
        
        if publication.is_active:
            publication.deactivate()
            action = "deactivated"
            ActivityLogger.log_publication_action('deactivate', publication)
        else:
            publication.activate()
            action = "activated"
            ActivityLogger.log_publication_action('activate', publication)
        
        current_app.logger.info(
            f"Publication '{publication.title}' (ID: {publication_id}) {action} "
            f"for member {publication.member.name}"
        )
        
        return publication, action

    @staticmethod
    def get_publication_by_id(publication_id: int) -> Optional[Publication]:
        """
        Get publication by ID.
        
        Args:
            publication_id: ID of the publication
            
        Returns:
            Publication instance or None if not found
        """
        return db.session.get(Publication, publication_id)

    @staticmethod
    def search_publications(
        member_id: int, 
        search_term: str, 
        page: int = 1, 
        per_page: int = 10
    ) -> Pagination:
        """
        Search publications by title for a specific member.
        
        Args:
            member_id: ID of the member
            search_term: Term to search for in title
            page: Page number for pagination
            per_page: Number of items per page
            
        Returns:
            Pagination object with matching publications
        """
        query = Publication.query.filter(
            Publication.member_id == member_id,
            Publication.is_active == True,
            Publication.title.contains(search_term)
        ).order_by(Publication.created_at.desc())
        
        return paginate_query(query, page=page, per_page=per_page)

    @staticmethod
    def _validate_type_specific_fields(publication_data: Dict[str, Any]) -> None:
        """
        Validate type-specific required fields.
        
        Args:
            publication_data: Dictionary containing publication data
            
        Raises:
            ValueError: If validation fails
        """
        pub_type = publication_data.get('publication_type')
        
        if pub_type == 'book_series':
            if not publication_data.get('series_title'):
                raise ValueError("Series title is required for book series")
                
        elif pub_type == 'book_set':
            if not publication_data.get('set_title'):
                raise ValueError("Set title is required for book sets")
                
        elif pub_type == 'book':
            if not publication_data.get('book_type'):
                raise ValueError("Book type is required for books")

    @staticmethod
    def _clear_type_specific_fields(publication: Publication, new_type: str) -> None:
        """
        Clear type-specific fields when publication type changes.
        
        Args:
            publication: Publication instance to update
            new_type: New publication type
        """
        # Define all type-specific fields
        all_type_fields = [
            # Journal fields
            'journal_abbreviated_title', 'journal_issn', 'journal_electronic_issn', 'journal_coden',
            # Book Series fields
            'series_title', 'series_subtitle', 'series_issn', 'series_electronic_issn', 
            'series_coden', 'series_number',
            # Book Set fields
            'set_title', 'set_subtitle', 'set_isbn', 'set_electronic_isbn', 'set_part_number',
            # Book fields
            'book_type', 'edition_number', 'isbn', 'electronic_isbn', 'noisbn_reason'
        ]
        
        # Clear all type-specific fields
        for field in all_type_fields:
            if hasattr(publication, field):
                setattr(publication, field, None)

    @staticmethod
    def _extract_form_data(form) -> Dict[str, Any]:
        """
        Extract data from publication form.
        
        Args:
            form: UniversalPublicationForm instance
            
        Returns:
            Dictionary with extracted form data
        """
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
        
        return publication_data

    @staticmethod
    def get_workflow_info(publication: Publication) -> Dict[str, Any]:
        """
        Get workflow information for a publication.
        
        Args:
            publication: Publication instance
            
        Returns:
            Dictionary with workflow information
        """
        return {
            'supports_multiple_drafts': publication.supports_multiple_drafts(),
            'is_single_draft_type': publication.is_single_draft_type(),
            'relationship_type': '1:N (Multiple Drafts)' if publication.supports_multiple_drafts() else '1:1 (Single Draft)'
        }