"""
Publication model - represents publications (journals, books, monographs) with Crossref metadata.
"""

import re
import enum
from datetime import datetime
from sqlalchemy.exc import IntegrityError
from sqlalchemy import JSON
from app import db
from app.models.base import BaseModel
from app.utils.validation import validate_issn, validate_isbn


class PublicationType(enum.Enum):
    """Enumeration for publication types supported by Crossref."""
    journal = 'journal'
    book_series = 'book_series' 
    book_set = 'book_set'
    book = 'book'


class Publication(BaseModel):
    """
    Publication model - represents publications that can have DOI registrations.
    Enhanced with Crossref metadata fields for XML generation.
    """

    __tablename__ = 'publications'

    # Foreign key relationship to Member
    member_id = db.Column(db.Integer, db.ForeignKey('members.id', ondelete='CASCADE'), 
                         nullable=False, index=True)

    # TPH Union - Zajednička polja za sve tipove
    publication_type = db.Column(db.Enum(PublicationType), nullable=False, index=True)
    title = db.Column(db.String(500), nullable=False, index=True)
    subtitle = db.Column(db.String(500), nullable=True)
    language_code = db.Column(db.String(10), nullable=False, default='en')  # ISO language code
    
    # TPH Union - Journal specifična polja
    journal_abbreviated_title = db.Column(db.String(200), nullable=True)
    journal_issn = db.Column(db.String(20), nullable=True)
    journal_electronic_issn = db.Column(db.String(20), nullable=True)
    journal_coden = db.Column(db.String(10), nullable=True)
    
    # TPH Union - Book Series specifična polja
    series_title = db.Column(db.String(200), nullable=True)
    series_subtitle = db.Column(db.String(200), nullable=True)
    series_issn = db.Column(db.String(20), nullable=True)
    series_electronic_issn = db.Column(db.String(20), nullable=True)
    series_coden = db.Column(db.String(10), nullable=True)
    series_number = db.Column(db.String(50), nullable=True)
    
    # TPH Union - Book Set specifična polja
    set_title = db.Column(db.String(200), nullable=True)
    set_subtitle = db.Column(db.String(200), nullable=True)  
    set_isbn = db.Column(db.String(20), nullable=True)
    set_electronic_isbn = db.Column(db.String(20), nullable=True)
    set_part_number = db.Column(db.String(50), nullable=True)
    
    # TPH Union - Book specifična polja
    book_type = db.Column(db.String(50), nullable=True)  # edited_book, monograph, reference, textbook, other
    edition_number = db.Column(db.Integer, nullable=True)
    isbn = db.Column(db.String(20), nullable=True)
    electronic_isbn = db.Column(db.String(20), nullable=True)
    noisbn_reason = db.Column(db.String(100), nullable=True)
    
    # Uklonjeni promenljivi podaci - sada idu u DOIDraft:
    # - publication_year/month/day (datum konkretnog članka)
    # - media_type (specifično za članak) 
    # - publication_doi (specifično za članak)
    # - resource_url (specifično za članak)
    # - crossref_metadata (kompleksni podaci za članak)
    # - publisher/publisher_place (može biti različit po članku)
    
    # Status
    is_active = db.Column(db.Boolean, default=True, nullable=False, index=True)

    # Relationships
    member = db.relationship('Member', backref=db.backref('publications', lazy='dynamic', cascade='all, delete-orphan'))

    # Indexes for performance
    __table_args__ = (
        db.Index('idx_publication_member_type', 'member_id', 'publication_type', 'is_active'),
        db.Index('idx_publication_title', 'title'),
        db.Index('idx_publication_type', 'publication_type'),
        # Type-specific indexes
        db.Index('idx_journal_issn', 'journal_issn'),
        db.Index('idx_series_issn', 'series_issn'),
        db.Index('idx_set_isbn', 'set_isbn'),
        db.Index('idx_book_isbn', 'isbn'),
    )

    def __repr__(self):
        """String representation for debugging."""
        primary_id = self.get_primary_identifier()
        return f"<Publication(id={self.id}, type='{self.publication_type.value}', title='{self.title[:50]}...', identifier='{primary_id}')>"

    def __str__(self):
        """Human-readable string representation."""
        primary_id = self.get_primary_identifier()
        return f"Publication: {self.title} ({self.publication_type.value.upper()}) - {primary_id}"

    def to_dict(self):
        """Convert model to dictionary for JSON serialization."""
        base_dict = super().to_dict()
        base_dict.update({
            'member_id': self.member_id,
            'publication_type': self.publication_type.value if self.publication_type else None,
            'title': self.title,
            'subtitle': self.subtitle,
            'language_code': self.language_code,
            # Journal fields
            'journal_abbreviated_title': self.journal_abbreviated_title,
            'journal_issn': self.journal_issn,
            'journal_electronic_issn': self.journal_electronic_issn,
            'journal_coden': self.journal_coden,
            # Book Series fields
            'series_title': self.series_title,
            'series_subtitle': self.series_subtitle,
            'series_issn': self.series_issn,
            'series_electronic_issn': self.series_electronic_issn,
            'series_coden': self.series_coden,
            'series_number': self.series_number,
            # Book Set fields
            'set_title': self.set_title,
            'set_subtitle': self.set_subtitle,
            'set_isbn': self.set_isbn,
            'set_electronic_isbn': self.set_electronic_isbn,
            'set_part_number': self.set_part_number,
            # Book fields
            'book_type': self.book_type,
            'edition_number': self.edition_number,
            'isbn': self.isbn,
            'electronic_isbn': self.electronic_isbn,
            'noisbn_reason': self.noisbn_reason,
            'is_active': self.is_active
        })
        return base_dict

    @classmethod
    def create_publication(cls, member_id, publication_type, title, 
                          language_code='en', subtitle=None, is_active=True, **type_specific_fields):
        """Create a new publication template with type-specific validation."""
        
        # Validate required fields
        if not title or not title.strip():
            raise ValueError("Publication title is required")
        
        # Convert string type to enum if needed
        if isinstance(publication_type, str):
            try:
                publication_type = PublicationType(publication_type.lower())
            except ValueError:
                valid_types = [t.value for t in PublicationType]
                raise ValueError(f"Invalid publication type: {publication_type}. Must be one of: {valid_types}")
        
        # Type-specific validation
        cls._validate_type_specific_fields(publication_type, type_specific_fields)
        
        # Create new publication template
        publication = cls(
            member_id=member_id,
            publication_type=publication_type,
            title=title.strip(),
            subtitle=subtitle.strip() if subtitle else None,
            language_code=language_code,
            is_active=is_active,
            **type_specific_fields
        )

        return publication.save()

    @classmethod
    def _validate_type_specific_fields(cls, publication_type, fields):
        """Validate type-specific fields based on publication type."""
        if publication_type == PublicationType.journal:
            # Journal requires ISSN
            issn = fields.get('journal_issn')
            if issn and not cls._validate_issn(issn):
                raise ValueError("Invalid ISSN format for journal publication")
                
        elif publication_type == PublicationType.book_series:
            # Book Series requires series ISSN
            series_issn = fields.get('series_issn')
            if series_issn and not cls._validate_issn(series_issn):
                raise ValueError("Invalid ISSN format for book series")
                
        elif publication_type == PublicationType.book_set:
            # Book Set requires set ISBN
            set_isbn = fields.get('set_isbn')
            if set_isbn and not cls._validate_isbn(set_isbn):
                raise ValueError("Invalid ISBN format for book set")
                
        elif publication_type == PublicationType.book:
            # Book requires ISBN
            isbn = fields.get('isbn')
            if isbn and not cls._validate_isbn(isbn):
                raise ValueError("Invalid ISBN format for book")
    
    @staticmethod
    def _validate_issn(issn):
        """Validate ISSN format using centralized validation."""
        return validate_issn(issn.upper())

    @staticmethod
    def _validate_isbn(isbn):
        """Validate ISBN format using centralized validation."""
        # Remove dashes and spaces for validation
        clean_isbn = re.sub(r'[-\s]', '', isbn.upper())
        return validate_isbn(clean_isbn)

    @classmethod
    def get_by_member(cls, member_id, active_only=True):
        """Get all publications for a member."""
        query = cls.query.filter_by(member_id=member_id)
        if active_only:
            query = query.filter_by(is_active=True)
        return query.all()

    @classmethod
    def get_by_type(cls, publication_type, active_only=True):
        """Get all publications of a specific type."""
        if isinstance(publication_type, str):
            publication_type = PublicationType(publication_type.lower())
        
        query = cls.query.filter_by(publication_type=publication_type)
        if active_only:
            query = query.filter_by(is_active=True)
        return query.all()

    @classmethod
    def get_by_identifier(cls, identifier):
        """Get publication by type-specific identifier (ISSN/ISBN)."""
        return cls.query.filter(
            db.or_(
                cls.journal_issn == identifier,
                cls.journal_electronic_issn == identifier,
                cls.series_issn == identifier,
                cls.series_electronic_issn == identifier,
                cls.set_isbn == identifier,
                cls.set_electronic_isbn == identifier,
                cls.isbn == identifier,
                cls.electronic_isbn == identifier
            )
        ).first()

    def deactivate(self):
        """Deactivate the publication."""
        self.is_active = False
        return self.save()

    def activate(self):
        """Activate the publication."""
        self.is_active = True
        return self.save()

    # Uklonjene metadata management metode - sada se radi u DOIDraft modelu:
    # - update_metadata() - kompleksni metapodaci se upravljaju na draft nivou
    # - add_contributor() - kontributori su specifični za članak/poglavlje

    # Uklonjena set_publication_date metoda - publication date se sada postavlja u DOIDraft

    def is_journal(self):
        """Check if this is a journal publication."""
        return self.publication_type == PublicationType.journal

    def is_book_series(self):
        """Check if this is a book series publication."""
        return self.publication_type == PublicationType.book_series
        
    def is_book_set(self):
        """Check if this is a book set publication."""
        return self.publication_type == PublicationType.book_set

    def is_book(self):
        """Check if this is a book publication."""
        return self.publication_type == PublicationType.book
        
    def supports_multiple_drafts(self):
        """Check if this publication type supports multiple drafts (1:N relationship)."""
        return self.publication_type in [PublicationType.journal, PublicationType.book_series, PublicationType.book_set]
        
    def is_single_draft_type(self):
        """Check if this publication type supports only single draft (1:1 relationship)."""
        return self.publication_type == PublicationType.book

    def get_primary_identifier(self):
        """Get the primary identifier for this publication type."""
        if self.is_journal():
            return self.journal_issn or self.journal_electronic_issn
        elif self.is_book_series():
            return self.series_issn or self.series_electronic_issn
        elif self.is_book_set():
            return self.set_isbn or self.set_electronic_isbn
        elif self.is_book():
            return self.isbn or self.electronic_isbn
        return None

    def get_template_metadata(self):
        """Get template metadata for this publication (fixed identifiers only)."""
        template_data = {
            'publication_type': self.publication_type.value,
            'title': self.title,
            'subtitle': self.subtitle,
            'language_code': self.language_code,
            'primary_identifier': self.get_primary_identifier(),
        }
        
        # Add type-specific template fields
        if self.is_journal():
            template_data.update({
                'abbreviated_title': self.journal_abbreviated_title,
                'issn': self.journal_issn,
                'electronic_issn': self.journal_electronic_issn,
                'coden': self.journal_coden,
            })
        elif self.is_book_series():
            template_data.update({
                'series_title': self.series_title,
                'series_subtitle': self.series_subtitle,
                'series_issn': self.series_issn,
                'series_electronic_issn': self.series_electronic_issn,
                'series_coden': self.series_coden,
                'series_number': self.series_number,
            })
        elif self.is_book_set():
            template_data.update({
                'set_title': self.set_title,
                'set_subtitle': self.set_subtitle,
                'set_isbn': self.set_isbn,
                'set_electronic_isbn': self.set_electronic_isbn,
                'set_part_number': self.set_part_number,
            })
        elif self.is_book():
            template_data.update({
                'book_type': self.book_type,
                'edition_number': self.edition_number,
                'isbn': self.isbn,
                'electronic_isbn': self.electronic_isbn,
                'noisbn_reason': self.noisbn_reason,
            })
            
        return template_data