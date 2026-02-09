"""
Tests for XML Preview functionality.

Story 5.5: XML Preview with Syntax Highlighting.
Tests for xml_preview view and template rendering.
"""

import pytest
from django.contrib.auth.models import Group
from django.urls import reverse

from doi_portal.articles.tests.factories import ArticleFactory
from doi_portal.issues.tests.factories import IssueFactory
from doi_portal.publications.tests.factories import JournalFactory
from doi_portal.publications.tests.factories import PublisherFactory
from doi_portal.users.tests.factories import UserFactory


@pytest.fixture
def user(db):
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
    """Create issue with generated XML content."""
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


@pytest.mark.django_db
class TestXMLPreviewView:
    """Tests for xml_preview view."""

    def test_preview_returns_modal_with_xml(self, client, user, issue_with_xml):
        """Preview endpoint returns modal template with XML content."""
        client.force_login(user)
        url = reverse("crossref:xml-preview", args=[issue_with_xml.pk])
        response = client.get(url)

        assert response.status_code == 200
        assert "xmlPreviewModal" in response.content.decode()
        assert "Test Article" in response.content.decode()

    def test_preview_without_xml_shows_warning(self, client, user, issue_without_xml):
        """Preview endpoint shows warning when no XML generated."""
        client.force_login(user)
        url = reverse("crossref:xml-preview", args=[issue_without_xml.pk])
        response = client.get(url)

        assert response.status_code == 200
        assert "XML nije generisan" in response.content.decode()

    def test_preview_includes_error_lines(self, client, user, issue_with_invalid_xml):
        """Preview includes error line numbers from XSD validation."""
        client.force_login(user)
        url = reverse("crossref:xml-preview", args=[issue_with_invalid_xml.pk])
        response = client.get(url)

        assert response.status_code == 200
        content = response.content.decode()
        # Should have error lines data attribute
        assert 'data-line="8,3"' in content or 'data-line="3,8"' in content

    def test_preview_requires_authentication(self, client, issue_with_xml):
        """Preview endpoint requires logged-in user."""
        url = reverse("crossref:xml-preview", args=[issue_with_xml.pk])
        response = client.get(url)

        # Should redirect to login
        assert response.status_code == 302
        assert "login" in response.url.lower() or "account" in response.url.lower()

    def test_preview_returns_404_for_nonexistent_issue(self, client, user):
        """Preview endpoint returns 404 for non-existent issue."""
        client.force_login(user)
        url = reverse("crossref:xml-preview", args=[99999])
        response = client.get(url)

        assert response.status_code == 404

    def test_preview_modal_has_action_buttons(self, client, user, issue_with_xml):
        """Preview modal includes all action buttons."""
        client.force_login(user)
        url = reverse("crossref:xml-preview", args=[issue_with_xml.pk])
        response = client.get(url)

        content = response.content.decode()
        assert "Kopiraj u clipboard" in content
        assert "Preuzmi XML" in content
        assert "Zatvori" in content

    def test_preview_shows_xsd_warning_for_invalid_xml(
        self, client, user, issue_with_invalid_xml,
    ):
        """Preview modal shows warning banner for invalid XML."""
        client.force_login(user)
        url = reverse("crossref:xml-preview", args=[issue_with_invalid_xml.pk])
        response = client.get(url)

        content = response.content.decode()
        # Should show warning about XSD errors
        assert "greške validacije" in content.lower() or "greška" in content.lower()

    def test_preview_has_prism_css_classes(self, client, user, issue_with_xml):
        """Preview modal has Prism.js CSS classes for syntax highlighting."""
        client.force_login(user)
        url = reverse("crossref:xml-preview", args=[issue_with_xml.pk])
        response = client.get(url)

        content = response.content.decode()
        assert "language-xml" in content
        assert "line-numbers" in content


@pytest.mark.django_db
class TestXMLPreviewTemplate:
    """Tests for XML preview template rendering."""

    def test_modal_renders_xml_content(self, client, user, issue_with_xml):
        """Modal template renders XML content correctly."""
        client.force_login(user)
        url = reverse("crossref:xml-preview", args=[issue_with_xml.pk])
        response = client.get(url)

        content = response.content.decode()
        # XML should be escaped and present
        assert "&lt;doi_batch" in content or "<doi_batch" in content

    def test_modal_has_close_button(self, client, user, issue_with_xml):
        """Modal has close button with proper Bootstrap attributes."""
        client.force_login(user)
        url = reverse("crossref:xml-preview", args=[issue_with_xml.pk])
        response = client.get(url)

        content = response.content.decode()
        assert 'data-bs-dismiss="modal"' in content

    def test_modal_has_fullscreen_option(self, client, user, issue_with_xml):
        """Modal supports fullscreen for large XML files."""
        client.force_login(user)
        url = reverse("crossref:xml-preview", args=[issue_with_xml.pk])
        response = client.get(url)

        content = response.content.decode()
        # Should have fullscreen class or option
        assert "modal-xl" in content or "modal-fullscreen" in content


@pytest.mark.django_db
class TestXMLDownloadEndpoint:
    """Tests for XML download functionality."""

    def test_download_returns_xml_file(self, client, user, issue_with_xml):
        """Download endpoint returns XML as file attachment."""
        client.force_login(user)
        url = reverse("crossref:xml-download", args=[issue_with_xml.pk])
        response = client.get(url)

        assert response.status_code == 200
        # Story 5.6: UTF-8 encoding added to Content-Type (AC2)
        assert "application/xml" in response["Content-Type"]
        assert "charset=utf-8" in response["Content-Type"].lower()
        assert "attachment" in response["Content-Disposition"]

    def test_download_has_correct_filename(self, client, user, issue_with_xml):
        """Download has descriptive filename."""
        client.force_login(user)
        url = reverse("crossref:xml-download", args=[issue_with_xml.pk])
        response = client.get(url)

        content_disposition = response["Content-Disposition"]
        # Should contain publication info in filename
        assert ".xml" in content_disposition

    def test_download_returns_404_without_xml(self, client, user, issue_without_xml):
        """Download returns 404 when no XML generated."""
        client.force_login(user)
        url = reverse("crossref:xml-download", args=[issue_without_xml.pk])
        response = client.get(url)

        assert response.status_code == 404

    def test_download_requires_authentication(self, client, issue_with_xml):
        """Download endpoint requires logged-in user."""
        url = reverse("crossref:xml-download", args=[issue_with_xml.pk])
        response = client.get(url)

        assert response.status_code == 302


@pytest.mark.django_db
class TestPreviewButtonInGenerationResult:
    """Tests for Pregled XML button integration."""

    def test_preview_button_url_resolves(self, issue_with_xml):
        """Preview URL pattern resolves correctly."""
        url = reverse("crossref:xml-preview", args=[issue_with_xml.pk])
        # URL is mounted under /dashboard/crossref/
        assert f"/issues/{issue_with_xml.pk}/preview/" in url
        assert "crossref" in url

    def test_download_button_url_resolves(self, issue_with_xml):
        """Download URL pattern resolves correctly."""
        url = reverse("crossref:xml-download", args=[issue_with_xml.pk])
        # URL is mounted under /dashboard/crossref/
        assert f"/issues/{issue_with_xml.pk}/download/" in url
        assert "crossref" in url


@pytest.mark.django_db
class TestPublisherPermissions:
    """Tests for publisher-level permission checks."""

    def test_preview_denied_for_user_without_publisher_access(
        self, client, publisher, journal_publication,
    ):
        """Preview returns 403 for user without access to issue's publisher."""
        # Create user assigned to different publisher
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
        url = reverse("crossref:xml-preview", args=[issue.pk])
        response = client.get(url)

        assert response.status_code == 403

    def test_preview_allowed_for_admin_user(
        self, client, publisher, journal_publication,
    ):
        """Preview allowed for Administrator regardless of publisher assignment."""
        admin_user = UserFactory()
        Group.objects.get_or_create(name="Administrator")
        admin_user.groups.add(Group.objects.get(name="Administrator"))

        issue = IssueFactory(
            publication=journal_publication,
            volume="1",
            issue_number="1",
            year=2026,
            crossref_xml="<test/>",
        )

        client.force_login(admin_user)
        url = reverse("crossref:xml-preview", args=[issue.pk])
        response = client.get(url)

        assert response.status_code == 200

    def test_download_denied_for_user_without_publisher_access(
        self, client, publisher, journal_publication,
    ):
        """Download returns 403 for user without access to issue's publisher."""
        other_publisher = PublisherFactory(name="Other Publisher 2", doi_prefix="10.88888")
        user_without_access = UserFactory(publisher=other_publisher)
        Group.objects.get_or_create(name="Bibliotekar")
        user_without_access.groups.add(Group.objects.get(name="Bibliotekar"))

        issue = IssueFactory(
            publication=journal_publication,
            volume="2",
            issue_number="1",
            year=2026,
            crossref_xml="<test/>",
        )

        client.force_login(user_without_access)
        url = reverse("crossref:xml-download", args=[issue.pk])
        response = client.get(url)

        assert response.status_code == 403


@pytest.mark.django_db
class TestLargeXMLHandling:
    """Tests for large XML file handling (Task 10: >100KB)."""

    def test_large_xml_shows_performance_warning(self, client, user, journal_publication):
        """Preview shows warning for large XML files (>100KB)."""
        # Generate XML larger than 100KB (approximately 150KB)
        large_xml_content = "<?xml version='1.0'?>\n<root>\n"
        large_xml_content += "<data>" + "x" * 150000 + "</data>\n"
        large_xml_content += "</root>"

        issue = IssueFactory(
            publication=journal_publication,
            volume="99",
            issue_number="1",
            year=2026,
            crossref_xml=large_xml_content,
            xsd_valid=True,
        )

        client.force_login(user)
        url = reverse("crossref:xml-preview", args=[issue.pk])
        response = client.get(url)

        content = response.content.decode()
        assert response.status_code == 200
        # Should show large file warning
        assert "Veliki XML fajl" in content or "xml_size_kb" in str(response.context)

    def test_small_xml_no_performance_warning(self, client, user, issue_with_xml):
        """Preview does not show warning for small XML files."""
        client.force_login(user)
        url = reverse("crossref:xml-preview", args=[issue_with_xml.pk])
        response = client.get(url)

        content = response.content.decode()
        assert response.status_code == 200
        # Should NOT show large file warning
        assert "Veliki XML fajl" not in content


@pytest.mark.django_db
class TestEdgeCases:
    """Tests for edge cases and error handling."""

    def test_preview_with_empty_xsd_errors_list(self, client, user, journal_publication):
        """Preview works correctly with empty xsd_errors list."""
        issue = IssueFactory(
            publication=journal_publication,
            volume="50",
            issue_number="1",
            year=2026,
            crossref_xml="<test>content</test>",
            xsd_valid=True,
            xsd_errors=[],
        )

        client.force_login(user)
        url = reverse("crossref:xml-preview", args=[issue.pk])
        response = client.get(url)

        content = response.content.decode()
        assert response.status_code == 200
        # Should NOT have data-line attribute when no errors
        assert 'data-line=""' not in content
        # Error lines should be empty - no data-line attribute at all when empty
        assert "Prva greška" not in content

    def test_preview_with_xsd_errors_without_line_numbers(
        self, client, user, journal_publication,
    ):
        """Preview handles XSD errors that don't have line numbers."""
        issue = IssueFactory(
            publication=journal_publication,
            volume="51",
            issue_number="1",
            year=2026,
            crossref_xml="<test>invalid</test>",
            xsd_valid=False,
            xsd_errors=[
                {
                    "message": "Some validation error",
                    "line": None,  # No line number
                    "column": None,
                    "element": "/test",
                },
            ],
        )

        client.force_login(user)
        url = reverse("crossref:xml-preview", args=[issue.pk])
        response = client.get(url)

        assert response.status_code == 200
        content = response.content.decode()
        # Should show error warning but no error line highlighting
        assert "greške validacije" in content.lower()

    def test_download_filename_contains_publication_info(
        self, client, user, issue_with_xml,
    ):
        """Download filename contains publication slug, volume, and issue."""
        client.force_login(user)
        url = reverse("crossref:xml-download", args=[issue_with_xml.pk])
        response = client.get(url)

        content_disposition = response["Content-Disposition"]
        # Should contain volume and issue from fixture (vol 10, issue 2)
        assert "10" in content_disposition
        assert "2" in content_disposition
        assert ".xml" in content_disposition
