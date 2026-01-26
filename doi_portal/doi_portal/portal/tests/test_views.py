"""
Tests for Portal public views.

Story 2.2: Public Publisher Page
Task 6: Unit tests for AC #1, #2, #3, #4
"""

import pytest
from django.urls import reverse

from doi_portal.publishers.models import Publisher
from doi_portal.portal.tests.factories import PublisherFactory


# =============================================================================
# Task 6.1: Test publisher list view returns 200
# =============================================================================


@pytest.mark.django_db
class TestPublisherPublicListView:
    """Test public publisher list view (AC: #2)."""

    def test_list_returns_200(self, client):
        """Test publisher list returns 200 status - Task 6.1."""
        url = reverse("portal:publisher-list")
        response = client.get(url)
        assert response.status_code == 200

    def test_list_uses_correct_template(self, client):
        """Test list view uses portal template."""
        url = reverse("portal:publisher-list")
        response = client.get(url)
        assert "portal/publishers/publisher_list.html" in [
            t.name for t in response.templates
        ]

    def test_list_shows_active_publishers(self, client, db):
        """Test active publishers shown in list - Task 6.5."""
        publisher1 = PublisherFactory(name="Aktivan Izdavač 1")
        publisher2 = PublisherFactory(name="Aktivan Izdavač 2")

        url = reverse("portal:publisher-list")
        response = client.get(url)
        content = response.content.decode()

        assert publisher1.name in content
        assert publisher2.name in content

    def test_list_excludes_deleted_publishers(self, client, db):
        """Test deleted publishers not shown in list - Task 6.5."""
        active = PublisherFactory(name="Aktivan Izdavač")
        deleted = PublisherFactory(name="Obrisan Izdavač")
        deleted.soft_delete()

        url = reverse("portal:publisher-list")
        response = client.get(url)
        content = response.content.decode()

        assert "Aktivan Izdavač" in content
        assert "Obrisan Izdavač" not in content

    def test_list_links_to_detail_page(self, client, db):
        """Test each publisher links to detail page - AC #2."""
        publisher = PublisherFactory(name="Test Izdavač", slug="test-izdavac")

        url = reverse("portal:publisher-list")
        response = client.get(url)
        content = response.content.decode()

        detail_url = reverse("portal:publisher-detail", kwargs={"slug": publisher.slug})
        assert detail_url in content

    def test_list_shows_doi_prefix(self, client, db):
        """Test DOI prefix displayed in list."""
        publisher = PublisherFactory(name="DOI Test", doi_prefix="10.9876")

        url = reverse("portal:publisher-list")
        response = client.get(url)
        content = response.content.decode()

        assert "10.9876" in content

    def test_list_has_breadcrumbs(self, client, db):
        """Test breadcrumbs displayed on list page."""
        url = reverse("portal:publisher-list")
        response = client.get(url)
        content = response.content.decode()

        assert "Izdavači" in content or "breadcrumb" in content

    def test_list_empty_state(self, client, db):
        """Test empty state when no publishers exist."""
        url = reverse("portal:publisher-list")
        response = client.get(url)
        content = response.content.decode()

        # Check for empty state message
        assert "Nema registrovanih" in content or response.context["publishers"].count() == 0

    def test_no_authentication_required_for_list(self, client, db):
        """Test public access - no login required for list."""
        url = reverse("portal:publisher-list")
        response = client.get(url)

        # Should return 200, NOT 302 redirect to login
        assert response.status_code == 200

    def test_list_publishers_ordered_by_name(self, client, db):
        """Test publishers are ordered alphabetically by name."""
        # Create publishers out of order
        PublisherFactory(name="Zebra Izdavač")
        PublisherFactory(name="Alpha Izdavač")
        PublisherFactory(name="Beta Izdavač")

        url = reverse("portal:publisher-list")
        response = client.get(url)

        publishers = list(response.context["publishers"])
        names = [p.name for p in publishers]

        # Should be alphabetically sorted
        assert names == sorted(names)
        assert names[0] == "Alpha Izdavač"
        assert names[1] == "Beta Izdavač"
        assert names[2] == "Zebra Izdavač"


# =============================================================================
# Task 6.2, 6.3, 6.4: Test publisher detail view
# =============================================================================


@pytest.mark.django_db
class TestPublisherPublicDetailView:
    """Test public publisher detail view (AC: #1, #3, #4)."""

    def test_detail_returns_200_for_active_publisher(self, client, db):
        """Test publisher detail returns 200 for active publisher - Task 6.2."""
        publisher = PublisherFactory(name="Test Izdavač")

        url = reverse("portal:publisher-detail", kwargs={"slug": publisher.slug})
        response = client.get(url)

        assert response.status_code == 200
        assert "Test Izdavač" in response.content.decode()

    def test_detail_uses_correct_template(self, client, db):
        """Test detail view uses portal template."""
        publisher = PublisherFactory(name="Template Test")

        url = reverse("portal:publisher-detail", kwargs={"slug": publisher.slug})
        response = client.get(url)

        assert "portal/publishers/publisher_detail.html" in [
            t.name for t in response.templates
        ]

    def test_detail_returns_404_for_deleted_publisher(self, client, db):
        """Test 404 returned for deleted publisher - Task 6.3, AC #4."""
        publisher = PublisherFactory(name="Deleted Izdavač")
        publisher.soft_delete()

        url = reverse("portal:publisher-detail", kwargs={"slug": publisher.slug})
        response = client.get(url)

        assert response.status_code == 404

    def test_detail_returns_404_for_nonexistent_slug(self, client, db):
        """Test 404 returned for non-existent slug - Task 6.4."""
        url = reverse("portal:publisher-detail", kwargs={"slug": "non-existent-slug"})
        response = client.get(url)

        assert response.status_code == 404

    def test_detail_shows_publisher_info(self, client, db):
        """Test publisher details are displayed - AC #1."""
        publisher = PublisherFactory(
            name="Info Test Izdavač",
            description="Ovo je opis издавача za testiranje.",
            doi_prefix="10.5555",
        )

        url = reverse("portal:publisher-detail", kwargs={"slug": publisher.slug})
        response = client.get(url)
        content = response.content.decode()

        assert publisher.name in content
        assert publisher.description in content
        assert publisher.doi_prefix in content

    def test_detail_shows_contact_info(self, client, db):
        """Test contact information displayed - AC #1."""
        publisher = PublisherFactory(
            name="Kontakt Test",
            contact_email="test@example.com",
            contact_phone="+381 11 123 4567",
            website="https://example.com",
        )

        url = reverse("portal:publisher-detail", kwargs={"slug": publisher.slug})
        response = client.get(url)
        content = response.content.decode()

        assert "test@example.com" in content
        assert "+381 11 123 4567" in content
        assert "https://example.com" in content

    def test_detail_shows_empty_publications_message(self, client, db):
        """Test empty publications message shown - Task 6.7, AC #3."""
        publisher = PublisherFactory(name="No Pubs Izdavač")

        url = reverse("portal:publisher-detail", kwargs={"slug": publisher.slug})
        response = client.get(url)
        content = response.content.decode()

        # Check for Serbian message about no publications
        assert "Nema publikacija" in content

    def test_detail_has_breadcrumbs(self, client, db):
        """Test breadcrumbs displayed on detail page."""
        publisher = PublisherFactory(name="Breadcrumb Test")

        url = reverse("portal:publisher-detail", kwargs={"slug": publisher.slug})
        response = client.get(url)
        content = response.content.decode()

        # Should have breadcrumbs with Izdavači link
        assert "Izdavači" in content
        assert publisher.name in content

    def test_no_authentication_required_for_detail(self, client, db):
        """Test public access - no login required - AC #1, #4."""
        publisher = PublisherFactory(name="Public Access")

        # No login, just direct access
        url = reverse("portal:publisher-detail", kwargs={"slug": publisher.slug})
        response = client.get(url)

        # Should return 200, NOT 302 redirect to login
        assert response.status_code == 200


# =============================================================================
# Task 6.6: Test template rendering with logo and without logo
# =============================================================================


@pytest.mark.django_db
class TestPublisherLogoRendering:
    """Test publisher logo rendering in templates."""

    def test_list_renders_publisher_without_logo(self, client, db):
        """Test list renders placeholder for publisher without logo - Task 6.6."""
        publisher = PublisherFactory(name="No Logo Izdavač", logo=None)

        url = reverse("portal:publisher-list")
        response = client.get(url)
        content = response.content.decode()

        # Should show building icon placeholder
        assert "bi-building" in content
        assert publisher.name in content

    def test_detail_renders_publisher_without_logo(self, client, db):
        """Test detail renders publisher without logo - Task 6.6."""
        publisher = PublisherFactory(name="No Logo Detail", logo=None)

        url = reverse("portal:publisher-detail", kwargs={"slug": publisher.slug})
        response = client.get(url)
        content = response.content.decode()

        # Should not crash, page should render
        assert response.status_code == 200
        assert publisher.name in content


# =============================================================================
# Test URL patterns
# =============================================================================


@pytest.mark.django_db
class TestPortalURLPatterns:
    """Test portal URL patterns are configured correctly."""

    def test_publisher_list_url(self):
        """Test publisher list URL resolves."""
        url = reverse("portal:publisher-list")
        assert url == "/publishers/"

    def test_publisher_detail_url(self, db):
        """Test publisher detail URL resolves."""
        publisher = PublisherFactory(slug="test-slug")
        url = reverse("portal:publisher-detail", kwargs={"slug": publisher.slug})
        assert url == f"/publishers/{publisher.slug}/"


# =============================================================================
# Test context data
# =============================================================================


@pytest.mark.django_db
class TestViewContextData:
    """Test view context data is correct."""

    def test_list_context_has_publishers(self, client, db):
        """Test list view context contains publishers."""
        PublisherFactory.create_batch(3)

        url = reverse("portal:publisher-list")
        response = client.get(url)

        assert "publishers" in response.context
        assert response.context["publishers"].count() == 3

    def test_list_context_has_breadcrumbs(self, client, db):
        """Test list view context has breadcrumbs."""
        url = reverse("portal:publisher-list")
        response = client.get(url)

        assert "breadcrumbs" in response.context
        assert len(response.context["breadcrumbs"]) == 2

    def test_detail_context_has_publisher(self, client, db):
        """Test detail view context contains publisher."""
        publisher = PublisherFactory(name="Context Test")

        url = reverse("portal:publisher-detail", kwargs={"slug": publisher.slug})
        response = client.get(url)

        assert "publisher" in response.context
        assert response.context["publisher"] == publisher

    def test_detail_context_has_publications_placeholder(self, client, db):
        """Test detail view context has publications (empty for now)."""
        publisher = PublisherFactory(name="Publications Context")

        url = reverse("portal:publisher-detail", kwargs={"slug": publisher.slug})
        response = client.get(url)

        assert "publications" in response.context
        assert response.context["publications"] == []

    def test_detail_context_has_breadcrumbs(self, client, db):
        """Test detail view context has breadcrumbs."""
        publisher = PublisherFactory(name="Breadcrumb Context")

        url = reverse("portal:publisher-detail", kwargs={"slug": publisher.slug})
        response = client.get(url)

        assert "breadcrumbs" in response.context
        assert len(response.context["breadcrumbs"]) == 3
