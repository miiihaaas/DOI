"""
Tests for Auto-Save Functionality.

Story 3.4 - Task 6: Comprehensive tests for auto-save HTMX endpoint,
partial field updates, publisher scoping, DRAFT-only restriction,
keywords JSON handling, and save indicator template responses.
"""

import json

import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.test import Client
from django.urls import reverse

from doi_portal.articles.models import Article, ArticleStatus
from doi_portal.issues.tests.factories import IssueFactory
from doi_portal.publications.tests.factories import (
    PublicationFactory,
    PublisherFactory,
)

from .factories import ArticleFactory

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
def bibliotekar_a(publisher_a):
    """Create a Bibliotekar user for publisher A."""
    group, _ = Group.objects.get_or_create(name="Bibliotekar")
    user = User.objects.create_user(
        email="biblio_autosave_a@example.com",
        password="testpass123",
    )
    user.groups.add(group)
    user.publisher = publisher_a
    user.save()
    return user


@pytest.fixture
def bibliotekar_b(publisher_b):
    """Create a Bibliotekar user for publisher B."""
    group, _ = Group.objects.get_or_create(name="Bibliotekar")
    user = User.objects.create_user(
        email="biblio_autosave_b@example.com",
        password="testpass123",
    )
    user.groups.add(group)
    user.publisher = publisher_b
    user.save()
    return user


@pytest.fixture
def admin_user():
    """Create an Administrator user."""
    group, _ = Group.objects.get_or_create(name="Administrator")
    user = User.objects.create_user(
        email="admin_autosave@example.com",
        password="testpass123",
    )
    user.groups.add(group)
    user.save()
    return user


@pytest.fixture
def draft_article_a(publisher_a):
    """Create a DRAFT article under publisher A."""
    publication = PublicationFactory(publisher=publisher_a)
    issue = IssueFactory(publication=publication)
    return ArticleFactory(
        issue=issue,
        status=ArticleStatus.DRAFT,
        title="Original naslov",
        abstract="Original apstrakt",
        keywords=["original"],
    )


@pytest.fixture
def review_article_a(publisher_a):
    """Create a REVIEW article under publisher A."""
    publication = PublicationFactory(publisher=publisher_a)
    issue = IssueFactory(publication=publication)
    return ArticleFactory(
        issue=issue,
        status=ArticleStatus.REVIEW,
    )


@pytest.fixture
def published_article_a(publisher_a):
    """Create a PUBLISHED article under publisher A."""
    publication = PublicationFactory(publisher=publisher_a)
    issue = IssueFactory(publication=publication)
    return ArticleFactory(
        issue=issue,
        status=ArticleStatus.PUBLISHED,
    )


@pytest.fixture
def draft_article_b(publisher_b):
    """Create a DRAFT article under publisher B."""
    publication = PublicationFactory(publisher=publisher_b)
    issue = IssueFactory(publication=publication)
    return ArticleFactory(
        issue=issue,
        status=ArticleStatus.DRAFT,
    )


# =============================================================================
# Task 6.1: View tests - autosave with valid data (partial update)
# =============================================================================


@pytest.mark.django_db
class TestArticleAutosaveValidData:
    """Tests for auto-save endpoint with valid partial data. AC: #1, #10."""

    def test_autosave_updates_title(self, client, bibliotekar_a, draft_article_a):
        """Auto-save updates title field only."""
        client.force_login(bibliotekar_a)
        url = reverse("articles:article-autosave", kwargs={"pk": draft_article_a.pk})
        response = client.post(
            url,
            {"title": "Novi naslov"},
            HTTP_HX_REQUEST="true",
        )
        assert response.status_code == 200
        draft_article_a.refresh_from_db()
        assert draft_article_a.title == "Novi naslov"

    def test_autosave_updates_abstract(self, client, bibliotekar_a, draft_article_a):
        """Auto-save updates abstract field only."""
        client.force_login(bibliotekar_a)
        url = reverse("articles:article-autosave", kwargs={"pk": draft_article_a.pk})
        response = client.post(
            url,
            {"abstract": "Novi apstrakt"},
            HTTP_HX_REQUEST="true",
        )
        assert response.status_code == 200
        draft_article_a.refresh_from_db()
        assert draft_article_a.abstract == "Novi apstrakt"

    def test_autosave_partial_fields_preserves_unchanged(
        self, client, bibliotekar_a, draft_article_a,
    ):
        """Auto-save only modifies sent fields, leaves others unchanged. AC: #10."""
        client.force_login(bibliotekar_a)
        original_title = draft_article_a.title
        url = reverse("articles:article-autosave", kwargs={"pk": draft_article_a.pk})
        response = client.post(
            url,
            {"abstract": "Samo apstrakt promenjen"},
            HTTP_HX_REQUEST="true",
        )
        assert response.status_code == 200
        draft_article_a.refresh_from_db()
        assert draft_article_a.abstract == "Samo apstrakt promenjen"
        assert draft_article_a.title == original_title  # Unchanged

    def test_autosave_updates_multiple_fields(
        self, client, bibliotekar_a, draft_article_a,
    ):
        """Auto-save can update multiple fields at once. AC: #8."""
        client.force_login(bibliotekar_a)
        url = reverse("articles:article-autosave", kwargs={"pk": draft_article_a.pk})
        response = client.post(
            url,
            {
                "title": "Ažurirani naslov",
                "subtitle": "Novi podnaslov",
                "first_page": "10",
                "last_page": "20",
            },
            HTTP_HX_REQUEST="true",
        )
        assert response.status_code == 200
        draft_article_a.refresh_from_db()
        assert draft_article_a.title == "Ažurirani naslov"
        assert draft_article_a.subtitle == "Novi podnaslov"
        assert draft_article_a.first_page == "10"
        assert draft_article_a.last_page == "20"

    def test_autosave_updates_doi_suffix(self, client, bibliotekar_a, draft_article_a):
        """Auto-save updates doi_suffix field."""
        client.force_login(bibliotekar_a)
        url = reverse("articles:article-autosave", kwargs={"pk": draft_article_a.pk})
        response = client.post(
            url,
            {"doi_suffix": "new.suffix.001"},
            HTTP_HX_REQUEST="true",
        )
        assert response.status_code == 200
        draft_article_a.refresh_from_db()
        assert draft_article_a.doi_suffix == "new.suffix.001"

    def test_autosave_updates_language(self, client, bibliotekar_a, draft_article_a):
        """Auto-save updates language field."""
        client.force_login(bibliotekar_a)
        url = reverse("articles:article-autosave", kwargs={"pk": draft_article_a.pk})
        response = client.post(
            url,
            {"language": "en"},
            HTTP_HX_REQUEST="true",
        )
        assert response.status_code == 200
        draft_article_a.refresh_from_db()
        assert draft_article_a.language == "en"

    def test_autosave_updates_publication_type(
        self, client, bibliotekar_a, draft_article_a,
    ):
        """Auto-save updates publication_type field."""
        client.force_login(bibliotekar_a)
        url = reverse("articles:article-autosave", kwargs={"pk": draft_article_a.pk})
        response = client.post(
            url,
            {"publication_type": "abstract_only"},
            HTTP_HX_REQUEST="true",
        )
        assert response.status_code == 200
        draft_article_a.refresh_from_db()
        assert draft_article_a.publication_type == "abstract_only"

    def test_autosave_updates_license_fields(
        self, client, bibliotekar_a, draft_article_a,
    ):
        """Auto-save updates license URL and applies_to fields."""
        client.force_login(bibliotekar_a)
        url = reverse("articles:article-autosave", kwargs={"pk": draft_article_a.pk})
        response = client.post(
            url,
            {
                "license_url": "https://creativecommons.org/licenses/by/4.0/",
                "license_applies_to": "vor",
            },
            HTTP_HX_REQUEST="true",
        )
        assert response.status_code == 200
        draft_article_a.refresh_from_db()
        assert draft_article_a.license_url == "https://creativecommons.org/licenses/by/4.0/"
        assert draft_article_a.license_applies_to == "vor"

    def test_autosave_updates_free_to_read_checkbox(
        self, client, bibliotekar_a, draft_article_a,
    ):
        """Auto-save handles boolean free_to_read checkbox."""
        client.force_login(bibliotekar_a)
        url = reverse("articles:article-autosave", kwargs={"pk": draft_article_a.pk})
        response = client.post(
            url,
            {"free_to_read": "on", "title": draft_article_a.title},
            HTTP_HX_REQUEST="true",
        )
        assert response.status_code == 200
        draft_article_a.refresh_from_db()
        assert draft_article_a.free_to_read is True

    def test_autosave_unchecked_free_to_read(
        self, client, bibliotekar_a, draft_article_a,
    ):
        """Auto-save handles unchecked free_to_read (checkbox not in POST)."""
        # First set it to True
        draft_article_a.free_to_read = True
        draft_article_a.save(update_fields=["free_to_read"])

        client.force_login(bibliotekar_a)
        url = reverse("articles:article-autosave", kwargs={"pk": draft_article_a.pk})
        # POST with another field but WITHOUT free_to_read = checkbox unchecked
        response = client.post(
            url,
            {"title": "Nešto"},
            HTTP_HX_REQUEST="true",
        )
        assert response.status_code == 200
        draft_article_a.refresh_from_db()
        assert draft_article_a.free_to_read is False

    def test_autosave_updates_free_to_read_start_date(
        self, client, bibliotekar_a, draft_article_a,
    ):
        """Auto-save handles date field for free_to_read_start_date."""
        client.force_login(bibliotekar_a)
        url = reverse("articles:article-autosave", kwargs={"pk": draft_article_a.pk})
        response = client.post(
            url,
            {"free_to_read_start_date": "2026-06-01"},
            HTTP_HX_REQUEST="true",
        )
        assert response.status_code == 200
        draft_article_a.refresh_from_db()
        assert str(draft_article_a.free_to_read_start_date) == "2026-06-01"

    def test_autosave_clears_date_with_empty_string(
        self, client, bibliotekar_a, draft_article_a,
    ):
        """Auto-save clears date field when empty string sent."""
        from datetime import date

        draft_article_a.free_to_read_start_date = date(2026, 1, 1)
        draft_article_a.save(update_fields=["free_to_read_start_date"])

        client.force_login(bibliotekar_a)
        url = reverse("articles:article-autosave", kwargs={"pk": draft_article_a.pk})
        response = client.post(
            url,
            {"free_to_read_start_date": ""},
            HTTP_HX_REQUEST="true",
        )
        assert response.status_code == 200
        draft_article_a.refresh_from_db()
        assert draft_article_a.free_to_read_start_date is None

    def test_autosave_returns_saved_status(
        self, client, bibliotekar_a, draft_article_a,
    ):
        """Auto-save returns HTML with 'saved' status indicator. AC: #3."""
        client.force_login(bibliotekar_a)
        url = reverse("articles:article-autosave", kwargs={"pk": draft_article_a.pk})
        response = client.post(
            url,
            {"title": "Test save"},
            HTTP_HX_REQUEST="true",
        )
        assert response.status_code == 200
        content = response.content.decode()
        assert "save-indicator" in content
        assert "bg-success" in content

    def test_autosave_updates_updated_at_timestamp(
        self, client, bibliotekar_a, draft_article_a,
    ):
        """Auto-save updates updated_at timestamp. AC: #10."""
        import time

        original_updated_at = draft_article_a.updated_at
        # Small delay to ensure timestamp difference is measurable
        time.sleep(0.01)
        client.force_login(bibliotekar_a)
        url = reverse("articles:article-autosave", kwargs={"pk": draft_article_a.pk})
        response = client.post(
            url,
            {"title": "Timestamp test"},
            HTTP_HX_REQUEST="true",
        )
        assert response.status_code == 200
        draft_article_a.refresh_from_db()
        assert draft_article_a.updated_at > original_updated_at


# =============================================================================
# Task 6.2: View tests - autosave with invalid data (partial save of valid fields)
# =============================================================================


@pytest.mark.django_db
class TestArticleAutosaveInvalidData:
    """Tests for auto-save with invalid/mixed data. AC: #7."""

    def test_autosave_invalid_date_format_returns_partial_error(
        self, client, bibliotekar_a, draft_article_a,
    ):
        """Invalid date format causes partial error, valid fields still saved."""
        client.force_login(bibliotekar_a)
        url = reverse("articles:article-autosave", kwargs={"pk": draft_article_a.pk})
        response = client.post(
            url,
            {
                "title": "Validan naslov",
                "free_to_read_start_date": "not-a-date",
            },
            HTTP_HX_REQUEST="true",
        )
        assert response.status_code == 200
        content = response.content.decode()
        assert "bg-warning" in content  # partial_error status
        draft_article_a.refresh_from_db()
        assert draft_article_a.title == "Validan naslov"  # Valid field saved

    def test_autosave_invalid_url_returns_partial_error(
        self, client, bibliotekar_a, draft_article_a,
    ):
        """Invalid license URL causes partial error, valid fields still saved."""
        client.force_login(bibliotekar_a)
        url = reverse("articles:article-autosave", kwargs={"pk": draft_article_a.pk})
        response = client.post(
            url,
            {
                "title": "Naslov sa URL greškom",
                "license_url": "not-a-valid-url",
            },
            HTTP_HX_REQUEST="true",
        )
        assert response.status_code == 200
        content = response.content.decode()
        assert "bg-warning" in content  # partial_error status
        draft_article_a.refresh_from_db()
        assert draft_article_a.title == "Naslov sa URL greškom"  # Valid field saved
        assert draft_article_a.license_url != "not-a-valid-url"  # Invalid URL NOT saved

    def test_autosave_valid_url_saves_successfully(
        self, client, bibliotekar_a, draft_article_a,
    ):
        """Valid license URL is saved without errors."""
        client.force_login(bibliotekar_a)
        url = reverse("articles:article-autosave", kwargs={"pk": draft_article_a.pk})
        response = client.post(
            url,
            {
                "license_url": "https://creativecommons.org/licenses/by/4.0/",
            },
            HTTP_HX_REQUEST="true",
        )
        assert response.status_code == 200
        content = response.content.decode()
        assert "bg-success" in content  # saved status
        draft_article_a.refresh_from_db()
        assert draft_article_a.license_url == "https://creativecommons.org/licenses/by/4.0/"

    def test_autosave_no_fields_submitted(
        self, client, bibliotekar_a, draft_article_a,
    ):
        """Auto-save with only CSRF token (no real fields) returns saved status."""
        client.force_login(bibliotekar_a)
        url = reverse("articles:article-autosave", kwargs={"pk": draft_article_a.pk})
        response = client.post(
            url,
            {},
            HTTP_HX_REQUEST="true",
        )
        assert response.status_code == 200


# =============================================================================
# Task 6.3: View tests - autosave rejects non-DRAFT articles
# =============================================================================


@pytest.mark.django_db
class TestArticleAutosaveNonDraft:
    """Tests for auto-save rejection of non-DRAFT articles. AC: #1, #7."""

    def test_autosave_rejects_review_article(
        self, client, bibliotekar_a, review_article_a,
    ):
        """Auto-save is rejected for REVIEW status articles."""
        client.force_login(bibliotekar_a)
        url = reverse("articles:article-autosave", kwargs={"pk": review_article_a.pk})
        response = client.post(
            url,
            {"title": "Pokušaj"},
            HTTP_HX_REQUEST="true",
        )
        assert response.status_code == 200
        content = response.content.decode()
        assert "bg-danger" in content  # error status
        assert "Nacrt" in content  # Status restriction message

    def test_autosave_rejects_published_article(
        self, client, bibliotekar_a, published_article_a,
    ):
        """Auto-save is rejected for PUBLISHED status articles."""
        client.force_login(bibliotekar_a)
        url = reverse("articles:article-autosave", kwargs={"pk": published_article_a.pk})
        response = client.post(
            url,
            {"title": "Pokušaj"},
            HTTP_HX_REQUEST="true",
        )
        assert response.status_code == 200
        content = response.content.decode()
        assert "bg-danger" in content

    def test_autosave_does_not_modify_non_draft_article(
        self, client, bibliotekar_a, review_article_a,
    ):
        """Auto-save does not change data on non-DRAFT articles."""
        original_title = review_article_a.title
        client.force_login(bibliotekar_a)
        url = reverse("articles:article-autosave", kwargs={"pk": review_article_a.pk})
        client.post(
            url,
            {"title": "Changed"},
            HTTP_HX_REQUEST="true",
        )
        review_article_a.refresh_from_db()
        assert review_article_a.title == original_title


# =============================================================================
# Task 6.4: Permission tests - publisher scoping for auto-save endpoint
# =============================================================================


@pytest.mark.django_db
class TestArticleAutosavePermissions:
    """Tests for publisher-scoped permissions on auto-save endpoint. AC: #10."""

    def test_bibliotekar_can_autosave_own_publisher(
        self, client, bibliotekar_a, draft_article_a,
    ):
        """Bibliotekar can auto-save own publisher's article."""
        client.force_login(bibliotekar_a)
        url = reverse("articles:article-autosave", kwargs={"pk": draft_article_a.pk})
        response = client.post(
            url,
            {"title": "Moja promena"},
            HTTP_HX_REQUEST="true",
        )
        assert response.status_code == 200
        draft_article_a.refresh_from_db()
        assert draft_article_a.title == "Moja promena"

    def test_bibliotekar_cannot_autosave_other_publisher(
        self, client, bibliotekar_b, draft_article_a,
    ):
        """Bibliotekar cannot auto-save other publisher's article."""
        client.force_login(bibliotekar_b)
        url = reverse("articles:article-autosave", kwargs={"pk": draft_article_a.pk})
        response = client.post(
            url,
            {"title": "Hack attempt"},
            HTTP_HX_REQUEST="true",
        )
        assert response.status_code == 403

    def test_admin_can_autosave_any_publisher(
        self, client, admin_user, draft_article_a,
    ):
        """Administrator can auto-save any article."""
        client.force_login(admin_user)
        url = reverse("articles:article-autosave", kwargs={"pk": draft_article_a.pk})
        response = client.post(
            url,
            {"title": "Admin promena"},
            HTTP_HX_REQUEST="true",
        )
        assert response.status_code == 200
        draft_article_a.refresh_from_db()
        assert draft_article_a.title == "Admin promena"

    def test_autosave_requires_login(self, client, draft_article_a):
        """Auto-save endpoint requires authentication."""
        url = reverse("articles:article-autosave", kwargs={"pk": draft_article_a.pk})
        response = client.post(url, {"title": "Anon"})
        assert response.status_code == 302  # Redirect to login

    def test_autosave_requires_post(self, client, bibliotekar_a, draft_article_a):
        """Auto-save endpoint only accepts POST requests."""
        client.force_login(bibliotekar_a)
        url = reverse("articles:article-autosave", kwargs={"pk": draft_article_a.pk})
        response = client.get(url)
        assert response.status_code == 405  # Method Not Allowed


# =============================================================================
# Task 6.5: View tests - keywords JSON parsing
# =============================================================================


@pytest.mark.django_db
class TestArticleAutosaveKeywords:
    """Tests for auto-save keywords JSON field handling. AC: #1."""

    def test_autosave_keywords_valid_json(
        self, client, bibliotekar_a, draft_article_a,
    ):
        """Auto-save handles valid keywords JSON array."""
        client.force_login(bibliotekar_a)
        url = reverse("articles:article-autosave", kwargs={"pk": draft_article_a.pk})
        response = client.post(
            url,
            {"keywords": json.dumps(["django", "python", "doi"])},
            HTTP_HX_REQUEST="true",
        )
        assert response.status_code == 200
        draft_article_a.refresh_from_db()
        assert draft_article_a.keywords == ["django", "python", "doi"]

    def test_autosave_keywords_empty_array(
        self, client, bibliotekar_a, draft_article_a,
    ):
        """Auto-save handles empty keywords array."""
        client.force_login(bibliotekar_a)
        url = reverse("articles:article-autosave", kwargs={"pk": draft_article_a.pk})
        response = client.post(
            url,
            {"keywords": "[]"},
            HTTP_HX_REQUEST="true",
        )
        assert response.status_code == 200
        draft_article_a.refresh_from_db()
        assert draft_article_a.keywords == []

    def test_autosave_keywords_empty_string(
        self, client, bibliotekar_a, draft_article_a,
    ):
        """Auto-save handles empty keywords string (clears keywords)."""
        client.force_login(bibliotekar_a)
        url = reverse("articles:article-autosave", kwargs={"pk": draft_article_a.pk})
        response = client.post(
            url,
            {"keywords": ""},
            HTTP_HX_REQUEST="true",
        )
        assert response.status_code == 200
        draft_article_a.refresh_from_db()
        assert draft_article_a.keywords == []

    def test_autosave_keywords_invalid_json_ignored(
        self, client, bibliotekar_a, draft_article_a,
    ):
        """Auto-save ignores invalid keywords JSON, keeps existing."""
        original_keywords = draft_article_a.keywords
        client.force_login(bibliotekar_a)
        url = reverse("articles:article-autosave", kwargs={"pk": draft_article_a.pk})
        response = client.post(
            url,
            {"keywords": "not valid json ["},
            HTTP_HX_REQUEST="true",
        )
        assert response.status_code == 200
        draft_article_a.refresh_from_db()
        assert draft_article_a.keywords == original_keywords

    def test_autosave_keywords_strips_whitespace(
        self, client, bibliotekar_a, draft_article_a,
    ):
        """Auto-save strips whitespace from keywords."""
        client.force_login(bibliotekar_a)
        url = reverse("articles:article-autosave", kwargs={"pk": draft_article_a.pk})
        response = client.post(
            url,
            {"keywords": json.dumps(["  django  ", " python ", ""])},
            HTTP_HX_REQUEST="true",
        )
        assert response.status_code == 200
        draft_article_a.refresh_from_db()
        assert draft_article_a.keywords == ["django", "python"]


# =============================================================================
# Task 6.6: View tests - HTMX header check
# =============================================================================


@pytest.mark.django_db
class TestArticleAutosaveHtmxHeaders:
    """Tests for HTMX header handling on auto-save endpoint. AC: #2."""

    def test_autosave_works_with_hx_request_header(
        self, client, bibliotekar_a, draft_article_a,
    ):
        """Auto-save works when HX-Request header is present."""
        client.force_login(bibliotekar_a)
        url = reverse("articles:article-autosave", kwargs={"pk": draft_article_a.pk})
        response = client.post(
            url,
            {"title": "HTMX request"},
            HTTP_HX_REQUEST="true",
        )
        assert response.status_code == 200
        assert "save-indicator" in response.content.decode()

    def test_autosave_works_without_hx_request_header(
        self, client, bibliotekar_a, draft_article_a,
    ):
        """Auto-save works even without HX-Request header (graceful)."""
        client.force_login(bibliotekar_a)
        url = reverse("articles:article-autosave", kwargs={"pk": draft_article_a.pk})
        response = client.post(
            url,
            {"title": "Non-HTMX request"},
        )
        assert response.status_code == 200


# =============================================================================
# Task 6.7: Template tests - save indicator response content
# =============================================================================


@pytest.mark.django_db
class TestSaveIndicatorContent:
    """Tests for save indicator HTML response content. AC: #2, #3, #4, #7."""

    def test_saved_status_contains_checkmark(
        self, client, bibliotekar_a, draft_article_a,
    ):
        """Saved status response contains checkmark icon."""
        client.force_login(bibliotekar_a)
        url = reverse("articles:article-autosave", kwargs={"pk": draft_article_a.pk})
        response = client.post(
            url,
            {"title": "Indicator test"},
            HTTP_HX_REQUEST="true",
        )
        content = response.content.decode()
        assert "bi-check-lg" in content
        assert "bg-success" in content

    def test_partial_error_status_shows_warning(
        self, client, bibliotekar_a, draft_article_a,
    ):
        """Partial error status shows warning badge with error message. AC: #7."""
        client.force_login(bibliotekar_a)
        url = reverse("articles:article-autosave", kwargs={"pk": draft_article_a.pk})
        response = client.post(
            url,
            {
                "title": "Valid",
                "free_to_read_start_date": "invalid-date",
            },
            HTTP_HX_REQUEST="true",
        )
        content = response.content.decode()
        assert "bg-warning" in content
        assert "greške" in content.lower() or "greš" in content

    def test_error_status_for_non_draft(
        self, client, bibliotekar_a, review_article_a,
    ):
        """Error status for non-DRAFT article shows danger badge."""
        client.force_login(bibliotekar_a)
        url = reverse("articles:article-autosave", kwargs={"pk": review_article_a.pk})
        response = client.post(
            url,
            {"title": "Test"},
            HTTP_HX_REQUEST="true",
        )
        content = response.content.decode()
        assert "bg-danger" in content
        assert "Nacrt" in content

    def test_save_indicator_has_correct_id(
        self, client, bibliotekar_a, draft_article_a,
    ):
        """Save indicator HTML has correct id for HTMX targeting."""
        client.force_login(bibliotekar_a)
        url = reverse("articles:article-autosave", kwargs={"pk": draft_article_a.pk})
        response = client.post(
            url,
            {"title": "ID test"},
            HTTP_HX_REQUEST="true",
        )
        content = response.content.decode()
        assert 'id="save-indicator"' in content


# =============================================================================
# URL routing tests
# =============================================================================


@pytest.mark.django_db
class TestAutosaveUrls:
    """Tests for auto-save URL routing."""

    def test_autosave_url_resolves(self):
        """Auto-save URL resolves correctly."""
        url = reverse("articles:article-autosave", kwargs={"pk": 1})
        assert "/1/autosave/" in url

    def test_autosave_url_uses_correct_name(self):
        """Auto-save URL uses 'article-autosave' name."""
        url = reverse("articles:article-autosave", kwargs={"pk": 42})
        assert url is not None


# =============================================================================
# Audit log tests for auto-save
# =============================================================================


@pytest.mark.django_db
class TestAutosaveAuditLog:
    """Tests for auditlog integration with auto-save. AC: #10."""

    def test_autosave_creates_audit_log_entry(
        self, client, bibliotekar_a, draft_article_a,
    ):
        """Auto-save creates auditlog entry for changes."""
        from auditlog.models import LogEntry

        client.force_login(bibliotekar_a)
        url = reverse("articles:article-autosave", kwargs={"pk": draft_article_a.pk})
        client.post(
            url,
            {"title": "Audit test naslov"},
            HTTP_HX_REQUEST="true",
        )

        update_logs = LogEntry.objects.filter(
            object_pk=str(draft_article_a.pk),
            action=LogEntry.Action.UPDATE,
        )
        assert update_logs.exists()


# =============================================================================
# AC #6: Previously saved data loaded on edit page
# =============================================================================


@pytest.mark.django_db
class TestAutosaveDataPersistence:
    """Tests for data persistence across page loads. AC: #6."""

    def test_autosaved_data_persists_on_reload(
        self, client, bibliotekar_a, draft_article_a,
    ):
        """Auto-saved data is loaded when page is reopened."""
        client.force_login(bibliotekar_a)
        # Auto-save some data
        url = reverse("articles:article-autosave", kwargs={"pk": draft_article_a.pk})
        client.post(
            url,
            {"title": "Persistentni naslov", "abstract": "Persistentni apstrakt"},
            HTTP_HX_REQUEST="true",
        )

        # Reload edit page
        edit_url = reverse("articles:update", kwargs={"pk": draft_article_a.pk})
        response = client.get(edit_url)
        assert response.status_code == 200
        content = response.content.decode()
        assert "Persistentni naslov" in content
        assert "Persistentni apstrakt" in content
