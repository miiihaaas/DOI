"""
Tests for Deleted Items views.

Story 6.3: Soft Delete Implementation - Task 14.
"""

import pytest
from django.contrib.auth.models import Group
from django.test import Client
from django.urls import reverse

from doi_portal.articles.models import Article, Author
from doi_portal.articles.tests.factories import ArticleFactory, AuthorFactory
from doi_portal.issues.models import Issue
from doi_portal.issues.tests.factories import IssueFactory
from doi_portal.publications.models import Publication
from doi_portal.publications.tests.factories import PublicationFactory, PublisherFactory
from doi_portal.publishers.models import Publisher
from doi_portal.users.tests.factories import UserFactory


@pytest.fixture
def superadmin_user(db):
    """Create a Superadmin user."""
    user = UserFactory()
    group, _ = Group.objects.get_or_create(name="Superadmin")
    user.groups.add(group)
    return user


@pytest.fixture
def regular_user(db):
    """Create a regular user with Bibliotekar role."""
    user = UserFactory()
    group, _ = Group.objects.get_or_create(name="Bibliotekar")
    user.groups.add(group)
    return user


@pytest.fixture
def superadmin_client(superadmin_user):
    """Client logged in as Superadmin."""
    client = Client()
    client.force_login(superadmin_user)
    return client


@pytest.fixture
def regular_client(regular_user):
    """Client logged in as regular user."""
    client = Client()
    client.force_login(regular_user)
    return client


# ============================================================================
# Task 14.1: Superadmin can access deleted-items page (200)
# ============================================================================


@pytest.mark.django_db
class TestDeletedItemsAccess:
    def test_superadmin_can_access(self, superadmin_client):
        url = reverse("core:deleted-items")
        response = superadmin_client.get(url)
        assert response.status_code == 200

    def test_non_superadmin_gets_403(self, regular_client):
        """Task 14.2: Non-Superadmin gets 403."""
        url = reverse("core:deleted-items")
        response = regular_client.get(url)
        assert response.status_code == 403

    def test_unauthenticated_redirects_to_login(self):
        """Task 14.3: Unauthenticated user redirected to login."""
        client = Client()
        url = reverse("core:deleted-items")
        response = client.get(url)
        assert response.status_code == 302
        assert "/accounts/login/" in response.url


# ============================================================================
# Task 14.4: Page displays soft-deleted records of all models
# ============================================================================


@pytest.mark.django_db
class TestDeletedItemsDisplay:
    def test_displays_soft_deleted_records(self, superadmin_client, superadmin_user):
        publisher = PublisherFactory()
        publisher.soft_delete(user=superadmin_user)

        publication = PublicationFactory()
        publication.soft_delete(user=superadmin_user)

        issue = IssueFactory()
        issue.soft_delete(user=superadmin_user)

        article = ArticleFactory()
        article.soft_delete(user=superadmin_user)

        author = AuthorFactory()
        author.soft_delete(user=superadmin_user)

        url = reverse("core:deleted-items")
        response = superadmin_client.get(url)

        assert response.status_code == 200
        context = response.context

        sections = {s["key"]: s for s in context["deleted_sections"]}
        assert sections["publisher"]["count"] == 1
        assert sections["publication"]["count"] == 1
        assert sections["issue"]["count"] == 1
        assert sections["article"]["count"] == 1
        assert sections["author"]["count"] == 1
        assert context["total_deleted_count"] == 5

    def test_filter_by_model_type(self, superadmin_client, superadmin_user):
        """Task 14.7: Filter by model type works."""
        publisher = PublisherFactory()
        publisher.soft_delete(user=superadmin_user)

        article = ArticleFactory()
        article.soft_delete(user=superadmin_user)

        url = reverse("core:deleted-items") + "?type=publisher"
        response = superadmin_client.get(url)

        assert response.status_code == 200
        context = response.context
        sections = {s["key"]: s for s in context["deleted_sections"]}
        assert sections["publisher"]["count"] == 1
        assert sections["publication"]["count"] == 0
        assert sections["article"]["count"] == 0

    def test_empty_state_message(self, superadmin_client):
        """No deleted items shows empty state message."""
        url = reverse("core:deleted-items")
        response = superadmin_client.get(url)

        assert response.status_code == 200
        assert response.context["total_deleted_count"] == 0
        assert "Nema obrisanih stavki" in response.content.decode()


# ============================================================================
# Task 14.5: Restore endpoint returns record to normal state
# ============================================================================


@pytest.mark.django_db
class TestRestoreEndpoint:
    def test_restore_publisher(self, superadmin_client, superadmin_user):
        publisher = PublisherFactory()
        publisher.soft_delete(user=superadmin_user)

        url = reverse(
            "core:deleted-item-restore",
            kwargs={"model_type": "publisher", "pk": publisher.pk},
        )
        response = superadmin_client.post(url)

        assert response.status_code == 200
        publisher.refresh_from_db()
        assert publisher.is_deleted is False
        assert publisher.deleted_at is None
        assert publisher.deleted_by is None

    def test_restore_requires_post(self, superadmin_client, superadmin_user):
        """Task 14.8: Restore requires POST method."""
        publisher = PublisherFactory()
        publisher.soft_delete(user=superadmin_user)

        url = reverse(
            "core:deleted-item-restore",
            kwargs={"model_type": "publisher", "pk": publisher.pk},
        )
        response = superadmin_client.get(url)
        assert response.status_code == 405

    def test_restore_requires_superadmin(self, regular_client, superadmin_user):
        """Task 14.9: Restore requires Superadmin access."""
        publisher = PublisherFactory()
        publisher.soft_delete(user=superadmin_user)

        url = reverse(
            "core:deleted-item-restore",
            kwargs={"model_type": "publisher", "pk": publisher.pk},
        )
        response = regular_client.post(url)
        assert response.status_code == 403


# ============================================================================
# Task 14.6: Permanent delete endpoint physically deletes record
# ============================================================================


@pytest.mark.django_db
class TestPermanentDeleteEndpoint:
    def test_permanent_delete_publisher(self, superadmin_client, superadmin_user):
        publisher = PublisherFactory()
        publisher.soft_delete(user=superadmin_user)
        pk = publisher.pk

        url = reverse(
            "core:deleted-item-permanent-delete",
            kwargs={"model_type": "publisher", "pk": pk},
        )
        response = superadmin_client.post(url)

        assert response.status_code == 200
        assert not Publisher.all_objects.filter(pk=pk).exists()

    def test_permanent_delete_requires_post(self, superadmin_client, superadmin_user):
        """Task 14.8: Permanent delete requires POST method."""
        publisher = PublisherFactory()
        publisher.soft_delete(user=superadmin_user)

        url = reverse(
            "core:deleted-item-permanent-delete",
            kwargs={"model_type": "publisher", "pk": publisher.pk},
        )
        response = superadmin_client.get(url)
        assert response.status_code == 405

    def test_permanent_delete_requires_superadmin(self, regular_client, superadmin_user):
        """Task 14.9: Permanent delete requires Superadmin access."""
        publisher = PublisherFactory()
        publisher.soft_delete(user=superadmin_user)

        url = reverse(
            "core:deleted-item-permanent-delete",
            kwargs={"model_type": "publisher", "pk": publisher.pk},
        )
        response = regular_client.post(url)
        assert response.status_code == 403

    def test_invalid_model_type_returns_404(self, superadmin_client):
        url = reverse(
            "core:deleted-item-restore",
            kwargs={"model_type": "invalid", "pk": 1},
        )
        response = superadmin_client.post(url)
        assert response.status_code == 404
