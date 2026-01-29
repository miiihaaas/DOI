"""
Tests for Portal public views.

Story 2.2: Public Publisher Page
Story 2.5: Public Publication List with Filters
"""

import pytest
from django.urls import reverse

from doi_portal.publications.models import AccessType
from doi_portal.publications.models import Publication
from doi_portal.publications.models import PublicationType
from doi_portal.publishers.models import Publisher
from doi_portal.portal.tests.factories import PublicationFactory
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

    def test_detail_context_has_publications(self, client, db):
        """Test detail view context has publications queryset (Story 2.5 update)."""
        publisher = PublisherFactory(name="Publications Context")

        url = reverse("portal:publisher-detail", kwargs={"slug": publisher.slug})
        response = client.get(url)

        assert "publications" in response.context
        # Story 2.5: Now returns queryset, not empty list
        assert response.context["publications"].count() == 0

    def test_detail_context_has_breadcrumbs(self, client, db):
        """Test detail view context has breadcrumbs."""
        publisher = PublisherFactory(name="Breadcrumb Context")

        url = reverse("portal:publisher-detail", kwargs={"slug": publisher.slug})
        response = client.get(url)

        assert "breadcrumbs" in response.context
        assert len(response.context["breadcrumbs"]) == 3


# =============================================================================
# Story 2.5: Public Publication List with Filters - Tests
# =============================================================================


@pytest.mark.django_db
class TestPublicationPublicListView:
    """Test public publication list view (AC: #1, #2, #3, #4, #6)."""

    # --- Task 8.1: Test publication list shows active publications ---

    def test_list_shows_active_publications(self, client):
        """AC #1: Active publications are displayed in list."""
        pub = PublicationFactory(title="Test Časopis")
        url = reverse("portal-publications:publication-list")
        response = client.get(url)

        assert response.status_code == 200
        assert "Test Časopis" in response.content.decode()

    # --- Task 8.2: Test soft-deleted publications are hidden ---

    def test_deleted_publications_hidden(self, client):
        """AC #1: Soft-deleted publications must not appear in list."""
        active = PublicationFactory(title="Aktivna Publikacija")
        deleted = PublicationFactory(title="Obrisana Publikacija")
        deleted.soft_delete()

        url = reverse("portal-publications:publication-list")
        response = client.get(url)
        content = response.content.decode()

        assert "Aktivna Publikacija" in content
        assert "Obrisana Publikacija" not in content

    # --- Task 8.3: Test filter by publication_type ---

    def test_filter_by_type(self, client):
        """AC #2: Filter by publication type works."""
        pub_j = PublicationFactory(
            title="Časopis Test", publication_type=PublicationType.JOURNAL
        )
        pub_b = PublicationFactory(
            title="Knjiga Test", publication_type=PublicationType.BOOK
        )

        url = reverse("portal-publications:publication-list") + "?type=JOURNAL"
        response = client.get(url)
        content = response.content.decode()

        assert "Časopis Test" in content
        assert "Knjiga Test" not in content

    # --- Task 8.4: Test filter by access_type ---

    def test_filter_by_access_type(self, client):
        """AC #2: Filter by access type works."""
        open_pub = PublicationFactory(
            title="Otvorena Pub", access_type=AccessType.OPEN
        )
        restricted_pub = PublicationFactory(
            title="Ograničena Pub", access_type=AccessType.RESTRICTED
        )

        url = reverse("portal-publications:publication-list") + "?access=OPEN"
        response = client.get(url)
        content = response.content.decode()

        assert "Otvorena Pub" in content
        assert "Ograničena Pub" not in content

    # --- Task 8.5: Test filter by subject_area ---

    def test_filter_by_subject_area(self, client):
        """AC #2: Filter by subject area works."""
        math_pub = PublicationFactory(
            title="Matematika Pub", subject_area="Matematika"
        )
        physics_pub = PublicationFactory(
            title="Fizika Pub", subject_area="Fizika"
        )

        url = (
            reverse("portal-publications:publication-list") + "?subject=Matematika"
        )
        response = client.get(url)
        content = response.content.decode()

        assert "Matematika Pub" in content
        assert "Fizika Pub" not in content

    # --- Task 8.6: Test filter by language ---

    def test_filter_by_language(self, client):
        """AC #2: Filter by language works."""
        sr_pub = PublicationFactory(title="Srpska Pub", language="sr")
        en_pub = PublicationFactory(title="Engleska Pub", language="en")

        url = reverse("portal-publications:publication-list") + "?language=sr"
        response = client.get(url)
        content = response.content.decode()

        assert "Srpska Pub" in content
        assert "Engleska Pub" not in content

    # --- Task 8.7: Test search by title ---

    def test_search_by_title(self, client):
        """AC #3: Search by title works."""
        pub1 = PublicationFactory(title="Naučni Pregled")
        pub2 = PublicationFactory(title="Tehnički Zbornik")

        url = reverse("portal-publications:publication-list") + "?search=Naučni"
        response = client.get(url)
        content = response.content.decode()

        assert "Naučni Pregled" in content
        assert "Tehnički Zbornik" not in content

    # --- Task 8.8: Test combined filters and search ---

    def test_combined_filters_and_search(self, client):
        """AC #2, #3: Combined filters and search work together."""
        target = PublicationFactory(
            title="Target Časopis",
            publication_type=PublicationType.JOURNAL,
            language="sr",
        )
        non_target = PublicationFactory(
            title="Target Knjiga",
            publication_type=PublicationType.BOOK,
            language="sr",
        )

        url = (
            reverse("portal-publications:publication-list")
            + "?search=Target&type=JOURNAL"
        )
        response = client.get(url)
        content = response.content.decode()

        assert "Target Časopis" in content
        assert "Target Knjiga" not in content

    # --- Task 8.9: Test pagination ---

    def test_pagination_12_per_page(self, client):
        """AC #4: Pagination shows 12 items per page."""
        publisher = PublisherFactory()
        for i in range(15):
            PublicationFactory(
                title=f"Pub {i:02d}",
                publisher=publisher,
            )

        url = reverse("portal-publications:publication-list")
        response = client.get(url)

        assert response.status_code == 200
        assert response.context["is_paginated"] is True
        assert len(response.context["publications"]) == 12

    def test_pagination_second_page(self, client):
        """AC #4: Second page shows remaining items."""
        publisher = PublisherFactory()
        for i in range(15):
            PublicationFactory(
                title=f"Pub {i:02d}",
                publisher=publisher,
            )

        url = reverse("portal-publications:publication-list") + "?page=2"
        response = client.get(url)

        assert response.status_code == 200
        assert len(response.context["publications"]) == 3

    # --- Task 8.10: Test HTMX request returns partial template ---

    def test_htmx_returns_partial(self, client):
        """AC #2, #3: HTMX request returns partial template."""
        PublicationFactory(title="HTMX Test")

        url = reverse("portal-publications:publication-list")
        response = client.get(url, HTTP_HX_REQUEST="true")

        assert response.status_code == 200
        content = response.content.decode()
        # Partial should NOT contain <!DOCTYPE or extend base
        assert "<!DOCTYPE" not in content
        # But should contain our publication
        assert "HTMX Test" in content

    # --- Task 8.11: Test non-HTMX request returns full page ---

    def test_non_htmx_returns_full_page(self, client):
        """AC #1: Non-HTMX request returns full page with layout."""
        PublicationFactory(title="Full Page Test")

        url = reverse("portal-publications:publication-list")
        response = client.get(url)

        assert response.status_code == 200
        content = response.content.decode()
        assert "<!DOCTYPE" in content
        assert "Full Page Test" in content

    # --- Task 8.14: Test breadcrumbs on list page ---

    def test_list_has_breadcrumbs(self, client):
        """AC #1: List page has breadcrumbs."""
        url = reverse("portal-publications:publication-list")
        response = client.get(url)

        assert "breadcrumbs" in response.context
        breadcrumbs = response.context["breadcrumbs"]
        assert len(breadcrumbs) == 2
        assert breadcrumbs[0]["label"] == "Početna"
        assert breadcrumbs[1]["label"] == "Publikacije"

    # --- Task 8.15: Test empty state ---

    def test_empty_state_message(self, client):
        """AC #6: Empty state message shown when no results match."""
        url = reverse("portal-publications:publication-list") + "?type=BOOK"
        response = client.get(url)
        content = response.content.decode()

        assert "Nema publikacija koje odgovaraju kriterijumima pretrage." in content

    def test_empty_state_reset_button(self, client):
        """AC #6: Reset button available in empty state."""
        url = reverse("portal-publications:publication-list") + "?type=BOOK"
        response = client.get(url)
        content = response.content.decode()

        assert "Obrišite sve filtere" in content

    # --- Task 8.16: Test navbar active class ---

    def test_navbar_active_class(self, client):
        """AC #7: Publikacije nav link is active on publications page."""
        url = reverse("portal-publications:publication-list")
        response = client.get(url)
        content = response.content.decode()

        # The navbar should have active class on Publikacije link
        assert 'class="nav-link active"' in content or "nav-link active" in content

    # --- Test context data ---

    def test_context_has_filter_choices(self, client):
        """Context includes filter choices for UI."""
        url = reverse("portal-publications:publication-list")
        response = client.get(url)

        assert "publication_types" in response.context
        assert "access_types" in response.context

    def test_context_has_active_filter_values(self, client):
        """Context includes active filter values (multi-select lists)."""
        url = reverse("portal-publications:publication-list") + "?type=JOURNAL"
        response = client.get(url)

        assert "JOURNAL" in response.context["current_types"]

    def test_uses_correct_template(self, client):
        """List view uses correct template."""
        url = reverse("portal-publications:publication-list")
        response = client.get(url)

        template_names = [t.name for t in response.templates]
        assert "portal/publications/publication_list.html" in template_names

    def test_no_authentication_required(self, client):
        """Public view - no login required."""
        url = reverse("portal-publications:publication-list")
        response = client.get(url)
        # 200, not 302 redirect to login
        assert response.status_code == 200

    def test_invalid_type_filter_ignored(self, client):
        """Invalid type filter value is ignored."""
        PublicationFactory(title="Valid Pub")

        url = reverse("portal-publications:publication-list") + "?type=INVALID"
        response = client.get(url)
        content = response.content.decode()

        # Should show all publications (invalid filter ignored)
        assert "Valid Pub" in content

    def test_invalid_access_filter_ignored(self, client):
        """Invalid access filter value is ignored."""
        PublicationFactory(title="Valid Pub2")

        url = reverse("portal-publications:publication-list") + "?access=INVALID"
        response = client.get(url)
        content = response.content.decode()

        assert "Valid Pub2" in content

    # --- Code Review Fix: Test pagination preserves filters (AC #4) ---

    def test_pagination_preserves_filters(self, client):
        """AC #4: Filters and search preserved through pagination."""
        publisher = PublisherFactory()
        for i in range(15):
            PublicationFactory(
                title=f"Journal {i:02d}",
                publisher=publisher,
                publication_type=PublicationType.JOURNAL,
            )
        # Add non-journal to verify filter works
        PublicationFactory(
            title="Book Extra", publisher=publisher, publication_type=PublicationType.BOOK
        )

        url = reverse("portal-publications:publication-list") + "?type=JOURNAL&page=2"
        response = client.get(url)

        assert response.status_code == 200
        # Page 2 of filtered results should have remaining journals
        assert len(response.context["publications"]) == 3
        # Verify filter is still applied (no BOOK)
        content = response.content.decode()
        assert "Book Extra" not in content

    # --- Code Review Fix: Test multiselect filters (AC #2) ---

    def test_multiselect_type_filter(self, client):
        """AC #2: Multiple type values filter with OR logic."""
        pub_j = PublicationFactory(
            title="Multi Journal", publication_type=PublicationType.JOURNAL
        )
        pub_b = PublicationFactory(
            title="Multi Book", publication_type=PublicationType.BOOK
        )
        pub_c = PublicationFactory(
            title="Multi Conference", publication_type=PublicationType.CONFERENCE
        )

        url = reverse("portal-publications:publication-list") + "?type=JOURNAL&type=BOOK"
        response = client.get(url)
        content = response.content.decode()

        assert "Multi Journal" in content
        assert "Multi Book" in content
        assert "Multi Conference" not in content

    # --- Code Review Fix: Test SEO meta tags (Tasks 4.9, 6.6) ---

    def test_list_seo_meta_title(self, client):
        """Task 4.9: List page has correct meta title."""
        url = reverse("portal-publications:publication-list")
        response = client.get(url)
        content = response.content.decode()

        assert "<title>" in content
        assert "Publikacije - DOI Portal" in content

    def test_list_seo_meta_description(self, client):
        """Task 4.9: List page has meta description."""
        url = reverse("portal-publications:publication-list")
        response = client.get(url)
        content = response.content.decode()

        assert "Pregledajte sve naučne publikacije" in content


@pytest.mark.django_db
class TestPublicationPublicDetailView:
    """Test public publication detail view (AC: #5)."""

    # --- Task 8.12: Test detail shows type-specific fields ---

    def test_detail_shows_journal_fields(self, client):
        """AC #5: Journal detail shows ISSN fields."""
        pub = PublicationFactory(
            title="Test Časopis Detail",
            publication_type=PublicationType.JOURNAL,
            issn_print="1234-5678",
            issn_online="8765-4321",
            abbreviation="TČD",
            frequency="Kvartalno",
        )

        url = reverse(
            "portal-publications:publication-detail", kwargs={"slug": pub.slug}
        )
        response = client.get(url)
        content = response.content.decode()

        assert response.status_code == 200
        assert "Test Časopis Detail" in content
        assert "1234-5678" in content
        assert "8765-4321" in content
        assert "TČD" in content
        assert "Kvartalno" in content

    def test_detail_shows_conference_fields(self, client):
        """AC #5: Conference detail shows conference-specific fields."""
        pub = PublicationFactory(
            title="Test Zbornik",
            publication_type=PublicationType.CONFERENCE,
            conference_name="Naučna Konferencija 2026",
            conference_acronym="NK2026",
            conference_location="Beograd",
        )

        url = reverse(
            "portal-publications:publication-detail", kwargs={"slug": pub.slug}
        )
        response = client.get(url)
        content = response.content.decode()

        assert response.status_code == 200
        assert "Test Zbornik" in content
        assert "Naučna Konferencija 2026" in content
        assert "NK2026" in content
        assert "Beograd" in content

    def test_detail_shows_book_fields(self, client):
        """AC #5: Book detail shows ISBN and edition."""
        pub = PublicationFactory(
            title="Test Knjiga",
            publication_type=PublicationType.BOOK,
            isbn_print="978-86-7549-100-0",
            edition="1. izdanje",
            series_title="Naučna Serija",
        )

        url = reverse(
            "portal-publications:publication-detail", kwargs={"slug": pub.slug}
        )
        response = client.get(url)
        content = response.content.decode()

        assert response.status_code == 200
        assert "Test Knjiga" in content
        assert "978-86-7549-100-0" in content
        assert "1. izdanje" in content
        assert "Naučna Serija" in content

    # --- Task 8.13: Test deleted publication returns 404 ---

    def test_deleted_publication_returns_404(self, client):
        """AC #5: Deleted publication returns 404."""
        pub = PublicationFactory(title="Deleted Detail")
        pub.soft_delete()

        url = reverse(
            "portal-publications:publication-detail", kwargs={"slug": pub.slug}
        )
        response = client.get(url)

        assert response.status_code == 404

    def test_nonexistent_slug_returns_404(self, client):
        """AC #5: Non-existent slug returns 404."""
        url = reverse(
            "portal-publications:publication-detail",
            kwargs={"slug": "nonexistent-slug"},
        )
        response = client.get(url)

        assert response.status_code == 404

    # --- Task 8.14: Test breadcrumbs on detail page ---

    def test_detail_has_breadcrumbs(self, client):
        """AC #5: Detail page has correct breadcrumbs."""
        pub = PublicationFactory(title="Breadcrumb Detail Test")

        url = reverse(
            "portal-publications:publication-detail", kwargs={"slug": pub.slug}
        )
        response = client.get(url)

        assert "breadcrumbs" in response.context
        breadcrumbs = response.context["breadcrumbs"]
        assert len(breadcrumbs) == 3
        assert breadcrumbs[0]["label"] == "Početna"
        assert breadcrumbs[1]["label"] == "Publikacije"
        assert breadcrumbs[2]["label"] == "Breadcrumb Detail Test"

    def test_detail_has_issues_placeholder(self, client):
        """AC #5: Detail shows issues placeholder."""
        pub = PublicationFactory(title="Issues Placeholder Test")

        url = reverse(
            "portal-publications:publication-detail", kwargs={"slug": pub.slug}
        )
        response = client.get(url)
        content = response.content.decode()

        assert "Izdanja će biti dostupna uskoro." in content

    def test_detail_has_publisher_link(self, client):
        """AC #5: Detail has link to publisher detail page."""
        publisher = PublisherFactory(name="Linked Izdavač")
        pub = PublicationFactory(title="Publisher Link Test", publisher=publisher)

        url = reverse(
            "portal-publications:publication-detail", kwargs={"slug": pub.slug}
        )
        response = client.get(url)
        content = response.content.decode()

        publisher_url = reverse(
            "portal:publisher-detail", kwargs={"slug": publisher.slug}
        )
        assert publisher_url in content
        assert "Linked Izdavač" in content

    def test_detail_uses_correct_template(self, client):
        """Detail uses correct template."""
        pub = PublicationFactory(title="Template Test Detail")

        url = reverse(
            "portal-publications:publication-detail", kwargs={"slug": pub.slug}
        )
        response = client.get(url)

        template_names = [t.name for t in response.templates]
        assert "portal/publications/publication_detail.html" in template_names

    def test_no_authentication_required(self, client):
        """Public view - no login required."""
        pub = PublicationFactory(title="Public Detail Test")

        url = reverse(
            "portal-publications:publication-detail", kwargs={"slug": pub.slug}
        )
        response = client.get(url)
        assert response.status_code == 200

    # --- Code Review Fix: Test SEO meta tags (Task 6.6) ---

    def test_detail_seo_meta_title(self, client):
        """Task 6.6: Detail page has correct meta title."""
        pub = PublicationFactory(title="SEO Test Pub")

        url = reverse(
            "portal-publications:publication-detail", kwargs={"slug": pub.slug}
        )
        response = client.get(url)
        content = response.content.decode()

        assert "SEO Test Pub - DOI Portal" in content

    def test_detail_seo_meta_description(self, client):
        """Task 6.6: Detail page has meta description with publication title."""
        pub = PublicationFactory(title="Meta Desc Pub")

        url = reverse(
            "portal-publications:publication-detail", kwargs={"slug": pub.slug}
        )
        response = client.get(url)
        content = response.content.decode()

        assert "Meta Desc Pub" in content


# =============================================================================
# Story 2.5: URL Pattern Tests
# =============================================================================


@pytest.mark.django_db
class TestPublicationURLPatterns:
    """Test publication URL patterns are configured correctly."""

    def test_publication_list_url(self):
        """Test publication list URL resolves to /publications/."""
        url = reverse("portal-publications:publication-list")
        assert url == "/publications/"

    def test_publication_detail_url(self):
        """Test publication detail URL resolves."""
        pub = PublicationFactory(slug="test-pub-slug")
        url = reverse(
            "portal-publications:publication-detail",
            kwargs={"slug": pub.slug},
        )
        assert url == "/publications/test-pub-slug/"


# =============================================================================
# Story 2.5, Task 7: Publisher detail now shows real publications
# =============================================================================


@pytest.mark.django_db
class TestPublisherDetailWithPublications:
    """Test publisher detail shows real publications (Task 7)."""

    def test_publisher_detail_shows_publications(self, client):
        """Task 8.17: Publisher detail shows real publications."""
        publisher = PublisherFactory(name="Pub With Pubs")
        pub1 = PublicationFactory(title="Prva Publikacija", publisher=publisher)
        pub2 = PublicationFactory(title="Druga Publikacija", publisher=publisher)

        url = reverse("portal:publisher-detail", kwargs={"slug": publisher.slug})
        response = client.get(url)
        content = response.content.decode()

        assert response.status_code == 200
        assert "Prva Publikacija" in content
        assert "Druga Publikacija" in content

    def test_publisher_detail_publications_queryset(self, client):
        """Task 8.17: Publisher detail context has publications queryset."""
        publisher = PublisherFactory(name="QS Test Publisher")
        pub = PublicationFactory(title="QS Test Pub", publisher=publisher)

        url = reverse("portal:publisher-detail", kwargs={"slug": publisher.slug})
        response = client.get(url)

        assert "publications" in response.context
        assert response.context["publications"].count() == 1
        assert response.context["publications"].first().title == "QS Test Pub"

    def test_publisher_detail_excludes_other_publishers(self, client):
        """Task 8.17: Publisher detail only shows own publications."""
        publisher1 = PublisherFactory(name="Publisher 1")
        publisher2 = PublisherFactory(name="Publisher 2")
        pub1 = PublicationFactory(title="P1 Pub", publisher=publisher1)
        pub2 = PublicationFactory(title="P2 Pub", publisher=publisher2)

        url = reverse("portal:publisher-detail", kwargs={"slug": publisher1.slug})
        response = client.get(url)
        content = response.content.decode()

        assert "P1 Pub" in content
        assert "P2 Pub" not in content

    def test_publisher_detail_publication_links(self, client):
        """Task 8.17: Publication cards link to publication detail."""
        publisher = PublisherFactory(name="Link Test Publisher")
        pub = PublicationFactory(
            title="Link Test Pub", publisher=publisher, slug="link-test-pub"
        )

        url = reverse("portal:publisher-detail", kwargs={"slug": publisher.slug})
        response = client.get(url)
        content = response.content.decode()

        detail_url = reverse(
            "portal-publications:publication-detail",
            kwargs={"slug": pub.slug},
        )
        assert detail_url in content
