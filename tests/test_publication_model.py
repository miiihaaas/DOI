"""
Unit tests for Publication model - Updated for TPH (Table Per Hierarchy) structure.
"""

import pytest
from datetime import datetime
from app import create_app, db
from app.models import Sponsor, Member, Publication, PublicationType


@pytest.fixture
def app():
    """Create and configure a test app."""
    app = create_app('testing')
    with app.app_context():
        db.create_all()
        yield app
        db.drop_all()


@pytest.fixture
def client(app):
    """Create a test client."""
    return app.test_client()


@pytest.fixture
def sponsor(app):
    """Create a test sponsor."""
    sponsor = Sponsor(
        name='Test Sponsor',
        email='sponsor@test.com',
        crossref_member_id='12345',
        is_active=True
    )
    sponsor.save()
    return sponsor


@pytest.fixture
def member(app, sponsor):
    """Create a test member."""
    member = Member.create_member(
        sponsor_id=sponsor.id,
        name='Test University',
        institution='Faculty of Science',
        contact_email='contact@testuni.edu',
        billing_address='123 University St',
        pib='123456789',
        matični_broj='987654321',
        šifra_delatnosti='8542',
        telefon='+381111234567',
        osoba_za_kontakt='Dr. Jane Doe',
        iban='RS35260005601001611379',
        naziv_banke='Komercijalna Banka',
        swift_bic='KOBBRSBG',
        pdv_status='Obveznik PDV-a',
        država_obveznika='Republika Srbija'
    )
    return member


class TestPublicationType:
    """Test cases for PublicationType enum."""

    def test_publication_type_values(self, app):
        """Test that PublicationType enum has correct values."""
        assert PublicationType.journal.value == 'journal'
        assert PublicationType.book_series.value == 'book_series'
        assert PublicationType.book_set.value == 'book_set'
        assert PublicationType.book.value == 'book'
        
    def test_enum_names_are_lowercase(self, app):
        """Test that enum names are lowercase (new structure)."""
        assert hasattr(PublicationType, 'journal')
        assert hasattr(PublicationType, 'book_series')
        assert hasattr(PublicationType, 'book_set')
        assert hasattr(PublicationType, 'book')


class TestPublicationModel:
    """Test cases for Publication model - TPH structure."""

    def test_journal_publication_creation(self, app, member):
        """Test creating a journal publication."""
        publication = Publication.create_publication(
            member_id=member.id,
            publication_type='journal',
            title='Advanced Materials Science Journal',
            language_code='en',
            subtitle='Research and Applications',
            journal_abbreviated_title='Adv. Mater. Sci.',
            journal_issn='1234-5678',
            journal_electronic_issn='1234-567X',
            journal_coden='AMSJA'
        )
        
        assert publication.id is not None
        assert publication.member_id == member.id
        assert publication.publication_type == PublicationType.journal
        assert publication.title == 'Advanced Materials Science Journal'
        assert publication.subtitle == 'Research and Applications'
        assert publication.language_code == 'en'
        assert publication.journal_issn == '1234-5678'
        assert publication.journal_electronic_issn == '1234-567X'
        assert publication.journal_abbreviated_title == 'Adv. Mater. Sci.'
        assert publication.journal_coden == 'AMSJA'
        assert publication.is_active is True

    def test_book_series_publication_creation(self, app, member):
        """Test creating a book series publication."""
        publication = Publication.create_publication(
            member_id=member.id,
            publication_type='book_series',
            title='Computer Science Research Series',
            language_code='en',
            series_title='CS Research Series',
            series_subtitle='Advanced Topics',
            series_issn='2345-6789',
            series_electronic_issn='2345-678X',
            series_coden='CSRSA',
            series_number='Volume 15'
        )
        
        assert publication.id is not None
        assert publication.publication_type == PublicationType.book_series
        assert publication.series_title == 'CS Research Series'
        assert publication.series_issn == '2345-6789'
        assert publication.series_number == 'Volume 15'

    def test_book_set_publication_creation(self, app, member):
        """Test creating a book set publication."""
        publication = Publication.create_publication(
            member_id=member.id,
            publication_type='book_set',
            title='Encyclopedia of Science',
            language_code='en',
            set_title='Science Encyclopedia Set',
            set_subtitle='Complete Collection',
            set_isbn='978-0-123456-78-9',
            set_electronic_isbn='978-0-123456-79-6',
            set_part_number='Part 1'
        )
        
        assert publication.id is not None
        assert publication.publication_type == PublicationType.book_set
        assert publication.set_title == 'Science Encyclopedia Set'
        assert publication.set_isbn == '978-0-123456-78-9'
        assert publication.set_part_number == 'Part 1'

    def test_book_publication_creation(self, app, member):
        """Test creating a book publication."""
        publication = Publication.create_publication(
            member_id=member.id,
            publication_type='book',
            title='Introduction to Machine Learning',
            language_code='en',
            book_type='textbook',
            edition_number=2,
            isbn='978-0-987654-32-1',
            electronic_isbn='978-0-987654-33-8'
        )
        
        assert publication.id is not None
        assert publication.publication_type == PublicationType.book
        assert publication.book_type == 'textbook'
        assert publication.edition_number == 2
        assert publication.isbn == '978-0-987654-32-1'

    def test_publication_creation_with_enum_object(self, app, member):
        """Test creating publication with PublicationType enum object."""
        publication = Publication.create_publication(
            member_id=member.id,
            publication_type=PublicationType.journal,
            title='Test Journal',
            language_code='sr',
            journal_issn='1111-2222'
        )
        
        assert publication.publication_type == PublicationType.journal
        assert publication.language_code == 'sr'

    def test_publication_creation_with_invalid_type(self, app, member):
        """Test that invalid publication type raises error."""
        with pytest.raises(ValueError, match="Invalid publication type"):
            Publication.create_publication(
                member_id=member.id,
                publication_type='invalid_type',
                title='Test Publication',
                language_code='en'
            )

    def test_publication_missing_required_fields(self, app, member):
        """Test that missing required fields raise errors."""
        # Empty title
        with pytest.raises(ValueError, match="Publication title is required"):
            Publication.create_publication(
                member_id=member.id,
                publication_type='journal',
                title='',  # Empty string should trigger validation
                language_code='en'
            )
        
        # None title
        with pytest.raises(ValueError, match="Publication title is required"):
            Publication.create_publication(
                member_id=member.id,
                publication_type='journal',
                title=None,  # None should trigger validation
                language_code='en'
            )

    def test_publication_relationship_with_member(self, app, member):
        """Test publication-member relationship."""
        publication = Publication.create_publication(
            member_id=member.id,
            publication_type='journal',
            title='Test Journal',
            language_code='en',
            journal_issn='1234-5678'
        )
        
        assert publication.member == member
        assert publication in member.publications.all()

    def test_publication_repr_and_str(self, app, member):
        """Test publication string representations."""
        publication = Publication.create_publication(
            member_id=member.id,
            publication_type='journal',
            title='Advanced Materials Science Journal',
            language_code='en',
            journal_issn='1234-5678'
        )
        
        repr_str = repr(publication)
        assert 'Publication' in repr_str
        assert 'journal' in repr_str
        assert 'Advanced Materials Science Journal' in repr_str

    def test_get_by_member(self, app, member):
        """Test getting publications by member."""
        # Create test publications
        pub1 = Publication.create_publication(
            member_id=member.id,
            publication_type='journal',
            title='Journal 1',
            language_code='en',
            journal_issn='1111-1111'
        )
        
        pub2 = Publication.create_publication(
            member_id=member.id,
            publication_type='book',
            title='Book 1',
            language_code='en',
            isbn='978-1-111111-11-1'
        )
        
        # Test query
        publications = Publication.query.filter_by(member_id=member.id).all()
        assert len(publications) == 2
        assert pub1 in publications
        assert pub2 in publications

    def test_get_by_type(self, app, member):
        """Test getting publications by type."""
        # Create different types
        journal = Publication.create_publication(
            member_id=member.id,
            publication_type='journal',
            title='Test Journal',
            language_code='en',
            journal_issn='1111-1111'
        )
        
        book = Publication.create_publication(
            member_id=member.id,
            publication_type='book',
            title='Test Book',
            language_code='en',
            isbn='978-1-111111-11-1'
        )
        
        # Test filtering
        journals = Publication.query.filter_by(publication_type=PublicationType.journal).all()
        books = Publication.query.filter_by(publication_type=PublicationType.book).all()
        
        assert len(journals) == 1
        assert len(books) == 1
        assert journal in journals
        assert book in books

    def test_publication_deactivate_activate(self, app, member):
        """Test publication activation/deactivation."""
        publication = Publication.create_publication(
            member_id=member.id,
            publication_type='journal',
            title='Test Journal',
            language_code='en',
            journal_issn='1234-5678'
        )
        
        # Test initial state
        assert publication.is_active is True
        
        # Test deactivation
        publication.deactivate()
        assert publication.is_active is False
        
        # Test activation
        publication.activate()
        assert publication.is_active is True

    def test_publication_type_checks(self, app, member):
        """Test publication type check methods."""
        journal = Publication.create_publication(
            member_id=member.id,
            publication_type='journal',
            title='Test Journal',
            language_code='en',
            journal_issn='1234-5678'
        )
        
        book_series = Publication.create_publication(
            member_id=member.id,
            publication_type='book_series',
            title='Test Series',
            language_code='en',
            series_title='Test Series Title',
            series_issn='2345-6789'
        )
        
        book = Publication.create_publication(
            member_id=member.id,
            publication_type='book',
            title='Test Book',
            language_code='en',
            isbn='978-0-123456-78-9'
        )
        
        # Test type checks
        assert journal.is_journal() is True
        assert journal.is_book() is False
        
        assert book_series.is_book_series() is True
        assert book_series.is_journal() is False
        
        assert book.is_book() is True
        assert book.is_journal() is False

    def test_workflow_type_checks(self, app, member):
        """Test workflow type differentiation (1:N vs 1:1)."""
        journal = Publication.create_publication(
            member_id=member.id,
            publication_type='journal',
            title='Test Journal',
            language_code='en',
            journal_issn='1234-5678'
        )
        
        book = Publication.create_publication(
            member_id=member.id,
            publication_type='book',
            title='Test Book',
            language_code='en',
            isbn='978-0-123456-78-9'
        )
        
        # Journal supports multiple drafts (1:N)
        assert journal.supports_multiple_drafts() is True
        assert journal.is_single_draft_type() is False
        
        # Book supports single draft (1:1)
        assert book.supports_multiple_drafts() is False
        assert book.is_single_draft_type() is True

    def test_create_publication_validates_type_specific_fields(self, app, member):
        """Test that create_publication validates type-specific fields."""
        # This test will depend on validation implementation
        # For now, just test that creation works with valid fields
        publication = Publication.create_publication(
            member_id=member.id,
            publication_type='journal',
            title='Test Journal',
            language_code='en',
            journal_issn='1234-5678'  # Valid ISSN format
        )
        
        assert publication.journal_issn == '1234-5678'