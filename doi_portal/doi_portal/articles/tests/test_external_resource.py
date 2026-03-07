"""
Tests for Story 3-1a: External Landing Page and PDF URL support.

Tests cover:
- Model fields: default values, field types
- Form validation: switch on/off + URL presence
- XML generation: conditional resource URL
- Portal landing page: external link display
"""

import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.contrib.sites.models import Site
from django.urls import reverse
from django.utils import timezone

from doi_portal.articles.forms import ArticleForm
from doi_portal.articles.models import Article, ArticleStatus
from doi_portal.core.models import SiteSettings
from doi_portal.crossref.services import CrossrefService
from doi_portal.issues.models import IssueStatus
from doi_portal.issues.tests.factories import IssueFactory
from doi_portal.publications.tests.factories import (
    JournalFactory,
    PublisherFactory,
)

from .factories import ArticleFactory, AuthorFactory

User = get_user_model()


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def admin_user(db):
    """Create an admin user."""
    user = User.objects.create_user(
        email="admin-ext@test.com", password="testpass123"
    )
    group, _ = Group.objects.get_or_create(name="Administrator")
    user.groups.add(group)
    return user


@pytest.fixture
def publisher(db):
    """Create test publisher."""
    return PublisherFactory(name="Test Izdavač", doi_prefix="10.12345")


@pytest.fixture
def journal(publisher):
    """Create test journal publication."""
    return JournalFactory(publisher=publisher)


@pytest.fixture
def issue(journal):
    """Create test issue."""
    return IssueFactory(
        publication=journal,
        volume="1",
        issue_number="1",
        status=IssueStatus.PUBLISHED,
    )


@pytest.fixture
def site(db):
    """Set up Django Site for tests."""
    site = Site.objects.get_current()
    site.domain = "testserver.example.com"
    site.name = "Test Server"
    site.save()
    return site


@pytest.fixture
def site_settings(db):
    """Create SiteSettings with test depositor data."""
    return SiteSettings.objects.create(
        depositor_name="Test Depositor",
        depositor_email="test@example.com",
    )


def _base_form_data(issue, **overrides):
    """Return base form data dict for ArticleForm."""
    data = {
        "issue": issue.pk,
        "title": "Test Article",
        "doi_suffix": "test.ext.001",
        "subtitle": "",
        "abstract": "",
        "keywords": "[]",
        "first_page": "",
        "last_page": "",
        "article_number": "",
        "language": "sr",
        "publication_type": "full_text",
        "license_url": "",
        "license_applies_to": "",
        "free_to_read_start_date": "",
        "use_external_resource": False,
        "external_landing_url": "",
        "external_pdf_url": "",
    }
    data.update(overrides)
    return data


# =============================================================================
# Task 6.1: Model Tests - default values
# =============================================================================


@pytest.mark.django_db
class TestExternalResourceModelFields:
    """Test new external resource fields on Article model."""

    def test_use_external_resource_default_false(self):
        """6.1: use_external_resource defaults to False."""
        article = ArticleFactory()
        assert article.use_external_resource is False

    def test_external_landing_url_default_empty(self):
        """6.1: external_landing_url defaults to empty string."""
        article = ArticleFactory()
        assert article.external_landing_url == ""

    def test_external_pdf_url_default_empty(self):
        """6.1: external_pdf_url defaults to empty string."""
        article = ArticleFactory()
        assert article.external_pdf_url == ""

    def test_can_set_external_resource_fields(self):
        """6.1: External resource fields can be set and saved."""
        article = ArticleFactory(
            use_external_resource=True,
            external_landing_url="https://example.com/article/1",
            external_pdf_url="https://example.com/article/1.pdf",
        )
        article.refresh_from_db()
        assert article.use_external_resource is True
        assert article.external_landing_url == "https://example.com/article/1"
        assert article.external_pdf_url == "https://example.com/article/1.pdf"

    def test_external_landing_url_max_length(self):
        """6.1: external_landing_url has max_length=500."""
        field = Article._meta.get_field("external_landing_url")
        assert field.max_length == 500

    def test_external_pdf_url_max_length(self):
        """6.1: external_pdf_url has max_length=500."""
        field = Article._meta.get_field("external_pdf_url")
        assert field.max_length == 500


# =============================================================================
# Task 6.2, 6.3: Form Tests - validation
# =============================================================================


@pytest.mark.django_db
class TestExternalResourceFormValidation:
    """Test ArticleForm validation for external resource fields."""

    def test_switch_off_empty_urls_valid(self, admin_user, issue):
        """6.3: Switch off + empty URLs = form is valid."""
        data = _base_form_data(issue, use_external_resource=False)
        form = ArticleForm(data=data, user=admin_user)
        assert form.is_valid(), form.errors

    def test_switch_on_with_landing_url_valid(self, admin_user, issue):
        """6.2: Switch on + landing URL filled = form is valid."""
        data = _base_form_data(
            issue,
            use_external_resource=True,
            external_landing_url="https://casopis.example.com/article/1",
        )
        form = ArticleForm(data=data, user=admin_user)
        assert form.is_valid(), form.errors

    def test_switch_on_empty_landing_url_invalid(self, admin_user, issue):
        """6.2: Switch on + empty landing URL = validation error."""
        data = _base_form_data(
            issue,
            use_external_resource=True,
            external_landing_url="",
        )
        form = ArticleForm(data=data, user=admin_user)
        assert not form.is_valid()
        assert "external_landing_url" in form.errors

    def test_switch_on_with_both_urls_valid(self, admin_user, issue):
        """6.2: Switch on + both URLs filled = form is valid."""
        data = _base_form_data(
            issue,
            use_external_resource=True,
            external_landing_url="https://casopis.example.com/article/1",
            external_pdf_url="https://casopis.example.com/article/1.pdf",
        )
        form = ArticleForm(data=data, user=admin_user)
        assert form.is_valid(), form.errors

    def test_switch_off_with_urls_filled_valid(self, admin_user, issue):
        """6.3: Switch off + URLs filled = form is still valid (fields ignored)."""
        data = _base_form_data(
            issue,
            use_external_resource=False,
            external_landing_url="https://casopis.example.com/article/1",
        )
        form = ArticleForm(data=data, user=admin_user)
        assert form.is_valid(), form.errors

    def test_invalid_url_format_rejected(self, admin_user, issue):
        """6.2: Invalid URL format is rejected by URLField validation."""
        data = _base_form_data(
            issue,
            use_external_resource=True,
            external_landing_url="not-a-valid-url",
        )
        form = ArticleForm(data=data, user=admin_user)
        assert not form.is_valid()
        assert "external_landing_url" in form.errors


# =============================================================================
# Task 6.4, 6.5: XML Generation Tests
# =============================================================================


@pytest.mark.django_db
class TestExternalResourceXMLGeneration:
    """Test XML generation with external resource URLs."""

    def test_external_url_used_when_switch_on(self, site, site_settings, issue):
        """6.4: When switch is on, XML <resource> uses external URL."""
        article = ArticleFactory(
            issue=issue,
            status=ArticleStatus.PUBLISHED,
            use_external_resource=True,
            external_landing_url="https://casopis.example.com/article/1",
        )
        AuthorFactory(article=article, sequence="first")

        service = CrossrefService()
        xml = service.generate_xml(issue)

        assert "https://casopis.example.com/article/1" in xml
        assert f"/articles/{article.pk}/" not in xml

    def test_portal_url_used_when_switch_off(self, site, site_settings, issue):
        """6.5: When switch is off, XML <resource> uses portal URL."""
        article = ArticleFactory(
            issue=issue,
            status=ArticleStatus.PUBLISHED,
            use_external_resource=False,
        )
        AuthorFactory(article=article, sequence="first")

        service = CrossrefService()
        xml = service.generate_xml(issue)

        assert f"/articles/{article.pk}/" in xml

    def test_portal_url_used_when_switch_on_but_no_url(
        self, site, site_settings, issue
    ):
        """6.5: When switch on but external URL empty, falls back to portal URL."""
        article = ArticleFactory(
            issue=issue,
            status=ArticleStatus.PUBLISHED,
            use_external_resource=True,
            external_landing_url="",
        )
        AuthorFactory(article=article, sequence="first")

        service = CrossrefService()
        xml = service.generate_xml(issue)

        assert f"/articles/{article.pk}/" in xml

    def test_external_url_with_ampersand_is_xml_escaped(self, site, site_settings, issue):
        """6.4: External URL with & is properly XML-escaped to &amp; in generated XML."""
        article = ArticleFactory(
            issue=issue,
            status=ArticleStatus.PUBLISHED,
            use_external_resource=True,
            external_landing_url="https://example.com/article?id=1&lang=sr",
        )
        AuthorFactory(article=article, sequence="first")

        service = CrossrefService()
        xml = service.generate_xml(issue)

        assert "https://example.com/article?id=1&amp;lang=sr" in xml
        # Ensure the raw unescaped ampersand is NOT present in the resource tag
        assert "https://example.com/article?id=1&lang=sr" not in xml

    def test_context_includes_external_fields(self, site, site_settings, issue):
        """6.4: _build_context includes external resource fields in articles_data."""
        ArticleFactory(
            issue=issue,
            use_external_resource=True,
            external_landing_url="https://example.com/art",
            external_pdf_url="https://example.com/art.pdf",
        )

        service = CrossrefService()
        context = service._build_context(issue)

        article_data = context["articles"][0]
        assert article_data["use_external_resource"] is True
        assert article_data["external_landing_url"] == "https://example.com/art"
        assert article_data["external_pdf_url"] == "https://example.com/art.pdf"


# =============================================================================
# Task 6.6: Portal Landing Page Tests
# =============================================================================


@pytest.mark.django_db
class TestExternalResourceLandingPage:
    """Test portal article detail page shows external links."""

    def test_shows_external_link_when_switch_on(self, client, issue):
        """6.6: Landing page shows external link when use_external_resource is True."""
        article = ArticleFactory(
            issue=issue,
            status=ArticleStatus.PUBLISHED,
            use_external_resource=True,
            external_landing_url="https://casopis.example.com/article/1",
            published_at=timezone.now(),
        )
        AuthorFactory(article=article, sequence="first")

        url = reverse("portal-articles:article-detail", kwargs={"pk": article.pk})
        response = client.get(url)

        assert response.status_code == 200
        content = response.content.decode()
        assert "https://casopis.example.com/article/1" in content
        assert "Originalni izvor" in content

    def test_shows_external_pdf_link_when_present(self, client, issue):
        """6.6: Landing page shows external PDF link when present."""
        article = ArticleFactory(
            issue=issue,
            status=ArticleStatus.PUBLISHED,
            use_external_resource=True,
            external_landing_url="https://casopis.example.com/article/1",
            external_pdf_url="https://casopis.example.com/article/1.pdf",
            published_at=timezone.now(),
        )
        AuthorFactory(article=article, sequence="first")

        url = reverse("portal-articles:article-detail", kwargs={"pk": article.pk})
        response = client.get(url)

        assert response.status_code == 200
        content = response.content.decode()
        assert "https://casopis.example.com/article/1.pdf" in content
        assert "Preuzmi PDF sa sajta izdavača" in content

    def test_no_external_section_when_switch_off(self, client, issue):
        """6.6: Landing page does NOT show external section when switch is off."""
        article = ArticleFactory(
            issue=issue,
            status=ArticleStatus.PUBLISHED,
            use_external_resource=False,
            published_at=timezone.now(),
        )
        AuthorFactory(article=article, sequence="first")

        url = reverse("portal-articles:article-detail", kwargs={"pk": article.pk})
        response = client.get(url)

        assert response.status_code == 200
        content = response.content.decode()
        assert "Originalni izvor" not in content
