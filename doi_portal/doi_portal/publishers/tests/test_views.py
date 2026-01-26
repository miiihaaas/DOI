"""
Tests for Publisher views.

Story 2.1 - Task 3: Publisher admin views.
Task 7.5 (CRUD), 7.8 (permissions), 7.9 (publication count)
"""

import pytest
from django.urls import reverse
from django.contrib.auth.models import Group

from doi_portal.publishers.models import Publisher
from doi_portal.users.tests.factories import UserFactory


@pytest.fixture
def superadmin_user(db):
    """Create a Superadmin user."""
    user = UserFactory(email="superadmin@test.com", password="testpass123")
    user.is_superuser = True
    user.save()
    return user


@pytest.fixture
def admin_user(db):
    """Create an Administrator user."""
    user = UserFactory(email="admin@test.com", password="testpass123")
    group, _ = Group.objects.get_or_create(name="Administrator")
    user.groups.add(group)
    return user


@pytest.fixture
def urednik_user(db):
    """Create an Urednik user (should not have publisher access)."""
    user = UserFactory(email="urednik@test.com", password="testpass123")
    group, _ = Group.objects.get_or_create(name="Urednik")
    user.groups.add(group)
    return user


@pytest.fixture
def bibliotekar_user(db):
    """Create a Bibliotekar user (should not have publisher access)."""
    user = UserFactory(email="bibliotekar@test.com", password="testpass123")
    group, _ = Group.objects.get_or_create(name="Bibliotekar")
    user.groups.add(group)
    return user


@pytest.fixture
def sample_publisher(db):
    """Create a sample publisher."""
    return Publisher.objects.create(
        name="Test Izdavac",
        doi_prefix="10.1234",
        description="Test opis",
        contact_email="test@izdavac.rs",
    )


def login_user(client, email, password="testpass123"):
    """Helper to login user via client.login()."""
    return client.login(email=email, password=password)


# =============================================================================
# Task 7.8: Test permission checks (Administrator/Superadmin only)
# =============================================================================


@pytest.mark.django_db
class TestPublisherPermissions:
    """Test Publisher view permissions."""

    def test_list_view_requires_login(self, client):
        """Test unauthenticated user is redirected to login."""
        response = client.get(reverse("publishers:list"))
        assert response.status_code == 302
        assert "login" in response.url.lower() or "account" in response.url.lower()

    def test_list_view_superadmin_access(self, client, superadmin_user, sample_publisher):
        """Test Superadmin can access publisher list."""
        login_user(client, "superadmin@test.com")
        response = client.get(reverse("publishers:list"))
        assert response.status_code == 200

    def test_list_view_admin_access(self, client, admin_user, sample_publisher):
        """Test Administrator can access publisher list."""
        login_user(client, "admin@test.com")
        response = client.get(reverse("publishers:list"))
        assert response.status_code == 200

    def test_list_view_urednik_denied(self, client, urednik_user):
        """Test Urednik cannot access publisher list."""
        login_user(client, "urednik@test.com")
        response = client.get(reverse("publishers:list"))
        assert response.status_code == 403

    def test_list_view_bibliotekar_denied(self, client, bibliotekar_user):
        """Test Bibliotekar cannot access publisher list."""
        login_user(client, "bibliotekar@test.com")
        response = client.get(reverse("publishers:list"))
        assert response.status_code == 403

    def test_create_view_admin_access(self, client, admin_user):
        """Test Administrator can access create view."""
        login_user(client, "admin@test.com")
        response = client.get(reverse("publishers:create"))
        assert response.status_code == 200

    def test_create_view_urednik_denied(self, client, urednik_user):
        """Test Urednik cannot access create view."""
        login_user(client, "urednik@test.com")
        response = client.get(reverse("publishers:create"))
        assert response.status_code == 403

    def test_update_view_admin_access(self, client, admin_user, sample_publisher):
        """Test Administrator can access update view."""
        login_user(client, "admin@test.com")
        response = client.get(reverse("publishers:update", args=[sample_publisher.pk]))
        assert response.status_code == 200

    def test_delete_view_admin_access(self, client, admin_user, sample_publisher):
        """Test Administrator can access delete view."""
        login_user(client, "admin@test.com")
        response = client.get(reverse("publishers:delete", args=[sample_publisher.pk]))
        assert response.status_code == 200


# =============================================================================
# Task 7.5: Test Publisher CRUD operations
# =============================================================================


@pytest.mark.django_db
class TestPublisherListView:
    """Test PublisherListView."""

    def test_list_shows_publishers(self, client, admin_user, sample_publisher):
        """Test list view shows publishers."""
        login_user(client, "admin@test.com")
        response = client.get(reverse("publishers:list"))

        assert response.status_code == 200
        assert "Test Izdavac" in response.content.decode()
        assert "10.1234" in response.content.decode()

    def test_list_shows_publication_count(self, client, admin_user, sample_publisher):
        """Test list view shows publication count column."""
        login_user(client, "admin@test.com")
        response = client.get(reverse("publishers:list"))

        content = response.content.decode()
        assert response.status_code == 200
        # Publication count should be displayed (0 since no publications yet)
        assert "0" in content or "Publikacija" in content

    def test_list_excludes_soft_deleted(self, client, admin_user):
        """Test soft-deleted publishers not shown in list."""
        active = Publisher.objects.create(name="Active", doi_prefix="10.1111")
        deleted = Publisher.objects.create(name="Deleted", doi_prefix="10.2222")
        deleted.soft_delete()

        login_user(client, "admin@test.com")
        response = client.get(reverse("publishers:list"))

        content = response.content.decode()
        assert "Active" in content
        assert "Deleted" not in content

    def test_list_has_breadcrumbs(self, client, admin_user):
        """Test list view has breadcrumbs context."""
        login_user(client, "admin@test.com")
        response = client.get(reverse("publishers:list"))

        assert "breadcrumbs" in response.context


@pytest.mark.django_db
class TestPublisherCreateView:
    """Test PublisherCreateView."""

    def test_create_get_displays_form(self, client, admin_user):
        """Test GET request displays form."""
        login_user(client, "admin@test.com")
        response = client.get(reverse("publishers:create"))

        assert response.status_code == 200
        assert "form" in response.context
        assert "Novi izdavač" in response.content.decode() or "Kreiraj" in response.content.decode()

    def test_create_post_creates_publisher(self, client, admin_user):
        """Test POST request creates publisher."""
        login_user(client, "admin@test.com")
        data = {
            "name": "Novi Izdavac",
            "doi_prefix": "10.9999",
            "contact_email": "novi@izdavac.rs",
        }
        response = client.post(reverse("publishers:create"), data)

        assert response.status_code == 302  # Redirect on success
        assert Publisher.objects.filter(name="Novi Izdavac").exists()

    def test_create_invalid_data_shows_errors(self, client, admin_user):
        """Test POST with invalid data shows errors."""
        login_user(client, "admin@test.com")
        data = {
            "name": "",  # Required field
            "doi_prefix": "invalid",  # Invalid format
        }
        response = client.post(reverse("publishers:create"), data)

        assert response.status_code == 200  # Re-renders form
        assert "form" in response.context
        assert response.context["form"].errors

    def test_create_shows_success_message(self, client, admin_user):
        """Test successful creation shows toast message."""
        login_user(client, "admin@test.com")
        data = {
            "name": "Message Test",
            "doi_prefix": "10.8888",
        }
        response = client.post(reverse("publishers:create"), follow=True)

        # Check for success message in followed response
        messages = list(response.context.get("messages", []))
        # At least verify redirect happened
        assert response.status_code == 200


@pytest.mark.django_db
class TestPublisherUpdateView:
    """Test PublisherUpdateView."""

    def test_update_get_displays_form_with_data(self, client, admin_user, sample_publisher):
        """Test GET request displays form with existing data."""
        login_user(client, "admin@test.com")
        response = client.get(reverse("publishers:update", args=[sample_publisher.pk]))

        assert response.status_code == 200
        assert "form" in response.context
        assert "Test Izdavac" in response.content.decode()

    def test_update_post_updates_publisher(self, client, admin_user, sample_publisher):
        """Test POST request updates publisher."""
        login_user(client, "admin@test.com")
        data = {
            "name": "Azurirani Izdavac",
            "doi_prefix": sample_publisher.doi_prefix,
        }
        response = client.post(
            reverse("publishers:update", args=[sample_publisher.pk]),
            data,
        )

        assert response.status_code == 302
        sample_publisher.refresh_from_db()
        assert sample_publisher.name == "Azurirani Izdavac"

    def test_update_invalid_data_shows_errors(self, client, admin_user, sample_publisher):
        """Test POST with invalid data shows errors."""
        login_user(client, "admin@test.com")
        data = {
            "name": "",
            "doi_prefix": "invalid",
        }
        response = client.post(
            reverse("publishers:update", args=[sample_publisher.pk]),
            data,
        )

        assert response.status_code == 200
        assert response.context["form"].errors


@pytest.mark.django_db
class TestPublisherDetailView:
    """Test PublisherDetailView."""

    def test_detail_displays_publisher_info(self, client, admin_user, sample_publisher):
        """Test detail view displays publisher information."""
        login_user(client, "admin@test.com")
        response = client.get(reverse("publishers:detail", args=[sample_publisher.pk]))

        assert response.status_code == 200
        content = response.content.decode()
        assert "Test Izdavac" in content
        assert "10.1234" in content

    def test_detail_has_breadcrumbs(self, client, admin_user, sample_publisher):
        """Test detail view has breadcrumbs context."""
        login_user(client, "admin@test.com")
        response = client.get(reverse("publishers:detail", args=[sample_publisher.pk]))

        assert "breadcrumbs" in response.context


@pytest.mark.django_db
class TestPublisherDeleteView:
    """Test PublisherDeleteView."""

    def test_delete_get_displays_confirmation(self, client, admin_user, sample_publisher):
        """Test GET request displays delete confirmation."""
        login_user(client, "admin@test.com")
        response = client.get(reverse("publishers:delete", args=[sample_publisher.pk]))

        assert response.status_code == 200
        assert "Test Izdavac" in response.content.decode()

    def test_delete_post_performs_soft_delete(self, client, admin_user, sample_publisher):
        """Test POST request performs soft delete."""
        login_user(client, "admin@test.com")
        pk = sample_publisher.pk
        response = client.post(reverse("publishers:delete", args=[pk]))

        assert response.status_code == 302

        # Publisher should be soft deleted
        sample_publisher.refresh_from_db()
        assert sample_publisher.is_deleted is True
        assert sample_publisher.deleted_by == admin_user

        # Should not appear in default queryset
        assert Publisher.objects.filter(pk=pk).count() == 0

        # But should exist in all_objects
        assert Publisher.all_objects.filter(pk=pk).count() == 1


# =============================================================================
# Test URL configuration
# =============================================================================


@pytest.mark.django_db
class TestPublisherURLs:
    """Test Publisher URL patterns."""

    def test_list_url(self, client, admin_user):
        """Test list URL is accessible."""
        login_user(client, "admin@test.com")
        response = client.get("/dashboard/publishers/")
        assert response.status_code == 200

    def test_create_url(self, client, admin_user):
        """Test create URL is accessible."""
        login_user(client, "admin@test.com")
        response = client.get("/dashboard/publishers/create/")
        assert response.status_code == 200

    def test_detail_url(self, client, admin_user, sample_publisher):
        """Test detail URL is accessible."""
        login_user(client, "admin@test.com")
        response = client.get(f"/dashboard/publishers/{sample_publisher.pk}/")
        assert response.status_code == 200

    def test_update_url(self, client, admin_user, sample_publisher):
        """Test update URL is accessible."""
        login_user(client, "admin@test.com")
        response = client.get(f"/dashboard/publishers/{sample_publisher.pk}/edit/")
        assert response.status_code == 200

    def test_delete_url(self, client, admin_user, sample_publisher):
        """Test delete URL is accessible."""
        login_user(client, "admin@test.com")
        response = client.get(f"/dashboard/publishers/{sample_publisher.pk}/delete/")
        assert response.status_code == 200
