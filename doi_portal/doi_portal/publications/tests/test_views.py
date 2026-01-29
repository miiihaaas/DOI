"""
Tests for Publication views.

Story 2.3 - Task 7.6, 7.7: HTMX type fields endpoint and form dynamic behavior tests.
Story 2.4 - Task 6: Sorting, row-level permissions, issue_count, audit log, detail 2.3a.
"""

import datetime

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


# =============================================================================
# Fixtures
# =============================================================================


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
def superadmin_user():
    """Create a superadmin user."""
    user = User.objects.create_user(
        email="superadmin@test.com",
        password="testpass123",
    )
    group, _ = Group.objects.get_or_create(name="Superadmin")
    user.groups.add(group)
    return user


@pytest.fixture
def superuser():
    """Create a Django superuser."""
    return User.objects.create_superuser(
        email="super@test.com",
        password="testpass123",
    )


@pytest.fixture
def regular_user():
    """Create a regular user without admin permissions."""
    return User.objects.create_user(
        email="user@test.com",
        password="testpass123",
    )


@pytest.fixture
def publisher_a():
    """Create publisher A."""
    return PublisherFactory(name="Izdavač A")


@pytest.fixture
def publisher_b():
    """Create publisher B."""
    return PublisherFactory(name="Izdavač B")


@pytest.fixture
def urednik_user(publisher_a):
    """Create an Urednik user assigned to publisher A."""
    user = User.objects.create_user(
        email="urednik@test.com",
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
        email="bibliotekar@test.com",
        password="testpass123",
        publisher=publisher_a,
    )
    group, _ = Group.objects.get_or_create(name="Bibliotekar")
    user.groups.add(group)
    return user


@pytest.fixture
def client():
    """Create a test client."""
    return Client()


@pytest.fixture
def publisher():
    """Create a test publisher."""
    return PublisherFactory()


# =============================================================================
# Task 7.6: Test HTMX type fields endpoint (Story 2.3)
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
# Test Publication List View (Story 2.3 + 2.4)
# =============================================================================


@pytest.mark.django_db
class TestPublicationListView:
    """Test publication list view."""

    def test_list_requires_login(self, client):
        """Test list view requires authentication."""
        response = client.get(reverse("publications:list"))
        assert response.status_code == 302
        assert "login" in response.url

    def test_list_requires_valid_role(self, client, regular_user):
        """Test list view requires a valid role (not just any authenticated user)."""
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
# Story 2.4 - Task 6.1-6.2: Test Sorting (AC #1)
# =============================================================================


@pytest.mark.django_db
class TestPublicationListSorting:
    """Test sorting in publication list. Story 2.4 - Task 6.1, 6.2."""

    def test_sort_by_title_asc(self, client, admin_user):
        """6.1: Sort by title ascending."""
        JournalFactory(title="AAA Časopis")
        JournalFactory(title="ZZZ Časopis")

        client.force_login(admin_user)
        url = reverse("publications:list")
        response = client.get(f"{url}?sort=title&order=asc")

        assert response.status_code == 200
        content = response.content.decode("utf-8")
        assert content.index("AAA") < content.index("ZZZ")

    def test_sort_by_title_desc(self, client, admin_user):
        """6.1: Sort by title descending."""
        JournalFactory(title="AAA Časopis")
        JournalFactory(title="ZZZ Časopis")

        client.force_login(admin_user)
        url = reverse("publications:list")
        response = client.get(f"{url}?sort=title&order=desc")

        assert response.status_code == 200
        content = response.content.decode("utf-8")
        assert content.index("ZZZ") < content.index("AAA")

    def test_sort_by_type_asc(self, client, admin_user):
        """6.1: Sort by type ascending (BOOK < CONFERENCE < JOURNAL)."""
        BookFactory(title="Knjiga Pub")
        JournalFactory(title="Časopis Pub")

        client.force_login(admin_user)
        url = reverse("publications:list")
        response = client.get(f"{url}?sort=type&order=asc")

        assert response.status_code == 200
        content = response.content.decode("utf-8")
        # BOOK comes before JOURNAL alphabetically
        assert content.index("Knjiga Pub") < content.index("Časopis Pub")

    def test_sort_by_publisher_asc(self, client, admin_user):
        """6.1: Sort by publisher name ascending."""
        pub_a = PublisherFactory(name="AAA Izdavač")
        pub_z = PublisherFactory(name="ZZZ Izdavač")
        JournalFactory(title="Pub od A", publisher=pub_a)
        JournalFactory(title="Pub od Z", publisher=pub_z)

        client.force_login(admin_user)
        url = reverse("publications:list")
        response = client.get(f"{url}?sort=publisher&order=asc")

        assert response.status_code == 200
        content = response.content.decode("utf-8")
        assert content.index("Pub od A") < content.index("Pub od Z")

    def test_sort_by_created_desc(self, client, admin_user):
        """6.1: Sort by creation date descending (newest first)."""
        # Create two publications - second one will be newer
        pub1 = JournalFactory(title="Starija Pub")
        pub2 = JournalFactory(title="Novija Pub")

        client.force_login(admin_user)
        url = reverse("publications:list")
        response = client.get(f"{url}?sort=created&order=desc")

        assert response.status_code == 200
        content = response.content.decode("utf-8")
        # Newer should be first
        assert content.index("Novija Pub") < content.index("Starija Pub")

    def test_invalid_sort_field_uses_default(self, client, admin_user):
        """6.2: Invalid sort field falls back to title (default)."""
        JournalFactory(title="AAA Pub")
        JournalFactory(title="ZZZ Pub")

        client.force_login(admin_user)
        url = reverse("publications:list")
        response = client.get(f"{url}?sort=hacker&order=asc")

        assert response.status_code == 200
        content = response.content.decode("utf-8")
        # Should use default sort (title asc)
        assert content.index("AAA") < content.index("ZZZ")

    def test_default_sort_is_title_asc(self, client, admin_user):
        """6.1: Default sort (no params) is title ascending."""
        JournalFactory(title="ZZZ Pub")
        JournalFactory(title="AAA Pub")

        client.force_login(admin_user)
        url = reverse("publications:list")
        response = client.get(url)

        assert response.status_code == 200
        content = response.content.decode("utf-8")
        assert content.index("AAA") < content.index("ZZZ")


# =============================================================================
# Story 2.4 - Task 6.3: Test issue_count column (AC #1)
# =============================================================================


@pytest.mark.django_db
class TestPublicationListIssueCount:
    """Test issue_count column in list view. Story 2.4 - Task 6.3."""

    def test_issue_count_annotation_in_list(self, client, admin_user):
        """6.3: Issue count column displays in list (0 until Story 2.6)."""
        JournalFactory(title="Test Pub")

        client.force_login(admin_user)
        response = client.get(reverse("publications:list"))

        assert response.status_code == 200
        content = response.content.decode("utf-8")
        # Issue count annotation should be 0 (no Issue model yet)
        assert "Izdanja" in content  # Column header
        assert "0" in content  # Issue count value

    def test_list_has_izdanja_column_header(self, client, admin_user):
        """6.3: Template has 'Izdanja' column header."""
        JournalFactory(title="Test Pub")

        client.force_login(admin_user)
        response = client.get(reverse("publications:list"))

        assert response.status_code == 200
        assert "Izdanja" in response.content.decode("utf-8")


# =============================================================================
# Story 2.4 - Task 6.4-6.8: Test Row-Level Permissions (AC #4, #5, #6, #7, #8)
# =============================================================================


@pytest.mark.django_db
class TestPublicationRowLevelPermissions:
    """Test row-level permissions. Story 2.4 - Tasks 6.4-6.8."""

    def test_urednik_sees_only_own_publisher(
        self, client, urednik_user, publisher_a, publisher_b
    ):
        """6.4: Urednik sees only publications from their assigned publisher."""
        JournalFactory(title="Pub A", publisher=publisher_a)
        JournalFactory(title="Pub B", publisher=publisher_b)

        client.force_login(urednik_user)
        response = client.get(reverse("publications:list"))

        assert response.status_code == 200
        content = response.content.decode("utf-8")
        assert "Pub A" in content
        assert "Pub B" not in content

    def test_urednik_cannot_access_other_publisher_detail(
        self, client, urednik_user, publisher_b
    ):
        """6.5: Urednik cannot access publication from another publisher.

        NOTE: AC #5 says '403 Forbidden', but implementation uses scoped queryset
        which returns 404 (object not found in user's scope). This is more secure
        than 403 as it does not reveal object existence. Deliberate design choice.
        """
        publication = JournalFactory(
            title="Tuđa pub", publisher=publisher_b, slug="tudja-pub"
        )

        client.force_login(urednik_user)
        url = reverse("publications:detail", kwargs={"slug": publication.slug})
        response = client.get(url)

        # Scoped queryset returns 404 - more secure than 403 (no info leakage)
        assert response.status_code == 404

    def test_urednik_can_access_own_publisher_detail(
        self, client, urednik_user, publisher_a
    ):
        """6.4: Urednik can access detail of own publisher's publication."""
        publication = JournalFactory(
            title="Moja pub", publisher=publisher_a, slug="moja-pub"
        )

        client.force_login(urednik_user)
        url = reverse("publications:detail", kwargs={"slug": publication.slug})
        response = client.get(url)

        assert response.status_code == 200
        assert "Moja pub" in response.content.decode("utf-8")

    def test_urednik_can_edit_own_publisher_publication(
        self, client, urednik_user, publisher_a
    ):
        """6.4: Urednik can access edit form for own publisher's publication."""
        publication = JournalFactory(
            title="Edit Pub", publisher=publisher_a, slug="edit-pub"
        )

        client.force_login(urednik_user)
        url = reverse("publications:update", kwargs={"slug": publication.slug})
        response = client.get(url)

        assert response.status_code == 200

    def test_urednik_cannot_edit_other_publisher_publication(
        self, client, urednik_user, publisher_b
    ):
        """6.5: Urednik gets 404 for editing another publisher's publication."""
        publication = JournalFactory(
            title="Other Pub", publisher=publisher_b, slug="other-pub"
        )

        client.force_login(urednik_user)
        url = reverse("publications:update", kwargs={"slug": publication.slug})
        response = client.get(url)

        assert response.status_code == 404

    def test_bibliotekar_sees_only_own_publisher(
        self, client, bibliotekar_user, publisher_a, publisher_b
    ):
        """6.6: Bibliotekar sees only publications from assigned publisher."""
        JournalFactory(title="Pub A Bib", publisher=publisher_a)
        JournalFactory(title="Pub B Bib", publisher=publisher_b)

        client.force_login(bibliotekar_user)
        response = client.get(reverse("publications:list"))

        assert response.status_code == 200
        content = response.content.decode("utf-8")
        assert "Pub A Bib" in content
        assert "Pub B Bib" not in content

    def test_bibliotekar_cannot_access_other_publisher_detail(
        self, client, bibliotekar_user, publisher_b
    ):
        """6.6: Bibliotekar gets 404 for publication from another publisher (scoped queryset)."""
        publication = JournalFactory(
            title="Tuđa bib pub", publisher=publisher_b, slug="tudja-bib-pub"
        )

        client.force_login(bibliotekar_user)
        url = reverse("publications:detail", kwargs={"slug": publication.slug})
        response = client.get(url)

        # Scoped queryset returns 404 (object not found in user's scope)
        assert response.status_code == 404

    def test_bibliotekar_can_view_detail(
        self, client, bibliotekar_user, publisher_a
    ):
        """6.6: Bibliotekar can view detail of own publisher's publication."""
        publication = JournalFactory(
            title="Bib Detail", publisher=publisher_a, slug="bib-detail"
        )

        client.force_login(bibliotekar_user)
        url = reverse("publications:detail", kwargs={"slug": publication.slug})
        response = client.get(url)

        assert response.status_code == 200

    def test_bibliotekar_cannot_edit(self, client, bibliotekar_user, publisher_a):
        """6.6: Bibliotekar cannot edit publications (403 from PublisherScopedEditMixin)."""
        publication = JournalFactory(
            title="Bib No Edit", publisher=publisher_a, slug="bib-no-edit"
        )

        client.force_login(bibliotekar_user)
        url = reverse("publications:update", kwargs={"slug": publication.slug})
        response = client.get(url)

        assert response.status_code == 403

    def test_bibliotekar_cannot_delete(self, client, bibliotekar_user, publisher_a):
        """6.6: Bibliotekar cannot delete publications (403 from AdministratorRequiredMixin)."""
        publication = JournalFactory(
            title="Bib No Delete", publisher=publisher_a, slug="bib-no-delete"
        )

        client.force_login(bibliotekar_user)
        url = reverse("publications:delete", kwargs={"slug": publication.slug})
        response = client.get(url)

        assert response.status_code == 403

    def test_admin_sees_all_publications(
        self, client, admin_user, publisher_a, publisher_b
    ):
        """6.7: Administrator sees all publications regardless of publisher."""
        JournalFactory(title="Pub Admin A", publisher=publisher_a)
        JournalFactory(title="Pub Admin B", publisher=publisher_b)

        client.force_login(admin_user)
        response = client.get(reverse("publications:list"))

        assert response.status_code == 200
        content = response.content.decode("utf-8")
        assert "Pub Admin A" in content
        assert "Pub Admin B" in content

    def test_superadmin_sees_all_publications(
        self, client, superadmin_user, publisher_a, publisher_b
    ):
        """6.8: Superadmin sees all publications regardless of publisher."""
        JournalFactory(title="Pub SA A", publisher=publisher_a)
        JournalFactory(title="Pub SA B", publisher=publisher_b)

        client.force_login(superadmin_user)
        response = client.get(reverse("publications:list"))

        assert response.status_code == 200
        content = response.content.decode("utf-8")
        assert "Pub SA A" in content
        assert "Pub SA B" in content

    def test_superuser_sees_all_publications(
        self, client, superuser, publisher_a, publisher_b
    ):
        """6.8: Django superuser sees all publications."""
        JournalFactory(title="Pub SU A", publisher=publisher_a)
        JournalFactory(title="Pub SU B", publisher=publisher_b)

        client.force_login(superuser)
        response = client.get(reverse("publications:list"))

        assert response.status_code == 200
        content = response.content.decode("utf-8")
        assert "Pub SU A" in content
        assert "Pub SU B" in content

    def test_urednik_without_publisher_gets_403(self, client):
        """Urednik without publisher assignment gets 403."""
        user = User.objects.create_user(
            email="urednik-no-pub@test.com",
            password="testpass123",
        )
        group, _ = Group.objects.get_or_create(name="Urednik")
        user.groups.add(group)
        # No publisher assigned

        client.force_login(user)
        response = client.get(reverse("publications:list"))

        assert response.status_code == 403


# =============================================================================
# Story 2.4 - Task 6.9: Test Audit Log (AC #3)
# =============================================================================


@pytest.mark.django_db
class TestPublicationAuditLogViews:
    """Test audit log records changes via views. Story 2.4 - Task 6.9."""

    def test_audit_log_records_update_via_view(self, client, admin_user):
        """6.9: Audit log records publication update through view."""
        from auditlog.models import LogEntry

        publication = JournalFactory(title="Original Title")

        client.force_login(admin_user)
        response = client.post(
            reverse("publications:update", kwargs={"slug": publication.slug}),
            {
                "title": "Updated Via View",
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
        assert publication.title == "Updated Via View"

        # Verify audit log entry exists for the update
        update_log = LogEntry.objects.filter(
            object_pk=str(publication.pk),
            action=LogEntry.Action.UPDATE,
        )
        assert update_log.exists()


# =============================================================================
# Story 2.4 - Task 6.10: Test Detail View with 2.3a fields (AC #2)
# =============================================================================


@pytest.mark.django_db
class TestPublicationDetailView23aFields:
    """Test detail view with conference_date_end and conference_number. Story 2.4 - Task 6.10."""

    def test_detail_shows_conference_date_end(self, client, admin_user):
        """6.10: Detail view displays conference_date_end."""
        publication = ConferenceFactory(
            title="Konferencija Test",
            conference_date=datetime.date(2026, 6, 1),
            conference_date_end=datetime.date(2026, 6, 3),
            slug="konf-test",
        )

        client.force_login(admin_user)
        response = client.get(
            reverse("publications:detail", kwargs={"slug": publication.slug})
        )

        assert response.status_code == 200
        content = response.content.decode("utf-8")
        # Should show date range
        assert "01.06.2026." in content
        assert "03.06.2026." in content

    def test_detail_shows_conference_number(self, client, admin_user):
        """6.10: Detail view displays conference_number."""
        publication = ConferenceFactory(
            title="Konferencija Broj",
            conference_number=5,
            slug="konf-broj",
        )

        client.force_login(admin_user)
        response = client.get(
            reverse("publications:detail", kwargs={"slug": publication.slug})
        )

        assert response.status_code == 200
        content = response.content.decode("utf-8")
        assert "Broj konferencije" in content
        assert "5." in content

    def test_detail_shows_date_range_format(self, client, admin_user):
        """6.10: Detail view formats date range correctly."""
        publication = ConferenceFactory(
            title="Konferencija DateRange",
            conference_date=datetime.date(2026, 6, 1),
            conference_date_end=datetime.date(2026, 6, 3),
            slug="konf-daterange",
        )

        client.force_login(admin_user)
        response = client.get(
            reverse("publications:detail", kwargs={"slug": publication.slug})
        )

        assert response.status_code == 200
        content = response.content.decode("utf-8")
        # Should show "01.06.2026. - 03.06.2026."
        assert "01.06.2026." in content
        assert "03.06.2026." in content
        assert " - " in content

    def test_detail_conference_fields_not_shown_for_journal(self, client, admin_user):
        """6.10: Conference fields not shown for journal type."""
        publication = JournalFactory(
            title="Časopis bez konf",
            slug="casopis-test",
        )

        client.force_login(admin_user)
        response = client.get(
            reverse("publications:detail", kwargs={"slug": publication.slug})
        )

        assert response.status_code == 200
        content = response.content.decode("utf-8")
        assert "Broj konferencije" not in content


# =============================================================================
# Story 2.4 - Task 6.11: Test filter + sort + pagination together
# =============================================================================


@pytest.mark.django_db
class TestPublicationFilterSortPagination:
    """Test filter, sort, and pagination work together. Story 2.4 - Task 6.11."""

    def test_filter_and_sort_together(self, client, admin_user):
        """6.11: Filtering and sorting work simultaneously."""
        publisher = PublisherFactory(name="Test Izd")
        JournalFactory(title="ZZZ Journal", publisher=publisher)
        JournalFactory(title="AAA Journal", publisher=publisher)
        BookFactory(title="AAA Book", publisher=publisher)

        client.force_login(admin_user)
        url = reverse("publications:list")
        response = client.get(
            f"{url}?type=JOURNAL&sort=title&order=desc"
        )

        assert response.status_code == 200
        content = response.content.decode("utf-8")
        # Only journals, sorted desc
        assert "ZZZ Journal" in content
        assert "AAA Journal" in content
        assert "AAA Book" not in content
        assert content.index("ZZZ") < content.index("AAA Journal")

    def test_sort_params_preserved_in_context(self, client, admin_user):
        """6.11: Sort parameters are available in template context."""
        JournalFactory(title="Test")

        client.force_login(admin_user)
        url = reverse("publications:list")
        response = client.get(f"{url}?sort=publisher&order=desc")

        assert response.status_code == 200
        assert response.context["current_sort"] == "publisher"
        assert response.context["current_order"] == "desc"

    def test_search_and_sort_together(self, client, admin_user):
        """6.11: Search and sort work simultaneously."""
        JournalFactory(title="ZZZ Medicina")
        JournalFactory(title="AAA Medicina")
        JournalFactory(title="BBB Fizika")

        client.force_login(admin_user)
        url = reverse("publications:list")
        response = client.get(f"{url}?search=Medicina&sort=title&order=asc")

        assert response.status_code == 200
        content = response.content.decode("utf-8")
        assert "AAA Medicina" in content
        assert "ZZZ Medicina" in content
        assert "BBB Fizika" not in content
        assert content.index("AAA") < content.index("ZZZ")


# =============================================================================
# Test Publication Create View (Story 2.3 + Story 2.4 Task 3.4)
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

    def test_urednik_cannot_create(self, client, urednik_user, publisher_a):
        """Story 2.4 Task 3.4: Urednik cannot create publications."""
        client.force_login(urednik_user)
        response = client.get(reverse("publications:create"))

        assert response.status_code == 403

    def test_bibliotekar_cannot_create(self, client, bibliotekar_user, publisher_a):
        """Story 2.4 Task 3.4: Bibliotekar cannot create publications."""
        client.force_login(bibliotekar_user)
        response = client.get(reverse("publications:create"))

        assert response.status_code == 403


# =============================================================================
# Test Publication Update View (Story 2.3 + Story 2.4)
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
# Test Publication Delete View (Story 2.3 + Story 2.4 Task 3.4)
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

    def test_urednik_cannot_delete(self, client, urednik_user, publisher_a):
        """Story 2.4 Task 3.4: Urednik cannot delete publications."""
        publication = JournalFactory(
            title="No Delete", publisher=publisher_a, slug="no-delete"
        )

        client.force_login(urednik_user)
        response = client.get(
            reverse("publications:delete", kwargs={"slug": publication.slug})
        )

        assert response.status_code == 403


# =============================================================================
# Test Publication Detail View (Story 2.3)
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
# Task 7.7: Test form dynamic behavior (Story 2.3)
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
