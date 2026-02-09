"""
Tests for XML Download functionality.

Story 5.6: XML Download - Export History Tracking.
Tests for CrossrefExport model, xml_download view, warning modal, export history.
"""

import pytest
from django.contrib.auth.models import Group
from django.urls import reverse
from django.utils import timezone

from doi_portal.crossref.models import CrossrefExport
from doi_portal.issues.tests.factories import IssueFactory
from doi_portal.publications.tests.factories import JournalFactory
from doi_portal.publications.tests.factories import PublisherFactory
from doi_portal.users.tests.factories import UserFactory


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def admin_user(db):
    """Create authenticated user with Administrator role (full access)."""
    admin_group, _ = Group.objects.get_or_create(name="Administrator")
    user = UserFactory()
    user.groups.add(admin_group)
    return user


@pytest.fixture
def publisher(db):
    """Create test publisher."""
    return PublisherFactory(
        name="Test Publisher",
        doi_prefix="10.12345",
    )


@pytest.fixture
def journal_publication(publisher):
    """Create test journal publication."""
    return JournalFactory(
        title="Test Journal",
        publisher=publisher,
        issn_print="1234-5678",
    )


@pytest.fixture
def issue_with_xml(journal_publication):
    """Create issue with generated valid XML content."""
    return IssueFactory(
        publication=journal_publication,
        volume="10",
        issue_number="2",
        year=2026,
        crossref_xml="""<?xml version="1.0" encoding="UTF-8"?>
<doi_batch xmlns="http://www.crossref.org/schema/5.4.0">
  <head>
    <doi_batch_id>test_batch</doi_batch_id>
    <timestamp>20260115120000</timestamp>
  </head>
  <body>
    <journal>
      <journal_article>
        <title>Test Article</title>
      </journal_article>
    </journal>
  </body>
</doi_batch>""",
        xsd_valid=True,
        xsd_errors=[],
    )


@pytest.fixture
def issue_with_invalid_xml(journal_publication):
    """Create issue with invalid XML and XSD errors."""
    return IssueFactory(
        publication=journal_publication,
        volume="12",
        issue_number="1",
        year=2026,
        crossref_xml="""<?xml version="1.0" encoding="UTF-8"?>
<doi_batch xmlns="http://www.crossref.org/schema/5.4.0">
  <head>
    <doi_batch_id>invalid_batch</doi_batch_id>
  </head>
  <body>
    <invalid_element>Test</invalid_element>
  </body>
</doi_batch>""",
        xsd_valid=False,
        xsd_errors=[
            {
                "message": "Element 'invalid_element': This element is not expected.",
                "line": 8,
                "column": 5,
                "element": "/doi_batch/body/invalid_element",
            },
            {
                "message": "Missing required element 'timestamp'.",
                "line": 3,
                "column": 10,
                "element": "/doi_batch/head",
            },
        ],
    )


@pytest.fixture
def issue_without_xml(journal_publication):
    """Create issue without XML content."""
    return IssueFactory(
        publication=journal_publication,
        volume="11",
        issue_number="1",
        year=2026,
        crossref_xml="",
        xsd_valid=None,
    )


@pytest.fixture
def export_record(issue_with_xml, admin_user):
    """Create a CrossrefExport record for testing re-download."""
    return CrossrefExport.objects.create(
        issue=issue_with_xml,
        xml_content=issue_with_xml.crossref_xml,
        exported_by=admin_user,
        filename="test-journal_10_2_20260115_120000.xml",
        xsd_valid_at_export=True,
    )


# =============================================================================
# Task 1: CrossrefExport Model Tests
# =============================================================================


@pytest.mark.django_db
class TestCrossrefExportModel:
    """Tests for CrossrefExport model (Task 1)."""

    def test_export_creation(self, issue_with_xml, admin_user):
        """Export record is created correctly with all fields."""
        export = CrossrefExport.objects.create(
            issue=issue_with_xml,
            xml_content=issue_with_xml.crossref_xml,
            exported_by=admin_user,
            filename="test-export.xml",
            xsd_valid_at_export=True,
        )

        assert export.pk is not None
        assert export.issue == issue_with_xml
        assert export.xml_content == issue_with_xml.crossref_xml
        assert export.exported_by == admin_user
        assert export.filename == "test-export.xml"
        assert export.xsd_valid_at_export is True
        assert export.exported_at is not None

    def test_export_ordering(self, issue_with_xml, admin_user):
        """Exports are ordered by exported_at descending (newest first)."""
        # Create first export
        export1 = CrossrefExport.objects.create(
            issue=issue_with_xml,
            xml_content="<xml>first</xml>",
            exported_by=admin_user,
            filename="first.xml",
            xsd_valid_at_export=True,
        )

        # Create second export (newer)
        export2 = CrossrefExport.objects.create(
            issue=issue_with_xml,
            xml_content="<xml>second</xml>",
            exported_by=admin_user,
            filename="second.xml",
            xsd_valid_at_export=True,
        )

        exports = list(issue_with_xml.crossref_exports.all())
        assert exports[0] == export2  # Newest first
        assert exports[1] == export1

    def test_export_str_representation(self, export_record):
        """Export __str__ includes filename and date."""
        str_repr = str(export_record)
        assert "test-journal_10_2_20260115_120000.xml" in str_repr

    def test_export_related_name(self, issue_with_xml, admin_user):
        """Issue has crossref_exports related name."""
        CrossrefExport.objects.create(
            issue=issue_with_xml,
            xml_content="<xml/>",
            exported_by=admin_user,
            filename="test.xml",
            xsd_valid_at_export=True,
        )

        assert issue_with_xml.crossref_exports.count() == 1

    def test_export_cascade_delete(self, issue_with_xml, admin_user):
        """Exports are deleted when issue is deleted."""
        CrossrefExport.objects.create(
            issue=issue_with_xml,
            xml_content="<xml/>",
            exported_by=admin_user,
            filename="test.xml",
            xsd_valid_at_export=True,
        )

        issue_pk = issue_with_xml.pk
        # Hard delete the issue (bypass soft delete for this test)
        from doi_portal.issues.models import Issue
        Issue.all_objects.filter(pk=issue_pk).delete()

        assert CrossrefExport.objects.count() == 0

    def test_export_user_set_null_on_delete(self, issue_with_xml, admin_user):
        """exported_by is set to null when user is deleted."""
        export = CrossrefExport.objects.create(
            issue=issue_with_xml,
            xml_content="<xml/>",
            exported_by=admin_user,
            filename="test.xml",
            xsd_valid_at_export=True,
        )

        admin_user.delete()
        export.refresh_from_db()

        assert export.exported_by is None

    def test_export_with_null_xsd_valid(self, issue_with_xml, admin_user):
        """Export can be created with null xsd_valid_at_export."""
        export = CrossrefExport.objects.create(
            issue=issue_with_xml,
            xml_content="<xml/>",
            exported_by=admin_user,
            filename="test.xml",
            xsd_valid_at_export=None,
        )

        assert export.xsd_valid_at_export is None


# =============================================================================
# Task 2: XML Download Creates Export Record
# =============================================================================


@pytest.mark.django_db
class TestXMLDownloadView:
    """Tests for xml_download view with export tracking (Task 2)."""

    def test_download_creates_export_record(self, client, admin_user, issue_with_xml):
        """Download creates CrossrefExport record."""
        client.force_login(admin_user)
        url = reverse("crossref:xml-download", args=[issue_with_xml.pk])

        assert CrossrefExport.objects.count() == 0

        response = client.get(url)

        assert response.status_code == 200
        assert CrossrefExport.objects.count() == 1

        export = CrossrefExport.objects.first()
        assert export.issue == issue_with_xml
        assert export.exported_by == admin_user
        assert export.xml_content == issue_with_xml.crossref_xml
        assert export.xsd_valid_at_export == issue_with_xml.xsd_valid

    def test_download_filename_format(self, client, admin_user, issue_with_xml):
        """Filename matches expected format: {publication-slug}_{volume}_{issue}_{timestamp}.xml"""
        client.force_login(admin_user)
        url = reverse("crossref:xml-download", args=[issue_with_xml.pk])
        response = client.get(url)

        content_disposition = response["Content-Disposition"]
        # Should contain volume 10, issue 2, and .xml extension
        assert "10" in content_disposition
        assert "2" in content_disposition
        assert ".xml" in content_disposition
        assert "attachment" in content_disposition

    def test_download_utf8_encoding(self, client, admin_user, issue_with_xml):
        """Response has UTF-8 encoding in Content-Type."""
        client.force_login(admin_user)
        url = reverse("crossref:xml-download", args=[issue_with_xml.pk])
        response = client.get(url)

        content_type = response["Content-Type"]
        assert "charset=utf-8" in content_type.lower()

    def test_download_requires_permission(self, client, publisher, journal_publication):
        """Download denied for users without publisher access."""
        other_publisher = PublisherFactory(name="Other Publisher", doi_prefix="10.99999")
        user_without_access = UserFactory(publisher=other_publisher)
        Group.objects.get_or_create(name="Urednik")
        user_without_access.groups.add(Group.objects.get(name="Urednik"))

        issue = IssueFactory(
            publication=journal_publication,
            volume="1",
            issue_number="1",
            year=2026,
            crossref_xml="<test/>",
        )

        client.force_login(user_without_access)
        url = reverse("crossref:xml-download", args=[issue.pk])
        response = client.get(url)

        assert response.status_code == 403

    def test_download_stores_filename_in_export(self, client, admin_user, issue_with_xml):
        """Export record stores the generated filename."""
        client.force_login(admin_user)
        url = reverse("crossref:xml-download", args=[issue_with_xml.pk])
        response = client.get(url)

        export = CrossrefExport.objects.first()
        assert export.filename is not None
        assert export.filename.endswith(".xml")

        # Filename in response should match stored filename
        content_disposition = response["Content-Disposition"]
        assert export.filename in content_disposition


# =============================================================================
# Task 3: Warning Modal for Invalid XML
# =============================================================================


@pytest.mark.django_db
class TestDownloadWarning:
    """Tests for download warning modal (Task 3)."""

    def test_warning_shown_for_invalid_xml(self, client, admin_user, issue_with_invalid_xml):
        """Warning modal returned for invalid XML."""
        client.force_login(admin_user)
        url = reverse("crossref:download-warning", args=[issue_with_invalid_xml.pk])
        response = client.get(url)

        assert response.status_code == 200
        content = response.content.decode()
        assert "downloadWarningModal" in content or "Upozorenje" in content

    def test_warning_includes_error_count(self, client, admin_user, issue_with_invalid_xml):
        """Warning shows correct error count."""
        client.force_login(admin_user)
        url = reverse("crossref:download-warning", args=[issue_with_invalid_xml.pk])
        response = client.get(url)

        content = response.content.decode()
        # Issue has 2 errors
        assert "2" in content

    def test_warning_has_proceed_button(self, client, admin_user, issue_with_invalid_xml):
        """Warning modal has 'Preuzmi svejedno' button."""
        client.force_login(admin_user)
        url = reverse("crossref:download-warning", args=[issue_with_invalid_xml.pk])
        response = client.get(url)

        content = response.content.decode()
        assert "Preuzmi svejedno" in content

    def test_warning_has_cancel_button(self, client, admin_user, issue_with_invalid_xml):
        """Warning modal has 'Otkaži' button."""
        client.force_login(admin_user)
        url = reverse("crossref:download-warning", args=[issue_with_invalid_xml.pk])
        response = client.get(url)

        content = response.content.decode()
        assert "Otkaži" in content

    def test_force_download_works(self, client, admin_user, issue_with_invalid_xml):
        """Force download proceeds despite validation errors."""
        client.force_login(admin_user)
        url = reverse("crossref:xml-download-force", args=[issue_with_invalid_xml.pk])
        response = client.get(url)

        assert response.status_code == 200
        assert response["Content-Type"].startswith("application/xml")

        # Should create export record
        assert CrossrefExport.objects.count() == 1
        export = CrossrefExport.objects.first()
        assert export.xsd_valid_at_export is False

    def test_warning_requires_permission(self, client, publisher, journal_publication):
        """Warning endpoint denied for users without publisher access."""
        other_publisher = PublisherFactory(name="Other Publisher 3", doi_prefix="10.77777")
        user_without_access = UserFactory(publisher=other_publisher)
        Group.objects.get_or_create(name="Bibliotekar")
        user_without_access.groups.add(Group.objects.get(name="Bibliotekar"))

        issue = IssueFactory(
            publication=journal_publication,
            volume="3",
            issue_number="1",
            year=2026,
            crossref_xml="<test/>",
            xsd_valid=False,
        )

        client.force_login(user_without_access)
        url = reverse("crossref:download-warning", args=[issue.pk])
        response = client.get(url)

        assert response.status_code == 403

    def test_force_download_returns_404_without_xml(
        self, client, admin_user, issue_without_xml,
    ):
        """Force download returns 404 when no XML generated."""
        client.force_login(admin_user)
        url = reverse("crossref:xml-download-force", args=[issue_without_xml.pk])
        response = client.get(url)

        assert response.status_code == 404


# =============================================================================
# Task 4 & 5: Export History
# =============================================================================


@pytest.mark.django_db
class TestExportHistory:
    """Tests for export history display and re-download (Task 4, 5)."""

    def test_history_displays_exports(self, client, admin_user, issue_with_xml):
        """Export history shows previous exports."""
        # Create some exports
        CrossrefExport.objects.create(
            issue=issue_with_xml,
            xml_content="<xml>first</xml>",
            exported_by=admin_user,
            filename="first.xml",
            xsd_valid_at_export=True,
        )
        CrossrefExport.objects.create(
            issue=issue_with_xml,
            xml_content="<xml>second</xml>",
            exported_by=admin_user,
            filename="second.xml",
            xsd_valid_at_export=False,
        )

        client.force_login(admin_user)
        url = reverse("crossref:export-history", args=[issue_with_xml.pk])
        response = client.get(url)

        assert response.status_code == 200
        content = response.content.decode()
        assert "first.xml" in content
        assert "second.xml" in content

    def test_history_empty_message(self, client, admin_user, issue_with_xml):
        """Empty state shown when no exports."""
        client.force_login(admin_user)
        url = reverse("crossref:export-history", args=[issue_with_xml.pk])
        response = client.get(url)

        content = response.content.decode()
        assert "Nema prethodnih eksporta" in content

    def test_history_shows_valid_status_badge(self, client, admin_user, export_record):
        """History shows 'Validan' badge for valid exports."""
        client.force_login(admin_user)
        url = reverse("crossref:export-history", args=[export_record.issue.pk])
        response = client.get(url)

        content = response.content.decode()
        assert "Validan" in content

    def test_history_shows_invalid_status_badge(self, client, admin_user, issue_with_xml):
        """History shows 'Nevažeći' badge for invalid exports."""
        CrossrefExport.objects.create(
            issue=issue_with_xml,
            xml_content="<xml/>",
            exported_by=admin_user,
            filename="invalid.xml",
            xsd_valid_at_export=False,
        )

        client.force_login(admin_user)
        url = reverse("crossref:export-history", args=[issue_with_xml.pk])
        response = client.get(url)

        content = response.content.decode()
        assert "Nevažeći" in content or "Nevalidan" in content or "bg-danger" in content

    def test_redownload_serves_correct_content(self, client, admin_user, export_record):
        """Re-download serves stored XML content."""
        client.force_login(admin_user)
        url = reverse("crossref:export-redownload", args=[export_record.pk])
        response = client.get(url)

        assert response.status_code == 200
        assert response.content.decode() == export_record.xml_content
        assert export_record.filename in response["Content-Disposition"]

    def test_redownload_requires_permission(self, client, publisher, journal_publication, admin_user):
        """Re-download denied for users without access."""
        issue = IssueFactory(
            publication=journal_publication,
            volume="5",
            issue_number="1",
            year=2026,
            crossref_xml="<test/>",
        )
        export = CrossrefExport.objects.create(
            issue=issue,
            xml_content="<private/>",
            exported_by=admin_user,
            filename="private.xml",
            xsd_valid_at_export=True,
        )

        other_publisher = PublisherFactory(name="Other Publisher 4", doi_prefix="10.66666")
        user_without_access = UserFactory(publisher=other_publisher)
        Group.objects.get_or_create(name="Urednik")
        user_without_access.groups.add(Group.objects.get(name="Urednik"))

        client.force_login(user_without_access)
        url = reverse("crossref:export-redownload", args=[export.pk])
        response = client.get(url)

        assert response.status_code == 403

    def test_history_requires_permission(self, client, publisher, journal_publication):
        """History endpoint denied for users without publisher access."""
        other_publisher = PublisherFactory(name="Other Publisher 5", doi_prefix="10.55555")
        user_without_access = UserFactory(publisher=other_publisher)
        Group.objects.get_or_create(name="Bibliotekar")
        user_without_access.groups.add(Group.objects.get(name="Bibliotekar"))

        issue = IssueFactory(
            publication=journal_publication,
            volume="6",
            issue_number="1",
            year=2026,
            crossref_xml="<test/>",
        )

        client.force_login(user_without_access)
        url = reverse("crossref:export-history", args=[issue.pk])
        response = client.get(url)

        assert response.status_code == 403


# =============================================================================
# Task 8: XML Declaration Validation
# =============================================================================


@pytest.mark.django_db
class TestXMLDeclaration:
    """Tests for XML declaration and encoding (Task 8)."""

    def test_xml_starts_with_declaration(self, client, admin_user, issue_with_xml):
        """Downloaded XML starts with proper XML declaration."""
        client.force_login(admin_user)
        url = reverse("crossref:xml-download", args=[issue_with_xml.pk])
        response = client.get(url)

        content = response.content.decode("utf-8")
        assert content.strip().startswith('<?xml version="1.0" encoding="UTF-8"?>')

    def test_response_utf8_charset(self, client, admin_user, issue_with_xml):
        """Response Content-Type includes charset=utf-8."""
        client.force_login(admin_user)
        url = reverse("crossref:xml-download", args=[issue_with_xml.pk])
        response = client.get(url)

        assert "charset=utf-8" in response["Content-Type"].lower()


# =============================================================================
# URL Resolution Tests
# =============================================================================


@pytest.mark.django_db
class TestURLPatterns:
    """Tests for URL pattern resolution."""

    def test_download_warning_url_resolves(self, issue_with_xml):
        """Download warning URL pattern resolves correctly."""
        url = reverse("crossref:download-warning", args=[issue_with_xml.pk])
        assert f"/issues/{issue_with_xml.pk}/download-warning/" in url

    def test_xml_download_force_url_resolves(self, issue_with_xml):
        """Force download URL pattern resolves correctly."""
        url = reverse("crossref:xml-download-force", args=[issue_with_xml.pk])
        assert f"/issues/{issue_with_xml.pk}/download-force/" in url

    def test_export_redownload_url_resolves(self, export_record):
        """Export re-download URL pattern resolves correctly."""
        url = reverse("crossref:export-redownload", args=[export_record.pk])
        assert f"/exports/{export_record.pk}/redownload/" in url

    def test_export_history_url_resolves(self, issue_with_xml):
        """Export history URL pattern resolves correctly."""
        url = reverse("crossref:export-history", args=[issue_with_xml.pk])
        assert f"/issues/{issue_with_xml.pk}/export-history/" in url
