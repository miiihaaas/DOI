"""
Tests for Publication model.

Story 2.3 - Task 7: Publication model tests.
"""

import pytest
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model

from doi_portal.publications.models import (
    AccessType,
    Publication,
    PublicationType,
)
from doi_portal.publishers.models import Publisher

from .factories import (
    BookFactory,
    ConferenceFactory,
    JournalFactory,
    PublicationFactory,
    PublisherFactory,
)

User = get_user_model()


# =============================================================================
# Task 7.1: Test Publication model creation with all types
# =============================================================================


@pytest.mark.django_db
class TestPublicationModel:
    """Test Publication model."""

    def test_create_publication_with_required_fields(self):
        """Test creating publication with required fields only."""
        publisher = PublisherFactory()
        publication = Publication.objects.create(
            title="Test Publikacija",
            publisher=publisher,
        )
        assert publication.pk is not None
        assert publication.title == "Test Publikacija"
        assert publication.publisher == publisher
        assert publication.publication_type == PublicationType.JOURNAL  # default

    def test_publication_str_returns_title(self):
        """Test __str__ returns publication title."""
        publisher = PublisherFactory()
        publication = Publication(title="Naučni časopis", publisher=publisher)
        assert str(publication) == "Naučni časopis"

    def test_publication_type_choices(self):
        """Test all publication type choices are valid."""
        assert PublicationType.JOURNAL == "JOURNAL"
        assert PublicationType.CONFERENCE == "CONFERENCE"
        assert PublicationType.BOOK == "BOOK"
        assert PublicationType.OTHER == "OTHER"

    def test_access_type_choices(self):
        """Test all access type choices are valid."""
        assert AccessType.OPEN == "OPEN"
        assert AccessType.RESTRICTED == "RESTRICTED"

    def test_timestamps_auto_set(self):
        """Test created_at and updated_at are auto-set."""
        publication = PublicationFactory()
        assert publication.created_at is not None
        assert publication.updated_at is not None


@pytest.mark.django_db
class TestJournalPublication:
    """Test Journal-specific publication fields (AC #2)."""

    def test_create_journal_publication(self):
        """Test creating a journal publication with type-specific fields."""
        publication = JournalFactory(
            title="Naučni časopis",
            issn_print="1234-5678",
            issn_online="2345-6789",
            abbreviation="Nauč. čas.",
            frequency="Kvartalno",
        )
        assert publication.pk is not None
        assert publication.publication_type == PublicationType.JOURNAL
        assert publication.issn_print == "1234-5678"
        assert publication.issn_online == "2345-6789"
        assert publication.abbreviation == "Nauč. čas."
        assert publication.frequency == "Kvartalno"

    def test_journal_type_icon(self):
        """Test journal type icon property."""
        publication = JournalFactory()
        assert publication.type_icon == "bi-journal-text"

    def test_journal_type_display(self):
        """Test journal type display property."""
        publication = JournalFactory()
        assert publication.type_display == "Časopis"


@pytest.mark.django_db
class TestConferencePublication:
    """Test Conference-specific publication fields (AC #3)."""

    def test_create_conference_publication(self):
        """Test creating a conference publication with type-specific fields."""
        import datetime

        publication = ConferenceFactory(
            title="Zbornik radova",
            conference_name="Naučna konferencija 2026",
            conference_acronym="NK2026",
            conference_location="Beograd, Srbija",
            conference_date=datetime.date(2026, 6, 15),
            series_issn="1111-2222",
        )
        assert publication.pk is not None
        assert publication.publication_type == PublicationType.CONFERENCE
        assert publication.conference_name == "Naučna konferencija 2026"
        assert publication.conference_acronym == "NK2026"
        assert publication.conference_location == "Beograd, Srbija"
        assert publication.conference_date == datetime.date(2026, 6, 15)
        assert publication.series_issn == "1111-2222"

    def test_conference_type_icon(self):
        """Test conference type icon property."""
        publication = ConferenceFactory()
        assert publication.type_icon == "bi-people"

    def test_conference_type_display(self):
        """Test conference type display property."""
        publication = ConferenceFactory()
        assert publication.type_display == "Zbornik"


@pytest.mark.django_db
class TestBookPublication:
    """Test Book-specific publication fields (AC #4)."""

    def test_create_book_publication(self):
        """Test creating a book/monograph publication with type-specific fields."""
        publication = BookFactory(
            title="Monografija",
            isbn_print="978-86-7549-123-4",
            isbn_online="978-86-7549-124-1",
            edition="1. izdanje",
            series_title="Naučna edicija",
        )
        assert publication.pk is not None
        assert publication.publication_type == PublicationType.BOOK
        assert publication.isbn_print == "978-86-7549-123-4"
        assert publication.isbn_online == "978-86-7549-124-1"
        assert publication.edition == "1. izdanje"
        assert publication.series_title == "Naučna edicija"

    def test_book_type_icon(self):
        """Test book type icon property."""
        publication = BookFactory()
        assert publication.type_icon == "bi-book"

    def test_book_type_display(self):
        """Test book type display property."""
        publication = BookFactory()
        assert publication.type_display == "Monografija"


@pytest.mark.django_db
class TestOtherPublication:
    """Test Other publication type."""

    def test_create_other_publication(self):
        """Test creating an 'other' type publication."""
        publisher = PublisherFactory()
        publication = Publication.objects.create(
            title="Ostala publikacija",
            publisher=publisher,
            publication_type=PublicationType.OTHER,
        )
        assert publication.pk is not None
        assert publication.publication_type == PublicationType.OTHER

    def test_other_type_icon(self):
        """Test other type icon property."""
        publisher = PublisherFactory()
        publication = Publication(
            title="Test",
            publisher=publisher,
            publication_type=PublicationType.OTHER,
        )
        assert publication.type_icon == "bi-file-earmark"

    def test_other_type_display(self):
        """Test other type display property."""
        publisher = PublisherFactory()
        publication = Publication(
            title="Test",
            publisher=publisher,
            publication_type=PublicationType.OTHER,
        )
        assert publication.type_display == "Ostalo"


# =============================================================================
# Task 7.2: Test type-specific field validation
# =============================================================================


@pytest.mark.django_db
class TestPublicationValidation:
    """Test Publication model field validation."""

    def test_invalid_issn_format_rejected(self):
        """Test invalid ISSN format raises validation error."""
        publisher = PublisherFactory()
        publication = Publication(
            title="Test",
            publisher=publisher,
            publication_type=PublicationType.JOURNAL,
            issn_print="invalid",
        )
        with pytest.raises(ValidationError) as exc_info:
            publication.full_clean()
        assert "issn_print" in exc_info.value.message_dict

    def test_invalid_isbn_format_rejected(self):
        """Test invalid ISBN format raises validation error."""
        publisher = PublisherFactory()
        publication = Publication(
            title="Test",
            publisher=publisher,
            publication_type=PublicationType.BOOK,
            isbn_print="invalid",
        )
        with pytest.raises(ValidationError) as exc_info:
            publication.full_clean()
        assert "isbn_print" in exc_info.value.message_dict

    def test_blank_optional_fields_allowed(self):
        """Test blank optional fields pass validation."""
        publisher = PublisherFactory()
        publication = Publication(
            title="Test",
            publisher=publisher,
            publication_type=PublicationType.JOURNAL,
            issn_print="",
            issn_online="",
            abbreviation="",
        )
        # Should not raise
        publication.full_clean()


# =============================================================================
# Task 7.5: Test soft delete functionality
# =============================================================================


@pytest.mark.django_db
class TestPublicationSoftDelete:
    """Test Publication soft delete functionality."""

    @pytest.fixture
    def admin_user(self):
        """Create an admin user for delete operations."""
        return User.objects.create_user(
            email="admin@test.com",
            password="testpass123",
        )

    def test_default_is_deleted_false(self):
        """Test is_deleted defaults to False."""
        publication = PublicationFactory()
        assert publication.is_deleted is False
        assert publication.deleted_at is None
        assert publication.deleted_by is None

    def test_soft_delete_sets_flags(self, admin_user):
        """Test soft_delete() sets is_deleted and timestamps."""
        publication = PublicationFactory()
        publication.soft_delete(user=admin_user)
        publication.refresh_from_db()

        assert publication.is_deleted is True
        assert publication.deleted_at is not None
        assert publication.deleted_by == admin_user

    def test_soft_deleted_excluded_from_default_queryset(self, admin_user):
        """Test soft-deleted publications excluded from default queryset."""
        publication = PublicationFactory()
        pk = publication.pk
        publication.soft_delete(user=admin_user)

        # Should not appear in objects (SoftDeleteManager)
        assert Publication.objects.filter(pk=pk).count() == 0

    def test_soft_deleted_included_in_all_objects(self, admin_user):
        """Test soft-deleted publications included in all_objects."""
        publication = PublicationFactory()
        pk = publication.pk
        publication.soft_delete(user=admin_user)

        # Should appear in all_objects
        assert Publication.all_objects.filter(pk=pk).count() == 1

    def test_restore_clears_delete_flags(self, admin_user):
        """Test restore() clears soft delete flags."""
        publication = PublicationFactory()
        publication.soft_delete(user=admin_user)
        publication.restore()
        publication.refresh_from_db()

        assert publication.is_deleted is False
        assert publication.deleted_at is None
        assert publication.deleted_by is None

        # Should appear in default queryset again
        assert Publication.objects.filter(pk=publication.pk).count() == 1


# =============================================================================
# Task 7.8: Test publisher association
# =============================================================================


@pytest.mark.django_db
class TestPublicationPublisherAssociation:
    """Test Publication-Publisher relationship."""

    def test_publication_has_publisher(self):
        """Test publication is associated with publisher."""
        publisher = PublisherFactory(name="Test Izdavač")
        publication = PublicationFactory(publisher=publisher)

        assert publication.publisher == publisher
        assert publication.publisher.name == "Test Izdavač"

    def test_publisher_publications_reverse_relation(self):
        """Test publisher.publications returns associated publications."""
        publisher = PublisherFactory()
        pub1 = PublicationFactory(publisher=publisher)
        pub2 = PublicationFactory(publisher=publisher)

        publications = publisher.publications.all()
        assert pub1 in publications
        assert pub2 in publications
        assert publications.count() == 2

    def test_publisher_publication_count(self):
        """Test publisher.publication_count returns correct count."""
        publisher = PublisherFactory()
        PublicationFactory(publisher=publisher)
        PublicationFactory(publisher=publisher)
        PublicationFactory(publisher=publisher)

        assert publisher.publication_count == 3

    def test_protect_on_delete(self):
        """Test cannot delete publisher with publications (PROTECT)."""
        from django.db.models import ProtectedError

        publisher = PublisherFactory()
        PublicationFactory(publisher=publisher)

        with pytest.raises(ProtectedError):
            publisher.delete()


# =============================================================================
# Test slug auto-generation
# =============================================================================


@pytest.mark.django_db
class TestPublicationSlug:
    """Test Publication slug auto-generation."""

    def test_slug_auto_generated_from_title(self):
        """Test slug is auto-generated from title."""
        publisher = PublisherFactory()
        publication = Publication.objects.create(
            title="Naučni časopis za fiziku",
            publisher=publisher,
        )
        assert publication.slug == "naucni-casopis-za-fiziku"

    def test_slug_uniqueness_with_duplicate_titles(self):
        """Test unique slugs for duplicate titles."""
        publisher = PublisherFactory()
        pub1 = Publication.objects.create(title="Test", publisher=publisher)
        pub2 = Publication.objects.create(title="Test", publisher=publisher)

        assert pub1.slug == "test"
        assert pub2.slug == "test-1"

    def test_slug_not_overwritten_on_update(self):
        """Test existing slug is preserved on update."""
        publication = PublicationFactory(title="Original Title")
        original_slug = publication.slug

        publication.title = "Updated Title"
        publication.save()

        assert publication.slug == original_slug

    def test_custom_slug_preserved(self):
        """Test custom slug is not overwritten."""
        publisher = PublisherFactory()
        publication = Publication.objects.create(
            title="Test Name",
            slug="custom-slug",
            publisher=publisher,
        )
        assert publication.slug == "custom-slug"


# =============================================================================
# Test audit log
# =============================================================================


@pytest.mark.django_db
class TestPublicationAuditLog:
    """Test Publication audit log registration."""

    def test_publication_registered_with_auditlog(self):
        """Test Publication model is registered with auditlog."""
        from auditlog.registry import auditlog

        assert Publication in auditlog.get_models()

    def test_create_logged(self):
        """Test publication creation is logged."""
        from auditlog.models import LogEntry

        publication = PublicationFactory()

        log_entry = LogEntry.objects.filter(
            object_pk=str(publication.pk),
            action=LogEntry.Action.CREATE,
        ).first()

        assert log_entry is not None

    def test_update_logged(self):
        """Test publication update is logged."""
        from auditlog.models import LogEntry

        publication = PublicationFactory(title="Original")
        publication.title = "Updated"
        publication.save()

        log_entry = LogEntry.objects.filter(
            object_pk=str(publication.pk),
            action=LogEntry.Action.UPDATE,
        ).first()

        assert log_entry is not None


# =============================================================================
# Test issue_count property
# =============================================================================


@pytest.mark.django_db
class TestPublicationIssueCount:
    """Test Publication.issue_count property."""

    def test_issue_count_returns_zero_when_no_issues(self):
        """Test issue_count returns 0 when no issues exist."""
        publication = PublicationFactory()
        assert publication.issue_count == 0
