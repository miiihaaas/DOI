"""
Tests for Crossref Deposit Workflow Page.

Story 5.7: Crossref Deposit Workflow Page.
Tests for CrossrefDepositView, mark_deposited, deposit tracking fields.
"""

import pytest
from django.contrib.auth.models import Group
from django.urls import reverse
from django.utils import timezone

from doi_portal.crossref.models import CrossrefExport
from doi_portal.issues.models import Issue
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
        name="Test Publisher Deposit",
        doi_prefix="10.12345",
    )


@pytest.fixture
def journal_publication(publisher):
    """Create test journal publication."""
    return JournalFactory(
        title="Test Journal Deposit",
        publisher=publisher,
        issn_print="1234-5678",
    )


@pytest.fixture
def issue(journal_publication):
    """Create issue without XML."""
    return IssueFactory(
        publication=journal_publication,
        volume="10",
        issue_number="2",
        year=2026,
        crossref_xml="",
        xsd_valid=None,
    )


@pytest.fixture
def issue_with_xml(journal_publication):
    """Create issue with generated valid XML content."""
    return IssueFactory(
        publication=journal_publication,
        volume="11",
        issue_number="1",
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
    """Create issue with invalid XML."""
    return IssueFactory(
        publication=journal_publication,
        volume="12",
        issue_number="1",
        year=2026,
        crossref_xml="<invalid/>",
        xsd_valid=False,
        xsd_errors=[{"message": "Invalid", "line": 1}],
    )


@pytest.fixture
def deposited_issue(journal_publication, admin_user):
    """Create issue that has been deposited."""
    return IssueFactory(
        publication=journal_publication,
        volume="13",
        issue_number="1",
        year=2026,
        crossref_xml="<xml/>",
        xsd_valid=True,
        crossref_deposited_at=timezone.now(),
        crossref_deposited_by=admin_user,
    )


@pytest.fixture
def other_user(db):
    """Create user without publisher access."""
    other_pub = PublisherFactory(name="Other Publisher Deposit", doi_prefix="10.99999")
    user = UserFactory(publisher=other_pub)
    urednik_group, _ = Group.objects.get_or_create(name="Urednik")
    user.groups.add(urednik_group)
    return user


# =============================================================================
# Task 1: Issue Deposit Fields Tests
# =============================================================================


@pytest.mark.django_db
class TestIssueDepositFields:
    """Tests for Issue model deposit tracking fields (Task 1)."""

    def test_is_crossref_deposited_false_by_default(self, issue):
        """New issues are not deposited."""
        assert issue.is_crossref_deposited is False

    def test_is_crossref_deposited_true_when_set(self, deposited_issue):
        """Issues with deposited_at are marked as deposited."""
        assert deposited_issue.is_crossref_deposited is True

    def test_crossref_deposited_at_nullable(self, issue):
        """crossref_deposited_at field is nullable."""
        assert issue.crossref_deposited_at is None

    def test_crossref_deposited_by_nullable(self, issue):
        """crossref_deposited_by field is nullable."""
        assert issue.crossref_deposited_by is None

    def test_crossref_deposited_by_set_null_on_user_delete(
        self, deposited_issue, admin_user,
    ):
        """crossref_deposited_by is set to null when user is deleted."""
        admin_user.delete()
        deposited_issue.refresh_from_db()
        assert deposited_issue.crossref_deposited_by is None
        # deposited_at should still be set
        assert deposited_issue.crossref_deposited_at is not None


# =============================================================================
# Task 2: CrossrefDepositView Tests
# =============================================================================


@pytest.mark.django_db
class TestCrossrefDepositView:
    """Tests for CrossrefDepositView (Task 2)."""

    def test_deposit_page_renders(self, client, admin_user, issue):
        """Deposit page renders with correct steps."""
        client.force_login(admin_user)
        url = reverse("crossref:issue-deposit", args=[issue.pk])
        response = client.get(url)

        assert response.status_code == 200
        content = response.content.decode()
        assert "Crossref Deposit" in content
        assert "Pre-validacija" in content
        assert "Generisanje XML" in content
        assert "XSD Validacija" in content
        assert "Pregled XML" in content
        assert "Preuzimanje XML" in content

    def test_deposit_page_requires_login(self, client, issue):
        """Unauthenticated users redirected to login."""
        url = reverse("crossref:issue-deposit", args=[issue.pk])
        response = client.get(url)

        assert response.status_code == 302
        assert "/accounts/login/" in response.url

    def test_deposit_page_requires_permission(self, client, other_user, issue):
        """Users without publisher access get 403."""
        client.force_login(other_user)
        url = reverse("crossref:issue-deposit", args=[issue.pk])
        response = client.get(url)

        assert response.status_code == 403

    def test_steps_disabled_without_xml(self, client, admin_user, issue):
        """Steps 3-5 disabled when no XML generated."""
        client.force_login(admin_user)
        url = reverse("crossref:issue-deposit", args=[issue.pk])
        response = client.get(url)

        context = response.context
        steps = context["steps"]
        # Step 3 (XSD), 4 (Preview), 5 (Download) should not be active/completed
        assert steps[2]["completed"] is False  # XSD
        assert steps[2]["active"] is False
        assert steps[3]["active"] is False  # Preview
        assert steps[4]["active"] is False  # Download

    def test_steps_enabled_with_xml(self, client, admin_user, issue_with_xml):
        """Steps 3-5 enabled when XML exists."""
        client.force_login(admin_user)
        url = reverse("crossref:issue-deposit", args=[issue_with_xml.pk])
        response = client.get(url)

        context = response.context
        steps = context["steps"]
        assert steps[1]["completed"] is True  # Generate - completed
        assert steps[2]["completed"] is True  # XSD - valid
        assert steps[3]["active"] is True  # Preview - active
        assert steps[4]["active"] is True  # Download - active

    def test_regenerate_button_shown_with_xml(self, client, admin_user, issue_with_xml):
        """Regenerate button appears when XML already exists."""
        client.force_login(admin_user)
        url = reverse("crossref:issue-deposit", args=[issue_with_xml.pk])
        response = client.get(url)

        content = response.content.decode()
        assert "Regeneriši XML" in content or "regenerisi" in content.lower()

    def test_deposit_status_shown_when_deposited(self, client, admin_user, deposited_issue):
        """Deposited status displayed correctly."""
        client.force_login(admin_user)
        url = reverse("crossref:issue-deposit", args=[deposited_issue.pk])
        response = client.get(url)

        content = response.content.decode()
        assert "Deponovano" in content

    def test_breadcrumbs_render(self, client, admin_user, issue):
        """Breadcrumbs render correctly on deposit page."""
        client.force_login(admin_user)
        url = reverse("crossref:issue-deposit", args=[issue.pk])
        response = client.get(url)

        context = response.context
        assert "breadcrumbs" in context
        breadcrumbs = context["breadcrumbs"]
        assert len(breadcrumbs) >= 2
        # Last breadcrumb should be Crossref Deposit
        assert "Crossref Deposit" in breadcrumbs[-1]["label"]

    def test_ready_for_crossref_shown_when_complete(
        self, client, admin_user, issue_with_xml,
    ):
        """Ready for Crossref message shown when all steps complete."""
        # Create an export to mark step 5 as completed
        CrossrefExport.objects.create(
            issue=issue_with_xml,
            xml_content=issue_with_xml.crossref_xml,
            exported_by=admin_user,
            filename="test.xml",
            xsd_valid_at_export=True,
        )
        client.force_login(admin_user)
        url = reverse("crossref:issue-deposit", args=[issue_with_xml.pk])
        response = client.get(url)

        content = response.content.decode()
        assert "Spremno za Crossref" in content
        assert "doi.crossref.org" in content

    def test_context_has_xml_flag(self, client, admin_user, issue_with_xml):
        """Context includes has_xml flag."""
        client.force_login(admin_user)
        url = reverse("crossref:issue-deposit", args=[issue_with_xml.pk])
        response = client.get(url)

        assert response.context["has_xml"] is True


# =============================================================================
# Task 5: Mark as Deposited Tests
# =============================================================================


@pytest.mark.django_db
class TestMarkDeposited:
    """Tests for mark_deposited view (Task 5)."""

    def test_mark_deposited_sets_fields(self, client, admin_user, issue_with_xml):
        """Mark deposited sets timestamp and user."""
        client.force_login(admin_user)
        url = reverse("crossref:mark-deposited", args=[issue_with_xml.pk])
        response = client.post(url)

        issue_with_xml.refresh_from_db()
        assert issue_with_xml.crossref_deposited_at is not None
        assert issue_with_xml.crossref_deposited_by == admin_user

    def test_mark_deposited_requires_login(self, client, issue_with_xml):
        """Mark deposited requires authentication."""
        url = reverse("crossref:mark-deposited", args=[issue_with_xml.pk])
        response = client.post(url)

        assert response.status_code == 302
        assert "/accounts/login/" in response.url

    def test_mark_deposited_requires_permission(self, client, other_user, issue):
        """Mark deposited requires publisher access."""
        client.force_login(other_user)
        url = reverse("crossref:mark-deposited", args=[issue.pk])
        response = client.post(url)

        assert response.status_code == 403

    def test_mark_deposited_returns_partial(self, client, admin_user, issue_with_xml):
        """Mark deposited returns HTMX partial response."""
        client.force_login(admin_user)
        url = reverse("crossref:mark-deposited", args=[issue_with_xml.pk])
        response = client.post(url)

        assert response.status_code == 200
        content = response.content.decode()
        assert "Deponovano" in content

    def test_mark_deposited_only_post(self, client, admin_user, issue_with_xml):
        """Mark deposited only accepts POST requests."""
        client.force_login(admin_user)
        url = reverse("crossref:mark-deposited", args=[issue_with_xml.pk])
        response = client.get(url)

        assert response.status_code == 405


# =============================================================================
# Task 7: Issue List Deposit Status Tests
# =============================================================================


@pytest.mark.django_db
class TestIssueListDepositStatus:
    """Tests for deposit status on issue list (Task 7)."""

    def test_deposited_badge_shown_on_list(self, client, admin_user, deposited_issue):
        """Deposited badge shown on issue list."""
        client.force_login(admin_user)
        url = reverse("issues:list")
        response = client.get(url)

        content = response.content.decode()
        assert "Deponovano" in content


# =============================================================================
# URL Resolution Tests
# =============================================================================


@pytest.mark.django_db
class TestDepositURLPatterns:
    """Tests for deposit URL pattern resolution."""

    def test_deposit_url_resolves(self, issue):
        """Deposit page URL pattern resolves correctly."""
        url = reverse("crossref:issue-deposit", args=[issue.pk])
        assert f"/issues/{issue.pk}/deposit/" in url

    def test_mark_deposited_url_resolves(self, issue):
        """Mark deposited URL pattern resolves correctly."""
        url = reverse("crossref:mark-deposited", args=[issue.pk])
        assert f"/issues/{issue.pk}/mark-deposited/" in url
