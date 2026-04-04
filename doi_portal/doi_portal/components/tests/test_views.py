"""
View tests for components app.

Tests CRUD views for ComponentGroup, Component, and contributor HTMX endpoints.
"""

import json

import pytest
from django.test import Client
from django.urls import reverse

from doi_portal.components.models import Component, ComponentContributor, ComponentGroup
from doi_portal.users.tests.factories import UserFactory

from .factories import ComponentContributorFactory, ComponentFactory, ComponentGroupFactory


@pytest.fixture
def admin_user(db):
    """Create an admin user with superuser status."""
    user = UserFactory(email="admin@test.com")
    user.is_superuser = True
    user.save()
    return user


@pytest.fixture
def publisher_user(db):
    """Create a user with publisher assignment."""
    from doi_portal.publications.tests.factories import PublisherFactory
    user = UserFactory(email="editor@test.com")
    publisher = PublisherFactory()
    user.publisher = publisher
    user.save()
    # Add Urednik group
    from django.contrib.auth.models import Group
    group, _ = Group.objects.get_or_create(name="Urednik")
    user.groups.add(group)
    return user, publisher


@pytest.mark.django_db
class TestComponentGroupListView:
    """Tests for ComponentGroupListView."""

    def test_list_requires_login(self, client):
        """Unauthenticated users are redirected to login."""
        url = reverse("components:group-list")
        response = client.get(url)
        assert response.status_code == 302
        assert "login" in response.url.lower() or "accounts" in response.url.lower()

    def test_list_authenticated(self, client, admin_user):
        """Authenticated admin can see list."""
        client.force_login(admin_user)
        ComponentGroupFactory()
        url = reverse("components:group-list")
        response = client.get(url)
        assert response.status_code == 200

    def test_list_scoped_to_publisher(self, client, publisher_user):
        """User sees only their publisher's groups."""
        user, publisher = publisher_user
        client.force_login(user)
        own = ComponentGroupFactory(publisher=publisher)
        other = ComponentGroupFactory()

        url = reverse("components:group-list")
        response = client.get(url)
        assert response.status_code == 200
        content = response.content.decode()
        assert own.parent_doi in content
        assert other.parent_doi not in content


@pytest.mark.django_db
class TestComponentGroupCreateView:
    """Tests for ComponentGroupCreateView."""

    def test_create_requires_login(self, client):
        url = reverse("components:group-create")
        response = client.get(url)
        assert response.status_code == 302

    def test_create_get(self, client, admin_user):
        client.force_login(admin_user)
        url = reverse("components:group-create")
        response = client.get(url)
        assert response.status_code == 200

    def test_create_post(self, client, admin_user):
        from doi_portal.publications.tests.factories import PublisherFactory
        client.force_login(admin_user)
        publisher = PublisherFactory()
        url = reverse("components:group-create")
        response = client.post(url, {
            "publisher": publisher.pk,
            "parent_doi": "10.12345/test.new",
            "title": "Test Group",
        })
        assert response.status_code == 302
        assert ComponentGroup.objects.filter(parent_doi="10.12345/test.new").exists()


@pytest.mark.django_db
class TestComponentGroupDetailView:
    """Tests for ComponentGroupDetailView."""

    def test_detail_authenticated(self, client, admin_user):
        client.force_login(admin_user)
        cg = ComponentGroupFactory()
        url = reverse("components:group-detail", args=[cg.pk])
        response = client.get(url)
        assert response.status_code == 200

    def test_detail_wrong_publisher(self, client, publisher_user):
        """User cannot see group from different publisher."""
        user, publisher = publisher_user
        client.force_login(user)
        cg = ComponentGroupFactory()  # Different publisher
        url = reverse("components:group-detail", args=[cg.pk])
        response = client.get(url)
        assert response.status_code == 403


@pytest.mark.django_db
class TestComponentGroupUpdateView:
    """Tests for ComponentGroupUpdateView."""

    def test_update_post(self, client, admin_user):
        client.force_login(admin_user)
        cg = ComponentGroupFactory()
        url = reverse("components:group-update", args=[cg.pk])
        response = client.post(url, {
            "publisher": cg.publisher.pk,
            "parent_doi": cg.parent_doi,
            "title": "Updated Title",
        })
        assert response.status_code == 302
        cg.refresh_from_db()
        assert cg.title == "Updated Title"


@pytest.mark.django_db
class TestComponentCRUD:
    """Tests for Component create/detail/update views."""

    def test_component_create(self, client, admin_user):
        client.force_login(admin_user)
        cg = ComponentGroupFactory()
        url = reverse("components:component-create", args=[cg.pk])
        response = client.post(url, {
            "title": "New Component",
            "doi_suffix": "comp.new",
            "format_mime_type": "audio/mpeg",
            "parent_relation": "isPartOf",
            "order": 0,
        })
        assert response.status_code == 302
        assert Component.objects.filter(doi_suffix="comp.new").exists()

    def test_component_detail(self, client, admin_user):
        client.force_login(admin_user)
        comp = ComponentFactory()
        url = reverse("components:component-detail", args=[
            comp.component_group.pk, comp.pk
        ])
        response = client.get(url)
        assert response.status_code == 200

    def test_component_update(self, client, admin_user):
        client.force_login(admin_user)
        comp = ComponentFactory()
        url = reverse("components:component-update", args=[
            comp.component_group.pk, comp.pk
        ])
        response = client.post(url, {
            "title": "Updated Component",
            "doi_suffix": comp.doi_suffix,
            "format_mime_type": "video/mp4",
            "parent_relation": "isPartOf",
            "order": 0,
        })
        assert response.status_code == 302
        comp.refresh_from_db()
        assert comp.title == "Updated Component"


@pytest.mark.django_db
class TestContributorHTMX:
    """Tests for contributor HTMX endpoints."""

    def test_contributor_add(self, client, admin_user):
        client.force_login(admin_user)
        comp = ComponentFactory()
        url = reverse("components:contributor-add", args=[comp.pk])
        response = client.post(url, {
            "given_name": "Petar",
            "surname": "Petrović",
            "sequence": "first",
            "contributor_role": "author",
        })
        assert response.status_code == 200
        assert ComponentContributor.objects.filter(
            component=comp, surname="Petrović"
        ).exists()

    def test_contributor_update(self, client, admin_user):
        client.force_login(admin_user)
        ct = ComponentContributorFactory(surname="Original")
        url = reverse("components:contributor-update", args=[ct.pk])
        response = client.post(url, {
            "given_name": ct.given_name,
            "surname": "Updated",
            "sequence": ct.sequence,
            "contributor_role": ct.contributor_role,
        })
        assert response.status_code == 200
        ct.refresh_from_db()
        assert ct.surname == "Updated"

    def test_contributor_delete(self, client, admin_user):
        client.force_login(admin_user)
        ct = ComponentContributorFactory()
        url = reverse("components:contributor-delete", args=[ct.pk])
        response = client.post(url)
        assert response.status_code == 200
        assert not ComponentContributor.objects.filter(pk=ct.pk).exists()

    def test_contributor_reorder(self, client, admin_user):
        client.force_login(admin_user)
        comp = ComponentFactory()
        ct1 = ComponentContributorFactory(component=comp, order=1)
        ct2 = ComponentContributorFactory(component=comp, order=2)
        url = reverse("components:contributor-reorder", args=[comp.pk])
        response = client.post(
            url,
            json.dumps({"order": [ct2.pk, ct1.pk]}),
            content_type="application/json",
        )
        assert response.status_code == 200
        ct1.refresh_from_db()
        ct2.refresh_from_db()
        assert ct2.order == 1
        assert ct1.order == 2

    def test_contributor_form_view(self, client, admin_user):
        client.force_login(admin_user)
        comp = ComponentFactory()
        url = reverse("components:contributor-form", args=[comp.pk])
        response = client.get(url)
        assert response.status_code == 200

    def test_contributor_edit_form_view(self, client, admin_user):
        client.force_login(admin_user)
        ct = ComponentContributorFactory()
        url = reverse("components:contributor-edit-form", args=[ct.pk])
        response = client.get(url)
        assert response.status_code == 200
