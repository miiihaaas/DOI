"""
Tests for Publisher model.

Story 2.1 - Task 1: Publisher model field validation.
Task 7.1, 7.2, 7.3, 7.6, 7.7
"""

import pytest
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group

from doi_portal.publishers.models import Publisher, validate_doi_prefix, SoftDeleteManager

User = get_user_model()


# =============================================================================
# Task 7.2: Test DOI prefix format validation
# =============================================================================


class TestDOIPrefixValidator:
    """Test validate_doi_prefix function."""

    def test_valid_doi_prefix_4_digits(self):
        """Test valid DOI prefix with 4 digits after dot."""
        # Should not raise
        validate_doi_prefix("10.1234")

    def test_valid_doi_prefix_5_digits(self):
        """Test valid DOI prefix with 5 digits after dot."""
        validate_doi_prefix("10.12345")

    def test_valid_doi_prefix_many_digits(self):
        """Test valid DOI prefix with many digits after dot."""
        validate_doi_prefix("10.123456789")

    def test_invalid_doi_prefix_wrong_start(self):
        """Test DOI prefix must start with 10."""
        with pytest.raises(ValidationError) as exc_info:
            validate_doi_prefix("11.1234")
        assert exc_info.value.code == "invalid_doi_prefix"

    def test_invalid_doi_prefix_no_dot(self):
        """Test DOI prefix must have dot."""
        with pytest.raises(ValidationError):
            validate_doi_prefix("101234")

    def test_invalid_doi_prefix_too_few_digits(self):
        """Test DOI prefix must have at least 4 digits after dot."""
        with pytest.raises(ValidationError):
            validate_doi_prefix("10.123")

    def test_invalid_doi_prefix_letters(self):
        """Test DOI prefix cannot have letters."""
        with pytest.raises(ValidationError):
            validate_doi_prefix("10.abcd")

    def test_invalid_doi_prefix_empty(self):
        """Test empty DOI prefix is invalid."""
        with pytest.raises(ValidationError):
            validate_doi_prefix("")


# =============================================================================
# Task 7.1: Test Publisher model field validation
# =============================================================================


@pytest.mark.django_db
class TestPublisherModel:
    """Test Publisher model."""

    def test_create_publisher_with_required_fields(self):
        """Test creating publisher with required fields."""
        publisher = Publisher.objects.create(
            name="Test Izdavac",
            doi_prefix="10.1234",
        )
        assert publisher.pk is not None
        assert publisher.name == "Test Izdavac"
        assert publisher.doi_prefix == "10.1234"

    def test_publisher_str_returns_name(self):
        """Test __str__ returns publisher name."""
        publisher = Publisher(name="Test Izdavac", doi_prefix="10.1234")
        assert str(publisher) == "Test Izdavac"

    def test_doi_prefix_uniqueness(self):
        """Test DOI prefix must be unique."""
        Publisher.objects.create(name="First", doi_prefix="10.1234")

        with pytest.raises(Exception):  # IntegrityError
            Publisher.objects.create(name="Second", doi_prefix="10.1234")

    def test_publisher_optional_fields(self):
        """Test publisher optional fields can be blank."""
        publisher = Publisher.objects.create(
            name="Test",
            doi_prefix="10.5555",
            description="",
            contact_email="",
            contact_phone="",
            website="",
        )
        assert publisher.pk is not None

    def test_publisher_full_fields(self):
        """Test publisher with all fields populated."""
        publisher = Publisher.objects.create(
            name="Puni Izdavac",
            doi_prefix="10.9999",
            description="Opis izdavaca",
            contact_email="kontakt@izdavac.rs",
            contact_phone="+381 11 123 4567",
            website="https://www.izdavac.rs",
        )
        assert publisher.description == "Opis izdavaca"
        assert publisher.contact_email == "kontakt@izdavac.rs"
        assert publisher.contact_phone == "+381 11 123 4567"
        assert publisher.website == "https://www.izdavac.rs"

    def test_timestamps_auto_set(self):
        """Test created_at and updated_at are auto-set."""
        publisher = Publisher.objects.create(
            name="Timestamp Test",
            doi_prefix="10.7777",
        )
        assert publisher.created_at is not None
        assert publisher.updated_at is not None

    def test_model_validation_invalid_doi(self):
        """Test full_clean validates DOI prefix."""
        publisher = Publisher(name="Test", doi_prefix="invalid")
        with pytest.raises(ValidationError) as exc_info:
            publisher.full_clean()
        assert "doi_prefix" in exc_info.value.message_dict


# =============================================================================
# Task 7.3: Test slug auto-generation
# =============================================================================


@pytest.mark.django_db
class TestPublisherSlug:
    """Test Publisher slug auto-generation."""

    def test_slug_auto_generated_from_name(self):
        """Test slug is auto-generated from name."""
        publisher = Publisher.objects.create(
            name="Test Izdavac",
            doi_prefix="10.1234",
        )
        assert publisher.slug == "test-izdavac"

    def test_slug_handles_special_characters(self):
        """Test slug handles Serbian characters."""
        publisher = Publisher.objects.create(
            name="Srpski Casopis",
            doi_prefix="10.2222",
        )
        assert publisher.slug == "srpski-casopis"

    def test_slug_uniqueness_with_duplicate_names(self):
        """Test unique slugs for duplicate names."""
        pub1 = Publisher.objects.create(name="Test", doi_prefix="10.1111")
        pub2 = Publisher.objects.create(name="Test", doi_prefix="10.2222")

        assert pub1.slug == "test"
        assert pub2.slug == "test-1"

    def test_slug_not_overwritten_on_update(self):
        """Test existing slug is preserved on update."""
        publisher = Publisher.objects.create(
            name="Original Name",
            doi_prefix="10.3333",
        )
        original_slug = publisher.slug

        publisher.name = "Updated Name"
        publisher.save()

        assert publisher.slug == original_slug

    def test_custom_slug_preserved(self):
        """Test custom slug is not overwritten."""
        publisher = Publisher.objects.create(
            name="Test Name",
            slug="custom-slug",
            doi_prefix="10.4444",
        )
        assert publisher.slug == "custom-slug"


# =============================================================================
# Task 7.6: Test soft delete functionality
# =============================================================================


@pytest.mark.django_db
class TestPublisherSoftDelete:
    """Test Publisher soft delete functionality."""

    @pytest.fixture
    def admin_user(self):
        """Create an admin user for delete operations."""
        user = User.objects.create_user(
            email="admin@test.com",
            password="testpass123",
        )
        group, _ = Group.objects.get_or_create(name="Administrator")
        user.groups.add(group)
        return user

    @pytest.fixture
    def publisher(self):
        """Create a test publisher."""
        return Publisher.objects.create(
            name="Test Izdavac",
            doi_prefix="10.8888",
        )

    def test_default_is_deleted_false(self, publisher):
        """Test is_deleted defaults to False."""
        assert publisher.is_deleted is False
        assert publisher.deleted_at is None
        assert publisher.deleted_by is None

    def test_soft_delete_sets_flags(self, publisher, admin_user):
        """Test soft_delete() sets is_deleted and timestamps."""
        publisher.soft_delete(user=admin_user)
        publisher.refresh_from_db()

        assert publisher.is_deleted is True
        assert publisher.deleted_at is not None
        assert publisher.deleted_by == admin_user

    def test_soft_deleted_excluded_from_default_queryset(self, publisher, admin_user):
        """Test soft-deleted publishers excluded from default queryset."""
        pk = publisher.pk
        publisher.soft_delete(user=admin_user)

        # Should not appear in objects (SoftDeleteManager)
        assert Publisher.objects.filter(pk=pk).count() == 0

    def test_soft_deleted_included_in_all_objects(self, publisher, admin_user):
        """Test soft-deleted publishers included in all_objects."""
        pk = publisher.pk
        publisher.soft_delete(user=admin_user)

        # Should appear in all_objects
        assert Publisher.all_objects.filter(pk=pk).count() == 1

    def test_restore_clears_delete_flags(self, publisher, admin_user):
        """Test restore() clears soft delete flags."""
        publisher.soft_delete(user=admin_user)
        publisher.restore()
        publisher.refresh_from_db()

        assert publisher.is_deleted is False
        assert publisher.deleted_at is None
        assert publisher.deleted_by is None

        # Should appear in default queryset again
        assert Publisher.objects.filter(pk=publisher.pk).count() == 1


# =============================================================================
# Task 7.7: Test audit log recording
# =============================================================================


@pytest.mark.django_db
class TestPublisherAuditLog:
    """Test Publisher audit log registration."""

    def test_publisher_registered_with_auditlog(self):
        """Test Publisher model is registered with auditlog."""
        from auditlog.registry import auditlog

        assert Publisher in auditlog.get_models()

    def test_create_logged(self):
        """Test publisher creation is logged."""
        from auditlog.models import LogEntry

        publisher = Publisher.objects.create(
            name="Audit Test",
            doi_prefix="10.6666",
        )

        log_entry = LogEntry.objects.filter(
            object_pk=str(publisher.pk),
            action=LogEntry.Action.CREATE,
        ).first()

        assert log_entry is not None

    def test_update_logged(self):
        """Test publisher update is logged."""
        from auditlog.models import LogEntry

        publisher = Publisher.objects.create(
            name="Original",
            doi_prefix="10.5656",
        )
        publisher.name = "Updated"
        publisher.save()

        log_entry = LogEntry.objects.filter(
            object_pk=str(publisher.pk),
            action=LogEntry.Action.UPDATE,
        ).first()

        assert log_entry is not None


# =============================================================================
# Test SoftDeleteManager
# =============================================================================


@pytest.mark.django_db
class TestSoftDeleteManager:
    """Test SoftDeleteManager functionality."""

    @pytest.fixture
    def setup_publishers(self):
        """Create mix of active and deleted publishers."""
        active1 = Publisher.objects.create(name="Active 1", doi_prefix="10.1001")
        active2 = Publisher.objects.create(name="Active 2", doi_prefix="10.1002")
        deleted = Publisher.objects.create(name="Deleted", doi_prefix="10.1003")
        deleted.soft_delete()
        return active1, active2, deleted

    def test_objects_excludes_deleted(self, setup_publishers):
        """Test objects manager excludes deleted records."""
        active1, active2, deleted = setup_publishers
        qs = Publisher.objects.all()

        assert active1 in qs
        assert active2 in qs
        assert deleted not in qs
        assert qs.count() == 2

    def test_all_with_deleted(self, setup_publishers):
        """Test all_with_deleted includes everything."""
        active1, active2, deleted = setup_publishers
        qs = Publisher.objects.all_with_deleted()

        assert active1 in qs
        assert active2 in qs
        assert deleted in qs
        assert qs.count() == 3

    def test_deleted_only(self, setup_publishers):
        """Test deleted_only returns only deleted records."""
        active1, active2, deleted = setup_publishers
        qs = Publisher.objects.deleted_only()

        assert active1 not in qs
        assert active2 not in qs
        assert deleted in qs
        assert qs.count() == 1


# =============================================================================
# Test publication_count property
# =============================================================================


@pytest.mark.django_db
class TestPublisherPublicationCount:
    """Test Publisher.publication_count property."""

    def test_publication_count_returns_zero_when_no_publications(self):
        """Test publication_count returns 0 when no publications exist."""
        publisher = Publisher.objects.create(
            name="No Publications",
            doi_prefix="10.7070",
        )
        assert publisher.publication_count == 0
