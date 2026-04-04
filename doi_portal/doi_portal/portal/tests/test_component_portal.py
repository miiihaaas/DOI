"""
Portal tests for component landing page.

Tests ComponentLandingView: access, context, 404 for deleted/nonexistent.
"""

import pytest
from django.urls import reverse

from doi_portal.components.tests.factories import (
    ComponentContributorFactory,
    ComponentFactory,
    ComponentGroupFactory,
)


@pytest.mark.django_db
class TestComponentLandingView:
    """Tests for ComponentLandingView (public portal)."""

    def test_component_landing_accessible(self, client):
        """Component landing page is accessible without authentication."""
        comp = ComponentFactory(title="Test Audio Track")
        url = reverse("portal-components:component-detail", args=[comp.pk])
        response = client.get(url)
        assert response.status_code == 200
        assert "Test Audio Track" in response.content.decode()

    def test_component_landing_context(self, client):
        """Landing page has correct context data."""
        comp = ComponentFactory(
            doi_suffix="comp.context",
            title="Context Test",
        )
        ComponentContributorFactory(
            component=comp,
            given_name="Petar",
            surname="Petrović",
        )
        url = reverse("portal-components:component-detail", args=[comp.pk])
        response = client.get(url)
        assert response.status_code == 200

        content = response.content.decode()
        assert comp.full_doi in content
        assert comp.component_group.parent_doi in content
        assert "Petrović" in content

    def test_nonexistent_component_404(self, client):
        """Nonexistent component returns 404."""
        url = reverse("portal-components:component-detail", args=[99999])
        response = client.get(url)
        assert response.status_code == 404

    def test_soft_deleted_component_404(self, client):
        """Soft-deleted component returns 404."""
        comp = ComponentFactory()
        comp.is_deleted = True
        comp.save()
        url = reverse("portal-components:component-detail", args=[comp.pk])
        response = client.get(url)
        assert response.status_code == 404

    def test_component_landing_with_mime_type(self, client):
        """Landing page displays MIME type badge."""
        comp = ComponentFactory(format_mime_type="audio/mpeg")
        url = reverse("portal-components:component-detail", args=[comp.pk])
        response = client.get(url)
        assert response.status_code == 200
        assert "audio/mpeg" in response.content.decode()

    def test_component_landing_with_description(self, client):
        """Landing page displays description."""
        comp = ComponentFactory(
            title="Desc Test",
            description="Ovo je test opis komponente",
        )
        url = reverse("portal-components:component-detail", args=[comp.pk])
        response = client.get(url)
        assert response.status_code == 200
        assert "Ovo je test opis komponente" in response.content.decode()

    def test_component_landing_publisher_info(self, client):
        """Landing page shows publisher name."""
        comp = ComponentFactory()
        url = reverse("portal-components:component-detail", args=[comp.pk])
        response = client.get(url)
        assert response.status_code == 200
        assert comp.component_group.publisher.name in response.content.decode()
