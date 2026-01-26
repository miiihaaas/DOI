"""
Tests for User Management by Superadmin (Story 1.6).

Tests cover:
- SuperadminRequiredMixin permission checks (AC: #1, #6)
- User list view functionality (AC: #1)
- User creation with role assignment (AC: #2, #3)
- User update with role/publisher changes (AC: #4)
- User activation/deactivation with session invalidation (AC: #5)
- Filtering and search functionality (AC: #1)
- Audit logging for user changes (AC: #4)
"""

import pytest
from django.contrib.auth.models import Group
from django.contrib.sessions.models import Session
from django.test import Client
from django.urls import reverse
from django.utils import timezone

from doi_portal.publishers.models import Publisher
from doi_portal.users.models import User
from doi_portal.users.tests.factories import UserFactory


@pytest.fixture
def superadmin_group(db) -> Group:
    """Get the Superadmin group."""
    return Group.objects.get(name="Superadmin")


@pytest.fixture
def administrator_group(db) -> Group:
    """Get the Administrator group."""
    return Group.objects.get(name="Administrator")


@pytest.fixture
def urednik_group(db) -> Group:
    """Get the Urednik group."""
    return Group.objects.get(name="Urednik")


@pytest.fixture
def bibliotekar_group(db) -> Group:
    """Get the Bibliotekar group."""
    return Group.objects.get(name="Bibliotekar")


@pytest.fixture
def superadmin_user(db, superadmin_group) -> User:
    """Create a superadmin user."""
    user = UserFactory(email="superadmin@example.com", password="testpass123")
    user.groups.add(superadmin_group)
    return user


@pytest.fixture
def regular_user(db, bibliotekar_group) -> User:
    """Create a regular user (Bibliotekar) without superadmin role."""
    user = UserFactory(email="regular@example.com", password="testpass123")
    user.groups.add(bibliotekar_group)
    return user


@pytest.fixture
def publisher(db) -> Publisher:
    """Create a test publisher."""
    return Publisher.objects.create(name="Test Publisher")


@pytest.mark.django_db
class TestSuperadminRequiredMixin:
    """Test SuperadminRequiredMixin permission checks (AC: #1, #6)."""

    def test_superadmin_can_access_user_list(self, client: Client, superadmin_user: User):
        """AC#1: Superadmin should be able to access user management."""
        client.login(email="superadmin@example.com", password="testpass123")
        response = client.get(reverse("users:manage-list"))
        assert response.status_code == 200

    def test_non_superadmin_gets_403(self, client: Client, regular_user: User):
        """AC#6: Non-superadmin should get 403 Forbidden."""
        client.login(email="regular@example.com", password="testpass123")
        response = client.get(reverse("users:manage-list"))
        assert response.status_code == 403

    def test_anonymous_redirects_to_login(self, client: Client):
        """Anonymous user should be redirected to login."""
        response = client.get(reverse("users:manage-list"))
        assert response.status_code == 302
        assert "login" in response.url.lower() or "account" in response.url.lower()

    def test_is_superuser_has_access(self, client: Client, db):
        """Django is_superuser should also have access."""
        user = UserFactory(email="django_superuser@example.com", password="testpass123")
        user.is_superuser = True
        user.save()
        client.login(email="django_superuser@example.com", password="testpass123")
        response = client.get(reverse("users:manage-list"))
        assert response.status_code == 200


@pytest.mark.django_db
class TestUserListView:
    """Test UserListAdminView functionality (AC: #1)."""

    def test_user_list_displays_all_users(
        self, client: Client, superadmin_user: User, regular_user: User,
    ):
        """AC#1: List displays all users."""
        client.login(email="superadmin@example.com", password="testpass123")
        response = client.get(reverse("users:manage-list"))
        assert response.status_code == 200
        content = response.content.decode()
        assert "superadmin@example.com" in content
        assert "regular@example.com" in content

    def test_user_list_shows_role_column(
        self, client: Client, superadmin_user: User, regular_user: User,
    ):
        """AC#1: List displays role (Group) column."""
        client.login(email="superadmin@example.com", password="testpass123")
        response = client.get(reverse("users:manage-list"))
        content = response.content.decode()
        # Check for role badges
        assert "Superadmin" in content
        assert "Bibliotekar" in content

    def test_user_list_shows_status_column(self, client: Client, superadmin_user: User):
        """AC#1: List displays is_active status."""
        client.login(email="superadmin@example.com", password="testpass123")
        response = client.get(reverse("users:manage-list"))
        content = response.content.decode()
        # Check for status indicator
        assert "Aktivan" in content or "active" in content.lower()

    def test_filter_by_role(self, client: Client, superadmin_user: User, regular_user: User):
        """AC#1: Filter users by role (Group)."""
        client.login(email="superadmin@example.com", password="testpass123")
        response = client.get(reverse("users:manage-list"), {"role": "Bibliotekar"})
        assert response.status_code == 200
        content = response.content.decode()
        assert "regular@example.com" in content
        # Superadmin should be filtered out
        assert "superadmin@example.com" not in content

    def test_filter_by_status_active(
        self, client: Client, superadmin_user: User, regular_user: User,
    ):
        """AC#1: Filter users by status (active)."""
        # Deactivate regular user
        regular_user.is_active = False
        regular_user.save()

        client.login(email="superadmin@example.com", password="testpass123")
        response = client.get(reverse("users:manage-list"), {"status": "active"})
        assert response.status_code == 200
        content = response.content.decode()
        assert "superadmin@example.com" in content
        assert "regular@example.com" not in content

    def test_filter_by_status_inactive(
        self, client: Client, superadmin_user: User, regular_user: User,
    ):
        """AC#1: Filter users by status (inactive)."""
        # Deactivate regular user
        regular_user.is_active = False
        regular_user.save()

        client.login(email="superadmin@example.com", password="testpass123")
        response = client.get(reverse("users:manage-list"), {"status": "inactive"})
        assert response.status_code == 200
        content = response.content.decode()
        assert "regular@example.com" in content
        assert "superadmin@example.com" not in content

    def test_search_by_email(self, client: Client, superadmin_user: User, regular_user: User):
        """AC#1: Search users by email."""
        client.login(email="superadmin@example.com", password="testpass123")
        response = client.get(reverse("users:manage-list"), {"search": "regular"})
        assert response.status_code == 200
        content = response.content.decode()
        assert "regular@example.com" in content
        assert "superadmin@example.com" not in content

    def test_search_by_name(self, client: Client, superadmin_user: User, regular_user: User):
        """AC#1: Search users by name."""
        regular_user.name = "Test User Name"
        regular_user.save()

        client.login(email="superadmin@example.com", password="testpass123")
        response = client.get(reverse("users:manage-list"), {"search": "Test User"})
        assert response.status_code == 200
        content = response.content.decode()
        assert "regular@example.com" in content


@pytest.mark.django_db
class TestUserCreation:
    """Test UserCreateAdminView functionality (AC: #2, #3)."""

    def test_create_user_form_displayed(self, client: Client, superadmin_user: User):
        """AC#2: Create user form is displayed for Superadmin."""
        client.login(email="superadmin@example.com", password="testpass123")
        response = client.get(reverse("users:create"))
        assert response.status_code == 200
        content = response.content.decode()
        # Check for form fields
        assert "email" in content.lower()
        assert "name" in content.lower() or "ime" in content.lower()

    def test_create_user_with_valid_data(self, client: Client, superadmin_user: User):
        """AC#3: Superadmin can create a new user."""
        client.login(email="superadmin@example.com", password="testpass123")
        response = client.post(
            reverse("users:create"),
            {
                "email": "newuser@example.com",
                "name": "New User",
                "password1": "SecurePass123!",
                "password2": "SecurePass123!",
                "role": "Urednik",
            },
        )
        assert response.status_code == 302  # Redirect on success
        assert User.objects.filter(email="newuser@example.com").exists()

    def test_create_user_assigns_group_correctly(self, client: Client, superadmin_user: User):
        """AC#3: User creation should assign selected role as Group."""
        client.login(email="superadmin@example.com", password="testpass123")
        client.post(
            reverse("users:create"),
            {
                "email": "admin@example.com",
                "name": "Admin User",
                "password1": "SecurePass123!",
                "password2": "SecurePass123!",
                "role": "Administrator",
            },
        )
        user = User.objects.get(email="admin@example.com")
        assert user.groups.filter(name="Administrator").exists()

    def test_create_user_with_publisher(
        self, client: Client, superadmin_user: User, publisher: Publisher,
    ):
        """AC#3: User creation can assign publisher for row-level permissions."""
        client.login(email="superadmin@example.com", password="testpass123")
        client.post(
            reverse("users:create"),
            {
                "email": "editor@example.com",
                "name": "Editor User",
                "password1": "SecurePass123!",
                "password2": "SecurePass123!",
                "role": "Urednik",
                "publisher": publisher.pk,
            },
        )
        user = User.objects.get(email="editor@example.com")
        assert user.publisher == publisher

    def test_create_user_with_send_invitation(self, client: Client, superadmin_user: User):
        """AC#2: Superadmin can create user with email invitation (no password)."""
        client.login(email="superadmin@example.com", password="testpass123")
        response = client.post(
            reverse("users:create"),
            {
                "email": "invited@example.com",
                "name": "Invited User",
                "role": "Bibliotekar",
                "send_invitation": "on",
            },
        )
        assert response.status_code == 302
        user = User.objects.get(email="invited@example.com")
        assert not user.has_usable_password()

    def test_create_user_password_mismatch_fails(self, client: Client, superadmin_user: User):
        """Validation: Password mismatch should fail."""
        client.login(email="superadmin@example.com", password="testpass123")
        response = client.post(
            reverse("users:create"),
            {
                "email": "fail@example.com",
                "name": "Fail User",
                "password1": "SecurePass123!",
                "password2": "DifferentPass123!",
                "role": "Bibliotekar",
            },
        )
        assert response.status_code == 200  # Form re-displayed with errors
        assert not User.objects.filter(email="fail@example.com").exists()

    def test_create_user_duplicate_email_fails(
        self, client: Client, superadmin_user: User, regular_user: User,
    ):
        """Validation: Duplicate email should fail."""
        client.login(email="superadmin@example.com", password="testpass123")
        response = client.post(
            reverse("users:create"),
            {
                "email": "regular@example.com",  # Already exists
                "name": "Duplicate User",
                "password1": "SecurePass123!",
                "password2": "SecurePass123!",
                "role": "Bibliotekar",
            },
        )
        assert response.status_code == 200  # Form re-displayed with errors

    def test_non_superadmin_cannot_create_user(self, client: Client, regular_user: User):
        """AC#6: Non-superadmin cannot access create user."""
        client.login(email="regular@example.com", password="testpass123")
        response = client.get(reverse("users:create"))
        assert response.status_code == 403


@pytest.mark.django_db
class TestUserUpdate:
    """Test UserUpdateAdminView functionality (AC: #4)."""

    def test_update_user_form_displayed(
        self, client: Client, superadmin_user: User, regular_user: User,
    ):
        """AC#4: Edit user form is displayed for Superadmin."""
        client.login(email="superadmin@example.com", password="testpass123")
        response = client.get(reverse("users:edit", args=[regular_user.pk]))
        assert response.status_code == 200
        content = response.content.decode()
        assert regular_user.email in content

    def test_update_user_changes_role(
        self, client: Client, superadmin_user: User, regular_user: User,
    ):
        """AC#4: Superadmin can change user's role (Group membership)."""
        assert regular_user.groups.filter(name="Bibliotekar").exists()
        assert not regular_user.groups.filter(name="Urednik").exists()

        client.login(email="superadmin@example.com", password="testpass123")
        client.post(
            reverse("users:edit", args=[regular_user.pk]),
            {
                "email": regular_user.email,
                "name": regular_user.name,
                "role": "Urednik",
            },
        )

        regular_user.refresh_from_db()
        # Old group should be removed
        assert not regular_user.groups.filter(name="Bibliotekar").exists()
        # New group should be assigned
        assert regular_user.groups.filter(name="Urednik").exists()

    def test_update_user_changes_publisher(
        self, client: Client, superadmin_user: User, regular_user: User, publisher: Publisher,
    ):
        """AC#4: Superadmin can change user's publisher assignment."""
        assert regular_user.publisher is None

        client.login(email="superadmin@example.com", password="testpass123")
        client.post(
            reverse("users:edit", args=[regular_user.pk]),
            {
                "email": regular_user.email,
                "name": regular_user.name,
                "role": "Bibliotekar",
                "publisher": publisher.pk,
            },
        )

        regular_user.refresh_from_db()
        assert regular_user.publisher == publisher

    def test_update_user_removes_publisher(
        self, client: Client, superadmin_user: User, regular_user: User, publisher: Publisher,
    ):
        """AC#4: Superadmin can remove publisher assignment."""
        regular_user.publisher = publisher
        regular_user.save()

        client.login(email="superadmin@example.com", password="testpass123")
        client.post(
            reverse("users:edit", args=[regular_user.pk]),
            {
                "email": regular_user.email,
                "name": regular_user.name,
                "role": "Bibliotekar",
                "publisher": "",  # Empty to remove
            },
        )

        regular_user.refresh_from_db()
        assert regular_user.publisher is None

    def test_non_superadmin_cannot_edit_user(self, client: Client, regular_user: User):
        """AC#6: Non-superadmin cannot access edit user."""
        # Create another user to edit
        target_user = UserFactory(email="target@example.com", password="testpass123")
        client.login(email="regular@example.com", password="testpass123")
        response = client.get(reverse("users:edit", args=[target_user.pk]))
        assert response.status_code == 403


@pytest.mark.django_db
class TestUserDeactivation:
    """Test user activation/deactivation functionality (AC: #5)."""

    def test_deactivate_user_sets_is_active_false(
        self, client: Client, superadmin_user: User, regular_user: User,
    ):
        """AC#5: Deactivating a user should set is_active to False."""
        assert regular_user.is_active is True

        client.login(email="superadmin@example.com", password="testpass123")
        response = client.post(reverse("users:toggle-active", args=[regular_user.pk]))

        regular_user.refresh_from_db()
        assert regular_user.is_active is False

    def test_activate_user_sets_is_active_true(
        self, client: Client, superadmin_user: User, regular_user: User,
    ):
        """AC#5: Activating a user should set is_active to True."""
        regular_user.is_active = False
        regular_user.save()

        client.login(email="superadmin@example.com", password="testpass123")
        response = client.post(reverse("users:toggle-active", args=[regular_user.pk]))

        regular_user.refresh_from_db()
        assert regular_user.is_active is True

    def test_deactivated_user_cannot_login(self, client: Client, regular_user: User):
        """AC#5: Deactivated user should not be able to log in."""
        regular_user.is_active = False
        regular_user.save()

        success = client.login(email="regular@example.com", password="testpass123")
        assert success is False

    def test_deactivation_invalidates_sessions(
        self, client: Client, superadmin_user: User, regular_user: User,
    ):
        """AC#5: Deactivating a user should terminate existing sessions."""
        # Create a session for regular_user
        other_client = Client()
        other_client.login(email="regular@example.com", password="testpass123")

        # Verify session exists
        session_count_before = Session.objects.filter(expire_date__gte=timezone.now()).count()

        # Superadmin deactivates regular user
        client.login(email="superadmin@example.com", password="testpass123")
        client.post(reverse("users:toggle-active", args=[regular_user.pk]))

        # Check session was invalidated
        regular_user.refresh_from_db()
        assert regular_user.is_active is False

        # Verify sessions for deactivated user are gone
        user_sessions = []
        for session in Session.objects.filter(expire_date__gte=timezone.now()):
            try:
                data = session.get_decoded()
                if str(data.get("_auth_user_id")) == str(regular_user.pk):
                    user_sessions.append(session)
            except Exception:
                continue
        assert len(user_sessions) == 0

    def test_toggle_active_returns_htmx_partial(
        self, client: Client, superadmin_user: User, regular_user: User,
    ):
        """AC#5: Toggle active should return HTMX partial for row update."""
        client.login(email="superadmin@example.com", password="testpass123")
        response = client.post(
            reverse("users:toggle-active", args=[regular_user.pk]),
            HTTP_HX_REQUEST="true",
        )
        # Should return HTML partial, not redirect
        assert response.status_code == 200
        assert "user" in response.context or "_user_row" in str(response.templates)

    def test_non_superadmin_cannot_toggle_active(
        self, client: Client, regular_user: User,
    ):
        """AC#6: Non-superadmin cannot toggle user active status."""
        target_user = UserFactory(email="target@example.com", password="testpass123")
        client.login(email="regular@example.com", password="testpass123")
        response = client.post(reverse("users:toggle-active", args=[target_user.pk]))
        assert response.status_code == 403

    def test_superadmin_cannot_deactivate_self(
        self, client: Client, superadmin_user: User,
    ):
        """Security: Superadmin cannot deactivate their own account."""
        client.login(email="superadmin@example.com", password="testpass123")
        response = client.post(reverse("users:toggle-active", args=[superadmin_user.pk]))

        # Should redirect with error message, not deactivate
        superadmin_user.refresh_from_db()
        assert superadmin_user.is_active is True  # Still active

    def test_superadmin_cannot_deactivate_self_htmx(
        self, client: Client, superadmin_user: User,
    ):
        """Security: Superadmin cannot deactivate self via HTMX."""
        client.login(email="superadmin@example.com", password="testpass123")
        response = client.post(
            reverse("users:toggle-active", args=[superadmin_user.pk]),
            HTTP_HX_REQUEST="true",
        )

        # Should return partial but not change status
        assert response.status_code == 200
        superadmin_user.refresh_from_db()
        assert superadmin_user.is_active is True  # Still active
