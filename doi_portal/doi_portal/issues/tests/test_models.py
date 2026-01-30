"""
Tests for Issue model.

Story 2.6 - Task 11: Comprehensive model tests.
"""

import pytest
from django.contrib.auth import get_user_model
from django.db import IntegrityError

from doi_portal.issues.models import Issue, IssueStatus
from doi_portal.publications.tests.factories import PublicationFactory

from .factories import IssueFactory

User = get_user_model()


# =============================================================================
# 11.1: Test Issue model creation with all fields
# =============================================================================


@pytest.mark.django_db
class TestIssueModelCreation:
    """Test Issue model creation with all fields."""

    def test_create_issue_with_required_fields(self):
        """11.1: Issue can be created with required fields."""
        publication = PublicationFactory()
        issue = Issue.objects.create(
            publication=publication,
            year=2026,
        )
        assert issue.pk is not None
        assert issue.year == 2026
        assert issue.status == IssueStatus.DRAFT

    def test_create_issue_with_all_fields(self):
        """11.1: Issue can be created with all fields."""
        issue = IssueFactory(
            volume="5",
            issue_number="2",
            year=2026,
            title="Posebno izdanje",
            status=IssueStatus.PUBLISHED,
            proceedings_title="Zbornik konferencije",
            proceedings_publisher_name="Akademija nauka",
            proceedings_publisher_place="Beograd",
        )
        assert issue.pk is not None
        assert issue.volume == "5"
        assert issue.issue_number == "2"
        assert issue.year == 2026
        assert issue.title == "Posebno izdanje"
        assert issue.status == IssueStatus.PUBLISHED
        assert issue.proceedings_title == "Zbornik konferencije"
        assert issue.proceedings_publisher_name == "Akademija nauka"
        assert issue.proceedings_publisher_place == "Beograd"

    def test_default_status_is_draft(self):
        """11.1: Default status is DRAFT (AC #1)."""
        issue = IssueFactory()
        assert issue.status == IssueStatus.DRAFT

    def test_str_representation(self):
        """11.1: __str__ returns expected format."""
        issue = IssueFactory(volume="3", issue_number="1", year=2026)
        expected = f"{issue.publication.title} - Vol. 3, No. 1 (2026)"
        assert str(issue) == expected

    def test_issue_related_name_on_publication(self):
        """11.1: related_name='issues' works on Publication FK (AC #1)."""
        publication = PublicationFactory()
        issue1 = IssueFactory(publication=publication, volume="1", issue_number="1")
        issue2 = IssueFactory(publication=publication, volume="1", issue_number="2")
        assert publication.issues.count() == 2
        assert issue1 in publication.issues.all()
        assert issue2 in publication.issues.all()

    def test_ordering(self):
        """11.1: Default ordering is -year, -volume, -issue_number."""
        publication = PublicationFactory()
        issue_old = IssueFactory(
            publication=publication, volume="1", issue_number="1", year=2025
        )
        issue_new = IssueFactory(
            publication=publication, volume="2", issue_number="1", year=2026
        )
        issues = list(Issue.objects.filter(publication=publication))
        assert issues[0] == issue_new
        assert issues[1] == issue_old

    def test_publication_protect_on_delete(self):
        """11.1: PROTECT prevents deleting publication with issues."""
        issue = IssueFactory()
        publication = issue.publication
        with pytest.raises(Exception):
            publication.delete()

    def test_verbose_names(self):
        """11.1: verbose_name and verbose_name_plural are correct."""
        assert Issue._meta.verbose_name == "Izdanje"
        assert Issue._meta.verbose_name_plural == "Izdanja"


# =============================================================================
# 11.2: Test unique constraint for (publication, volume, issue_number)
# =============================================================================


@pytest.mark.django_db
class TestIssueUniqueConstraint:
    """Test unique constraint for (publication, volume, issue_number)."""

    def test_duplicate_issue_raises_error(self):
        """11.2: Duplicate (publication, volume, issue_number) raises IntegrityError."""
        publication = PublicationFactory()
        IssueFactory(publication=publication, volume="1", issue_number="1")
        with pytest.raises(IntegrityError):
            IssueFactory(publication=publication, volume="1", issue_number="1")

    def test_same_volume_issue_different_publication_ok(self):
        """11.2: Same vol/issue in different publications is allowed."""
        pub1 = PublicationFactory()
        pub2 = PublicationFactory()
        issue1 = IssueFactory(publication=pub1, volume="1", issue_number="1")
        issue2 = IssueFactory(publication=pub2, volume="1", issue_number="1")
        assert issue1.pk != issue2.pk

    def test_soft_deleted_does_not_block_new_issue(self):
        """11.2: Soft-deleted issue does not block creating new with same vol/issue."""
        publication = PublicationFactory()
        issue = IssueFactory(publication=publication, volume="1", issue_number="1")
        issue.soft_delete()
        # Should not raise - soft-deleted excluded from constraint
        new_issue = Issue.objects.create(
            publication=publication, volume="1", issue_number="1", year=2026
        )
        assert new_issue.pk is not None


# =============================================================================
# 11.3: Test soft delete and restore
# =============================================================================


@pytest.mark.django_db
class TestIssueSoftDelete:
    """Test soft delete and restore functionality."""

    def test_soft_delete(self):
        """11.3: Soft delete sets is_deleted and deleted_at."""
        user = User.objects.create_user(
            email="deleter@test.com", password="testpass123"
        )
        issue = IssueFactory()
        issue.soft_delete(user=user)

        issue.refresh_from_db()
        assert issue.is_deleted is True
        assert issue.deleted_at is not None
        assert issue.deleted_by == user

    def test_soft_deleted_excluded_from_default_queryset(self):
        """11.3: Soft-deleted issues not in default queryset."""
        issue = IssueFactory()
        issue.soft_delete()

        assert not Issue.objects.filter(pk=issue.pk).exists()
        assert Issue.all_objects.filter(pk=issue.pk).exists()

    def test_restore(self):
        """11.3: Restore clears soft-delete fields."""
        issue = IssueFactory()
        issue.soft_delete()
        issue.restore()

        issue.refresh_from_db()
        assert issue.is_deleted is False
        assert issue.deleted_at is None
        assert issue.deleted_by is None
        assert Issue.objects.filter(pk=issue.pk).exists()


# =============================================================================
# 11.4: Test IssueStatus choices
# =============================================================================


@pytest.mark.django_db
class TestIssueStatusChoices:
    """Test IssueStatus TextChoices."""

    def test_status_choices_exist(self):
        """11.4: All status choices are defined."""
        assert IssueStatus.DRAFT == "DRAFT"
        assert IssueStatus.SCHEDULED == "SCHEDULED"
        assert IssueStatus.PUBLISHED == "PUBLISHED"
        assert IssueStatus.ARCHIVE == "ARCHIVE"

    def test_status_labels(self):
        """11.4: Status labels are in Serbian."""
        assert IssueStatus.DRAFT.label == "Nacrt"
        assert IssueStatus.SCHEDULED.label == "Zakazano"
        assert IssueStatus.PUBLISHED.label == "Objavljeno"
        assert IssueStatus.ARCHIVE.label == "Arhivirano"

    def test_all_statuses_valid(self):
        """11.4: All statuses can be assigned to Issue."""
        for status_value, _ in IssueStatus.choices:
            issue = IssueFactory(status=status_value)
            assert issue.status == status_value


# =============================================================================
# 11.5: Test article_count property (returns 0)
# =============================================================================


@pytest.mark.django_db
class TestIssueArticleCount:
    """Test article_count property."""

    def test_article_count_returns_zero(self):
        """11.5: article_count returns 0 (placeholder until Story 3.1)."""
        issue = IssueFactory()
        assert issue.article_count == 0


# =============================================================================
# 11.6: Test status_badge_class property
# =============================================================================


@pytest.mark.django_db
class TestIssueStatusBadgeClass:
    """Test status_badge_class property."""

    def test_draft_badge(self):
        """11.6: DRAFT status returns bg-secondary."""
        issue = IssueFactory(status=IssueStatus.DRAFT)
        assert issue.status_badge_class == "bg-secondary"

    def test_scheduled_badge(self):
        """11.6: SCHEDULED status returns bg-info."""
        issue = IssueFactory(status=IssueStatus.SCHEDULED)
        assert issue.status_badge_class == "bg-info"

    def test_published_badge(self):
        """11.6: PUBLISHED status returns bg-success."""
        issue = IssueFactory(status=IssueStatus.PUBLISHED)
        assert issue.status_badge_class == "bg-success"

    def test_archive_badge(self):
        """11.6: ARCHIVE status returns bg-warning."""
        issue = IssueFactory(status=IssueStatus.ARCHIVE)
        assert issue.status_badge_class == "bg-warning"


# =============================================================================
# 11.20: Test Publication.issue_count returns correct number
# =============================================================================


@pytest.mark.django_db
class TestPublicationIssueCount:
    """Test Publication.issue_count with real Issue model."""

    def test_publication_issue_count_with_issues(self):
        """11.20: Publication.issue_count returns correct count."""
        publication = PublicationFactory()
        IssueFactory(publication=publication, volume="1", issue_number="1")
        IssueFactory(publication=publication, volume="1", issue_number="2")
        assert publication.issue_count == 2

    def test_publication_issue_count_without_issues(self):
        """11.20: Publication.issue_count returns 0 with no issues."""
        publication = PublicationFactory()
        assert publication.issue_count == 0

    def test_publication_issue_count_excludes_deleted(self):
        """11.20: Publication.issue_count excludes soft-deleted issues."""
        publication = PublicationFactory()
        issue1 = IssueFactory(publication=publication, volume="1", issue_number="1")
        IssueFactory(publication=publication, volume="1", issue_number="2")
        issue1.soft_delete()
        assert publication.issue_count == 1
