"""
Crossref workflow tests for component support.

Tests validation, generation, preview, download, deposit views.
"""

import pytest
from django.urls import reverse

from doi_portal.components.tests.factories import (
    ComponentContributorFactory,
    ComponentFactory,
    ComponentGroupFactory,
)
from doi_portal.crossref.models import CrossrefExport, ExportType
from doi_portal.users.tests.factories import UserFactory


@pytest.fixture
def admin_user(db):
    """Create an admin user with superuser status."""
    user = UserFactory(email="crossref-admin@test.com")
    user.is_superuser = True
    user.save()
    return user


@pytest.fixture
def component_group_with_data(db):
    """Create a component group with components and contributors."""
    cg = ComponentGroupFactory(parent_doi="10.12345/workflow.test")
    comp = ComponentFactory(
        component_group=cg,
        doi_suffix="comp.workflow",
        title="Workflow Test",
        format_mime_type="audio/mpeg",
    )
    ComponentContributorFactory(
        component=comp,
        given_name="Test",
        surname="Author",
    )
    return cg


@pytest.mark.django_db
class TestComponentValidationView:
    """Tests for ComponentGroupValidationView."""

    def test_validation_returns_partial(self, client, admin_user, component_group_with_data):
        client.force_login(admin_user)
        url = reverse("crossref:component-group-validate", args=[component_group_with_data.pk])
        response = client.get(url)
        assert response.status_code == 200

    def test_validation_unauthenticated(self, client, component_group_with_data):
        url = reverse("crossref:component-group-validate", args=[component_group_with_data.pk])
        response = client.get(url)
        assert response.status_code == 302


@pytest.mark.django_db
class TestGenerateComponentXMLView:
    """Tests for GenerateComponentXMLView."""

    def test_generate_sync(self, client, admin_user, component_group_with_data):
        client.force_login(admin_user)
        url = reverse("crossref:component-group-generate", args=[component_group_with_data.pk])
        response = client.post(url)
        assert response.status_code == 200
        component_group_with_data.refresh_from_db()
        assert component_group_with_data.crossref_xml != ""

    def test_generate_requires_post(self, client, admin_user, component_group_with_data):
        client.force_login(admin_user)
        url = reverse("crossref:component-group-generate", args=[component_group_with_data.pk])
        response = client.get(url)
        assert response.status_code == 405


@pytest.mark.django_db
class TestComponentXMLPreview:
    """Tests for component_xml_preview."""

    def test_preview_with_xml(self, client, admin_user, component_group_with_data):
        from doi_portal.crossref.services import CrossrefService
        service = CrossrefService()
        service.generate_and_store_component_xml(component_group_with_data)

        client.force_login(admin_user)
        url = reverse("crossref:component-xml-preview", args=[component_group_with_data.pk])
        response = client.get(url)
        assert response.status_code == 200

    def test_preview_without_xml(self, client, admin_user, component_group_with_data):
        client.force_login(admin_user)
        url = reverse("crossref:component-xml-preview", args=[component_group_with_data.pk])
        response = client.get(url)
        assert response.status_code == 200
        assert "nije generisan" in response.content.decode()


@pytest.mark.django_db
class TestComponentXMLDownload:
    """Tests for component_xml_download."""

    def test_download_creates_export(self, client, admin_user, component_group_with_data):
        from doi_portal.crossref.services import CrossrefService
        service = CrossrefService()
        service.generate_and_store_component_xml(component_group_with_data)

        client.force_login(admin_user)
        url = reverse("crossref:component-xml-download", args=[component_group_with_data.pk])
        response = client.get(url)
        assert response.status_code == 200
        assert response["Content-Type"] == "application/xml; charset=utf-8"

        # Verify export record created
        export = CrossrefExport.objects.filter(
            component_group=component_group_with_data
        ).first()
        assert export is not None
        assert export.export_type == ExportType.COMPONENT_GROUP
        assert export.issue is None

    def test_download_without_xml(self, client, admin_user, component_group_with_data):
        client.force_login(admin_user)
        url = reverse("crossref:component-xml-download", args=[component_group_with_data.pk])
        response = client.get(url)
        assert response.status_code == 404


@pytest.mark.django_db
class TestComponentDeposit:
    """Tests for ComponentGroupDepositView and mark_deposited."""

    def test_deposit_page(self, client, admin_user, component_group_with_data):
        client.force_login(admin_user)
        url = reverse("crossref:component-group-deposit", args=[component_group_with_data.pk])
        response = client.get(url)
        assert response.status_code == 200

    def test_mark_deposited(self, client, admin_user, component_group_with_data):
        client.force_login(admin_user)
        url = reverse("crossref:component-mark-deposited", args=[component_group_with_data.pk])
        response = client.post(url)
        assert response.status_code == 200
        component_group_with_data.refresh_from_db()
        assert component_group_with_data.crossref_deposited_at is not None
        assert component_group_with_data.crossref_deposited_by == admin_user

    def test_mark_deposited_get_not_allowed(self, client, admin_user, component_group_with_data):
        client.force_login(admin_user)
        url = reverse("crossref:component-mark-deposited", args=[component_group_with_data.pk])
        response = client.get(url)
        assert response.status_code == 405


@pytest.mark.django_db
class TestComponentExportHistory:
    """Tests for component_export_history and export_redownload."""

    def test_export_history(self, client, admin_user, component_group_with_data):
        client.force_login(admin_user)
        url = reverse("crossref:component-export-history", args=[component_group_with_data.pk])
        response = client.get(url)
        assert response.status_code == 200

    def test_export_redownload_with_component_group(self, client, admin_user, component_group_with_data):
        """export_redownload works for component_group exports (nullable issue)."""
        from doi_portal.crossref.services import CrossrefService
        service = CrossrefService()
        service.generate_and_store_component_xml(component_group_with_data)

        # Create export via download
        client.force_login(admin_user)
        download_url = reverse("crossref:component-xml-download", args=[component_group_with_data.pk])
        client.get(download_url)

        export = CrossrefExport.objects.filter(
            component_group=component_group_with_data
        ).first()
        assert export is not None

        redownload_url = reverse("crossref:component-export-redownload", args=[export.pk])
        response = client.get(redownload_url)
        assert response.status_code == 200
        assert response["Content-Type"] == "application/xml; charset=utf-8"

    def test_original_export_redownload_still_works(self, client, admin_user):
        """Original export_redownload with issue exports still works."""
        from doi_portal.crossref.services import CrossrefService
        from doi_portal.issues.tests.factories import IssueFactory

        issue = IssueFactory()
        service = CrossrefService()
        service.generate_and_store_xml(issue)

        # Create export
        CrossrefExport.objects.create(
            issue=issue,
            export_type=ExportType.ISSUE,
            xml_content=issue.crossref_xml,
            exported_by=admin_user,
            filename="test.xml",
            xsd_valid_at_export=True,
        )

        export = CrossrefExport.objects.filter(issue=issue).first()
        client.force_login(admin_user)
        url = reverse("crossref:export-redownload", args=[export.pk])
        response = client.get(url)
        assert response.status_code == 200
