"""
Tests for Article model.

Story 3.1 - Task 7: Comprehensive model tests.
"""

import pytest
from django.contrib.auth import get_user_model
from django.db import IntegrityError

from doi_portal.articles.models import (
    Article,
    ArticleContentType,
    ArticleStatus,
    LicenseAppliesTo,
)
from doi_portal.issues.tests.factories import IssueFactory

from .factories import ArticleFactory

User = get_user_model()


# =============================================================================
# 7.2: Test Article model creation with all fields
# =============================================================================


@pytest.mark.django_db
class TestArticleModelCreation:
    """Test Article model creation with all fields."""

    def test_create_article_with_required_fields(self):
        """7.2: Article can be created with required fields."""
        issue = IssueFactory()
        user = User.objects.create_user(
            email="creator@test.com", password="testpass123"
        )
        article = Article.objects.create(
            issue=issue,
            title="Test članak",
            doi_suffix="article.2026.001",
            created_by=user,
        )
        assert article.pk is not None
        assert article.title == "Test članak"
        assert article.status == ArticleStatus.DRAFT

    def test_create_article_with_all_fields(self):
        """7.2: Article can be created with all fields."""
        article = ArticleFactory(
            title="Kompletni članak",
            subtitle="Sa svim poljima",
            abstract="Ovo je apstrakt.",
            keywords=["python", "django"],
            doi_suffix="complete.001",
            first_page="1",
            last_page="15",
            article_number="e001",
            language="en",
            publication_type=ArticleContentType.ABSTRACT_ONLY,
            license_url="https://creativecommons.org/licenses/by/4.0/",
            license_applies_to=LicenseAppliesTo.VOR,
            free_to_read=True,
        )
        assert article.pk is not None
        assert article.title == "Kompletni članak"
        assert article.subtitle == "Sa svim poljima"
        assert article.abstract == "Ovo je apstrakt."
        assert article.keywords == ["python", "django"]
        assert article.first_page == "1"
        assert article.last_page == "15"
        assert article.article_number == "e001"
        assert article.language == "en"
        assert article.publication_type == ArticleContentType.ABSTRACT_ONLY
        assert article.license_url == "https://creativecommons.org/licenses/by/4.0/"
        assert article.license_applies_to == LicenseAppliesTo.VOR
        assert article.free_to_read is True

    def test_default_status_is_draft(self):
        """7.2: Default status is DRAFT (AC #1)."""
        article = ArticleFactory()
        assert article.status == ArticleStatus.DRAFT

    def test_default_language_is_sr(self):
        """7.2: Default language is 'sr'."""
        article = ArticleFactory()
        assert article.language == "sr"

    def test_default_publication_type_is_full_text(self):
        """7.2: Default publication_type is FULL_TEXT."""
        article = ArticleFactory()
        assert article.publication_type == ArticleContentType.FULL_TEXT

    def test_default_free_to_read_is_false(self):
        """7.2: Default free_to_read is False."""
        article = ArticleFactory()
        assert article.free_to_read is False

    def test_str_representation(self):
        """7.2: __str__ returns title."""
        article = ArticleFactory(title="Moj članak")
        assert str(article) == "Moj članak"

    def test_issue_protect_on_delete(self):
        """7.2: PROTECT prevents deleting issue with articles."""
        article = ArticleFactory()
        issue = article.issue
        with pytest.raises(Exception):
            issue.delete()

    def test_created_by_set_null_on_delete(self):
        """7.2: created_by is SET_NULL when user deleted."""
        user = User.objects.create_user(
            email="willdelete@test.com", password="testpass123"
        )
        article = ArticleFactory(created_by=user)
        user.delete()
        article.refresh_from_db()
        assert article.created_by is None

    def test_verbose_names(self):
        """7.2: verbose_name and verbose_name_plural are correct."""
        assert Article._meta.verbose_name == "Članak"
        assert Article._meta.verbose_name_plural == "Članci"

    def test_ordering_by_created_at_desc(self):
        """7.2: Default ordering is -created_at."""
        issue = IssueFactory()
        article1 = ArticleFactory(issue=issue, doi_suffix="a.001")
        article2 = ArticleFactory(issue=issue, doi_suffix="a.002")
        articles = list(Article.objects.filter(issue=issue))
        assert articles[0] == article2
        assert articles[1] == article1

    def test_keywords_default_empty_list(self):
        """7.2: keywords default is empty list."""
        issue = IssueFactory()
        user = User.objects.create_user(
            email="kw@test.com", password="testpass123"
        )
        article = Article.objects.create(
            issue=issue,
            title="No keywords",
            doi_suffix="nokw.001",
            created_by=user,
        )
        assert article.keywords == []

    def test_issue_related_name(self):
        """7.2: related_name='articles' works on Issue FK."""
        issue = IssueFactory()
        article1 = ArticleFactory(issue=issue, doi_suffix="r.001")
        article2 = ArticleFactory(issue=issue, doi_suffix="r.002")
        assert issue.articles.count() == 2
        assert article1 in issue.articles.all()
        assert article2 in issue.articles.all()


# =============================================================================
# 7.2: Test unique constraint (issue, doi_suffix)
# =============================================================================


@pytest.mark.django_db
class TestArticleUniqueConstraint:
    """Test unique constraint for (issue, doi_suffix)."""

    def test_duplicate_doi_suffix_same_issue_raises_error(self):
        """7.2: Duplicate (issue, doi_suffix) raises IntegrityError."""
        issue = IssueFactory()
        ArticleFactory(issue=issue, doi_suffix="dup.001")
        with pytest.raises(IntegrityError):
            ArticleFactory(issue=issue, doi_suffix="dup.001")

    def test_same_doi_suffix_different_issue_ok(self):
        """7.2: Same doi_suffix in different issues is allowed."""
        issue1 = IssueFactory()
        issue2 = IssueFactory()
        article1 = ArticleFactory(issue=issue1, doi_suffix="same.001")
        article2 = ArticleFactory(issue=issue2, doi_suffix="same.001")
        assert article1.pk != article2.pk

    def test_soft_deleted_does_not_block_new_article(self):
        """7.2: Soft-deleted article does not block creating new with same doi_suffix."""
        issue = IssueFactory()
        article = ArticleFactory(issue=issue, doi_suffix="soft.001")
        article.soft_delete()
        # Should not raise - soft-deleted excluded from constraint
        new_article = Article.objects.create(
            issue=issue,
            title="New article",
            doi_suffix="soft.001",
        )
        assert new_article.pk is not None


# =============================================================================
# 7.2: Test soft delete and restore
# =============================================================================


@pytest.mark.django_db
class TestArticleSoftDelete:
    """Test soft delete and restore functionality."""

    def test_soft_delete(self):
        """7.2: Soft delete sets is_deleted, deleted_at, deleted_by."""
        user = User.objects.create_user(
            email="deleter@test.com", password="testpass123"
        )
        article = ArticleFactory()
        article.soft_delete(user=user)

        article.refresh_from_db()
        assert article.is_deleted is True
        assert article.deleted_at is not None
        assert article.deleted_by == user

    def test_soft_delete_without_user(self):
        """7.2: Soft delete works without user."""
        article = ArticleFactory()
        article.soft_delete()

        article.refresh_from_db()
        assert article.is_deleted is True
        assert article.deleted_at is not None
        assert article.deleted_by is None

    def test_soft_deleted_excluded_from_default_queryset(self):
        """7.2: Soft-deleted articles not in default queryset."""
        article = ArticleFactory()
        article.soft_delete()

        assert not Article.objects.filter(pk=article.pk).exists()
        assert Article.all_objects.filter(pk=article.pk).exists()

    def test_restore(self):
        """7.2: Restore clears soft-delete fields."""
        article = ArticleFactory()
        article.soft_delete()
        article.restore()

        article.refresh_from_db()
        assert article.is_deleted is False
        assert article.deleted_at is None
        assert article.deleted_by is None
        assert Article.objects.filter(pk=article.pk).exists()


# =============================================================================
# 7.2: Test ArticleStatus choices
# =============================================================================


@pytest.mark.django_db
class TestArticleStatusChoices:
    """Test ArticleStatus TextChoices."""

    def test_status_choices_exist(self):
        """7.2: All status choices are defined."""
        assert ArticleStatus.DRAFT == "DRAFT"
        assert ArticleStatus.REVIEW == "REVIEW"
        assert ArticleStatus.READY == "READY"
        assert ArticleStatus.PUBLISHED == "PUBLISHED"
        assert ArticleStatus.WITHDRAWN == "WITHDRAWN"

    def test_status_labels(self):
        """7.2: Status labels are in Serbian."""
        assert ArticleStatus.DRAFT.label == "Nacrt"
        assert ArticleStatus.REVIEW.label == "Na pregledu"
        assert ArticleStatus.READY.label == "Spremno za objavu"
        assert ArticleStatus.PUBLISHED.label == "Objavljeno"
        assert ArticleStatus.WITHDRAWN.label == "Povučeno"

    def test_all_statuses_valid(self):
        """7.2: All statuses can be assigned to Article."""
        for status_value, _ in ArticleStatus.choices:
            article = ArticleFactory(status=status_value)
            assert article.status == status_value


# =============================================================================
# 7.2: Test ArticleContentType choices
# =============================================================================


@pytest.mark.django_db
class TestArticleContentTypeChoices:
    """Test ArticleContentType TextChoices."""

    def test_content_type_choices_exist(self):
        """7.2: All content type choices are defined."""
        assert ArticleContentType.FULL_TEXT == "full_text"
        assert ArticleContentType.ABSTRACT_ONLY == "abstract_only"
        assert ArticleContentType.BIBLIOGRAPHIC_RECORD == "bibliographic_record"

    def test_content_type_labels(self):
        """7.2: Content type labels are in Serbian."""
        assert ArticleContentType.FULL_TEXT.label == "Puni tekst"
        assert ArticleContentType.ABSTRACT_ONLY.label == "Samo apstrakt"
        assert ArticleContentType.BIBLIOGRAPHIC_RECORD.label == "Bibliografski zapis"


# =============================================================================
# 7.2: Test LicenseAppliesTo choices
# =============================================================================


@pytest.mark.django_db
class TestLicenseAppliesToChoices:
    """Test LicenseAppliesTo TextChoices."""

    def test_license_applies_to_choices_exist(self):
        """7.2: All license_applies_to choices are defined."""
        assert LicenseAppliesTo.VOR == "vor"
        assert LicenseAppliesTo.AM == "am"
        assert LicenseAppliesTo.TDM == "tdm"

    def test_license_applies_to_labels(self):
        """7.2: License applies to labels are in Serbian."""
        assert LicenseAppliesTo.VOR.label == "Verzija zapisa (VoR)"
        assert LicenseAppliesTo.AM.label == "Prihvaćeni rukopis (AM)"
        assert LicenseAppliesTo.TDM.label == "Rudarenje teksta (TDM)"


# =============================================================================
# 7.2: Test status_badge_class property
# =============================================================================


@pytest.mark.django_db
class TestArticleStatusBadgeClass:
    """Test status_badge_class property."""

    def test_draft_badge(self):
        """7.2: DRAFT status returns bg-secondary."""
        article = ArticleFactory(status=ArticleStatus.DRAFT)
        assert article.status_badge_class == "bg-secondary"

    def test_review_badge(self):
        """7.2: REVIEW status returns bg-info."""
        article = ArticleFactory(status=ArticleStatus.REVIEW)
        assert article.status_badge_class == "bg-info"

    def test_ready_badge(self):
        """7.2: READY status returns bg-primary."""
        article = ArticleFactory(status=ArticleStatus.READY)
        assert article.status_badge_class == "bg-primary"

    def test_published_badge(self):
        """7.2: PUBLISHED status returns bg-success."""
        article = ArticleFactory(status=ArticleStatus.PUBLISHED)
        assert article.status_badge_class == "bg-success"

    def test_withdrawn_badge(self):
        """7.2: WITHDRAWN status returns bg-danger."""
        article = ArticleFactory(status=ArticleStatus.WITHDRAWN)
        assert article.status_badge_class == "bg-danger"


# =============================================================================
# 7.2: Test Issue.article_count property (AC #6)
# =============================================================================


@pytest.mark.django_db
class TestIssueArticleCountWithArticles:
    """Test Issue.article_count returns correct count with real articles."""

    def test_article_count_with_articles(self):
        """7.2: Issue.article_count returns correct count (AC #6)."""
        issue = IssueFactory()
        ArticleFactory(issue=issue, doi_suffix="cnt.001")
        ArticleFactory(issue=issue, doi_suffix="cnt.002")
        assert issue.article_count == 2

    def test_article_count_without_articles(self):
        """7.2: Issue.article_count returns 0 with no articles."""
        issue = IssueFactory()
        assert issue.article_count == 0

    def test_article_count_excludes_deleted(self):
        """7.2: Issue.article_count excludes soft-deleted articles."""
        issue = IssueFactory()
        article1 = ArticleFactory(issue=issue, doi_suffix="del.001")
        ArticleFactory(issue=issue, doi_suffix="del.002")
        article1.soft_delete()
        assert issue.article_count == 1
