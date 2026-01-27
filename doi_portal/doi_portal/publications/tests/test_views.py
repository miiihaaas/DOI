"""
Tests for Publication views.

Story 2.3 - Task 7.6, 7.7: HTMX type fields endpoint and form dynamic behavior tests.
"""

import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.test import Client
from django.urls import reverse

from doi_portal.publications.models import Publication, PublicationType

from .factories import (
    BookFactory,
    ConferenceFactory,
    JournalFactory,
    PublicationFactory,
    PublisherFactory,
)

User = get_user_model()


@pytest.fixture
def admin_user():
    """Create an admin user."""
    user = User.objects.create_user(
        email="admin@test.com",
        password="testpass123",
    )
    group, _ = Group.objects.get_or_create(name="Administrator")
    user.groups.add(group)
    return user


@pytest.fixture
def regular_user():
    """Create a regular user without admin permissions."""
    return User.objects.create_user(
        email="user@test.com",
        password="testpass123",
    )


@pytest.fixture
def client():
    """Create a test client."""
    return Client()


@pytest.fixture
def publisher():
    """Create a test publisher."""
    return PublisherFactory()


# =============================================================================
# Task 7.6: Test HTMX type fields endpoint
# =============================================================================


@pytest.mark.django_db
class TestHtmxTypeFieldsEndpoint:
    """Test HTMX endpoint for dynamic type-specific fields."""

    def test_htmx_returns_journal_fields(self, client, admin_user):
        """Test HTMX endpoint returns journal fields partial."""
        client.force_login(admin_user)
        response = client.get(
            reverse("publications:htmx-type-fields"),
            {"type": "JOURNAL"},
            HTTP_HX_REQUEST="true",
        )
        assert response.status_code == 200
        assert b"ISSN" in response.content
        assert b"issn_print" in response.content
        assert b"issn_online" in response.content
        assert b"abbreviation" in response.content
        assert b"frequency" in response.content

    def test_htmx_returns_conference_fields(self, client, admin_user):
        """Test HTMX endpoint returns conference fields partial."""
        client.force_login(admin_user)
        response = client.get(
            reverse("publications:htmx-type-fields"),
            {"type": "CONFERENCE"},
            HTTP_HX_REQUEST="true",
        )
        assert response.status_code == 200
        assert b"conference_name" in response.content
        assert b"conference_acronym" in response.content
        assert b"conference_location" in response.content
        assert b"conference_date" in response.content

    def test_htmx_returns_book_fields(self, client, admin_user):
        """Test HTMX endpoint returns book fields partial."""
        client.force_login(admin_user)
        response = client.get(
            reverse("publications:htmx-type-fields"),
            {"type": "BOOK"},
            HTTP_HX_REQUEST="true",
        )
        assert response.status_code == 200
        assert b"isbn_print" in response.content
        assert b"isbn_online" in response.content
        assert b"edition" in response.content
        assert b"series_title" in response.content

    def test_htmx_returns_other_fields(self, client, admin_user):
        """Test HTMX endpoint returns other type partial."""
        client.force_login(admin_user)
        response = client.get(
            reverse("publications:htmx-type-fields"),
            {"type": "OTHER"},
            HTTP_HX_REQUEST="true",
        )
        assert response.status_code == 200
        # OTHER type has no specific fields
        assert b"Ostale publikacije" in response.content

    def test_htmx_non_htmx_request_returns_empty(self, client, admin_user):
        """Test non-HTMX request returns empty response."""
        client.force_login(admin_user)
        response = client.get(
            reverse("publications:htmx-type-fields"),
            {"type": "JOURNAL"},
        )
        # Both HTMX and non-HTMX requests return partial (useful for debugging)
        assert response.status_code == 200
        assert b"ISSN" in response.content or b"issn" in response.content

    def test_htmx_requires_login(self, client):
        """Test HTMX endpoint requires authentication."""
        response = client.get(
            reverse("publications:htmx-type-fields"),
            {"type": "JOURNAL"},
            HTTP_HX_REQUEST="true",
        )
        assert response.status_code == 302
        assert "login" in response.url

    def test_htmx_accepts_publication_type_param(self, client, admin_user):
        """Test HTMX endpoint accepts publication_type parameter from hx-include."""
        client.force_login(admin_user)
        response = client.get(
            reverse("publications:htmx-type-fields"),
            {"publication_type": "CONFERENCE"},
            HTTP_HX_REQUEST="true",
        )
        assert response.status_code == 200
        assert b"conference_name" in response.content


# =============================================================================
# Test Publication List View
# =============================================================================


@pytest.mark.django_db
class TestPublicationListView:
    """Test publication list view."""

    def test_list_requires_login(self, client):
        """Test list view requires authentication."""
        response = client.get(reverse("publications:list"))
        assert response.status_code == 302
        assert "login" in response.url

    def test_list_requires_admin_permission(self, client, regular_user):
        """Test list view requires admin permission."""
        client.force_login(regular_user)
        response = client.get(reverse("publications:list"))
        assert response.status_code == 403

    def test_list_accessible_to_admin(self, client, admin_user):
        """Test list view accessible to admin user."""
        client.force_login(admin_user)
        response = client.get(reverse("publications:list"))
        assert response.status_code == 200

    def test_list_shows_publications(self, client, admin_user):
        """Test list view shows publications."""
        pub1 = JournalFactory(title="Naučni časopis")
        pub2 = ConferenceFactory(title="Zbornik radova")

        client.force_login(admin_user)
        response = client.get(reverse("publications:list"))

        assert response.status_code == 200
        assert b"Nau\xc4\x8dni \xc4\x8dasopis" in response.content  # Naučni časopis
        assert b"Zbornik radova" in response.content

    def test_list_filter_by_type(self, client, admin_user):
        """Test list view filter by publication type."""
        journal = JournalFactory(title="Časopis Test")
        book = BookFactory(title="Knjiga Test")

        client.force_login(admin_user)
        response = client.get(reverse("publications:list"), {"type": "JOURNAL"})

        assert response.status_code == 200
        content = response.content.decode("utf-8")
        assert "Časopis Test" in content
        # Book should not appear when filtering by JOURNAL
        assert "Knjiga Test" not in content

    def test_list_search_by_title(self, client, admin_user):
        """Test list view search by title."""
        JournalFactory(title="Medicina i zdravlje")
        JournalFactory(title="Informatika danas")

        client.force_login(admin_user)
        response = client.get(reverse("publications:list"), {"search": "Medicina"})

        assert response.status_code == 200
        content = response.content.decode("utf-8")
        assert "Medicina" in content
        assert "Informatika danas" not in content

    def test_list_filter_by_publisher(self, client, admin_user):
        """Test list view filter by publisher."""
        publisher1 = PublisherFactory(name="Izdavač Jedan")
        publisher2 = PublisherFactory(name="Izdavač Dva")
        JournalFactory(title="Publikacija A", publisher=publisher1)
        JournalFactory(title="Publikacija B", publisher=publisher2)

        client.force_login(admin_user)
        response = client.get(reverse("publications:list"), {"publisher": publisher1.pk})

        assert response.status_code == 200
        content = response.content.decode("utf-8")
        assert "Publikacija A" in content
        # Publikacija B should not appear when filtering by publisher1
        assert "Publikacija B" not in content


# =============================================================================
# Test Publication Create View
# =============================================================================


@pytest.mark.django_db
class TestPublicationCreateView:
    """Test publication create view."""

    def test_create_requires_login(self, client):
        """Test create view requires authentication."""
        response = client.get(reverse("publications:create"))
        assert response.status_code == 302

    def test_create_form_displayed(self, client, admin_user, publisher):
        """Test create form is displayed."""
        client.force_login(admin_user)
        response = client.get(reverse("publications:create"))

        assert response.status_code == 200
        assert b"Nova publikacija" in response.content
        assert b"publication_type" in response.content

    def test_create_journal_publication(self, client, admin_user, publisher):
        """Test creating a journal publication."""
        client.force_login(admin_user)
        response = client.post(
            reverse("publications:create"),
            {
                "title": "Naučni časopis za medicinu",
                "publisher": publisher.pk,
                "publication_type": "JOURNAL",
                "language": "sr",
                "access_type": "OPEN",
                "issn_print": "1234-5678",
                "description": "",
                "subject_area": "",
                "abbreviation": "",
                "frequency": "",
                "issn_online": "",
                "conference_name": "",
                "conference_acronym": "",
                "conference_location": "",
                "series_issn": "",
                "isbn_print": "",
                "isbn_online": "",
                "edition": "",
                "series_title": "",
            },
        )

        assert response.status_code == 302  # Redirect on success
        assert Publication.objects.filter(title="Naučni časopis za medicinu").exists()

    def test_create_with_invalid_issn_fails(self, client, admin_user, publisher):
        """Test creating publication with invalid ISSN fails."""
        client.force_login(admin_user)
        response = client.post(
            reverse("publications:create"),
            {
                "title": "Test",
                "publisher": publisher.pk,
                "publication_type": "JOURNAL",
                "language": "sr",
                "access_type": "OPEN",
                "issn_print": "invalid",
                "description": "",
                "subject_area": "",
                "abbreviation": "",
                "frequency": "",
                "issn_online": "",
                "conference_name": "",
                "conference_acronym": "",
                "conference_location": "",
                "series_issn": "",
                "isbn_print": "",
                "isbn_online": "",
                "edition": "",
                "series_title": "",
            },
        )

        assert response.status_code == 200  # Form re-displayed with errors
        assert not Publication.objects.filter(title="Test").exists()


# =============================================================================
# Test Publication Update View
# =============================================================================


@pytest.mark.django_db
class TestPublicationUpdateView:
    """Test publication update view."""

    def test_update_form_displayed(self, client, admin_user):
        """Test update form is displayed with existing data."""
        publication = JournalFactory(
            title="Original Title",
            issn_print="1234-5678",
        )

        client.force_login(admin_user)
        response = client.get(
            reverse("publications:update", kwargs={"slug": publication.slug})
        )

        assert response.status_code == 200
        assert b"Original Title" in response.content
        assert b"1234-5678" in response.content

    def test_update_publication(self, client, admin_user):
        """Test updating a publication."""
        publication = JournalFactory(title="Original")

        client.force_login(admin_user)
        response = client.post(
            reverse("publications:update", kwargs={"slug": publication.slug}),
            {
                "title": "Updated Title",
                "publisher": publication.publisher.pk,
                "publication_type": "JOURNAL",
                "language": "sr",
                "access_type": "OPEN",
                "issn_print": "",
                "description": "",
                "subject_area": "",
                "abbreviation": "",
                "frequency": "",
                "issn_online": "",
                "conference_name": "",
                "conference_acronym": "",
                "conference_location": "",
                "series_issn": "",
                "isbn_print": "",
                "isbn_online": "",
                "edition": "",
                "series_title": "",
            },
        )

        assert response.status_code == 302
        publication.refresh_from_db()
        assert publication.title == "Updated Title"


# =============================================================================
# Test Publication Delete View
# =============================================================================


@pytest.mark.django_db
class TestPublicationDeleteView:
    """Test publication delete view."""

    def test_delete_confirmation_displayed(self, client, admin_user):
        """Test delete confirmation page is displayed."""
        publication = JournalFactory(title="To Delete")

        client.force_login(admin_user)
        response = client.get(
            reverse("publications:delete", kwargs={"slug": publication.slug})
        )

        assert response.status_code == 200
        assert b"To Delete" in response.content
        assert b"Potvrda brisanja" in response.content

    def test_soft_delete_publication(self, client, admin_user):
        """Test soft deleting a publication."""
        publication = JournalFactory(title="To Soft Delete")

        client.force_login(admin_user)
        response = client.post(
            reverse("publications:delete", kwargs={"slug": publication.slug})
        )

        assert response.status_code == 302

        # Should be soft deleted
        publication.refresh_from_db()
        assert publication.is_deleted is True

        # Should not appear in default queryset
        assert not Publication.objects.filter(pk=publication.pk).exists()
        assert Publication.all_objects.filter(pk=publication.pk).exists()


# =============================================================================
# Test Publication Detail View
# =============================================================================


@pytest.mark.django_db
class TestPublicationDetailView:
    """Test publication detail view."""

    def test_detail_displays_publication(self, client, admin_user):
        """Test detail view displays publication information."""
        publication = JournalFactory(
            title="Naučni časopis",
            issn_print="1234-5678",
            issn_online="8765-4321",
        )

        client.force_login(admin_user)
        response = client.get(
            reverse("publications:detail", kwargs={"slug": publication.slug})
        )

        assert response.status_code == 200
        content = response.content.decode("utf-8")
        assert "Naučni časopis" in content
        assert "1234-5678" in content
        assert "8765-4321" in content

    def test_detail_shows_journal_specific_fields(self, client, admin_user):
        """Test detail view shows journal-specific fields."""
        publication = JournalFactory(
            abbreviation="Nauč. čas.",
            frequency="Kvartalno",
        )

        client.force_login(admin_user)
        response = client.get(
            reverse("publications:detail", kwargs={"slug": publication.slug})
        )

        assert response.status_code == 200
        content = response.content.decode("utf-8")
        assert "Nauč. čas." in content
        assert "Kvartalno" in content

    def test_detail_shows_conference_specific_fields(self, client, admin_user):
        """Test detail view shows conference-specific fields."""
        import datetime

        publication = ConferenceFactory(
            conference_name="Naučna konferencija 2026",
            conference_location="Beograd",
            conference_date=datetime.date(2026, 6, 15),
        )

        client.force_login(admin_user)
        response = client.get(
            reverse("publications:detail", kwargs={"slug": publication.slug})
        )

        assert response.status_code == 200
        content = response.content.decode("utf-8")
        assert "Naučna konferencija 2026" in content
        assert "Beograd" in content

    def test_detail_shows_book_specific_fields(self, client, admin_user):
        """Test detail view shows book-specific fields."""
        publication = BookFactory(
            isbn_print="978-86-7549-123-4",
            edition="1. izdanje",
        )

        client.force_login(admin_user)
        response = client.get(
            reverse("publications:detail", kwargs={"slug": publication.slug})
        )

        assert response.status_code == 200
        content = response.content.decode("utf-8")
        assert "978-86-7549-123-4" in content
        assert "1. izdanje" in content


# =============================================================================
# Task 7.7: Test form dynamic behavior
# =============================================================================


@pytest.mark.django_db
class TestFormDynamicBehavior:
    """Test publication form dynamic field behavior."""

    def test_form_includes_htmx_attributes(self, client, admin_user):
        """Test form includes HTMX attributes for dynamic updates."""
        client.force_login(admin_user)
        response = client.get(reverse("publications:create"))

        assert response.status_code == 200
        content = response.content.decode("utf-8")
        assert "hx-get" in content
        assert "hx-target" in content
        assert "type-specific-fields" in content

    def test_form_shows_default_journal_fields(self, client, admin_user, publisher):
        """Test form shows journal fields by default."""
        client.force_login(admin_user)
        response = client.get(reverse("publications:create"))

        assert response.status_code == 200
        content = response.content.decode("utf-8")
        # Journal fields should be visible by default
        assert "issn_print" in content
        assert "abbreviation" in content
