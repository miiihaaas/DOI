"""
Tests for Submit Article for Review functionality.

Story 3.5 - Task 10: Comprehensive tests covering AC #1-#8.
Service tests, view tests, permission tests, template tests, integration tests.
"""

import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.test import Client
from django.urls import reverse

from doi_portal.articles.models import Article, ArticleStatus, PdfStatus
from doi_portal.articles.services import (
    InvalidStatusTransition,
    submit_article_for_review,
    validate_article_for_submit,
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
        email="admin-submit@test.com", password="testpass123"
    )
    group, _ = Group.objects.get_or_create(name="Administrator")
    user.groups.add(group)
    return user


@pytest.fixture
def bibliotekar_user(publisher_a):
    """Create a Bibliotekar user assigned to publisher A."""
    user = User.objects.create_user(
        email="bib-submit@test.com",
        password="testpass123",
        publisher=publisher_a,
    )
    group, _ = Group.objects.get_or_create(name="Bibliotekar")
    user.groups.add(group)
    return user


@pytest.fixture
def urednik_user(publisher_a):
    """Create an Urednik user assigned to publisher A."""
    user = User.objects.create_user(
        email="ured-submit@test.com",
        password="testpass123",
        publisher=publisher_a,
    )
    group, _ = Group.objects.get_or_create(name="Urednik")
    user.groups.add(group)
    return user


@pytest.fixture
def other_publisher_user(publisher_b):
    """Create a Bibliotekar user assigned to publisher B."""
    user = User.objects.create_user(
        email="other-bib@test.com",
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
        email="regular-submit@test.com", password="testpass123"
    )


@pytest.fixture
def draft_article_with_author_and_pdf(issue_a, bibliotekar_user):
    """Create a complete DRAFT article ready for submission."""
    article = ArticleFactory(
        issue=issue_a,
        title="Kompletni članak",
        abstract="Ovo je apstrakt za testiranje.",
        status=ArticleStatus.DRAFT,
        pdf_status=PdfStatus.CLEAN,
        pdf_file="articles/pdfs/test.pdf",
        created_by=bibliotekar_user,
    )
    AuthorFactory(article=article, given_name="Petar", surname="Petrović", order=1)
    return article


@pytest.fixture
def draft_article_no_authors(issue_a, bibliotekar_user):
    """Create a DRAFT article without authors."""
    return ArticleFactory(
        issue=issue_a,
        title="Članak bez autora",
        abstract="Apstrakt postoji.",
        status=ArticleStatus.DRAFT,
        pdf_status=PdfStatus.CLEAN,
        pdf_file="articles/pdfs/test.pdf",
        created_by=bibliotekar_user,
    )


@pytest.fixture
def draft_article_no_pdf(issue_a, bibliotekar_user):
    """Create a DRAFT article without clean PDF."""
    article = ArticleFactory(
        issue=issue_a,
        title="Članak bez PDF-a",
        abstract="Apstrakt postoji.",
        status=ArticleStatus.DRAFT,
        pdf_status=PdfStatus.NONE,
        created_by=bibliotekar_user,
    )
    AuthorFactory(article=article, given_name="Ana", surname="Anić", order=1)
    return article


@pytest.fixture
def draft_article_no_title(issue_a, bibliotekar_user):
    """Create a DRAFT article without title."""
    article = ArticleFactory(
        issue=issue_a,
        title="",
        abstract="Apstrakt postoji.",
        status=ArticleStatus.DRAFT,
        pdf_status=PdfStatus.CLEAN,
        pdf_file="articles/pdfs/test.pdf",
        created_by=bibliotekar_user,
    )
    AuthorFactory(article=article, given_name="Marko", surname="Marković", order=1)
    return article


@pytest.fixture
def draft_article_no_abstract(issue_a, bibliotekar_user):
    """Create a DRAFT article without abstract."""
    article = ArticleFactory(
        issue=issue_a,
        title="Naslov postoji",
        abstract="",
        status=ArticleStatus.DRAFT,
        pdf_status=PdfStatus.CLEAN,
        pdf_file="articles/pdfs/test.pdf",
        created_by=bibliotekar_user,
    )
    AuthorFactory(article=article, given_name="Jovan", surname="Jovanović", order=1)
    return article


@pytest.fixture
def review_article(issue_a, bibliotekar_user):
    """Create a REVIEW status article."""
    article = ArticleFactory(
        issue=issue_a,
        title="Članak na pregledu",
        abstract="Apstrakt.",
        status=ArticleStatus.REVIEW,
        pdf_status=PdfStatus.CLEAN,
        pdf_file="articles/pdfs/test.pdf",
        created_by=bibliotekar_user,
    )
    AuthorFactory(article=article, given_name="Ivan", surname="Ivanović", order=1)
    return article


@pytest.fixture
def draft_article_incomplete(issue_a, bibliotekar_user):
    """Create a DRAFT article missing multiple fields (no authors, no PDF)."""
    return ArticleFactory(
        issue=issue_a,
        title="Nekompletni članak",
        abstract="Apstrakt postoji.",
        status=ArticleStatus.DRAFT,
        pdf_status=PdfStatus.NONE,
        created_by=bibliotekar_user,
    )


# =============================================================================
# 10.1-10.5: Service tests for submit_article_for_review
# =============================================================================


@pytest.mark.django_db
class TestSubmitArticleForReviewService:
    """Tests for submit_article_for_review service function."""

    def test_submit_valid_draft_article(
        self, draft_article_with_author_and_pdf, bibliotekar_user
    ):
        """10.1: Valid DRAFT article transitions to REVIEW (AC #4, #8)."""
        article = draft_article_with_author_and_pdf
        result = submit_article_for_review(article, bibliotekar_user)
        assert result.status == ArticleStatus.REVIEW
        assert result.submitted_by == bibliotekar_user
        assert result.submitted_at is not None

    def test_submit_persists_to_database(
        self, draft_article_with_author_and_pdf, bibliotekar_user
    ):
        """10.1: Submit persists status change to database (AC #8)."""
        article = draft_article_with_author_and_pdf
        submit_article_for_review(article, bibliotekar_user)
        article.refresh_from_db()
        assert article.status == ArticleStatus.REVIEW
        assert article.submitted_by == bibliotekar_user

    def test_submit_rejects_non_draft(self, review_article, bibliotekar_user):
        """10.2: Non-DRAFT article raises InvalidStatusTransition (AC #7)."""
        with pytest.raises(InvalidStatusTransition, match="Nacrt"):
            submit_article_for_review(review_article, bibliotekar_user)

    def test_submit_rejects_published_article(self, issue_a, bibliotekar_user):
        """10.2: PUBLISHED article raises InvalidStatusTransition (AC #7)."""
        article = ArticleFactory(
            issue=issue_a,
            status=ArticleStatus.PUBLISHED,
            pdf_status=PdfStatus.CLEAN,
        )
        AuthorFactory(article=article)
        with pytest.raises(InvalidStatusTransition, match="Nacrt"):
            submit_article_for_review(article, bibliotekar_user)

    def test_submit_rejects_no_authors(
        self, draft_article_no_authors, bibliotekar_user
    ):
        """10.3: Article without authors raises InvalidStatusTransition (AC #8)."""
        with pytest.raises(InvalidStatusTransition, match="autor"):
            submit_article_for_review(draft_article_no_authors, bibliotekar_user)

    def test_submit_rejects_no_pdf(self, draft_article_no_pdf, bibliotekar_user):
        """10.4: Article without clean PDF raises InvalidStatusTransition (AC #8)."""
        with pytest.raises(InvalidStatusTransition, match="PDF"):
            submit_article_for_review(draft_article_no_pdf, bibliotekar_user)

    def test_submit_rejects_empty_title(
        self, draft_article_no_title, bibliotekar_user
    ):
        """10.5: Article without title raises InvalidStatusTransition (AC #8)."""
        with pytest.raises(InvalidStatusTransition, match="Naslov"):
            submit_article_for_review(draft_article_no_title, bibliotekar_user)

    def test_submit_rejects_empty_abstract(
        self, draft_article_no_abstract, bibliotekar_user
    ):
        """10.5: Article without abstract raises InvalidStatusTransition (AC #8)."""
        with pytest.raises(InvalidStatusTransition, match="Apstrakt"):
            submit_article_for_review(draft_article_no_abstract, bibliotekar_user)

    def test_submit_rejects_scanning_pdf(self, issue_a, bibliotekar_user):
        """10.4: Article with SCANNING PDF raises InvalidStatusTransition (AC #8)."""
        article = ArticleFactory(
            issue=issue_a,
            title="Članak sa skeniranjem",
            abstract="Apstrakt.",
            status=ArticleStatus.DRAFT,
            pdf_status=PdfStatus.SCANNING,
        )
        AuthorFactory(article=article)
        with pytest.raises(InvalidStatusTransition, match="PDF"):
            submit_article_for_review(article, bibliotekar_user)

    def test_submit_rejects_whitespace_only_title(self, issue_a, bibliotekar_user):
        """10.5: Article with whitespace-only title raises InvalidStatusTransition."""
        article = ArticleFactory(
            issue=issue_a,
            title="   ",
            abstract="Apstrakt.",
            status=ArticleStatus.DRAFT,
            pdf_status=PdfStatus.CLEAN,
        )
        AuthorFactory(article=article)
        with pytest.raises(InvalidStatusTransition, match="Naslov"):
            submit_article_for_review(article, bibliotekar_user)


# =============================================================================
# Shared validation function tests
# =============================================================================


@pytest.mark.django_db
class TestValidateArticleForSubmit:
    """Tests for validate_article_for_submit shared validation function."""

    def test_valid_article_returns_empty_list(
        self, draft_article_with_author_and_pdf
    ):
        """Valid DRAFT article returns no errors."""
        errors = validate_article_for_submit(draft_article_with_author_and_pdf)
        assert errors == []

    def test_non_draft_returns_status_error(self, review_article):
        """Non-DRAFT article returns status error."""
        errors = validate_article_for_submit(review_article)
        assert any("Nacrt" in e for e in errors)

    def test_missing_authors_returns_error(self, draft_article_no_authors):
        """Article without authors returns author error."""
        errors = validate_article_for_submit(draft_article_no_authors)
        assert any("autor" in e.lower() for e in errors)

    def test_missing_pdf_returns_error(self, draft_article_no_pdf):
        """Article without clean PDF returns PDF error."""
        errors = validate_article_for_submit(draft_article_no_pdf)
        assert any("PDF" in e for e in errors)

    def test_multiple_errors_returned(self, draft_article_incomplete):
        """Article missing multiple fields returns multiple errors."""
        errors = validate_article_for_submit(draft_article_incomplete)
        assert len(errors) >= 2


# =============================================================================
# 10.6-10.7: View tests for article_submit_check
# =============================================================================


@pytest.mark.django_db
class TestArticleSubmitCheckView:
    """Tests for article_submit_check HTMX GET endpoint."""

    def test_submit_check_valid_article(
        self, client, bibliotekar_user, draft_article_with_author_and_pdf
    ):
        """10.6: Submit check for valid article returns is_ready=True (AC #2)."""
        client.force_login(bibliotekar_user)
        url = reverse(
            "articles:article-submit-check",
            kwargs={"pk": draft_article_with_author_and_pdf.pk},
        )
        response = client.get(url)
        assert response.status_code == 200
        content = response.content.decode()
        assert "Potvrda slanja" in content
        assert "Pošalji na pregled" in content

    def test_submit_check_invalid_article_missing_authors(
        self, client, bibliotekar_user, draft_article_no_authors
    ):
        """10.7: Submit check for article without authors returns errors (AC #3)."""
        client.force_login(bibliotekar_user)
        url = reverse(
            "articles:article-submit-check",
            kwargs={"pk": draft_article_no_authors.pk},
        )
        response = client.get(url)
        assert response.status_code == 200
        content = response.content.decode()
        assert "nije spreman" in content
        assert "autor" in content.lower()

    def test_submit_check_invalid_article_missing_pdf(
        self, client, bibliotekar_user, draft_article_no_pdf
    ):
        """10.7: Submit check for article without PDF returns errors (AC #3)."""
        client.force_login(bibliotekar_user)
        url = reverse(
            "articles:article-submit-check",
            kwargs={"pk": draft_article_no_pdf.pk},
        )
        response = client.get(url)
        assert response.status_code == 200
        content = response.content.decode()
        assert "PDF" in content

    def test_submit_check_incomplete_article_shows_multiple_errors(
        self, client, bibliotekar_user, draft_article_incomplete
    ):
        """10.7: Submit check for article missing multiple fields shows all errors."""
        client.force_login(bibliotekar_user)
        url = reverse(
            "articles:article-submit-check",
            kwargs={"pk": draft_article_incomplete.pk},
        )
        response = client.get(url)
        assert response.status_code == 200
        content = response.content.decode()
        assert "autor" in content.lower()
        assert "PDF" in content

    def test_submit_check_requires_login(self, client, draft_article_with_author_and_pdf):
        """10.10: Submit check requires authentication."""
        url = reverse(
            "articles:article-submit-check",
            kwargs={"pk": draft_article_with_author_and_pdf.pk},
        )
        response = client.get(url)
        assert response.status_code == 302
        assert "login" in response.url

    def test_submit_check_publisher_scoping(
        self, client, other_publisher_user, draft_article_with_author_and_pdf
    ):
        """10.10: Submit check respects publisher scoping (AC #6)."""
        client.force_login(other_publisher_user)
        url = reverse(
            "articles:article-submit-check",
            kwargs={"pk": draft_article_with_author_and_pdf.pk},
        )
        response = client.get(url)
        assert response.status_code == 403

    def test_submit_check_regular_user_denied(
        self, client, regular_user, draft_article_with_author_and_pdf
    ):
        """10.10: Regular user without role is denied access (AC #6)."""
        client.force_login(regular_user)
        url = reverse(
            "articles:article-submit-check",
            kwargs={"pk": draft_article_with_author_and_pdf.pk},
        )
        response = client.get(url)
        assert response.status_code == 403

    def test_submit_check_non_draft_shows_error(
        self, client, bibliotekar_user, review_article
    ):
        """10.7: Submit check for non-DRAFT article shows status error (AC #7)."""
        client.force_login(bibliotekar_user)
        url = reverse(
            "articles:article-submit-check",
            kwargs={"pk": review_article.pk},
        )
        response = client.get(url)
        assert response.status_code == 200
        content = response.content.decode()
        assert "nije spreman" in content
        assert "Nacrt" in content


# =============================================================================
# 10.8-10.9: View tests for article_submit_for_review
# =============================================================================


@pytest.mark.django_db
class TestArticleSubmitForReviewView:
    """Tests for article_submit_for_review POST endpoint."""

    def test_submit_success(
        self, client, bibliotekar_user, draft_article_with_author_and_pdf
    ):
        """10.8: Successful submit redirects to detail with success message (AC #4)."""
        client.force_login(bibliotekar_user)
        url = reverse(
            "articles:article-submit",
            kwargs={"pk": draft_article_with_author_and_pdf.pk},
        )
        response = client.post(url)
        assert response.status_code == 302
        assert reverse(
            "articles:detail",
            kwargs={"pk": draft_article_with_author_and_pdf.pk},
        ) in response.url
        draft_article_with_author_and_pdf.refresh_from_db()
        assert draft_article_with_author_and_pdf.status == ArticleStatus.REVIEW
        assert draft_article_with_author_and_pdf.submitted_by == bibliotekar_user
        assert draft_article_with_author_and_pdf.submitted_at is not None

    def test_submit_success_message(
        self, client, bibliotekar_user, draft_article_with_author_and_pdf
    ):
        """10.8: Successful submit shows success toast message (AC #4)."""
        client.force_login(bibliotekar_user)
        url = reverse(
            "articles:article-submit",
            kwargs={"pk": draft_article_with_author_and_pdf.pk},
        )
        response = client.post(url, follow=True)
        assert response.status_code == 200
        messages_list = list(response.context["messages"])
        assert len(messages_list) == 1
        assert "Članak poslat na pregled" in str(messages_list[0])

    def test_submit_rejects_non_draft(
        self, client, bibliotekar_user, review_article
    ):
        """10.9: Submit for non-DRAFT article shows error (AC #7)."""
        client.force_login(bibliotekar_user)
        url = reverse(
            "articles:article-submit",
            kwargs={"pk": review_article.pk},
        )
        response = client.post(url, follow=True)
        assert response.status_code == 200
        messages_list = list(response.context["messages"])
        assert len(messages_list) == 1
        assert "Nacrt" in str(messages_list[0])

    def test_submit_rejects_incomplete_article(
        self, client, bibliotekar_user, draft_article_no_authors
    ):
        """10.9: Submit for incomplete article shows error message."""
        client.force_login(bibliotekar_user)
        url = reverse(
            "articles:article-submit",
            kwargs={"pk": draft_article_no_authors.pk},
        )
        response = client.post(url, follow=True)
        messages_list = list(response.context["messages"])
        assert len(messages_list) == 1
        assert "autor" in str(messages_list[0]).lower()
        # Article should remain DRAFT
        draft_article_no_authors.refresh_from_db()
        assert draft_article_no_authors.status == ArticleStatus.DRAFT

    def test_submit_publisher_scoping(
        self, client, other_publisher_user, draft_article_with_author_and_pdf
    ):
        """10.10: Submit respects publisher scoping (AC #6)."""
        client.force_login(other_publisher_user)
        url = reverse(
            "articles:article-submit",
            kwargs={"pk": draft_article_with_author_and_pdf.pk},
        )
        response = client.post(url)
        assert response.status_code == 403

    def test_submit_requires_login(self, client, draft_article_with_author_and_pdf):
        """10.10: Submit requires authentication."""
        url = reverse(
            "articles:article-submit",
            kwargs={"pk": draft_article_with_author_and_pdf.pk},
        )
        response = client.post(url)
        assert response.status_code == 302
        assert "login" in response.url

    def test_submit_rejects_get_method(
        self, client, bibliotekar_user, draft_article_with_author_and_pdf
    ):
        """10.10: Submit endpoint rejects GET requests."""
        client.force_login(bibliotekar_user)
        url = reverse(
            "articles:article-submit",
            kwargs={"pk": draft_article_with_author_and_pdf.pk},
        )
        response = client.get(url)
        assert response.status_code == 405  # Method Not Allowed

    def test_submit_regular_user_denied(
        self, client, regular_user, draft_article_with_author_and_pdf
    ):
        """10.10: Regular user without role is denied submit (AC #6)."""
        client.force_login(regular_user)
        url = reverse(
            "articles:article-submit",
            kwargs={"pk": draft_article_with_author_and_pdf.pk},
        )
        response = client.post(url)
        assert response.status_code == 403

    def test_submit_urednik_can_submit(
        self, client, urednik_user, draft_article_with_author_and_pdf
    ):
        """10.10: Urednik can submit articles from own publisher."""
        client.force_login(urednik_user)
        url = reverse(
            "articles:article-submit",
            kwargs={"pk": draft_article_with_author_and_pdf.pk},
        )
        response = client.post(url)
        assert response.status_code == 302
        draft_article_with_author_and_pdf.refresh_from_db()
        assert draft_article_with_author_and_pdf.status == ArticleStatus.REVIEW

    def test_submit_admin_can_submit(
        self, client, admin_user, draft_article_with_author_and_pdf
    ):
        """10.10: Admin can submit any article."""
        client.force_login(admin_user)
        url = reverse(
            "articles:article-submit",
            kwargs={"pk": draft_article_with_author_and_pdf.pk},
        )
        response = client.post(url)
        assert response.status_code == 302
        draft_article_with_author_and_pdf.refresh_from_db()
        assert draft_article_with_author_and_pdf.status == ArticleStatus.REVIEW


# =============================================================================
# 10.11: Permission tests - non-DRAFT rejects submit
# =============================================================================


@pytest.mark.django_db
class TestSubmitPermissions:
    """Permission-specific tests for submit endpoints."""

    def test_non_draft_article_rejects_submit_via_url(
        self, client, bibliotekar_user, review_article
    ):
        """10.11: Direct URL submit for non-DRAFT article is rejected (AC #7)."""
        client.force_login(bibliotekar_user)
        url = reverse(
            "articles:article-submit",
            kwargs={"pk": review_article.pk},
        )
        response = client.post(url, follow=True)
        messages_list = list(response.context["messages"])
        assert any("Nacrt" in str(m) for m in messages_list)
        review_article.refresh_from_db()
        assert review_article.status == ArticleStatus.REVIEW  # Unchanged

    def test_published_article_rejects_submit(
        self, client, admin_user, issue_a
    ):
        """10.11: PUBLISHED article rejects submit (AC #7)."""
        article = ArticleFactory(
            issue=issue_a,
            status=ArticleStatus.PUBLISHED,
            pdf_status=PdfStatus.CLEAN,
        )
        AuthorFactory(article=article)
        client.force_login(admin_user)
        url = reverse(
            "articles:article-submit",
            kwargs={"pk": article.pk},
        )
        response = client.post(url, follow=True)
        messages_list = list(response.context["messages"])
        assert any("Nacrt" in str(m) for m in messages_list)

    def test_withdrawn_article_rejects_submit(
        self, client, admin_user, issue_a
    ):
        """10.11: WITHDRAWN article rejects submit."""
        article = ArticleFactory(
            issue=issue_a,
            status=ArticleStatus.WITHDRAWN,
            pdf_status=PdfStatus.CLEAN,
        )
        AuthorFactory(article=article)
        client.force_login(admin_user)
        url = reverse(
            "articles:article-submit",
            kwargs={"pk": article.pk},
        )
        response = client.post(url, follow=True)
        messages_list = list(response.context["messages"])
        assert any("Nacrt" in str(m) for m in messages_list)


# =============================================================================
# 10.12: Template tests - button visibility
# =============================================================================


@pytest.mark.django_db
class TestSubmitButtonVisibility:
    """Tests for submit button visibility in article_detail.html."""

    def test_submit_button_visible_for_draft(
        self, client, bibliotekar_user, draft_article_with_author_and_pdf
    ):
        """10.12: Submit button is visible for DRAFT articles (AC #1)."""
        client.force_login(bibliotekar_user)
        url = reverse(
            "articles:detail",
            kwargs={"pk": draft_article_with_author_and_pdf.pk},
        )
        response = client.get(url)
        content = response.content.decode()
        assert "Pošalji na pregled" in content

    def test_submit_button_hidden_for_review(
        self, client, bibliotekar_user, review_article
    ):
        """10.12: Submit button is NOT visible for REVIEW articles (AC #5)."""
        client.force_login(bibliotekar_user)
        url = reverse(
            "articles:detail",
            kwargs={"pk": review_article.pk},
        )
        response = client.get(url)
        content = response.content.decode()
        assert "Pošalji na pregled" not in content

    def test_edit_button_hidden_for_review(
        self, client, bibliotekar_user, review_article
    ):
        """10.12: Edit button is NOT visible for REVIEW articles (AC #5)."""
        client.force_login(bibliotekar_user)
        url = reverse(
            "articles:detail",
            kwargs={"pk": review_article.pk},
        )
        response = client.get(url)
        content = response.content.decode()
        # The "Izmeni" button should not appear
        assert 'Izmeni</a>' not in content

    def test_review_status_message_shown(
        self, client, bibliotekar_user, review_article
    ):
        """10.12: Review status message is displayed for REVIEW articles (AC #5)."""
        client.force_login(bibliotekar_user)
        url = reverse(
            "articles:detail",
            kwargs={"pk": review_article.pk},
        )
        response = client.get(url)
        content = response.content.decode()
        assert "Članak čeka odobrenje urednika" in content

    def test_review_status_message_not_shown_for_draft(
        self, client, bibliotekar_user, draft_article_with_author_and_pdf
    ):
        """10.12: Review status message is NOT shown for DRAFT articles."""
        client.force_login(bibliotekar_user)
        url = reverse(
            "articles:detail",
            kwargs={"pk": draft_article_with_author_and_pdf.pk},
        )
        response = client.get(url)
        content = response.content.decode()
        assert "Članak čeka odobrenje urednika" not in content

    def test_submit_button_hidden_for_published(
        self, client, admin_user, issue_a
    ):
        """10.12: Submit button is NOT visible for PUBLISHED articles."""
        article = ArticleFactory(
            issue=issue_a, status=ArticleStatus.PUBLISHED
        )
        client.force_login(admin_user)
        url = reverse("articles:detail", kwargs={"pk": article.pk})
        response = client.get(url)
        content = response.content.decode()
        assert "Pošalji na pregled" not in content


# =============================================================================
# 10.13: Integration tests - complete DRAFT -> REVIEW flow
# =============================================================================


@pytest.mark.django_db
class TestSubmitIntegrationFlow:
    """Integration tests for complete DRAFT -> REVIEW flow."""

    def test_complete_submit_flow(
        self, client, bibliotekar_user, draft_article_with_author_and_pdf
    ):
        """10.13: Complete flow: view detail -> check -> submit -> verify (AC #1-#5)."""
        article = draft_article_with_author_and_pdf

        # Step 1: View article detail - submit button visible
        detail_url = reverse("articles:detail", kwargs={"pk": article.pk})
        client.force_login(bibliotekar_user)
        response = client.get(detail_url)
        assert response.status_code == 200
        content = response.content.decode()
        assert "Pošalji na pregled" in content

        # Step 2: Check article readiness (HTMX GET)
        check_url = reverse(
            "articles:article-submit-check", kwargs={"pk": article.pk}
        )
        response = client.get(check_url)
        assert response.status_code == 200
        content = response.content.decode()
        assert "Potvrda slanja" in content

        # Step 3: Submit article (POST)
        submit_url = reverse(
            "articles:article-submit", kwargs={"pk": article.pk}
        )
        response = client.post(submit_url)
        assert response.status_code == 302

        # Step 4: Verify article is in REVIEW status
        article.refresh_from_db()
        assert article.status == ArticleStatus.REVIEW
        assert article.submitted_by == bibliotekar_user
        assert article.submitted_at is not None

        # Step 5: View detail again - no submit/edit buttons, review message shown
        response = client.get(detail_url)
        content = response.content.decode()
        assert "Članak čeka odobrenje urednika" in content
        assert "Pošalji na pregled" not in content

    def test_submit_flow_with_validation_failure(
        self, client, bibliotekar_user, draft_article_no_authors
    ):
        """10.13: Flow with validation failure keeps article in DRAFT."""
        article = draft_article_no_authors

        client.force_login(bibliotekar_user)

        # Step 1: Check article readiness - should show errors
        check_url = reverse(
            "articles:article-submit-check", kwargs={"pk": article.pk}
        )
        response = client.get(check_url)
        content = response.content.decode()
        assert "nije spreman" in content

        # Step 2: Try to submit anyway via direct POST
        submit_url = reverse(
            "articles:article-submit", kwargs={"pk": article.pk}
        )
        response = client.post(submit_url)
        assert response.status_code == 302

        # Step 3: Article should still be DRAFT
        article.refresh_from_db()
        assert article.status == ArticleStatus.DRAFT

    def test_double_submit_prevention(
        self, client, bibliotekar_user, draft_article_with_author_and_pdf
    ):
        """10.13: Second submit attempt after first succeeds is rejected."""
        article = draft_article_with_author_and_pdf
        client.force_login(bibliotekar_user)

        submit_url = reverse(
            "articles:article-submit", kwargs={"pk": article.pk}
        )

        # First submit - success
        response = client.post(submit_url)
        assert response.status_code == 302
        article.refresh_from_db()
        assert article.status == ArticleStatus.REVIEW

        # Second submit - should fail with error
        response = client.post(submit_url, follow=True)
        messages_list = list(response.context["messages"])
        assert any("Nacrt" in str(m) for m in messages_list)

    def test_review_article_not_editable(
        self, client, admin_user, review_article
    ):
        """10.13: REVIEW article cannot be edited via update view."""
        client.force_login(admin_user)
        url = reverse("articles:update", kwargs={"pk": review_article.pk})
        response = client.get(url)
        assert response.status_code == 404
