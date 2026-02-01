"""
Tests for Article Publishing & Withdrawal.

Story 3.7 - Task 14: Comprehensive tests covering AC #1-#8.
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
    publish_article,
    withdraw_article,
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
    return PublisherFactory(name="Izdavač A Publish")


@pytest.fixture
def publisher_b():
    """Create publisher B."""
    return PublisherFactory(name="Izdavač B Publish")


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
    """Create an Administrator user."""
    user = User.objects.create_user(
        email="admin-publish@test.com", password="testpass123"
    )
    group, _ = Group.objects.get_or_create(name="Administrator")
    user.groups.add(group)
    return user


@pytest.fixture
def urednik_user(publisher_a):
    """Create an Urednik user assigned to publisher A."""
    user = User.objects.create_user(
        email="ured-publish@test.com",
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
        email="bib-publish@test.com",
        password="testpass123",
        publisher=publisher_a,
    )
    group, _ = Group.objects.get_or_create(name="Bibliotekar")
    user.groups.add(group)
    return user


@pytest.fixture
def superuser():
    """Create a superuser."""
    return User.objects.create_superuser(
        email="super-publish@test.com", password="testpass123"
    )


@pytest.fixture
def regular_user():
    """Create a regular user without roles."""
    return User.objects.create_user(
        email="regular-publish@test.com", password="testpass123"
    )


@pytest.fixture
def draft_article(issue_a, bibliotekar_user):
    """Create a DRAFT article."""
    article = ArticleFactory(
        issue=issue_a,
        title="Članak u nacrtu (publish test)",
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
        title="Članak na pregledu (publish test)",
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
def ready_article(issue_a, bibliotekar_user, urednik_user):
    """Create a READY status article (approved by Urednik)."""
    article = ArticleFactory(
        issue=issue_a,
        title="Članak spreman za objavu (publish test)",
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
def published_article(issue_a, bibliotekar_user, admin_user):
    """Create a PUBLISHED status article."""
    article = ArticleFactory(
        issue=issue_a,
        title="Objavljeni članak (publish test)",
        abstract="Apstrakt.",
        status=ArticleStatus.PUBLISHED,
        pdf_status=PdfStatus.CLEAN,
        pdf_file="articles/pdfs/test.pdf",
        created_by=bibliotekar_user,
        published_by=admin_user,
        published_at=timezone.now(),
    )
    AuthorFactory(article=article)
    return article


@pytest.fixture
def withdrawn_article(issue_a, bibliotekar_user, admin_user):
    """Create a WITHDRAWN status article."""
    article = ArticleFactory(
        issue=issue_a,
        title="Povučeni članak (publish test)",
        abstract="Apstrakt.",
        status=ArticleStatus.WITHDRAWN,
        pdf_status=PdfStatus.CLEAN,
        pdf_file="articles/pdfs/test.pdf",
        created_by=bibliotekar_user,
        published_by=admin_user,
        published_at=timezone.now(),
        withdrawal_reason="Duplicirani podaci",
        withdrawn_by=admin_user,
        withdrawn_at=timezone.now(),
    )
    AuthorFactory(article=article)
    return article


@pytest.fixture
def ready_article_b(issue_b):
    """Create a READY article for publisher B."""
    article = ArticleFactory(
        issue=issue_b,
        title="Članak izdavača B",
        abstract="Apstrakt.",
        status=ArticleStatus.READY,
        pdf_status=PdfStatus.CLEAN,
        pdf_file="articles/pdfs/test.pdf",
    )
    AuthorFactory(article=article)
    return article


@pytest.fixture
def published_article_b(issue_b):
    """Create a PUBLISHED article for publisher B."""
    article = ArticleFactory(
        issue=issue_b,
        title="Objavljeni članak izdavača B",
        abstract="Apstrakt.",
        status=ArticleStatus.PUBLISHED,
        pdf_status=PdfStatus.CLEAN,
        pdf_file="articles/pdfs/test.pdf",
    )
    AuthorFactory(article=article)
    return article


# =============================================================================
# 14.1-14.3: Service tests for publish_article
# =============================================================================


@pytest.mark.django_db
class TestPublishArticleService:
    """Tests for publish_article service function."""

    def test_publish_valid_ready_article(self, ready_article, admin_user):
        """14.1: Valid READY article transitions to PUBLISHED (AC #2)."""
        result = publish_article(ready_article, admin_user)
        assert result.status == ArticleStatus.PUBLISHED
        assert result.published_by == admin_user
        assert result.published_at is not None

    def test_publish_persists_to_database(self, ready_article, admin_user):
        """14.1: Publish persists to database (AC #2)."""
        publish_article(ready_article, admin_user)
        ready_article.refresh_from_db()
        assert ready_article.status == ArticleStatus.PUBLISHED
        assert ready_article.published_by == admin_user
        assert ready_article.published_at is not None

    def test_publish_rejects_draft(self, draft_article, admin_user):
        """14.2: DRAFT article raises InvalidStatusTransition (AC #7)."""
        with pytest.raises(InvalidStatusTransition, match="spremni za objavu"):
            publish_article(draft_article, admin_user)

    def test_publish_rejects_review(self, review_article, admin_user):
        """14.2: REVIEW article raises InvalidStatusTransition (AC #7)."""
        with pytest.raises(InvalidStatusTransition, match="spremni za objavu"):
            publish_article(review_article, admin_user)

    def test_publish_rejects_published(self, published_article, admin_user):
        """14.2: PUBLISHED article raises InvalidStatusTransition (AC #7)."""
        with pytest.raises(InvalidStatusTransition):
            publish_article(published_article, admin_user)

    def test_publish_rejects_withdrawn(self, withdrawn_article, admin_user):
        """14.2: WITHDRAWN article raises InvalidStatusTransition (AC #7)."""
        with pytest.raises(InvalidStatusTransition):
            publish_article(withdrawn_article, admin_user)

    def test_publish_saves_published_by(self, ready_article, admin_user):
        """14.3: published_by is saved correctly (AC #2)."""
        result = publish_article(ready_article, admin_user)
        assert result.published_by == admin_user

    def test_publish_saves_published_at(self, ready_article, admin_user):
        """14.3: published_at is saved correctly (AC #2)."""
        before = timezone.now()
        result = publish_article(ready_article, admin_user)
        after = timezone.now()
        assert result.published_at is not None
        assert before <= result.published_at <= after


# =============================================================================
# 14.4-14.7: Service tests for withdraw_article
# =============================================================================


@pytest.mark.django_db
class TestWithdrawArticleService:
    """Tests for withdraw_article service function."""

    def test_withdraw_valid_published_article(self, published_article, admin_user):
        """14.4: Valid PUBLISHED article with reason transitions to WITHDRAWN (AC #4)."""
        result = withdraw_article(published_article, admin_user, "Duplicirani podaci")
        assert result.status == ArticleStatus.WITHDRAWN
        assert result.withdrawal_reason == "Duplicirani podaci"
        assert result.withdrawn_by == admin_user
        assert result.withdrawn_at is not None

    def test_withdraw_persists_to_database(self, published_article, admin_user):
        """14.4: Withdraw persists to database (AC #4)."""
        withdraw_article(published_article, admin_user, "Greška u podacima")
        published_article.refresh_from_db()
        assert published_article.status == ArticleStatus.WITHDRAWN
        assert published_article.withdrawal_reason == "Greška u podacima"
        assert published_article.withdrawn_by == admin_user

    def test_withdraw_rejects_draft(self, draft_article, admin_user):
        """14.5: DRAFT article raises InvalidStatusTransition (AC #7)."""
        with pytest.raises(InvalidStatusTransition, match="objavljeni"):
            withdraw_article(draft_article, admin_user, "Razlog")

    def test_withdraw_rejects_review(self, review_article, admin_user):
        """14.5: REVIEW article raises InvalidStatusTransition (AC #7)."""
        with pytest.raises(InvalidStatusTransition, match="objavljeni"):
            withdraw_article(review_article, admin_user, "Razlog")

    def test_withdraw_rejects_ready(self, ready_article, admin_user):
        """14.5: READY article raises InvalidStatusTransition (AC #7)."""
        with pytest.raises(InvalidStatusTransition, match="objavljeni"):
            withdraw_article(ready_article, admin_user, "Razlog")

    def test_withdraw_rejects_withdrawn(self, withdrawn_article, admin_user):
        """14.5: WITHDRAWN article raises InvalidStatusTransition (AC #7)."""
        with pytest.raises(InvalidStatusTransition):
            withdraw_article(withdrawn_article, admin_user, "Razlog")

    def test_withdraw_rejects_empty_reason(self, published_article, admin_user):
        """14.6: Empty reason raises InvalidStatusTransition (AC #4)."""
        with pytest.raises(InvalidStatusTransition, match="Razlog"):
            withdraw_article(published_article, admin_user, "")

    def test_withdraw_rejects_whitespace_reason(self, published_article, admin_user):
        """14.6: Whitespace-only reason raises InvalidStatusTransition."""
        with pytest.raises(InvalidStatusTransition, match="Razlog"):
            withdraw_article(published_article, admin_user, "   ")

    def test_withdraw_rejects_none_reason(self, published_article, admin_user):
        """14.6: None reason raises InvalidStatusTransition."""
        with pytest.raises(InvalidStatusTransition):
            withdraw_article(published_article, admin_user, None)

    def test_withdraw_saves_withdrawal_reason(self, published_article, admin_user):
        """14.7: withdrawal_reason is saved correctly (AC #4)."""
        result = withdraw_article(
            published_article, admin_user, "Plagijat detektovan"
        )
        assert result.withdrawal_reason == "Plagijat detektovan"

    def test_withdraw_saves_withdrawn_by(self, published_article, admin_user):
        """14.7: withdrawn_by is saved correctly (AC #4)."""
        result = withdraw_article(published_article, admin_user, "Razlog")
        assert result.withdrawn_by == admin_user

    def test_withdraw_saves_withdrawn_at(self, published_article, admin_user):
        """14.7: withdrawn_at is saved correctly (AC #4)."""
        before = timezone.now()
        result = withdraw_article(published_article, admin_user, "Razlog")
        after = timezone.now()
        assert result.withdrawn_at is not None
        assert before <= result.withdrawn_at <= after

    def test_withdraw_strips_reason(self, published_article, admin_user):
        """14.4: Reason is stripped of leading/trailing whitespace."""
        result = withdraw_article(
            published_article, admin_user, "  Razlog sa razmacima  "
        )
        assert result.withdrawal_reason == "Razlog sa razmacima"


# =============================================================================
# 14.8-14.10: View tests for article_publish_check
# =============================================================================


@pytest.mark.django_db
class TestArticlePublishCheckView:
    """Tests for article_publish_check HTMX GET endpoint."""

    def test_publish_check_valid(self, client, admin_user, ready_article):
        """14.8: Publish check for READY article returns modal (AC #1, #2)."""
        client.force_login(admin_user)
        url = reverse(
            "articles:article-publish-check",
            kwargs={"pk": ready_article.pk},
        )
        response = client.get(url)
        assert response.status_code == 200
        content = response.content.decode()
        assert "Potvrda objavljivanja" in content
        assert "Objavi" in content

    def test_publish_check_non_ready_shows_error(
        self, client, admin_user, draft_article
    ):
        """14.8: Publish check for non-READY article shows error."""
        client.force_login(admin_user)
        url = reverse(
            "articles:article-publish-check",
            kwargs={"pk": draft_article.pk},
        )
        response = client.get(url)
        assert response.status_code == 200
        content = response.content.decode()
        assert "Nije moguće objaviti" in content

    def test_publish_check_rejects_urednik(
        self, client, urednik_user, ready_article
    ):
        """14.9: Urednik cannot access publish check (AC #6, #8)."""
        client.force_login(urednik_user)
        url = reverse(
            "articles:article-publish-check",
            kwargs={"pk": ready_article.pk},
        )
        response = client.get(url)
        assert response.status_code == 403

    def test_publish_check_rejects_bibliotekar(
        self, client, bibliotekar_user, ready_article
    ):
        """14.10: Bibliotekar cannot access publish check (AC #6, #8)."""
        client.force_login(bibliotekar_user)
        url = reverse(
            "articles:article-publish-check",
            kwargs={"pk": ready_article.pk},
        )
        response = client.get(url)
        assert response.status_code == 403

    def test_publish_check_requires_login(self, client, ready_article):
        """Publish check requires authentication."""
        url = reverse(
            "articles:article-publish-check",
            kwargs={"pk": ready_article.pk},
        )
        response = client.get(url)
        assert response.status_code == 302
        assert "login" in response.url


# =============================================================================
# 14.11-14.12: View tests for article_publish
# =============================================================================


@pytest.mark.django_db
class TestArticlePublishView:
    """Tests for article_publish POST endpoint."""

    def test_publish_success(self, client, admin_user, ready_article):
        """14.11: Successful publish redirects with success message (AC #2)."""
        client.force_login(admin_user)
        url = reverse(
            "articles:article-publish",
            kwargs={"pk": ready_article.pk},
        )
        response = client.post(url)
        assert response.status_code == 302
        ready_article.refresh_from_db()
        assert ready_article.status == ArticleStatus.PUBLISHED

    def test_publish_success_message(self, client, admin_user, ready_article):
        """14.11: Successful publish shows toast message (AC #2)."""
        client.force_login(admin_user)
        url = reverse(
            "articles:article-publish",
            kwargs={"pk": ready_article.pk},
        )
        response = client.post(url, follow=True)
        messages_list = list(response.context["messages"])
        assert len(messages_list) == 1
        assert "Članak objavljen" in str(messages_list[0])

    def test_publish_non_ready_shows_error(
        self, client, admin_user, draft_article
    ):
        """14.12: Publish for non-READY article shows error message (AC #7)."""
        client.force_login(admin_user)
        url = reverse(
            "articles:article-publish",
            kwargs={"pk": draft_article.pk},
        )
        response = client.post(url, follow=True)
        messages_list = list(response.context["messages"])
        assert any("spremni za objavu" in str(m) for m in messages_list)
        draft_article.refresh_from_db()
        assert draft_article.status == ArticleStatus.DRAFT  # Unchanged

    def test_publish_rejects_get(self, client, admin_user, ready_article):
        """Publish endpoint rejects GET requests."""
        client.force_login(admin_user)
        url = reverse(
            "articles:article-publish",
            kwargs={"pk": ready_article.pk},
        )
        response = client.get(url)
        assert response.status_code == 405

    def test_publish_rejects_urednik(
        self, client, urednik_user, ready_article
    ):
        """14.18: Urednik cannot publish (AC #6, #8)."""
        client.force_login(urednik_user)
        url = reverse(
            "articles:article-publish",
            kwargs={"pk": ready_article.pk},
        )
        response = client.post(url)
        assert response.status_code == 403

    def test_publish_rejects_bibliotekar(
        self, client, bibliotekar_user, ready_article
    ):
        """14.19: Bibliotekar cannot publish (AC #6, #8)."""
        client.force_login(bibliotekar_user)
        url = reverse(
            "articles:article-publish",
            kwargs={"pk": ready_article.pk},
        )
        response = client.post(url)
        assert response.status_code == 403


# =============================================================================
# 14.13-14.14: View tests for article_withdraw_check
# =============================================================================


@pytest.mark.django_db
class TestArticleWithdrawCheckView:
    """Tests for article_withdraw_check HTMX GET endpoint."""

    def test_withdraw_check_valid(self, client, admin_user, published_article):
        """14.13: Withdraw check for PUBLISHED article returns modal (AC #3, #4)."""
        client.force_login(admin_user)
        url = reverse(
            "articles:article-withdraw-check",
            kwargs={"pk": published_article.pk},
        )
        response = client.get(url)
        assert response.status_code == 200
        content = response.content.decode()
        assert "withdrawal_reason" in content

    def test_withdraw_check_non_published_shows_error(
        self, client, admin_user, ready_article
    ):
        """14.13: Withdraw check for non-PUBLISHED article shows error."""
        client.force_login(admin_user)
        url = reverse(
            "articles:article-withdraw-check",
            kwargs={"pk": ready_article.pk},
        )
        response = client.get(url)
        assert response.status_code == 200
        content = response.content.decode()
        assert "Nije moguće povući" in content

    def test_withdraw_check_rejects_urednik(
        self, client, urednik_user, published_article
    ):
        """14.14: Urednik cannot access withdraw check (AC #6, #8)."""
        client.force_login(urednik_user)
        url = reverse(
            "articles:article-withdraw-check",
            kwargs={"pk": published_article.pk},
        )
        response = client.get(url)
        assert response.status_code == 403

    def test_withdraw_check_rejects_bibliotekar(
        self, client, bibliotekar_user, published_article
    ):
        """Bibliotekar cannot access withdraw check (AC #6, #8)."""
        client.force_login(bibliotekar_user)
        url = reverse(
            "articles:article-withdraw-check",
            kwargs={"pk": published_article.pk},
        )
        response = client.get(url)
        assert response.status_code == 403

    def test_withdraw_check_requires_login(self, client, published_article):
        """Withdraw check requires authentication."""
        url = reverse(
            "articles:article-withdraw-check",
            kwargs={"pk": published_article.pk},
        )
        response = client.get(url)
        assert response.status_code == 302
        assert "login" in response.url


# =============================================================================
# 14.15-14.16: View tests for article_withdraw
# =============================================================================


@pytest.mark.django_db
class TestArticleWithdrawView:
    """Tests for article_withdraw POST endpoint."""

    def test_withdraw_success(self, client, admin_user, published_article):
        """14.15: Successful withdraw with reason redirects (AC #4)."""
        client.force_login(admin_user)
        url = reverse(
            "articles:article-withdraw",
            kwargs={"pk": published_article.pk},
        )
        response = client.post(url, {"withdrawal_reason": "Duplikat"})
        assert response.status_code == 302
        published_article.refresh_from_db()
        assert published_article.status == ArticleStatus.WITHDRAWN
        assert published_article.withdrawal_reason == "Duplikat"

    def test_withdraw_success_message(self, client, admin_user, published_article):
        """14.15: Successful withdraw shows toast message (AC #4)."""
        client.force_login(admin_user)
        url = reverse(
            "articles:article-withdraw",
            kwargs={"pk": published_article.pk},
        )
        response = client.post(
            url, {"withdrawal_reason": "Duplikat"}, follow=True
        )
        messages_list = list(response.context["messages"])
        assert len(messages_list) == 1
        assert "Članak povučen" in str(messages_list[0])

    def test_withdraw_without_reason_fails(
        self, client, admin_user, published_article
    ):
        """14.16: Withdraw without reason shows error (AC #4)."""
        client.force_login(admin_user)
        url = reverse(
            "articles:article-withdraw",
            kwargs={"pk": published_article.pk},
        )
        response = client.post(url, {"withdrawal_reason": ""})
        assert response.status_code == 302  # Redirects with error
        published_article.refresh_from_db()
        assert published_article.status == ArticleStatus.PUBLISHED  # Unchanged

    def test_withdraw_without_reason_error_message(
        self, client, admin_user, published_article
    ):
        """14.16: Withdraw without reason shows appropriate error message."""
        client.force_login(admin_user)
        url = reverse(
            "articles:article-withdraw",
            kwargs={"pk": published_article.pk},
        )
        response = client.post(
            url, {"withdrawal_reason": ""}, follow=True
        )
        messages_list = list(response.context["messages"])
        assert any("Razlog" in str(m) for m in messages_list)

    def test_withdraw_rejects_get(self, client, admin_user, published_article):
        """Withdraw endpoint rejects GET requests."""
        client.force_login(admin_user)
        url = reverse(
            "articles:article-withdraw",
            kwargs={"pk": published_article.pk},
        )
        response = client.get(url)
        assert response.status_code == 405

    def test_withdraw_rejects_urednik(
        self, client, urednik_user, published_article
    ):
        """14.18: Urednik cannot withdraw (AC #6, #8)."""
        client.force_login(urednik_user)
        url = reverse(
            "articles:article-withdraw",
            kwargs={"pk": published_article.pk},
        )
        response = client.post(url, {"withdrawal_reason": "Razlog"})
        assert response.status_code == 403

    def test_withdraw_rejects_bibliotekar(
        self, client, bibliotekar_user, published_article
    ):
        """14.19: Bibliotekar cannot withdraw (AC #6, #8)."""
        client.force_login(bibliotekar_user)
        url = reverse(
            "articles:article-withdraw",
            kwargs={"pk": published_article.pk},
        )
        response = client.post(url, {"withdrawal_reason": "Razlog"})
        assert response.status_code == 403


# =============================================================================
# 14.17: Permission tests - publisher scoping
# =============================================================================


@pytest.mark.django_db
class TestPublishWithdrawPermissions:
    """Permission-specific tests for publish/withdraw endpoints."""

    def test_publisher_scoping_publish_check(
        self, client, urednik_user, ready_article_b
    ):
        """14.17: Urednik cannot access publish check for other publisher's article."""
        client.force_login(urednik_user)
        url = reverse(
            "articles:article-publish-check",
            kwargs={"pk": ready_article_b.pk},
        )
        response = client.get(url)
        assert response.status_code == 403

    def test_publisher_scoping_publish(
        self, client, urednik_user, ready_article_b
    ):
        """14.17: Urednik cannot publish other publisher's article."""
        client.force_login(urednik_user)
        url = reverse(
            "articles:article-publish",
            kwargs={"pk": ready_article_b.pk},
        )
        response = client.post(url)
        assert response.status_code == 403

    def test_publisher_scoping_withdraw_check(
        self, client, urednik_user, published_article_b
    ):
        """14.17: Urednik cannot access withdraw check for other publisher's article."""
        client.force_login(urednik_user)
        url = reverse(
            "articles:article-withdraw-check",
            kwargs={"pk": published_article_b.pk},
        )
        response = client.get(url)
        assert response.status_code == 403

    def test_publisher_scoping_withdraw(
        self, client, urednik_user, published_article_b
    ):
        """14.17: Urednik cannot withdraw other publisher's article."""
        client.force_login(urednik_user)
        url = reverse(
            "articles:article-withdraw",
            kwargs={"pk": published_article_b.pk},
        )
        response = client.post(url, {"withdrawal_reason": "Razlog"})
        assert response.status_code == 403

    def test_superadmin_can_publish(self, client, superuser, ready_article):
        """14.20: Superadmin can publish articles (AC #2)."""
        client.force_login(superuser)
        url = reverse(
            "articles:article-publish",
            kwargs={"pk": ready_article.pk},
        )
        response = client.post(url)
        assert response.status_code == 302
        ready_article.refresh_from_db()
        assert ready_article.status == ArticleStatus.PUBLISHED

    def test_superadmin_can_withdraw(self, client, superuser, published_article):
        """14.20: Superadmin can withdraw articles (AC #4)."""
        client.force_login(superuser)
        url = reverse(
            "articles:article-withdraw",
            kwargs={"pk": published_article.pk},
        )
        response = client.post(url, {"withdrawal_reason": "Razlog"})
        assert response.status_code == 302
        published_article.refresh_from_db()
        assert published_article.status == ArticleStatus.WITHDRAWN

    def test_regular_user_cannot_publish(
        self, client, regular_user, ready_article
    ):
        """Regular user without role cannot publish (AC #6)."""
        client.force_login(regular_user)
        url = reverse(
            "articles:article-publish",
            kwargs={"pk": ready_article.pk},
        )
        response = client.post(url)
        assert response.status_code == 403

    def test_regular_user_cannot_withdraw(
        self, client, regular_user, published_article
    ):
        """Regular user without role cannot withdraw (AC #6)."""
        client.force_login(regular_user)
        url = reverse(
            "articles:article-withdraw",
            kwargs={"pk": published_article.pk},
        )
        response = client.post(url, {"withdrawal_reason": "Razlog"})
        assert response.status_code == 403


# =============================================================================
# 14.21: Template tests - button visibility
# =============================================================================


@pytest.mark.django_db
class TestPublishWithdrawButtonVisibility:
    """Tests for publish/withdraw button visibility in article_detail.html."""

    def test_publish_button_visible_for_admin_ready_article(
        self, client, admin_user, ready_article
    ):
        """14.21: Publish button visible for Administrator + READY status (AC #1)."""
        client.force_login(admin_user)
        url = reverse("articles:detail", kwargs={"pk": ready_article.pk})
        response = client.get(url)
        content = response.content.decode()
        assert "publish-check" in content
        assert "Objavi" in content

    def test_publish_button_hidden_for_urednik(
        self, client, urednik_user, ready_article
    ):
        """14.21: Publish button NOT visible for Urednik (AC #8)."""
        client.force_login(urednik_user)
        url = reverse("articles:detail", kwargs={"pk": ready_article.pk})
        response = client.get(url)
        content = response.content.decode()
        assert "publish-check" not in content

    def test_publish_button_hidden_for_bibliotekar(
        self, client, bibliotekar_user, ready_article
    ):
        """14.21: Publish button NOT visible for Bibliotekar (AC #8)."""
        client.force_login(bibliotekar_user)
        url = reverse("articles:detail", kwargs={"pk": ready_article.pk})
        response = client.get(url)
        content = response.content.decode()
        assert "publish-check" not in content

    def test_withdraw_button_visible_for_admin_published_article(
        self, client, admin_user, published_article
    ):
        """14.21: Withdraw button visible for Administrator + PUBLISHED status (AC #3)."""
        client.force_login(admin_user)
        url = reverse("articles:detail", kwargs={"pk": published_article.pk})
        response = client.get(url)
        content = response.content.decode()
        assert "withdraw-check" in content
        assert "Povuci" in content

    def test_withdraw_button_hidden_for_urednik(
        self, client, urednik_user, published_article
    ):
        """14.21: Withdraw button NOT visible for Urednik (AC #8)."""
        client.force_login(urednik_user)
        url = reverse("articles:detail", kwargs={"pk": published_article.pk})
        response = client.get(url)
        content = response.content.decode()
        assert "withdraw-check" not in content

    def test_published_alert_shown(
        self, client, admin_user, published_article
    ):
        """14.21: PUBLISHED status alert is displayed (AC #3)."""
        client.force_login(admin_user)
        url = reverse("articles:detail", kwargs={"pk": published_article.pk})
        response = client.get(url)
        content = response.content.decode()
        assert "Članak je objavljen" in content

    def test_withdrawn_alert_shown(
        self, client, admin_user, withdrawn_article
    ):
        """14.21: WITHDRAWN status alert with reason is displayed (AC #5)."""
        client.force_login(admin_user)
        url = reverse("articles:detail", kwargs={"pk": withdrawn_article.pk})
        response = client.get(url)
        content = response.content.decode()
        assert "Članak je povučen" in content
        assert "Duplicirani podaci" in content

    def test_no_actions_for_withdrawn(
        self, client, admin_user, withdrawn_article
    ):
        """14.21: No publish/withdraw actions for WITHDRAWN articles (AC #5)."""
        client.force_login(admin_user)
        url = reverse("articles:detail", kwargs={"pk": withdrawn_article.pk})
        response = client.get(url)
        content = response.content.decode()
        assert "publish-check" not in content
        assert "withdraw-check" not in content


# =============================================================================
# 14.22-14.24: Integration tests
# =============================================================================


@pytest.mark.django_db
class TestPublishWithdrawIntegration:
    """Integration tests for complete publish/withdraw flows."""

    def test_publish_flow(self, client, admin_user, ready_article):
        """14.22: Complete flow READY -> PUBLISHED (publish) (AC #2)."""
        client.force_login(admin_user)
        article = ready_article

        # Step 1: View detail - publish button visible
        detail_url = reverse("articles:detail", kwargs={"pk": article.pk})
        response = client.get(detail_url)
        content = response.content.decode()
        assert "Objavi" in content

        # Step 2: Check publish (HTMX GET)
        check_url = reverse(
            "articles:article-publish-check", kwargs={"pk": article.pk}
        )
        response = client.get(check_url)
        assert response.status_code == 200
        content = response.content.decode()
        assert "Potvrda objavljivanja" in content

        # Step 3: Publish (POST)
        publish_url = reverse(
            "articles:article-publish", kwargs={"pk": article.pk}
        )
        response = client.post(publish_url)
        assert response.status_code == 302

        # Step 4: Verify status is PUBLISHED
        article.refresh_from_db()
        assert article.status == ArticleStatus.PUBLISHED
        assert article.published_by == admin_user
        assert article.published_at is not None

        # Step 5: View detail - PUBLISHED message, withdraw available
        response = client.get(detail_url)
        content = response.content.decode()
        assert "Članak je objavljen" in content
        assert "Povuci" in content
        assert "publish-check" not in content

    def test_withdraw_flow(self, client, admin_user, published_article):
        """14.23: Complete flow PUBLISHED -> WITHDRAWN (withdraw) (AC #4)."""
        client.force_login(admin_user)
        article = published_article

        # Step 1: View detail - withdraw button visible
        detail_url = reverse("articles:detail", kwargs={"pk": article.pk})
        response = client.get(detail_url)
        content = response.content.decode()
        assert "Povuci" in content

        # Step 2: Check withdraw (HTMX GET)
        check_url = reverse(
            "articles:article-withdraw-check", kwargs={"pk": article.pk}
        )
        response = client.get(check_url)
        assert response.status_code == 200
        content = response.content.decode()
        assert "withdrawal_reason" in content

        # Step 3: Withdraw with reason (POST)
        withdraw_url = reverse(
            "articles:article-withdraw", kwargs={"pk": article.pk}
        )
        response = client.post(
            withdraw_url, {"withdrawal_reason": "Plagijat"}
        )
        assert response.status_code == 302

        # Step 4: Verify status is WITHDRAWN
        article.refresh_from_db()
        assert article.status == ArticleStatus.WITHDRAWN
        assert article.withdrawal_reason == "Plagijat"
        assert article.withdrawn_by == admin_user
        assert article.withdrawn_at is not None

        # Step 5: View detail - WITHDRAWN message, no actions
        response = client.get(detail_url)
        content = response.content.decode()
        assert "Članak je povučen" in content
        assert "Plagijat" in content
        assert "publish-check" not in content
        assert "withdraw-check" not in content

    def test_full_lifecycle(
        self, client, admin_user, urednik_user, bibliotekar_user, draft_article
    ):
        """14.24: DRAFT -> REVIEW -> READY -> PUBLISHED -> WITHDRAWN (full lifecycle)."""
        article = draft_article

        # Step 1: Bibliotekar submits (DRAFT -> REVIEW)
        client.force_login(bibliotekar_user)
        submit_url = reverse(
            "articles:article-submit", kwargs={"pk": article.pk}
        )
        response = client.post(submit_url)
        assert response.status_code == 302
        article.refresh_from_db()
        assert article.status == ArticleStatus.REVIEW

        # Step 2: Urednik approves (REVIEW -> READY)
        client.force_login(urednik_user)
        approve_url = reverse(
            "articles:article-approve", kwargs={"pk": article.pk}
        )
        response = client.post(approve_url)
        assert response.status_code == 302
        article.refresh_from_db()
        assert article.status == ArticleStatus.READY

        # Step 3: Administrator publishes (READY -> PUBLISHED)
        client.force_login(admin_user)
        publish_url = reverse(
            "articles:article-publish", kwargs={"pk": article.pk}
        )
        response = client.post(publish_url)
        assert response.status_code == 302
        article.refresh_from_db()
        assert article.status == ArticleStatus.PUBLISHED
        assert article.published_by == admin_user

        # Step 4: Administrator withdraws (PUBLISHED -> WITHDRAWN)
        withdraw_url = reverse(
            "articles:article-withdraw", kwargs={"pk": article.pk}
        )
        response = client.post(
            withdraw_url, {"withdrawal_reason": "Duplikat"}
        )
        assert response.status_code == 302
        article.refresh_from_db()
        assert article.status == ArticleStatus.WITHDRAWN
        assert article.withdrawal_reason == "Duplikat"
        assert article.withdrawn_by == admin_user

        # Step 5: Verify terminal state - no further transitions
        detail_url = reverse("articles:detail", kwargs={"pk": article.pk})
        response = client.get(detail_url)
        content = response.content.decode()
        assert "Članak je povučen" in content
        assert "publish-check" not in content
        assert "withdraw-check" not in content
