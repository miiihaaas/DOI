"""
Tests for Editorial Review Process.

Story 3.6 - Task 14: Comprehensive tests covering AC #1-#8.
Service tests, view tests, permission tests, template tests, integration tests.
"""

import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.test import Client
from django.urls import reverse
from django.utils import timezone

from doi_portal.articles.models import Article, ArticleStatus, PdfStatus
from doi_portal.articles.services import (
    InvalidStatusTransition,
    approve_article,
    return_article_for_revision,
)
from doi_portal.issues.tests.factories import IssueFactory
from doi_portal.publications.tests.factories import (
    PublicationFactory,
    PublisherFactory,
)

from .factories import ArticleFactory, AuthorFactory

User = get_user_model()


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def client():
    """Create a test client."""
    return Client()


@pytest.fixture
def publisher_a():
    """Create publisher A."""
    return PublisherFactory(name="Izdavač A Review")


@pytest.fixture
def publisher_b():
    """Create publisher B."""
    return PublisherFactory(name="Izdavač B Review")


@pytest.fixture
def publication_a(publisher_a):
    """Create publication for publisher A."""
    return PublicationFactory(publisher=publisher_a)


@pytest.fixture
def publication_b(publisher_b):
    """Create publication for publisher B."""
    return PublicationFactory(publisher=publisher_b)


@pytest.fixture
def issue_a(publication_a):
    """Create issue for publication A."""
    return IssueFactory(publication=publication_a, volume="1", issue_number="1")


@pytest.fixture
def issue_b(publication_b):
    """Create issue for publication B."""
    return IssueFactory(publication=publication_b, volume="1", issue_number="1")


@pytest.fixture
def admin_user():
    """Create an admin user."""
    user = User.objects.create_user(
        email="admin-review@test.com", password="testpass123"
    )
    group, _ = Group.objects.get_or_create(name="Administrator")
    user.groups.add(group)
    return user


@pytest.fixture
def urednik_user(publisher_a):
    """Create an Urednik user assigned to publisher A."""
    user = User.objects.create_user(
        email="ured-review@test.com",
        password="testpass123",
        publisher=publisher_a,
    )
    group, _ = Group.objects.get_or_create(name="Urednik")
    user.groups.add(group)
    return user


@pytest.fixture
def bibliotekar_user(publisher_a):
    """Create a Bibliotekar user assigned to publisher A."""
    user = User.objects.create_user(
        email="bib-review@test.com",
        password="testpass123",
        publisher=publisher_a,
    )
    group, _ = Group.objects.get_or_create(name="Bibliotekar")
    user.groups.add(group)
    return user


@pytest.fixture
def other_publisher_user(publisher_b):
    """Create a Bibliotekar user assigned to publisher B."""
    user = User.objects.create_user(
        email="other-bib-review@test.com",
        password="testpass123",
        publisher=publisher_b,
    )
    group, _ = Group.objects.get_or_create(name="Bibliotekar")
    user.groups.add(group)
    return user


@pytest.fixture
def regular_user():
    """Create a regular user without roles."""
    return User.objects.create_user(
        email="regular-review@test.com", password="testpass123"
    )


@pytest.fixture
def superuser():
    """Create a superuser."""
    return User.objects.create_superuser(
        email="super-review@test.com", password="testpass123"
    )


@pytest.fixture
def draft_article(issue_a, bibliotekar_user):
    """Create a DRAFT article."""
    article = ArticleFactory(
        issue=issue_a,
        title="Članak u nacrtu",
        abstract="Apstrakt.",
        status=ArticleStatus.DRAFT,
        pdf_status=PdfStatus.CLEAN,
        pdf_file="articles/pdfs/test.pdf",
        created_by=bibliotekar_user,
    )
    AuthorFactory(article=article, given_name="Petar", surname="Petrović", order=1)
    return article


@pytest.fixture
def review_article(issue_a, bibliotekar_user):
    """Create a REVIEW status article."""
    article = ArticleFactory(
        issue=issue_a,
        title="Članak na pregledu",
        abstract="Apstrakt za pregled.",
        status=ArticleStatus.REVIEW,
        pdf_status=PdfStatus.CLEAN,
        pdf_file="articles/pdfs/test.pdf",
        created_by=bibliotekar_user,
        submitted_by=bibliotekar_user,
        submitted_at=timezone.now(),
    )
    AuthorFactory(article=article, given_name="Ivan", surname="Ivanović", order=1)
    return article


@pytest.fixture
def review_article_with_comment(issue_a, bibliotekar_user):
    """Create a REVIEW article with existing revision comment from previous return."""
    article = ArticleFactory(
        issue=issue_a,
        title="Članak sa komentarom",
        abstract="Apstrakt.",
        status=ArticleStatus.REVIEW,
        pdf_status=PdfStatus.CLEAN,
        pdf_file="articles/pdfs/test.pdf",
        created_by=bibliotekar_user,
        submitted_by=bibliotekar_user,
        submitted_at=timezone.now(),
        revision_comment="Stari komentar iz prethodnog vracanja",
    )
    AuthorFactory(article=article, given_name="Marko", surname="Marković", order=1)
    return article


@pytest.fixture
def review_article_b(issue_b, other_publisher_user):
    """Create a REVIEW article for publisher B."""
    article = ArticleFactory(
        issue=issue_b,
        title="Članak izdavača B",
        abstract="Apstrakt.",
        status=ArticleStatus.REVIEW,
        pdf_status=PdfStatus.CLEAN,
        pdf_file="articles/pdfs/test.pdf",
        created_by=other_publisher_user,
    )
    AuthorFactory(article=article)
    return article


@pytest.fixture
def ready_article(issue_a, bibliotekar_user, urednik_user):
    """Create a READY status article."""
    article = ArticleFactory(
        issue=issue_a,
        title="Članak spreman za objavu",
        abstract="Apstrakt.",
        status=ArticleStatus.READY,
        pdf_status=PdfStatus.CLEAN,
        pdf_file="articles/pdfs/test.pdf",
        created_by=bibliotekar_user,
        reviewed_by=urednik_user,
        reviewed_at=timezone.now(),
    )
    AuthorFactory(article=article)
    return article


@pytest.fixture
def returned_draft_article(issue_a, bibliotekar_user, urednik_user):
    """Create a DRAFT article that was returned from review with a revision comment."""
    article = ArticleFactory(
        issue=issue_a,
        title="Vraćeni članak",
        abstract="Apstrakt.",
        status=ArticleStatus.DRAFT,
        pdf_status=PdfStatus.CLEAN,
        pdf_file="articles/pdfs/test.pdf",
        created_by=bibliotekar_user,
        revision_comment="Dodajte reference.",
        returned_by=urednik_user,
        returned_at=timezone.now(),
    )
    AuthorFactory(article=article, given_name="Ana", surname="Anić", order=1)
    return article


# =============================================================================
# 14.1-14.2: Service tests for approve_article
# =============================================================================


@pytest.mark.django_db
class TestApproveArticleService:
    """Tests for approve_article service function."""

    def test_approve_valid_review_article(self, review_article, urednik_user):
        """14.1: Valid REVIEW article transitions to READY (AC #3)."""
        result = approve_article(review_article, urednik_user)
        assert result.status == ArticleStatus.READY
        assert result.reviewed_by == urednik_user
        assert result.reviewed_at is not None

    def test_approve_persists_to_database(self, review_article, urednik_user):
        """14.1: Approve persists to database."""
        approve_article(review_article, urednik_user)
        review_article.refresh_from_db()
        assert review_article.status == ArticleStatus.READY
        assert review_article.reviewed_by == urednik_user

    def test_approve_rejects_draft(self, draft_article, urednik_user):
        """14.2: DRAFT article raises InvalidStatusTransition (AC #8)."""
        with pytest.raises(InvalidStatusTransition, match="pregledu"):
            approve_article(draft_article, urednik_user)

    def test_approve_rejects_ready(self, ready_article, urednik_user):
        """14.2: READY article raises InvalidStatusTransition (AC #8)."""
        with pytest.raises(InvalidStatusTransition, match="pregledu"):
            approve_article(ready_article, urednik_user)

    def test_approve_rejects_published(self, issue_a, urednik_user):
        """14.2: PUBLISHED article raises InvalidStatusTransition (AC #8)."""
        article = ArticleFactory(issue=issue_a, status=ArticleStatus.PUBLISHED)
        with pytest.raises(InvalidStatusTransition):
            approve_article(article, urednik_user)

    def test_approve_clears_revision_comment(
        self, review_article_with_comment, urednik_user
    ):
        """14.1: Approve clears previous revision comment (AC #3)."""
        assert review_article_with_comment.revision_comment != ""
        result = approve_article(review_article_with_comment, urednik_user)
        assert result.revision_comment == ""


# =============================================================================
# 14.3-14.6: Service tests for return_article_for_revision
# =============================================================================


@pytest.mark.django_db
class TestReturnArticleForRevisionService:
    """Tests for return_article_for_revision service function."""

    def test_return_valid_review_article(self, review_article, urednik_user):
        """14.3: Valid REVIEW article with comment returns to DRAFT (AC #4)."""
        result = return_article_for_revision(
            review_article, urednik_user, "Dodaj apstrakt"
        )
        assert result.status == ArticleStatus.DRAFT
        assert result.revision_comment == "Dodaj apstrakt"
        assert result.returned_by == urednik_user
        assert result.returned_at is not None

    def test_return_persists_to_database(self, review_article, urednik_user):
        """14.3: Return persists to database."""
        return_article_for_revision(
            review_article, urednik_user, "Ispraviti greške"
        )
        review_article.refresh_from_db()
        assert review_article.status == ArticleStatus.DRAFT
        assert review_article.revision_comment == "Ispraviti greške"

    def test_return_rejects_draft(self, draft_article, urednik_user):
        """14.4: DRAFT article raises InvalidStatusTransition (AC #8)."""
        with pytest.raises(InvalidStatusTransition, match="pregledu"):
            return_article_for_revision(draft_article, urednik_user, "Komentar")

    def test_return_rejects_ready(self, ready_article, urednik_user):
        """14.4: READY article raises InvalidStatusTransition (AC #8)."""
        with pytest.raises(InvalidStatusTransition, match="pregledu"):
            return_article_for_revision(ready_article, urednik_user, "Komentar")

    def test_return_rejects_empty_comment(self, review_article, urednik_user):
        """14.5: Empty comment raises InvalidStatusTransition (AC #4)."""
        with pytest.raises(InvalidStatusTransition, match="Komentar"):
            return_article_for_revision(review_article, urednik_user, "")

    def test_return_rejects_whitespace_comment(self, review_article, urednik_user):
        """14.5: Whitespace-only comment raises InvalidStatusTransition."""
        with pytest.raises(InvalidStatusTransition, match="Komentar"):
            return_article_for_revision(review_article, urednik_user, "   ")

    def test_return_rejects_none_comment(self, review_article, urednik_user):
        """14.5: None comment raises InvalidStatusTransition."""
        with pytest.raises(InvalidStatusTransition, match="Komentar"):
            return_article_for_revision(review_article, urednik_user, None)

    def test_return_resets_submit_tracking(self, review_article, urednik_user):
        """14.6: Return resets submitted_by and submitted_at (AC #4)."""
        assert review_article.submitted_by is not None
        assert review_article.submitted_at is not None
        result = return_article_for_revision(
            review_article, urednik_user, "Ispraviti"
        )
        assert result.submitted_by is None
        assert result.submitted_at is None

    def test_return_strips_comment(self, review_article, urednik_user):
        """14.3: Return strips leading/trailing whitespace from comment."""
        result = return_article_for_revision(
            review_article, urednik_user, "  Dodaj reference  "
        )
        assert result.revision_comment == "Dodaj reference"


# =============================================================================
# 14.7-14.8: View tests for article_approve_check
# =============================================================================


@pytest.mark.django_db
class TestArticleApproveCheckView:
    """Tests for article_approve_check HTMX GET endpoint."""

    def test_approve_check_valid(self, client, urednik_user, review_article):
        """14.7: Approve check for REVIEW article returns modal (AC #2, #3)."""
        client.force_login(urednik_user)
        url = reverse(
            "articles:article-approve-check",
            kwargs={"pk": review_article.pk},
        )
        response = client.get(url)
        assert response.status_code == 200
        content = response.content.decode()
        assert "Potvrda odobrenja" in content
        assert "Odobri" in content

    def test_approve_check_non_review_shows_error(
        self, client, urednik_user, draft_article
    ):
        """14.7: Approve check for non-REVIEW article shows error."""
        client.force_login(urednik_user)
        url = reverse(
            "articles:article-approve-check",
            kwargs={"pk": draft_article.pk},
        )
        response = client.get(url)
        assert response.status_code == 200
        content = response.content.decode()
        assert "Nije moguće odobriti" in content

    def test_approve_check_rejects_bibliotekar(
        self, client, bibliotekar_user, review_article
    ):
        """14.8: Bibliotekar cannot access approve check (AC #7)."""
        client.force_login(bibliotekar_user)
        url = reverse(
            "articles:article-approve-check",
            kwargs={"pk": review_article.pk},
        )
        response = client.get(url)
        assert response.status_code == 403

    def test_approve_check_requires_login(self, client, review_article):
        """Approve check requires authentication."""
        url = reverse(
            "articles:article-approve-check",
            kwargs={"pk": review_article.pk},
        )
        response = client.get(url)
        assert response.status_code == 302
        assert "login" in response.url


# =============================================================================
# 14.9-14.10: View tests for article_approve
# =============================================================================


@pytest.mark.django_db
class TestArticleApproveView:
    """Tests for article_approve POST endpoint."""

    def test_approve_success(self, client, urednik_user, review_article):
        """14.9: Successful approve redirects with success message (AC #3)."""
        client.force_login(urednik_user)
        url = reverse(
            "articles:article-approve",
            kwargs={"pk": review_article.pk},
        )
        response = client.post(url)
        assert response.status_code == 302
        review_article.refresh_from_db()
        assert review_article.status == ArticleStatus.READY
        assert review_article.reviewed_by == urednik_user

    def test_approve_success_message(self, client, urednik_user, review_article):
        """14.9: Successful approve shows toast message (AC #3)."""
        client.force_login(urednik_user)
        url = reverse(
            "articles:article-approve",
            kwargs={"pk": review_article.pk},
        )
        response = client.post(url, follow=True)
        messages_list = list(response.context["messages"])
        assert len(messages_list) == 1
        assert "Članak odobren" in str(messages_list[0])

    def test_approve_non_review_shows_error(
        self, client, urednik_user, draft_article
    ):
        """14.10: Approve for non-REVIEW article shows error message (AC #8)."""
        client.force_login(urednik_user)
        url = reverse(
            "articles:article-approve",
            kwargs={"pk": draft_article.pk},
        )
        response = client.post(url, follow=True)
        messages_list = list(response.context["messages"])
        assert any("pregledu" in str(m) for m in messages_list)
        draft_article.refresh_from_db()
        assert draft_article.status == ArticleStatus.DRAFT  # Unchanged

    def test_approve_rejects_get(self, client, urednik_user, review_article):
        """Approve endpoint rejects GET requests."""
        client.force_login(urednik_user)
        url = reverse(
            "articles:article-approve",
            kwargs={"pk": review_article.pk},
        )
        response = client.get(url)
        assert response.status_code == 405

    def test_approve_rejects_bibliotekar(
        self, client, bibliotekar_user, review_article
    ):
        """14.15: Bibliotekar cannot approve (AC #7)."""
        client.force_login(bibliotekar_user)
        url = reverse(
            "articles:article-approve",
            kwargs={"pk": review_article.pk},
        )
        response = client.post(url)
        assert response.status_code == 403


# =============================================================================
# 14.11: View tests for article_return_check
# =============================================================================


@pytest.mark.django_db
class TestArticleReturnCheckView:
    """Tests for article_return_check HTMX GET endpoint."""

    def test_return_check_valid(self, client, urednik_user, review_article):
        """14.11: Return check for REVIEW article returns modal with textarea (AC #2, #4)."""
        client.force_login(urednik_user)
        url = reverse(
            "articles:article-return-check",
            kwargs={"pk": review_article.pk},
        )
        response = client.get(url)
        assert response.status_code == 200
        content = response.content.decode()
        assert "Vrati na doradu" in content
        assert "revision_comment" in content

    def test_return_check_non_review_shows_error(
        self, client, urednik_user, draft_article
    ):
        """14.11: Return check for non-REVIEW article shows error."""
        client.force_login(urednik_user)
        url = reverse(
            "articles:article-return-check",
            kwargs={"pk": draft_article.pk},
        )
        response = client.get(url)
        assert response.status_code == 200
        content = response.content.decode()
        assert "Nije moguće vratiti" in content

    def test_return_check_rejects_bibliotekar(
        self, client, bibliotekar_user, review_article
    ):
        """14.11: Bibliotekar cannot access return check (AC #7)."""
        client.force_login(bibliotekar_user)
        url = reverse(
            "articles:article-return-check",
            kwargs={"pk": review_article.pk},
        )
        response = client.get(url)
        assert response.status_code == 403


# =============================================================================
# 14.12-14.13: View tests for article_return_for_revision
# =============================================================================


@pytest.mark.django_db
class TestArticleReturnForRevisionView:
    """Tests for article_return_for_revision POST endpoint."""

    def test_return_success(self, client, urednik_user, review_article):
        """14.12: Successful return with comment redirects (AC #4)."""
        client.force_login(urednik_user)
        url = reverse(
            "articles:article-return",
            kwargs={"pk": review_article.pk},
        )
        response = client.post(url, {"revision_comment": "Dodaj reference"})
        assert response.status_code == 302
        review_article.refresh_from_db()
        assert review_article.status == ArticleStatus.DRAFT
        assert review_article.revision_comment == "Dodaj reference"

    def test_return_success_message(self, client, urednik_user, review_article):
        """14.12: Successful return shows toast message (AC #4)."""
        client.force_login(urednik_user)
        url = reverse(
            "articles:article-return",
            kwargs={"pk": review_article.pk},
        )
        response = client.post(
            url, {"revision_comment": "Ispraviti"}, follow=True
        )
        messages_list = list(response.context["messages"])
        assert len(messages_list) == 1
        assert "Članak vraćen na doradu" in str(messages_list[0])

    def test_return_without_comment_fails(
        self, client, urednik_user, review_article
    ):
        """14.13: Return without comment shows error (AC #4)."""
        client.force_login(urednik_user)
        url = reverse(
            "articles:article-return",
            kwargs={"pk": review_article.pk},
        )
        response = client.post(url, {"revision_comment": ""})
        assert response.status_code == 302  # Redirects with error message
        review_article.refresh_from_db()
        assert review_article.status == ArticleStatus.REVIEW  # Unchanged

    def test_return_without_comment_error_message(
        self, client, urednik_user, review_article
    ):
        """14.13: Return without comment shows appropriate error message."""
        client.force_login(urednik_user)
        url = reverse(
            "articles:article-return",
            kwargs={"pk": review_article.pk},
        )
        response = client.post(
            url, {"revision_comment": ""}, follow=True
        )
        messages_list = list(response.context["messages"])
        assert any("Komentar" in str(m) for m in messages_list)

    def test_return_rejects_get(self, client, urednik_user, review_article):
        """Return endpoint rejects GET requests."""
        client.force_login(urednik_user)
        url = reverse(
            "articles:article-return",
            kwargs={"pk": review_article.pk},
        )
        response = client.get(url)
        assert response.status_code == 405

    def test_return_rejects_bibliotekar(
        self, client, bibliotekar_user, review_article
    ):
        """14.15: Bibliotekar cannot return for revision (AC #7)."""
        client.force_login(bibliotekar_user)
        url = reverse(
            "articles:article-return",
            kwargs={"pk": review_article.pk},
        )
        response = client.post(url, {"revision_comment": "Komentar"})
        assert response.status_code == 403


# =============================================================================
# 14.14-14.16: Permission tests
# =============================================================================


@pytest.mark.django_db
class TestReviewPermissions:
    """Permission-specific tests for review endpoints."""

    def test_publisher_scoping_approve_check(
        self, client, urednik_user, review_article_b
    ):
        """14.14: Urednik cannot access approve check for other publisher's article."""
        client.force_login(urednik_user)
        url = reverse(
            "articles:article-approve-check",
            kwargs={"pk": review_article_b.pk},
        )
        response = client.get(url)
        assert response.status_code == 403

    def test_publisher_scoping_approve(
        self, client, urednik_user, review_article_b
    ):
        """14.14: Urednik cannot approve other publisher's article."""
        client.force_login(urednik_user)
        url = reverse(
            "articles:article-approve",
            kwargs={"pk": review_article_b.pk},
        )
        response = client.post(url)
        assert response.status_code == 403

    def test_publisher_scoping_return_check(
        self, client, urednik_user, review_article_b
    ):
        """14.14: Urednik cannot access return check for other publisher's article."""
        client.force_login(urednik_user)
        url = reverse(
            "articles:article-return-check",
            kwargs={"pk": review_article_b.pk},
        )
        response = client.get(url)
        assert response.status_code == 403

    def test_publisher_scoping_return(
        self, client, urednik_user, review_article_b
    ):
        """14.14: Urednik cannot return other publisher's article."""
        client.force_login(urednik_user)
        url = reverse(
            "articles:article-return",
            kwargs={"pk": review_article_b.pk},
        )
        response = client.post(url, {"revision_comment": "Komentar"})
        assert response.status_code == 403

    def test_bibliotekar_cannot_approve(
        self, client, bibliotekar_user, review_article
    ):
        """14.15: Bibliotekar ne moze approve (AC #7)."""
        client.force_login(bibliotekar_user)
        url = reverse(
            "articles:article-approve",
            kwargs={"pk": review_article.pk},
        )
        response = client.post(url)
        assert response.status_code == 403

    def test_bibliotekar_cannot_return(
        self, client, bibliotekar_user, review_article
    ):
        """14.15: Bibliotekar ne moze return (AC #7)."""
        client.force_login(bibliotekar_user)
        url = reverse(
            "articles:article-return",
            kwargs={"pk": review_article.pk},
        )
        response = client.post(url, {"revision_comment": "Komentar"})
        assert response.status_code == 403

    def test_regular_user_cannot_approve(
        self, client, regular_user, review_article
    ):
        """14.15: Regular user without role cannot approve (AC #7)."""
        client.force_login(regular_user)
        url = reverse(
            "articles:article-approve",
            kwargs={"pk": review_article.pk},
        )
        response = client.post(url)
        assert response.status_code == 403

    def test_admin_can_approve(self, client, admin_user, review_article):
        """14.16: Administrator can approve (AC #3)."""
        client.force_login(admin_user)
        url = reverse(
            "articles:article-approve",
            kwargs={"pk": review_article.pk},
        )
        response = client.post(url)
        assert response.status_code == 302
        review_article.refresh_from_db()
        assert review_article.status == ArticleStatus.READY

    def test_admin_can_return(self, client, admin_user, review_article):
        """14.16: Administrator can return for revision (AC #4)."""
        client.force_login(admin_user)
        url = reverse(
            "articles:article-return",
            kwargs={"pk": review_article.pk},
        )
        response = client.post(url, {"revision_comment": "Admin komentar"})
        assert response.status_code == 302
        review_article.refresh_from_db()
        assert review_article.status == ArticleStatus.DRAFT

    def test_superuser_can_approve(self, client, superuser, review_article):
        """Superuser can approve articles (AC #3)."""
        client.force_login(superuser)
        url = reverse(
            "articles:article-approve",
            kwargs={"pk": review_article.pk},
        )
        response = client.post(url)
        assert response.status_code == 302
        review_article.refresh_from_db()
        assert review_article.status == ArticleStatus.READY

    def test_superuser_can_return(self, client, superuser, review_article):
        """Superuser can return articles for revision (AC #4)."""
        client.force_login(superuser)
        url = reverse(
            "articles:article-return",
            kwargs={"pk": review_article.pk},
        )
        response = client.post(url, {"revision_comment": "Superuser komentar"})
        assert response.status_code == 302
        review_article.refresh_from_db()
        assert review_article.status == ArticleStatus.DRAFT
        assert review_article.revision_comment == "Superuser komentar"


# =============================================================================
# Data integrity tests - stale tracking field cleanup
# =============================================================================


@pytest.mark.django_db
class TestTrackingFieldCleanup:
    """Tests for proper cleanup of stale tracking fields during transitions."""

    def test_approve_clears_returned_by_and_returned_at(
        self, review_article, urednik_user
    ):
        """Approve clears stale returned_by/returned_at from prior return cycle."""
        # Simulate a prior return cycle's stale data
        review_article.returned_by = urednik_user
        review_article.returned_at = timezone.now()
        review_article.save(update_fields=["returned_by", "returned_at"])

        result = approve_article(review_article, urednik_user)
        assert result.returned_by is None
        assert result.returned_at is None

    def test_approve_clears_returned_tracking_persists_to_db(
        self, review_article, urednik_user
    ):
        """Approve cleared returned tracking persists to database."""
        review_article.returned_by = urednik_user
        review_article.returned_at = timezone.now()
        review_article.save(update_fields=["returned_by", "returned_at"])

        approve_article(review_article, urednik_user)
        review_article.refresh_from_db()
        assert review_article.returned_by is None
        assert review_article.returned_at is None

    def test_return_clears_reviewed_by_and_reviewed_at(
        self, review_article, urednik_user
    ):
        """Return clears stale reviewed_by/reviewed_at from prior approve attempt."""
        # Simulate a prior approve cycle's stale data
        review_article.reviewed_by = urednik_user
        review_article.reviewed_at = timezone.now()
        review_article.save(update_fields=["reviewed_by", "reviewed_at"])

        result = return_article_for_revision(
            review_article, urednik_user, "Ispraviti"
        )
        assert result.reviewed_by is None
        assert result.reviewed_at is None

    def test_return_clears_reviewed_tracking_persists_to_db(
        self, review_article, urednik_user
    ):
        """Return cleared reviewed tracking persists to database."""
        review_article.reviewed_by = urednik_user
        review_article.reviewed_at = timezone.now()
        review_article.save(update_fields=["reviewed_by", "reviewed_at"])

        return_article_for_revision(review_article, urednik_user, "Komentar")
        review_article.refresh_from_db()
        assert review_article.reviewed_by is None
        assert review_article.reviewed_at is None


# =============================================================================
# 14.17: Template tests - button visibility
# =============================================================================


@pytest.mark.django_db
class TestReviewButtonVisibility:
    """Tests for review button visibility in article_detail.html."""

    def test_review_buttons_visible_for_urednik_review_article(
        self, client, urednik_user, review_article
    ):
        """14.17: Review buttons visible for Urednik + REVIEW status (AC #2)."""
        client.force_login(urednik_user)
        url = reverse("articles:detail", kwargs={"pk": review_article.pk})
        response = client.get(url)
        content = response.content.decode()
        assert "Odobri" in content
        assert "Vrati na doradu" in content

    def test_review_buttons_hidden_for_bibliotekar(
        self, client, bibliotekar_user, review_article
    ):
        """14.17: Review buttons NOT visible for Bibliotekar (AC #7)."""
        client.force_login(bibliotekar_user)
        url = reverse("articles:detail", kwargs={"pk": review_article.pk})
        response = client.get(url)
        content = response.content.decode()
        assert "approve-check" not in content
        assert "return-check" not in content

    def test_review_buttons_hidden_for_draft(
        self, client, urednik_user, draft_article
    ):
        """14.17: Review buttons NOT visible for DRAFT articles."""
        client.force_login(urednik_user)
        url = reverse("articles:detail", kwargs={"pk": draft_article.pk})
        response = client.get(url)
        content = response.content.decode()
        assert "approve-check" not in content
        assert "return-check" not in content

    def test_ready_status_message_shown(
        self, client, urednik_user, ready_article
    ):
        """14.17: READY status message is displayed (AC #5)."""
        client.force_login(urednik_user)
        url = reverse("articles:detail", kwargs={"pk": ready_article.pk})
        response = client.get(url)
        content = response.content.decode()
        assert "Članak je odobren i spreman za objavu" in content

    def test_no_review_buttons_for_ready(
        self, client, urednik_user, ready_article
    ):
        """14.17: No review buttons for READY articles (AC #5)."""
        client.force_login(urednik_user)
        url = reverse("articles:detail", kwargs={"pk": ready_article.pk})
        response = client.get(url)
        content = response.content.decode()
        assert "approve-check" not in content
        assert "return-check" not in content

    def test_revision_comment_shown_for_returned_draft(
        self, client, bibliotekar_user, returned_draft_article
    ):
        """14.17: Revision comment visible for returned DRAFT article (AC #6)."""
        client.force_login(bibliotekar_user)
        url = reverse(
            "articles:detail", kwargs={"pk": returned_draft_article.pk}
        )
        response = client.get(url)
        content = response.content.decode()
        assert "Komentar urednika" in content
        assert "Dodajte reference" in content

    def test_revision_comment_hidden_for_review(
        self, client, urednik_user, review_article_with_comment
    ):
        """14.17: Revision comment NOT visible while in REVIEW status."""
        client.force_login(urednik_user)
        url = reverse(
            "articles:detail",
            kwargs={"pk": review_article_with_comment.pk},
        )
        response = client.get(url)
        content = response.content.decode()
        assert "Komentar urednika:" not in content

    def test_edit_button_visible_for_returned_draft(
        self, client, bibliotekar_user, returned_draft_article
    ):
        """14.17: Edit button visible for returned DRAFT article (AC #6)."""
        client.force_login(bibliotekar_user)
        url = reverse(
            "articles:detail", kwargs={"pk": returned_draft_article.pk}
        )
        response = client.get(url)
        content = response.content.decode()
        assert "Izmeni" in content


# =============================================================================
# 14.18-14.20: Integration tests
# =============================================================================


@pytest.mark.django_db
class TestEditorialReviewIntegration:
    """Integration tests for complete editorial review flows."""

    def test_approve_flow(self, client, urednik_user, review_article):
        """14.18: Complete flow REVIEW -> READY (approve) (AC #3)."""
        client.force_login(urednik_user)
        article = review_article

        # Step 1: View detail - review buttons visible
        detail_url = reverse("articles:detail", kwargs={"pk": article.pk})
        response = client.get(detail_url)
        content = response.content.decode()
        assert "Odobri" in content

        # Step 2: Check approval (HTMX GET)
        check_url = reverse(
            "articles:article-approve-check", kwargs={"pk": article.pk}
        )
        response = client.get(check_url)
        assert response.status_code == 200
        content = response.content.decode()
        assert "Potvrda odobrenja" in content

        # Step 3: Approve (POST)
        approve_url = reverse(
            "articles:article-approve", kwargs={"pk": article.pk}
        )
        response = client.post(approve_url)
        assert response.status_code == 302

        # Step 4: Verify status is READY
        article.refresh_from_db()
        assert article.status == ArticleStatus.READY
        assert article.reviewed_by == urednik_user
        assert article.reviewed_at is not None

        # Step 5: View detail again - READY message, no review buttons
        response = client.get(detail_url)
        content = response.content.decode()
        assert "Članak je odobren i spreman za objavu" in content
        assert "approve-check" not in content

    def test_return_flow(self, client, urednik_user, review_article):
        """14.19: Complete flow REVIEW -> DRAFT (return) (AC #4)."""
        client.force_login(urednik_user)
        article = review_article

        # Step 1: Check return (HTMX GET)
        check_url = reverse(
            "articles:article-return-check", kwargs={"pk": article.pk}
        )
        response = client.get(check_url)
        assert response.status_code == 200
        content = response.content.decode()
        assert "revision_comment" in content

        # Step 2: Return with comment (POST)
        return_url = reverse(
            "articles:article-return", kwargs={"pk": article.pk}
        )
        response = client.post(
            return_url, {"revision_comment": "Potrebne reference"}
        )
        assert response.status_code == 302

        # Step 3: Verify status is DRAFT
        article.refresh_from_db()
        assert article.status == ArticleStatus.DRAFT
        assert article.revision_comment == "Potrebne reference"
        assert article.returned_by == urednik_user
        assert article.submitted_by is None

    def test_resubmit_cycle(
        self, client, urednik_user, bibliotekar_user, review_article
    ):
        """14.20: DRAFT -> REVIEW -> DRAFT -> REVIEW -> READY (resubmit cycle) (AC #6)."""
        article = review_article

        # Step 1: Urednik returns article for revision (REVIEW -> DRAFT)
        client.force_login(urednik_user)
        return_url = reverse(
            "articles:article-return", kwargs={"pk": article.pk}
        )
        client.post(return_url, {"revision_comment": "Dodaj apstrakt"})
        article.refresh_from_db()
        assert article.status == ArticleStatus.DRAFT
        assert article.revision_comment == "Dodaj apstrakt"
        assert article.submitted_by is None

        # Step 2: Bibliotekar views detail - sees revision comment, edit button
        client.force_login(bibliotekar_user)
        detail_url = reverse("articles:detail", kwargs={"pk": article.pk})
        response = client.get(detail_url)
        content = response.content.decode()
        assert "Komentar urednika" in content
        assert "Dodaj apstrakt" in content
        assert "Izmeni" in content

        # Step 3: Bibliotekar resubmits article (DRAFT -> REVIEW)
        submit_url = reverse(
            "articles:article-submit", kwargs={"pk": article.pk}
        )
        response = client.post(submit_url)
        assert response.status_code == 302
        article.refresh_from_db()
        assert article.status == ArticleStatus.REVIEW
        assert article.submitted_by == bibliotekar_user

        # Step 4: Urednik approves (REVIEW -> READY)
        client.force_login(urednik_user)
        approve_url = reverse(
            "articles:article-approve", kwargs={"pk": article.pk}
        )
        response = client.post(approve_url)
        assert response.status_code == 302
        article.refresh_from_db()
        assert article.status == ArticleStatus.READY
        assert article.reviewed_by == urednik_user
        assert article.revision_comment == ""  # Cleared on approve

    def test_status_filter_review(self, client, urednik_user, review_article):
        """14.18: Articles with REVIEW status can be filtered in list (AC #1)."""
        client.force_login(urednik_user)
        url = reverse("articles:list") + "?status=REVIEW"
        response = client.get(url)
        assert response.status_code == 200
        content = response.content.decode()
        assert review_article.title in content
