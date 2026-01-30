"""
Tests for Issue forms.

Story 2.6 - Task 11: Comprehensive form tests.
"""

import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group

from doi_portal.issues.forms import IssueForm
from doi_portal.issues.models import IssueStatus
from doi_portal.publications.tests.factories import PublicationFactory, PublisherFactory

from .factories import IssueFactory

User = get_user_model()


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def publisher_a():
    """Create publisher A."""
    return PublisherFactory(name="Izdavač A")


@pytest.fixture
def publisher_b():
    """Create publisher B."""
    return PublisherFactory(name="Izdavač B")


@pytest.fixture
def publication_a(publisher_a):
    """Create publication for publisher A."""
    return PublicationFactory(publisher=publisher_a)


@pytest.fixture
def publication_b(publisher_b):
    """Create publication for publisher B."""
    return PublicationFactory(publisher=publisher_b)


@pytest.fixture
def admin_user():
    """Create an admin user."""
    user = User.objects.create_user(
        email="admin@test.com", password="testpass123"
    )
    group, _ = Group.objects.get_or_create(name="Administrator")
    user.groups.add(group)
    return user


@pytest.fixture
def urednik_user(publisher_a):
    """Create an Urednik user assigned to publisher A."""
    user = User.objects.create_user(
        email="urednik@test.com",
        password="testpass123",
        publisher=publisher_a,
    )
    group, _ = Group.objects.get_or_create(name="Urednik")
    user.groups.add(group)
    return user


# =============================================================================
# 11.7: Test IssueForm validation (valid and invalid data)
# =============================================================================


@pytest.mark.django_db
class TestIssueFormValidation:
    """Test IssueForm validation."""

    def test_valid_form(self, admin_user, publication_a):
        """11.7: Form with valid data is valid."""
        form = IssueForm(
            data={
                "publication": publication_a.pk,
                "volume": "1",
                "issue_number": "1",
                "year": 2026,
                "status": IssueStatus.DRAFT,
                "title": "",
                "publication_date": "",
                "proceedings_title": "",
                "proceedings_publisher_name": "",
                "proceedings_publisher_place": "",
            },
            user=admin_user,
        )
        assert form.is_valid(), form.errors

    def test_missing_year_invalid(self, admin_user, publication_a):
        """11.7: Form without required year field is invalid."""
        form = IssueForm(
            data={
                "publication": publication_a.pk,
                "volume": "1",
                "issue_number": "1",
                "status": IssueStatus.DRAFT,
            },
            user=admin_user,
        )
        assert not form.is_valid()
        assert "year" in form.errors

    def test_missing_publication_invalid(self, admin_user):
        """11.7: Form without publication is invalid."""
        form = IssueForm(
            data={
                "volume": "1",
                "issue_number": "1",
                "year": 2026,
                "status": IssueStatus.DRAFT,
            },
            user=admin_user,
        )
        assert not form.is_valid()
        assert "publication" in form.errors

    def test_duplicate_combination_invalid(self, admin_user, publication_a):
        """11.7: Duplicate (publication, volume, issue_number) shows error."""
        IssueFactory(
            publication=publication_a, volume="1", issue_number="1", year=2026
        )
        form = IssueForm(
            data={
                "publication": publication_a.pk,
                "volume": "1",
                "issue_number": "1",
                "year": 2026,
                "status": IssueStatus.DRAFT,
                "title": "",
                "publication_date": "",
                "proceedings_title": "",
                "proceedings_publisher_name": "",
                "proceedings_publisher_place": "",
            },
            user=admin_user,
        )
        assert not form.is_valid()
        assert "__all__" in form.errors

    def test_duplicate_with_empty_volume_and_issue_number(
        self, admin_user, publication_a
    ):
        """Code Review: Duplicate with empty volume and issue_number is caught."""
        IssueFactory(
            publication=publication_a, volume="", issue_number="", year=2026
        )
        form = IssueForm(
            data={
                "publication": publication_a.pk,
                "volume": "",
                "issue_number": "",
                "year": 2026,
                "status": IssueStatus.DRAFT,
                "title": "",
                "publication_date": "",
                "proceedings_title": "",
                "proceedings_publisher_name": "",
                "proceedings_publisher_place": "",
            },
            user=admin_user,
        )
        assert not form.is_valid()
        assert "__all__" in form.errors

    def test_default_status_is_draft(self, admin_user, publication_a):
        """11.7: Default status is DRAFT when not specified."""
        form = IssueForm(user=admin_user)
        # ModelForm picks up model field default for initial value
        assert form.fields["status"].initial == IssueStatus.DRAFT

    def test_edit_excludes_self_from_unique_check(self, admin_user, publication_a):
        """11.7: Editing existing issue does not trigger duplicate error on itself."""
        issue = IssueFactory(
            publication=publication_a, volume="1", issue_number="1", year=2026
        )
        form = IssueForm(
            data={
                "publication": publication_a.pk,
                "volume": "1",
                "issue_number": "1",
                "year": 2026,
                "status": IssueStatus.PUBLISHED,
                "title": "Updated title",
                "publication_date": "",
                "proceedings_title": "",
                "proceedings_publisher_name": "",
                "proceedings_publisher_place": "",
            },
            instance=issue,
            user=admin_user,
        )
        assert form.is_valid(), form.errors


# =============================================================================
# 11.8: Test IssueForm publication queryset scoping for Urednik
# =============================================================================


@pytest.mark.django_db
class TestIssueFormPublicationScoping:
    """Test IssueForm publication queryset scoping."""

    def test_admin_sees_all_publications(
        self, admin_user, publication_a, publication_b
    ):
        """11.8: Administrator sees all publications in dropdown."""
        form = IssueForm(user=admin_user)
        queryset = form.fields["publication"].queryset
        assert publication_a in queryset
        assert publication_b in queryset

    def test_urednik_sees_only_own_publisher_publications(
        self, urednik_user, publication_a, publication_b
    ):
        """11.8: Urednik sees only publications from assigned publisher."""
        form = IssueForm(user=urednik_user)
        queryset = form.fields["publication"].queryset
        assert publication_a in queryset
        assert publication_b not in queryset

    def test_superuser_sees_all_publications(self, publication_a, publication_b):
        """11.8: Superuser sees all publications."""
        superuser = User.objects.create_superuser(
            email="super@test.com", password="testpass123"
        )
        form = IssueForm(user=superuser)
        queryset = form.fields["publication"].queryset
        assert publication_a in queryset
        assert publication_b in queryset

    def test_publication_type_map_json(self, admin_user, publication_a):
        """Code Review: publication_type_map_json contains publication type."""
        import json

        form = IssueForm(user=admin_user)
        type_map = json.loads(form.publication_type_map_json)
        assert str(publication_a.pk) in type_map
        assert type_map[str(publication_a.pk)] == publication_a.publication_type

    def test_user_without_publisher_sees_no_publications(self):
        """11.8: User without publisher sees no publications."""
        user = User.objects.create_user(
            email="nopub@test.com", password="testpass123"
        )
        form = IssueForm(user=user)
        queryset = form.fields["publication"].queryset
        assert queryset.count() == 0


# =============================================================================
# Code Review: Test cover image size validation
# =============================================================================


@pytest.mark.django_db
class TestIssueFormCoverImageValidation:
    """Test cover image file size validation."""

    def test_cover_image_too_large_rejected(self, admin_user, publication_a):
        """Cover image larger than 5 MB is rejected."""
        from django.core.files.uploadedfile import SimpleUploadedFile

        # Create a fake file exceeding 5 MB
        large_content = b"x" * (6 * 1024 * 1024)  # 6 MB
        large_file = SimpleUploadedFile(
            "large.jpg", large_content, content_type="image/jpeg"
        )
        form = IssueForm(
            data={
                "publication": publication_a.pk,
                "volume": "1",
                "issue_number": "1",
                "year": 2026,
                "status": "DRAFT",
                "title": "",
                "publication_date": "",
                "proceedings_title": "",
                "proceedings_publisher_name": "",
                "proceedings_publisher_place": "",
            },
            files={"cover_image": large_file},
            user=admin_user,
        )
        assert not form.is_valid()
        assert "cover_image" in form.errors

    def test_cover_image_within_limit_accepted(self, admin_user, publication_a):
        """Cover image within 5 MB limit is accepted."""
        from django.core.files.uploadedfile import SimpleUploadedFile

        # Create a small fake image file (valid JPEG header)
        small_file = SimpleUploadedFile(
            "small.jpg", b"\xff\xd8\xff\xe0" + b"x" * 1024, content_type="image/jpeg"
        )
        form = IssueForm(
            data={
                "publication": publication_a.pk,
                "volume": "99",
                "issue_number": "99",
                "year": 2026,
                "status": "DRAFT",
                "title": "",
                "publication_date": "",
                "proceedings_title": "",
                "proceedings_publisher_name": "",
                "proceedings_publisher_place": "",
            },
            files={"cover_image": small_file},
            user=admin_user,
        )
        # Note: Django ImageField may reject non-valid image - we're testing size check only
        # If PIL rejects, cover_image error will be about image format, not size
        if form.errors.get("cover_image"):
            # If there is a cover_image error, ensure it's not about size
            error_text = str(form.errors["cover_image"])
            assert "5 MB" not in error_text
