"""
End-to-end row-level permission integration tests.

Story 2.8: Comprehensive permission testing for all content hierarchy views.
Covers Tasks 3-6 with tests for Publisher, Publication, Issue views,
guardian permission sync, and publisher assignment changes.

AC Coverage:
- AC#1: Guardian auto-assignment on publisher FK set
- AC#2: Queryset filtering for Urednik/Bibliotekar
- AC#3: Direct URL access blocked (403/404)
- AC#4: Administrator full access (no filtering)
- AC#5: Permission sync on publisher change
- AC#6: Issue queryset filtering via publication__publisher
- AC#7: Bibliotekar cannot edit (403)
- AC#8: User without publisher gets empty queryset / 403
"""

import pytest
from django.contrib.auth.models import Group
from django.test import Client

from doi_portal.issues.tests.factories import IssueFactory
from doi_portal.publications.tests.factories import PublicationFactory, PublisherFactory
from doi_portal.users.tests.factories import UserFactory


# ============================================================================
# Shared Fixtures
# ============================================================================


@pytest.fixture
def two_publishers(db):
    """Create two publishers for isolation testing."""
    pub_a = PublisherFactory(name="Publisher A", doi_prefix="10.1111")
    pub_b = PublisherFactory(name="Publisher B", doi_prefix="10.2222")
    return pub_a, pub_b


@pytest.fixture
def urednik_a(two_publishers):
    """Urednik assigned to Publisher A."""
    user = UserFactory()
    user.publisher = two_publishers[0]
    user.save()
    Group.objects.get(name="Urednik").user_set.add(user)
    return user


@pytest.fixture
def urednik_b(two_publishers):
    """Urednik assigned to Publisher B."""
    user = UserFactory()
    user.publisher = two_publishers[1]
    user.save()
    Group.objects.get(name="Urednik").user_set.add(user)
    return user


@pytest.fixture
def bibliotekar_a(two_publishers):
    """Bibliotekar assigned to Publisher A."""
    user = UserFactory()
    user.publisher = two_publishers[0]
    user.save()
    Group.objects.get(name="Bibliotekar").user_set.add(user)
    return user


@pytest.fixture
def administrator_user(db):
    """Administrator user with full access."""
    user = UserFactory()
    Group.objects.get(name="Administrator").user_set.add(user)
    return user


@pytest.fixture
def superuser_user(db):
    """Django superuser with full access."""
    user = UserFactory(is_superuser=True)
    return user


@pytest.fixture
def urednik_no_publisher(db):
    """Urednik without publisher assignment."""
    user = UserFactory()
    Group.objects.get(name="Urednik").user_set.add(user)
    return user


@pytest.fixture
def no_role_user(db):
    """User without any role group."""
    user = UserFactory()
    return user


@pytest.fixture
def publication_a(two_publishers):
    """Publication belonging to Publisher A."""
    return PublicationFactory(publisher=two_publishers[0])


@pytest.fixture
def publication_b(two_publishers):
    """Publication belonging to Publisher B."""
    return PublicationFactory(publisher=two_publishers[1])


@pytest.fixture
def issue_a(publication_a):
    """Issue belonging to Publication A (Publisher A)."""
    return IssueFactory(publication=publication_a)


@pytest.fixture
def issue_b(publication_b):
    """Issue belonging to Publication B (Publisher B)."""
    return IssueFactory(publication=publication_b)


def login_user(client, user):
    """Log in a user using the test client."""
    client.force_login(user)


# ============================================================================
# Task 3: Publisher Admin Views Permissions (AC#3, #4)
# ============================================================================


@pytest.mark.django_db
class TestPublisherViewsPermissions:
    """Test Publisher admin views are Admin-only (Story 2.8 - Task 3)."""

    def test_publisher_list_accessible_by_administrator(
        self, administrator_user, two_publishers
    ):
        """AC#4: Administrator can access publisher list."""
        client = Client()
        login_user(client, administrator_user)
        response = client.get("/dashboard/publishers/")
        assert response.status_code == 200

    def test_publisher_list_accessible_by_superuser(
        self, superuser_user, two_publishers
    ):
        """AC#4: Superuser can access publisher list."""
        client = Client()
        login_user(client, superuser_user)
        response = client.get("/dashboard/publishers/")
        assert response.status_code == 200

    def test_publisher_list_denied_for_urednik(self, urednik_a):
        """AC#3: Urednik cannot access publisher list (Admin-only)."""
        client = Client()
        login_user(client, urednik_a)
        response = client.get("/dashboard/publishers/")
        assert response.status_code == 403

    def test_publisher_list_denied_for_bibliotekar(self, bibliotekar_a):
        """AC#3: Bibliotekar cannot access publisher list (Admin-only)."""
        client = Client()
        login_user(client, bibliotekar_a)
        response = client.get("/dashboard/publishers/")
        assert response.status_code == 403

    def test_publisher_create_denied_for_urednik(self, urednik_a):
        """AC#3: Urednik cannot create publishers."""
        client = Client()
        login_user(client, urednik_a)
        response = client.get("/dashboard/publishers/create/")
        assert response.status_code == 403

    def test_publisher_create_allowed_for_administrator(self, administrator_user):
        """AC#4: Administrator can access publisher create."""
        client = Client()
        login_user(client, administrator_user)
        response = client.get("/dashboard/publishers/create/")
        assert response.status_code == 200

    def test_publisher_detail_denied_for_urednik(self, urednik_a, two_publishers):
        """AC#3: Urednik cannot view publisher detail."""
        client = Client()
        login_user(client, urednik_a)
        response = client.get(f"/dashboard/publishers/{two_publishers[0].pk}/")
        assert response.status_code == 403

    def test_publisher_update_denied_for_urednik(self, urednik_a, two_publishers):
        """AC#3: Urednik cannot edit publishers."""
        client = Client()
        login_user(client, urednik_a)
        response = client.get(f"/dashboard/publishers/{two_publishers[0].pk}/edit/")
        assert response.status_code == 403

    def test_publisher_delete_denied_for_urednik(self, urednik_a, two_publishers):
        """AC#3: Urednik cannot delete publishers."""
        client = Client()
        login_user(client, urednik_a)
        response = client.get(f"/dashboard/publishers/{two_publishers[0].pk}/delete/")
        assert response.status_code == 403

    def test_publisher_detail_allowed_for_administrator(
        self, administrator_user, two_publishers
    ):
        """AC#4: Administrator can view publisher detail."""
        client = Client()
        login_user(client, administrator_user)
        response = client.get(f"/dashboard/publishers/{two_publishers[0].pk}/")
        assert response.status_code == 200

    def test_publisher_update_allowed_for_administrator(
        self, administrator_user, two_publishers
    ):
        """AC#4: Administrator can edit publishers."""
        client = Client()
        login_user(client, administrator_user)
        response = client.get(f"/dashboard/publishers/{two_publishers[0].pk}/edit/")
        assert response.status_code == 200

    def test_publisher_delete_allowed_for_administrator(
        self, administrator_user, two_publishers
    ):
        """AC#4: Administrator can access publisher delete."""
        client = Client()
        login_user(client, administrator_user)
        response = client.get(f"/dashboard/publishers/{two_publishers[0].pk}/delete/")
        assert response.status_code == 200

    def test_publisher_list_denied_for_unauthenticated(self):
        """Unauthenticated users are redirected to login."""
        client = Client()
        response = client.get("/dashboard/publishers/")
        assert response.status_code == 302  # Redirect to login


# ============================================================================
# Task 4: Publication Admin Views Permissions (AC#2, #3, #4, #7)
# ============================================================================


@pytest.mark.django_db
class TestPublicationViewsPermissions:
    """Test Publication admin views permissions (Story 2.8 - Task 4)."""

    def test_publication_list_shows_only_own_for_urednik(
        self, urednik_a, publication_a, publication_b
    ):
        """AC#2: Urednik sees ONLY publications from assigned publisher."""
        client = Client()
        login_user(client, urednik_a)
        response = client.get("/dashboard/publications/")
        assert response.status_code == 200
        publications = list(response.context["publications"])
        assert publication_a in publications
        assert publication_b not in publications

    def test_publication_list_shows_all_for_administrator(
        self, administrator_user, publication_a, publication_b
    ):
        """AC#4: Administrator sees ALL publications."""
        client = Client()
        login_user(client, administrator_user)
        response = client.get("/dashboard/publications/")
        assert response.status_code == 200
        publications = list(response.context["publications"])
        assert publication_a in publications
        assert publication_b in publications

    def test_publication_list_shows_all_for_superuser(
        self, superuser_user, publication_a, publication_b
    ):
        """AC#4: Superuser sees ALL publications."""
        client = Client()
        login_user(client, superuser_user)
        response = client.get("/dashboard/publications/")
        assert response.status_code == 200
        publications = list(response.context["publications"])
        assert publication_a in publications
        assert publication_b in publications

    def test_publication_detail_allowed_for_own_publisher_urednik(
        self, urednik_a, publication_a
    ):
        """AC#2: Urednik can view detail of own publisher's publication."""
        client = Client()
        login_user(client, urednik_a)
        response = client.get(f"/dashboard/publications/{publication_a.slug}/")
        assert response.status_code == 200

    def test_publication_detail_blocked_for_other_publisher_urednik(
        self, urednik_a, publication_b
    ):
        """AC#3: Urednik cannot access publication of another publisher via direct URL."""
        client = Client()
        login_user(client, urednik_a)
        response = client.get(f"/dashboard/publications/{publication_b.slug}/")
        # Queryset scoping returns 404 (object not in filtered queryset)
        assert response.status_code == 404

    def test_publication_update_allowed_for_own_publisher_urednik(
        self, urednik_a, publication_a
    ):
        """AC#2: Urednik can edit own publisher's publication."""
        client = Client()
        login_user(client, urednik_a)
        response = client.get(f"/dashboard/publications/{publication_a.slug}/edit/")
        assert response.status_code == 200

    def test_publication_update_blocked_for_other_publisher_urednik(
        self, urednik_a, publication_b
    ):
        """AC#3: Urednik cannot edit publication of another publisher."""
        client = Client()
        login_user(client, urednik_a)
        response = client.get(f"/dashboard/publications/{publication_b.slug}/edit/")
        # Queryset scoping returns 404
        assert response.status_code == 404

    def test_publication_update_blocked_for_bibliotekar(
        self, bibliotekar_a, publication_a
    ):
        """AC#7: Bibliotekar cannot edit publications (read-only)."""
        client = Client()
        login_user(client, bibliotekar_a)
        response = client.get(f"/dashboard/publications/{publication_a.slug}/edit/")
        assert response.status_code == 403

    def test_publication_list_accessible_for_bibliotekar(
        self, bibliotekar_a, publication_a, publication_b
    ):
        """AC#7: Bibliotekar can view publication list (read-only)."""
        client = Client()
        login_user(client, bibliotekar_a)
        response = client.get("/dashboard/publications/")
        assert response.status_code == 200
        publications = list(response.context["publications"])
        # Bibliotekar sees only own publisher's publications
        assert publication_a in publications
        assert publication_b not in publications

    def test_publication_create_denied_for_urednik(self, urednik_a):
        """AC#3: Only Administrator can create publications."""
        client = Client()
        login_user(client, urednik_a)
        response = client.get("/dashboard/publications/create/")
        assert response.status_code == 403

    def test_publication_create_denied_for_bibliotekar(self, bibliotekar_a):
        """AC#7: Bibliotekar cannot create publications."""
        client = Client()
        login_user(client, bibliotekar_a)
        response = client.get("/dashboard/publications/create/")
        assert response.status_code == 403

    def test_publication_create_allowed_for_administrator(self, administrator_user):
        """AC#4: Administrator can create publications."""
        client = Client()
        login_user(client, administrator_user)
        response = client.get("/dashboard/publications/create/")
        assert response.status_code == 200

    def test_publication_delete_denied_for_urednik(self, urednik_a, publication_a):
        """AC#3: Urednik cannot delete publications."""
        client = Client()
        login_user(client, urednik_a)
        response = client.get(f"/dashboard/publications/{publication_a.slug}/delete/")
        assert response.status_code == 403

    def test_publication_delete_denied_for_bibliotekar(
        self, bibliotekar_a, publication_a
    ):
        """AC#7: Bibliotekar cannot delete publications."""
        client = Client()
        login_user(client, bibliotekar_a)
        response = client.get(f"/dashboard/publications/{publication_a.slug}/delete/")
        assert response.status_code == 403

    def test_publication_delete_allowed_for_administrator(
        self, administrator_user, publication_a
    ):
        """AC#4: Administrator can delete publications."""
        client = Client()
        login_user(client, administrator_user)
        response = client.get(f"/dashboard/publications/{publication_a.slug}/delete/")
        assert response.status_code == 200


# ============================================================================
# Task 5: Issue Admin Views Permissions (AC#6, #3, #7)
# ============================================================================


@pytest.mark.django_db
class TestIssueViewsPermissions:
    """Test Issue admin views permissions (Story 2.8 - Task 5)."""

    def test_issue_list_shows_only_own_for_urednik(
        self, urednik_a, issue_a, issue_b
    ):
        """AC#6: Urednik sees ONLY issues from assigned publisher's publications."""
        client = Client()
        login_user(client, urednik_a)
        response = client.get("/dashboard/issues/")
        assert response.status_code == 200
        issues = list(response.context["issues"])
        assert issue_a in issues
        assert issue_b not in issues

    def test_issue_list_shows_all_for_administrator(
        self, administrator_user, issue_a, issue_b
    ):
        """AC#4: Administrator sees ALL issues."""
        client = Client()
        login_user(client, administrator_user)
        response = client.get("/dashboard/issues/")
        assert response.status_code == 200
        issues = list(response.context["issues"])
        assert issue_a in issues
        assert issue_b in issues

    def test_issue_list_shows_all_for_superuser(
        self, superuser_user, issue_a, issue_b
    ):
        """AC#4: Superuser sees ALL issues."""
        client = Client()
        login_user(client, superuser_user)
        response = client.get("/dashboard/issues/")
        assert response.status_code == 200
        issues = list(response.context["issues"])
        assert issue_a in issues
        assert issue_b in issues

    def test_issue_detail_allowed_for_own_publisher_urednik(
        self, urednik_a, issue_a
    ):
        """AC#6: Urednik can view detail of own publisher's issue."""
        client = Client()
        login_user(client, urednik_a)
        response = client.get(f"/dashboard/issues/{issue_a.pk}/")
        assert response.status_code == 200

    def test_issue_detail_blocked_for_other_publisher_urednik(
        self, urednik_a, issue_b
    ):
        """AC#3: Urednik cannot access issue of another publisher via direct URL."""
        client = Client()
        login_user(client, urednik_a)
        response = client.get(f"/dashboard/issues/{issue_b.pk}/")
        # Queryset scoping returns 404
        assert response.status_code == 404

    def test_issue_update_allowed_for_own_publisher_urednik(
        self, urednik_a, issue_a
    ):
        """AC#6: Urednik can edit own publisher's issue."""
        client = Client()
        login_user(client, urednik_a)
        response = client.get(f"/dashboard/issues/{issue_a.pk}/edit/")
        assert response.status_code == 200

    def test_issue_update_blocked_for_other_publisher_urednik(
        self, urednik_a, issue_b
    ):
        """AC#3: Urednik cannot edit issue of another publisher."""
        client = Client()
        login_user(client, urednik_a)
        response = client.get(f"/dashboard/issues/{issue_b.pk}/edit/")
        # Queryset scoping returns 404
        assert response.status_code == 404

    def test_issue_create_allowed_for_urednik(self, urednik_a):
        """AC#6: Urednik can access issue create form."""
        client = Client()
        login_user(client, urednik_a)
        response = client.get("/dashboard/issues/create/")
        assert response.status_code == 200

    def test_issue_create_blocked_for_bibliotekar(self, bibliotekar_a):
        """AC#7: Bibliotekar cannot create issues."""
        client = Client()
        login_user(client, bibliotekar_a)
        response = client.get("/dashboard/issues/create/")
        assert response.status_code == 403

    def test_issue_update_blocked_for_bibliotekar(self, bibliotekar_a, issue_a):
        """AC#7: Bibliotekar cannot edit issues."""
        client = Client()
        login_user(client, bibliotekar_a)
        response = client.get(f"/dashboard/issues/{issue_a.pk}/edit/")
        assert response.status_code == 403

    def test_issue_delete_denied_for_urednik(self, urednik_a, issue_a):
        """AC#3: Urednik cannot delete issues (Admin-only)."""
        client = Client()
        login_user(client, urednik_a)
        response = client.get(f"/dashboard/issues/{issue_a.pk}/delete/")
        assert response.status_code == 403

    def test_issue_delete_denied_for_bibliotekar(self, bibliotekar_a, issue_a):
        """AC#7: Bibliotekar cannot delete issues."""
        client = Client()
        login_user(client, bibliotekar_a)
        response = client.get(f"/dashboard/issues/{issue_a.pk}/delete/")
        assert response.status_code == 403

    def test_issue_delete_allowed_for_administrator(
        self, administrator_user, issue_a
    ):
        """AC#4: Administrator can delete issues."""
        client = Client()
        login_user(client, administrator_user)
        response = client.get(f"/dashboard/issues/{issue_a.pk}/delete/")
        assert response.status_code == 200

    def test_issue_list_for_bibliotekar_is_read_only(
        self, bibliotekar_a, issue_a, issue_b
    ):
        """AC#7: Bibliotekar sees only own issues (read-only)."""
        client = Client()
        login_user(client, bibliotekar_a)
        response = client.get("/dashboard/issues/")
        assert response.status_code == 200
        issues = list(response.context["issues"])
        assert issue_a in issues
        assert issue_b not in issues


# ============================================================================
# Task 6: End-to-end permission integration tests (AC#1-#8)
# ============================================================================


@pytest.mark.django_db
class TestRowLevelPermissionsPublications:
    """E2E publication permission scenarios (Story 2.8 - Task 6.1)."""

    def test_urednik_a_sees_publication_a_not_b(
        self, urednik_a, publication_a, publication_b
    ):
        """AC#2: Urednik A sees publication_a, NOT publication_b."""
        client = Client()
        login_user(client, urednik_a)
        response = client.get("/dashboard/publications/")
        publications = list(response.context["publications"])
        assert publication_a in publications
        assert publication_b not in publications

    def test_urednik_b_sees_publication_b_not_a(
        self, urednik_b, publication_a, publication_b
    ):
        """AC#2: Urednik B sees publication_b, NOT publication_a."""
        client = Client()
        login_user(client, urednik_b)
        response = client.get("/dashboard/publications/")
        publications = list(response.context["publications"])
        assert publication_b in publications
        assert publication_a not in publications

    def test_admin_sees_all_publications(
        self, administrator_user, publication_a, publication_b
    ):
        """AC#4: Administrator sees both publications."""
        client = Client()
        login_user(client, administrator_user)
        response = client.get("/dashboard/publications/")
        publications = list(response.context["publications"])
        assert publication_a in publications
        assert publication_b in publications


@pytest.mark.django_db
class TestRowLevelPermissionsIssues:
    """E2E issue permission scenarios (Story 2.8 - Task 6.2)."""

    def test_urednik_a_sees_issue_a_not_b(self, urednik_a, issue_a, issue_b):
        """AC#6: Urednik A sees issue_a, NOT issue_b."""
        client = Client()
        login_user(client, urednik_a)
        response = client.get("/dashboard/issues/")
        issues = list(response.context["issues"])
        assert issue_a in issues
        assert issue_b not in issues

    def test_admin_sees_all_issues(self, administrator_user, issue_a, issue_b):
        """AC#4: Administrator sees all issues."""
        client = Client()
        login_user(client, administrator_user)
        response = client.get("/dashboard/issues/")
        issues = list(response.context["issues"])
        assert issue_a in issues
        assert issue_b in issues


@pytest.mark.django_db
class TestGuardianPermissionSync:
    """Guardian permission sync scenarios (Story 2.8 - Task 6.3)."""

    def test_guardian_permissions_assigned_on_user_save(self, two_publishers):
        """AC#1: Guardian permissions auto-assigned when publisher is set."""
        from guardian.shortcuts import get_perms

        user = UserFactory()
        user.publisher = two_publishers[0]
        user.save()

        perms = get_perms(user, two_publishers[0])
        assert "view_publisher" in perms
        assert "change_publisher" in perms

    def test_guardian_permissions_synced_via_signal(self, two_publishers):
        """AC#5: Signal syncs guardian permissions on publisher change."""
        from guardian.shortcuts import get_perms

        user = UserFactory()
        user.publisher = two_publishers[0]
        user.save()

        # Change publisher
        user.publisher = two_publishers[1]
        user.save()

        perms_a = get_perms(user, two_publishers[0])
        perms_b = get_perms(user, two_publishers[1])
        assert "view_publisher" not in perms_a
        assert "view_publisher" in perms_b

    def test_guardian_permissions_removed_when_publisher_cleared(self, two_publishers):
        """AC#5: Guardian permissions removed when publisher is cleared."""
        from guardian.shortcuts import get_perms

        user = UserFactory()
        user.publisher = two_publishers[0]
        user.save()

        user.publisher = None
        user.save()

        perms = get_perms(user, two_publishers[0])
        assert "view_publisher" not in perms
        assert "change_publisher" not in perms


@pytest.mark.django_db
class TestPublisherAssignmentChange:
    """Publisher assignment change scenarios (Story 2.8 - Task 6.4)."""

    def test_changing_publisher_updates_queryset_access(
        self, two_publishers, publication_a, publication_b
    ):
        """AC#5: After publisher change, user sees new publisher's content."""
        user = UserFactory()
        user.publisher = two_publishers[0]
        user.save()
        Group.objects.get(name="Urednik").user_set.add(user)

        client = Client()
        login_user(client, user)

        # Initially sees only publication_a
        response = client.get("/dashboard/publications/")
        publications = list(response.context["publications"])
        assert publication_a in publications
        assert publication_b not in publications

        # Change publisher to B
        user.publisher = two_publishers[1]
        user.save()

        response = client.get("/dashboard/publications/")
        publications = list(response.context["publications"])
        assert publication_b in publications
        assert publication_a not in publications

    def test_changing_publisher_updates_issue_access(
        self, two_publishers, issue_a, issue_b
    ):
        """AC#5: After publisher change, user sees new publisher's issues."""
        user = UserFactory()
        user.publisher = two_publishers[0]
        user.save()
        Group.objects.get(name="Urednik").user_set.add(user)

        client = Client()
        login_user(client, user)

        # Initially sees only issue_a
        response = client.get("/dashboard/issues/")
        issues = list(response.context["issues"])
        assert issue_a in issues
        assert issue_b not in issues

        # Change publisher to B
        user.publisher = two_publishers[1]
        user.save()

        response = client.get("/dashboard/issues/")
        issues = list(response.context["issues"])
        assert issue_b in issues
        assert issue_a not in issues


@pytest.mark.django_db
class TestNoPublisherAccess:
    """Test users without publisher assignment (Story 2.8 - Task 6.5, 6.6)."""

    def test_urednik_without_publisher_gets_empty_publication_list(
        self, urednik_no_publisher, publication_a
    ):
        """AC#8: Urednik without publisher gets empty queryset."""
        client = Client()
        login_user(client, urednik_no_publisher)
        response = client.get("/dashboard/publications/")
        # User has Urednik role but no publisher -> denied by test_func
        assert response.status_code == 403

    def test_urednik_without_publisher_gets_empty_issue_list(
        self, urednik_no_publisher, issue_a
    ):
        """AC#8: Urednik without publisher gets 403 on issues."""
        client = Client()
        login_user(client, urednik_no_publisher)
        response = client.get("/dashboard/issues/")
        assert response.status_code == 403

    def test_user_without_role_gets_403_on_publications(
        self, no_role_user, publication_a
    ):
        """AC#8: User without any role gets 403."""
        client = Client()
        login_user(client, no_role_user)
        response = client.get("/dashboard/publications/")
        assert response.status_code == 403

    def test_user_without_role_gets_403_on_issues(self, no_role_user, issue_a):
        """AC#8: User without any role gets 403 on issues."""
        client = Client()
        login_user(client, no_role_user)
        response = client.get("/dashboard/issues/")
        assert response.status_code == 403


@pytest.mark.django_db
class TestSuperuserFullAccess:
    """Test superuser (is_superuser=True) has full access (Story 2.8 - Task 6.7)."""

    def test_superuser_sees_all_publications(
        self, superuser_user, publication_a, publication_b
    ):
        """AC#4: Superuser sees all publications regardless of groups."""
        client = Client()
        login_user(client, superuser_user)
        response = client.get("/dashboard/publications/")
        assert response.status_code == 200
        publications = list(response.context["publications"])
        assert publication_a in publications
        assert publication_b in publications

    def test_superuser_sees_all_issues(self, superuser_user, issue_a, issue_b):
        """AC#4: Superuser sees all issues regardless of groups."""
        client = Client()
        login_user(client, superuser_user)
        response = client.get("/dashboard/issues/")
        assert response.status_code == 200
        issues = list(response.context["issues"])
        assert issue_a in issues
        assert issue_b in issues

    def test_superuser_can_access_publishers(self, superuser_user, two_publishers):
        """AC#4: Superuser can access publisher management."""
        client = Client()
        login_user(client, superuser_user)
        response = client.get("/dashboard/publishers/")
        assert response.status_code == 200

    def test_superuser_can_edit_any_publication(
        self, superuser_user, publication_a, publication_b
    ):
        """AC#4: Superuser can edit any publication."""
        client = Client()
        login_user(client, superuser_user)
        response = client.get(f"/dashboard/publications/{publication_a.slug}/edit/")
        assert response.status_code == 200
        response = client.get(f"/dashboard/publications/{publication_b.slug}/edit/")
        assert response.status_code == 200

    def test_superuser_can_edit_any_issue(self, superuser_user, issue_a, issue_b):
        """AC#4: Superuser can edit any issue."""
        client = Client()
        login_user(client, superuser_user)
        response = client.get(f"/dashboard/issues/{issue_a.pk}/edit/")
        assert response.status_code == 200
        response = client.get(f"/dashboard/issues/{issue_b.pk}/edit/")
        assert response.status_code == 200
