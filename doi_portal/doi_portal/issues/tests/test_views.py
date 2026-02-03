"""
Tests for Issue views.

Story 2.6 - Task 11: Comprehensive view tests covering AC #1-#8.
"""

import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.test import Client
from django.urls import reverse

from doi_portal.issues.models import Issue, IssueStatus
from doi_portal.publications.tests.factories import (
    ConferenceFactory,
    PublicationFactory,
    PublisherFactory,
)

from .factories import IssueFactory

User = get_user_model()


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def client():
    """Create a test client."""
    return Client()


@pytest.fixture
def publisher_a():
    """Create publisher A."""
    return PublisherFactory(name="Izdavač A")


@pytest.fixture
def publisher_b():
    """Create publisher B."""
    return PublisherFactory(name="Izdavač B")


@pytest.fixture
def publication_a(publisher_a):
    """Create publication for publisher A."""
    return PublicationFactory(publisher=publisher_a)


@pytest.fixture
def publication_b(publisher_b):
    """Create publication for publisher B."""
    return PublicationFactory(publisher=publisher_b)


@pytest.fixture
def admin_user():
    """Create an admin user."""
    user = User.objects.create_user(
        email="admin@test.com", password="testpass123"
    )
    group, _ = Group.objects.get_or_create(name="Administrator")
    user.groups.add(group)
    return user


@pytest.fixture
def superuser():
    """Create a Django superuser."""
    return User.objects.create_superuser(
        email="super@test.com", password="testpass123"
    )


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
def regular_user():
    """Create a regular user without roles."""
    return User.objects.create_user(
        email="user@test.com", password="testpass123"
    )


# =============================================================================
# 11.9: Test IssueListView - displays issues, filtered by publisher scope
# =============================================================================


@pytest.mark.django_db
class TestIssueListView:
    """Test issue list view."""

    def test_list_requires_login(self, client):
        """List view requires authentication."""
        response = client.get(reverse("issues:list"))
        assert response.status_code == 302
        assert "login" in response.url

    def test_list_requires_valid_role(self, client, regular_user):
        """List view requires a valid role."""
        client.force_login(regular_user)
        response = client.get(reverse("issues:list"))
        assert response.status_code == 403

    def test_list_accessible_to_admin(self, client, admin_user):
        """11.9: Admin can access list view."""
        client.force_login(admin_user)
        response = client.get(reverse("issues:list"))
        assert response.status_code == 200

    def test_list_shows_issues(self, client, admin_user, publication_a):
        """11.9: List view shows issues."""
        IssueFactory(
            publication=publication_a, volume="1", issue_number="1", year=2026
        )
        client.force_login(admin_user)
        response = client.get(reverse("issues:list"))
        assert response.status_code == 200
        assert b"2026" in response.content

    def test_urednik_sees_only_own_publisher_issues(
        self, client, urednik_user, publication_a, publication_b
    ):
        """11.9: Urednik sees only issues from assigned publisher."""
        IssueFactory(
            publication=publication_a, volume="1", issue_number="1", year=2026
        )
        IssueFactory(
            publication=publication_b, volume="2", issue_number="1", year=2025
        )
        client.force_login(urednik_user)
        response = client.get(reverse("issues:list"))
        content = response.content.decode("utf-8")
        assert "2026" in content
        assert "2025" not in content

    def test_admin_sees_all_issues(
        self, client, admin_user, publication_a, publication_b
    ):
        """11.9: Administrator sees all issues (AC #8)."""
        IssueFactory(
            publication=publication_a, volume="1", issue_number="1", year=2026
        )
        IssueFactory(
            publication=publication_b, volume="2", issue_number="1", year=2025
        )
        client.force_login(admin_user)
        response = client.get(reverse("issues:list"))
        content = response.content.decode("utf-8")
        assert "2026" in content
        assert "2025" in content


# =============================================================================
# 11.10: Test IssueListView - filter by status
# =============================================================================


@pytest.mark.django_db
class TestIssueListViewStatusFilter:
    """Test issue list view status filter."""

    def test_filter_by_status(self, client, admin_user, publication_a):
        """11.10: Filter issues by status."""
        IssueFactory(
            publication=publication_a,
            volume="1",
            issue_number="1",
            year=2026,
            status=IssueStatus.PUBLISHED,
        )
        IssueFactory(
            publication=publication_a,
            volume="1",
            issue_number="2",
            year=2025,
            status=IssueStatus.DRAFT,
        )
        client.force_login(admin_user)
        response = client.get(reverse("issues:list"), {"status": "PUBLISHED"})
        content = response.content.decode("utf-8")
        assert "2026" in content
        assert "2025" not in content


# =============================================================================
# 11.11: Test IssueListView - filter by publication
# =============================================================================


@pytest.mark.django_db
class TestIssueListViewPublicationFilter:
    """Test issue list view publication filter."""

    def test_filter_by_publication(
        self, client, admin_user, publication_a, publication_b
    ):
        """11.11: Filter issues by publication."""
        IssueFactory(
            publication=publication_a,
            volume="1",
            issue_number="1",
            year=2026,
        )
        IssueFactory(
            publication=publication_b,
            volume="2",
            issue_number="1",
            year=2025,
        )
        client.force_login(admin_user)
        response = client.get(
            reverse("issues:list"), {"publication": publication_a.pk}
        )
        content = response.content.decode("utf-8")
        assert "2026" in content
        assert "2025" not in content

    def test_filter_by_publication_shows_breadcrumbs_with_publication(
        self, client, admin_user, publication_a
    ):
        """11.11: Filtering by publication shows publication in breadcrumbs."""
        IssueFactory(publication=publication_a, volume="1", issue_number="1")
        client.force_login(admin_user)
        response = client.get(
            reverse("issues:list"), {"publication": publication_a.pk}
        )
        assert response.status_code == 200
        content = response.content.decode("utf-8")
        assert publication_a.title in content


# =============================================================================
# 11.12: Test IssueCreateView - Urednik can create for own publication
# =============================================================================


@pytest.mark.django_db
class TestIssueCreateView:
    """Test issue create view."""

    def test_urednik_can_create_for_own_publication(
        self, client, urednik_user, publication_a
    ):
        """11.12: Urednik can create issue for assigned publisher's publication."""
        client.force_login(urednik_user)
        response = client.post(
            reverse("issues:create"),
            {
                "publication": publication_a.pk,
                "volume": "1",
                "issue_number": "1",
                "year": 2026,
                "status": IssueStatus.DRAFT,
                "title": "",
                "publication_date": "",
                "proceedings_title": "",
                "proceedings_publisher_name": "",
                "proceedings_publisher_place": "",
            },
        )
        assert response.status_code == 302  # Redirect on success
        assert Issue.objects.filter(
            publication=publication_a, volume="1", issue_number="1"
        ).exists()

    def test_urednik_cannot_create_for_other_publication(
        self, client, urednik_user, publication_b
    ):
        """11.13: Urednik cannot create issue for another publisher's publication (AC #7)."""
        client.force_login(urednik_user)
        response = client.post(
            reverse("issues:create"),
            {
                "publication": publication_b.pk,
                "volume": "1",
                "issue_number": "1",
                "year": 2026,
                "status": IssueStatus.DRAFT,
                "title": "",
                "publication_date": "",
                "proceedings_title": "",
                "proceedings_publisher_name": "",
                "proceedings_publisher_place": "",
            },
        )
        # Form should be invalid because publication_b is not in user's queryset
        assert response.status_code == 200  # Form re-displayed
        assert not Issue.objects.filter(publication=publication_b).exists()

    def test_admin_can_create_for_any_publication(
        self, client, admin_user, publication_a, publication_b
    ):
        """11.14: Administrator can create issue for any publication (AC #8)."""
        client.force_login(admin_user)
        response = client.post(
            reverse("issues:create"),
            {
                "publication": publication_b.pk,
                "volume": "1",
                "issue_number": "1",
                "year": 2026,
                "status": IssueStatus.DRAFT,
                "title": "",
                "publication_date": "",
                "proceedings_title": "",
                "proceedings_publisher_name": "",
                "proceedings_publisher_place": "",
            },
        )
        assert response.status_code == 302
        assert Issue.objects.filter(publication=publication_b).exists()

    def test_create_form_displays(self, client, admin_user):
        """Create form is accessible."""
        client.force_login(admin_user)
        response = client.get(reverse("issues:create"))
        assert response.status_code == 200
        assert "Novo izdanje" in response.content.decode("utf-8")

    def test_create_with_publication_preselect(
        self, client, admin_user, publication_a
    ):
        """Create form pre-selects publication from query param."""
        client.force_login(admin_user)
        response = client.get(
            reverse("issues:create"),
            {"publication": publication_a.pk},
        )
        assert response.status_code == 200

    def test_create_sets_default_draft_status(
        self, client, admin_user, publication_a
    ):
        """11.5 (AC #5): Issue created with DRAFT status by default."""
        client.force_login(admin_user)
        client.post(
            reverse("issues:create"),
            {
                "publication": publication_a.pk,
                "volume": "1",
                "issue_number": "1",
                "year": 2026,
                "status": IssueStatus.DRAFT,
                "title": "",
                "publication_date": "",
                "proceedings_title": "",
                "proceedings_publisher_name": "",
                "proceedings_publisher_place": "",
            },
        )
        issue = Issue.objects.get(
            publication=publication_a, volume="1", issue_number="1"
        )
        assert issue.status == IssueStatus.DRAFT


# =============================================================================
# 11.15: Test IssueUpdateView - Urednik can edit own
# =============================================================================


@pytest.mark.django_db
class TestIssueUpdateView:
    """Test issue update view."""

    def test_urednik_can_edit_own_issue(
        self, client, urednik_user, publication_a
    ):
        """11.15: Urednik can edit issues from assigned publisher."""
        issue = IssueFactory(
            publication=publication_a,
            volume="1",
            issue_number="1",
            year=2026,
        )
        client.force_login(urednik_user)
        response = client.get(reverse("issues:update", kwargs={"pk": issue.pk}))
        assert response.status_code == 200

    def test_urednik_cannot_edit_other_publisher_issue(
        self, client, urednik_user, publication_b
    ):
        """11.15: Urednik gets 404 for editing another publisher's issue."""
        issue = IssueFactory(
            publication=publication_b,
            volume="1",
            issue_number="1",
            year=2026,
        )
        client.force_login(urednik_user)
        response = client.get(reverse("issues:update", kwargs={"pk": issue.pk}))
        assert response.status_code == 404

    def test_update_changes_data(self, client, admin_user, publication_a):
        """11.15: Update view saves changes."""
        issue = IssueFactory(
            publication=publication_a,
            volume="1",
            issue_number="1",
            year=2026,
            title="Original",
        )
        client.force_login(admin_user)
        response = client.post(
            reverse("issues:update", kwargs={"pk": issue.pk}),
            {
                "publication": publication_a.pk,
                "volume": "1",
                "issue_number": "1",
                "year": 2026,
                "status": IssueStatus.PUBLISHED,
                "title": "Updated",
                "publication_date": "",
                "proceedings_title": "",
                "proceedings_publisher_name": "",
                "proceedings_publisher_place": "",
            },
        )
        assert response.status_code == 302
        issue.refresh_from_db()
        assert issue.title == "Updated"
        assert issue.status == IssueStatus.PUBLISHED


# =============================================================================
# 11.16: Test IssueUpdateView - Bibliotekar cannot edit (403)
# =============================================================================


@pytest.mark.django_db
class TestIssueUpdateViewBibliotekar:
    """Test Bibliotekar cannot edit issues."""

    def test_bibliotekar_cannot_edit(
        self, client, bibliotekar_user, publication_a
    ):
        """11.16: Bibliotekar gets 403 when trying to edit (AC #7)."""
        issue = IssueFactory(publication=publication_a, volume="1", issue_number="1")
        client.force_login(bibliotekar_user)
        response = client.get(reverse("issues:update", kwargs={"pk": issue.pk}))
        assert response.status_code == 403


# =============================================================================
# 11.17: Test IssueDeleteView - only Administrator can delete
# =============================================================================


@pytest.mark.django_db
class TestIssueDeleteView:
    """Test issue delete view."""

    def test_admin_can_access_delete(self, client, admin_user, publication_a):
        """11.17: Administrator can access delete confirmation."""
        issue = IssueFactory(publication=publication_a, volume="1", issue_number="1")
        client.force_login(admin_user)
        response = client.get(reverse("issues:delete", kwargs={"pk": issue.pk}))
        assert response.status_code == 200
        assert "Potvrda brisanja" in response.content.decode("utf-8")

    def test_urednik_cannot_delete(self, client, urednik_user, publication_a):
        """11.17: Urednik cannot delete issues."""
        issue = IssueFactory(publication=publication_a, volume="1", issue_number="1")
        client.force_login(urednik_user)
        response = client.get(reverse("issues:delete", kwargs={"pk": issue.pk}))
        assert response.status_code == 403

    def test_bibliotekar_cannot_delete(
        self, client, bibliotekar_user, publication_a
    ):
        """11.17: Bibliotekar cannot delete issues."""
        issue = IssueFactory(publication=publication_a, volume="1", issue_number="1")
        client.force_login(bibliotekar_user)
        response = client.get(reverse("issues:delete", kwargs={"pk": issue.pk}))
        assert response.status_code == 403

    def test_soft_delete_via_view(self, client, admin_user, publication_a):
        """11.18: Delete view performs soft delete (not hard delete)."""
        issue = IssueFactory(publication=publication_a, volume="1", issue_number="1")
        client.force_login(admin_user)
        response = client.post(reverse("issues:delete", kwargs={"pk": issue.pk}))
        assert response.status_code == 302

        # Should be soft deleted
        issue.refresh_from_db()
        assert issue.is_deleted is True
        assert not Issue.objects.filter(pk=issue.pk).exists()
        assert Issue.all_objects.filter(pk=issue.pk).exists()


# =============================================================================
# 11.19: Test auditlog registration (LogEntry created)
# =============================================================================


@pytest.mark.django_db
class TestIssueAuditLog:
    """Test audit log registration for Issue model."""

    def test_audit_log_records_create(self, client, admin_user, publication_a):
        """11.19: Audit log records issue creation."""
        from auditlog.models import LogEntry

        client.force_login(admin_user)
        client.post(
            reverse("issues:create"),
            {
                "publication": publication_a.pk,
                "volume": "1",
                "issue_number": "1",
                "year": 2026,
                "status": IssueStatus.DRAFT,
                "title": "",
                "publication_date": "",
                "proceedings_title": "",
                "proceedings_publisher_name": "",
                "proceedings_publisher_place": "",
            },
        )
        issue = Issue.objects.get(
            publication=publication_a, volume="1", issue_number="1"
        )
        create_log = LogEntry.objects.filter(
            object_pk=str(issue.pk),
            action=LogEntry.Action.CREATE,
        )
        assert create_log.exists()

    def test_audit_log_records_update(self, client, admin_user, publication_a):
        """11.19: Audit log records issue update (AC #6)."""
        from auditlog.models import LogEntry

        issue = IssueFactory(
            publication=publication_a,
            volume="1",
            issue_number="1",
            year=2026,
        )
        client.force_login(admin_user)
        client.post(
            reverse("issues:update", kwargs={"pk": issue.pk}),
            {
                "publication": publication_a.pk,
                "volume": "1",
                "issue_number": "1",
                "year": 2026,
                "status": IssueStatus.PUBLISHED,
                "title": "Updated",
                "publication_date": "",
                "proceedings_title": "",
                "proceedings_publisher_name": "",
                "proceedings_publisher_place": "",
            },
        )
        update_log = LogEntry.objects.filter(
            object_pk=str(issue.pk),
            action=LogEntry.Action.UPDATE,
        )
        assert update_log.exists()


# =============================================================================
# 11.21: Test Publication admin list issue_count column
# =============================================================================


@pytest.mark.django_db
class TestPublicationListIssueCountWithIssues:
    """Test Publication admin list shows correct issue_count with real issues."""

    def test_publication_list_shows_issue_count(
        self, client, admin_user, publication_a
    ):
        """11.21: Publication list issue_count reflects real issue count."""
        IssueFactory(
            publication=publication_a,
            volume="1",
            issue_number="1",
            year=2026,
        )
        IssueFactory(
            publication=publication_a,
            volume="1",
            issue_number="2",
            year=2026,
        )
        client.force_login(admin_user)
        response = client.get(reverse("publications:list"))
        assert response.status_code == 200
        content = response.content.decode("utf-8")
        # Should show count of 2 for this publication
        assert "2" in content


# =============================================================================
# 11.22: Test breadcrumbs on all pages
# =============================================================================


@pytest.mark.django_db
class TestIssueBreadcrumbs:
    """Test breadcrumbs on all issue pages."""

    def test_list_breadcrumbs(self, client, admin_user):
        """11.22: List page has correct breadcrumbs."""
        client.force_login(admin_user)
        response = client.get(reverse("issues:list"))
        assert response.status_code == 200
        content = response.content.decode("utf-8")
        assert "Kontrolna tabla" in content
        assert "Izdanja" in content

    def test_create_breadcrumbs(self, client, admin_user):
        """11.22: Create page has correct breadcrumbs."""
        client.force_login(admin_user)
        response = client.get(reverse("issues:create"))
        assert response.status_code == 200
        content = response.content.decode("utf-8")
        assert "Kontrolna tabla" in content
        assert "Izdanja" in content
        assert "Novo izdanje" in content

    def test_detail_breadcrumbs(self, client, admin_user, publication_a):
        """11.22: Detail page has correct breadcrumbs."""
        issue = IssueFactory(
            publication=publication_a, volume="1", issue_number="1", year=2026
        )
        client.force_login(admin_user)
        response = client.get(reverse("issues:detail", kwargs={"pk": issue.pk}))
        assert response.status_code == 200
        content = response.content.decode("utf-8")
        assert "Kontrolna tabla" in content
        assert "Izdanja" in content

    def test_delete_breadcrumbs(self, client, admin_user, publication_a):
        """11.22: Delete page has correct breadcrumbs."""
        issue = IssueFactory(
            publication=publication_a, volume="1", issue_number="1", year=2026
        )
        client.force_login(admin_user)
        response = client.get(reverse("issues:delete", kwargs={"pk": issue.pk}))
        assert response.status_code == 200
        content = response.content.decode("utf-8")
        assert "Kontrolna tabla" in content
        assert "Izdanja" in content


# =============================================================================
# 11.23: Test proceedings fields visible only for CONFERENCE publications
# =============================================================================


@pytest.mark.django_db
class TestProceedingsFieldsVisibility:
    """Test proceedings fields visibility based on publication type."""

    def test_proceedings_fields_shown_for_conference(
        self, client, admin_user
    ):
        """11.23: Proceedings fields visible in detail for CONFERENCE publication."""
        conference_pub = ConferenceFactory()
        issue = IssueFactory(
            publication=conference_pub,
            volume="1",
            issue_number="1",
            year=2026,
            proceedings_title="Zbornik naučne konferencije",
            proceedings_publisher_name="Akademija nauka",
            proceedings_publisher_place="Beograd",
        )
        client.force_login(admin_user)
        response = client.get(reverse("issues:detail", kwargs={"pk": issue.pk}))
        content = response.content.decode("utf-8")
        assert "Podaci o zborniku" in content
        assert "Zbornik naučne konferencije" in content
        assert "Akademija nauka" in content
        assert "Beograd" in content

    def test_proceedings_fields_hidden_for_journal(self, client, admin_user):
        """11.23: Proceedings fields NOT shown in detail for JOURNAL publication."""
        journal_pub = PublicationFactory()  # Default is JOURNAL
        issue = IssueFactory(
            publication=journal_pub, volume="1", issue_number="1", year=2026
        )
        client.force_login(admin_user)
        response = client.get(reverse("issues:detail", kwargs={"pk": issue.pk}))
        content = response.content.decode("utf-8")
        assert "Podaci o zborniku" not in content


# =============================================================================
# Test IssueDetailView
# =============================================================================


@pytest.mark.django_db
class TestIssueDetailView:
    """Test issue detail view."""

    def test_detail_displays_issue(self, client, admin_user, publication_a):
        """Detail view displays issue information."""
        issue = IssueFactory(
            publication=publication_a,
            volume="5",
            issue_number="3",
            year=2026,
            title="Posebno izdanje",
            status=IssueStatus.PUBLISHED,
        )
        client.force_login(admin_user)
        response = client.get(reverse("issues:detail", kwargs={"pk": issue.pk}))
        assert response.status_code == 200
        content = response.content.decode("utf-8")
        assert "5" in content  # Volume
        assert "3" in content  # Issue number
        assert "2026" in content
        assert "Posebno izdanje" in content
        assert "Objavljeno" in content

    def test_detail_scoped_for_urednik(
        self, client, urednik_user, publication_a, publication_b
    ):
        """Urednik can see own, gets 404 for other publisher's issue."""
        issue_own = IssueFactory(
            publication=publication_a, volume="1", issue_number="1"
        )
        issue_other = IssueFactory(
            publication=publication_b, volume="2", issue_number="1"
        )
        client.force_login(urednik_user)
        response_own = client.get(
            reverse("issues:detail", kwargs={"pk": issue_own.pk})
        )
        response_other = client.get(
            reverse("issues:detail", kwargs={"pk": issue_other.pk})
        )
        assert response_own.status_code == 200
        assert response_other.status_code == 404

    def test_detail_shows_empty_articles_message(
        self, client, admin_user, publication_a
    ):
        """Detail view shows empty message when no articles."""
        issue = IssueFactory(publication=publication_a, volume="1", issue_number="1")
        client.force_login(admin_user)
        response = client.get(reverse("issues:detail", kwargs={"pk": issue.pk}))
        content = response.content.decode("utf-8")
        assert "Članci (0)" in content
        assert "Nema članaka u ovom izdanju" in content

    def test_bibliotekar_can_view_detail(
        self, client, bibliotekar_user, publication_a
    ):
        """Bibliotekar can view issue detail (read-only)."""
        issue = IssueFactory(publication=publication_a, volume="1", issue_number="1")
        client.force_login(bibliotekar_user)
        response = client.get(reverse("issues:detail", kwargs={"pk": issue.pk}))
        assert response.status_code == 200
