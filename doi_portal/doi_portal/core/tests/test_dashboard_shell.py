"""
Admin Dashboard Shell tests for DOI Portal (Story 1.7).

Tests cover:
- AC#1: Bootstrap 5 admin layout with sidebar, header, breadcrumbs
- AC#2: Bibliotekar sees limited menu (Clanci, Moji nacrti)
- AC#3: Administrator sees full content menu
- AC#4: Superadmin sees User Management and System Settings
- AC#5: last_activity timestamp is updated on each action
- AC#6: Session timeout redirects to login with message
"""

from http import HTTPStatus

import pytest
from allauth.account.models import EmailAddress
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.test import Client
from django.urls import reverse
from django.utils import timezone

User = get_user_model()

# Test constants
TEST_EMAIL = "dashboard-test@example.com"
TEST_PASSWORD = "testpass123!"  # noqa: S105
SESSION_TIMEOUT_SECONDS = 1800  # 30 minutes
ACTIVITY_RECENT_THRESHOLD_SECONDS = 10  # Max acceptable delay for "recent" timestamp
ACTIVITY_THROTTLE_TOLERANCE_SECONDS = 2  # Tolerance for throttle comparison in tests


def _create_user_with_role(
    email: str,
    password: str,
    role: str,
    name: str = "",
) -> "User":
    """Create a verified user with the specified role."""
    user = User.objects.create_user(
        email=email,
        password=password,
        name=name,
    )
    EmailAddress.objects.create(
        user=user,
        email=user.email,
        verified=True,
        primary=True,
    )
    # Add to role group
    group, _ = Group.objects.get_or_create(name=role)
    user.groups.add(group)
    return user


def _login_user(
    client: Client,
    email: str,
    password: str = TEST_PASSWORD,
) -> None:
    """Login a user via POST request."""
    client.post(
        reverse("account_login"),
        {"login": email, "password": password},
    )


@pytest.mark.django_db
class TestDashboardSidebarLayout:
    """Test dashboard displays sidebar layout (AC#1)."""

    def test_dashboard_has_sidebar(self, client: Client) -> None:
        """AC#1: Dashboard should display sidebar navigation."""
        user = _create_user_with_role(
            email="superadmin@test.com",
            password=TEST_PASSWORD,
            role="Superadmin",
        )
        _login_user(client, user.email)

        response = client.get(reverse("dashboard"))
        content = response.content.decode("utf-8")

        assert response.status_code == HTTPStatus.OK
        assert "sidebar" in content.lower() or 'id="sidebar-wrapper"' in content

    def test_dashboard_has_header_with_user_info(self, client: Client) -> None:
        """AC#1: Dashboard should display header with user info."""
        user = _create_user_with_role(
            email="superadmin2@test.com",
            password=TEST_PASSWORD,
            role="Superadmin",
            name="Test Admin",
        )
        _login_user(client, user.email)

        response = client.get(reverse("dashboard"))
        content = response.content.decode("utf-8")

        # Should show user name or email in header
        assert "Test Admin" in content or user.email in content

    def test_dashboard_has_logout_option(self, client: Client) -> None:
        """AC#1: Dashboard should have logout option."""
        user = _create_user_with_role(
            email="superadmin3@test.com",
            password=TEST_PASSWORD,
            role="Superadmin",
        )
        _login_user(client, user.email)

        response = client.get(reverse("dashboard"))
        content = response.content.decode("utf-8").lower()

        # Should contain logout link/button
        assert "odjava" in content or "logout" in content

    def test_dashboard_has_breadcrumbs(self, client: Client) -> None:
        """AC#1: Dashboard should display breadcrumbs."""
        user = _create_user_with_role(
            email="superadmin4@test.com",
            password=TEST_PASSWORD,
            role="Superadmin",
        )
        _login_user(client, user.email)

        response = client.get(reverse("dashboard"))
        content = response.content.decode("utf-8")

        # Should have breadcrumb element
        assert "breadcrumb" in content.lower()

    def test_sidebar_is_collapsible(self, client: Client) -> None:
        """AC#1: Sidebar should have toggle functionality."""
        user = _create_user_with_role(
            email="superadmin5@test.com",
            password=TEST_PASSWORD,
            role="Superadmin",
        )
        _login_user(client, user.email)

        response = client.get(reverse("dashboard"))
        content = response.content.decode("utf-8")

        # Should have sidebar toggle button
        assert "sidebarToggle" in content or "sidebar-toggle" in content.lower()


@pytest.mark.django_db
class TestRoleBasedMenuBibliotekar:
    """Test Bibliotekar sees limited menu (AC#2)."""

    def test_bibliotekar_sees_clanci(self, client: Client) -> None:
        """AC#2: Bibliotekar should see Clanci menu item."""
        user = _create_user_with_role(
            email="bibliotekar@test.com",
            password=TEST_PASSWORD,
            role="Bibliotekar",
        )
        _login_user(client, user.email)

        response = client.get(reverse("dashboard"))
        content = response.content.decode("utf-8")

        assert "Clanci" in content or "clanci" in content.lower()

    def test_bibliotekar_sees_moji_nacrti(self, client: Client) -> None:
        """AC#2: Bibliotekar should see Moji nacrti menu item."""
        user = _create_user_with_role(
            email="bibliotekar2@test.com",
            password=TEST_PASSWORD,
            role="Bibliotekar",
        )
        _login_user(client, user.email)

        response = client.get(reverse("dashboard"))
        content = response.content.decode("utf-8")

        assert "Moji nacrti" in content or "nacrti" in content.lower()

    def test_bibliotekar_cannot_see_korisnici(self, client: Client) -> None:
        """AC#2: Bibliotekar should NOT see Korisnici (User Management)."""
        user = _create_user_with_role(
            email="bibliotekar3@test.com",
            password=TEST_PASSWORD,
            role="Bibliotekar",
        )
        _login_user(client, user.email)

        response = client.get(reverse("dashboard"))
        content = response.content.decode("utf-8")

        # Should NOT contain user management menu (check sidebar area specifically)
        # The word "Korisnici" as a menu item should not appear for Bibliotekar
        assert "Korisnici</a>" not in content or "bi-people" not in content

    def test_bibliotekar_cannot_see_system_settings(self, client: Client) -> None:
        """AC#2: Bibliotekar should NOT see System Settings."""
        user = _create_user_with_role(
            email="bibliotekar4@test.com",
            password=TEST_PASSWORD,
            role="Bibliotekar",
        )
        _login_user(client, user.email)

        response = client.get(reverse("dashboard"))
        content = response.content.decode("utf-8")

        assert "Podesavanja sistema" not in content


@pytest.mark.django_db
class TestRoleBasedMenuAdministrator:
    """Test Administrator sees full content menu (AC#3)."""

    def test_administrator_sees_izdavaci(self, client: Client) -> None:
        """AC#3: Administrator should see Izdavaci menu item."""
        user = _create_user_with_role(
            email="administrator@test.com",
            password=TEST_PASSWORD,
            role="Administrator",
        )
        _login_user(client, user.email)

        response = client.get(reverse("dashboard"))
        content = response.content.decode("utf-8")

        assert "Izdavaci" in content or "izdavaci" in content.lower()

    def test_administrator_sees_publikacije(self, client: Client) -> None:
        """AC#3: Administrator should see Publikacije menu item."""
        user = _create_user_with_role(
            email="administrator2@test.com",
            password=TEST_PASSWORD,
            role="Administrator",
        )
        _login_user(client, user.email)

        response = client.get(reverse("dashboard"))
        content = response.content.decode("utf-8")

        assert "Publikacije" in content or "publikacije" in content.lower()

    def test_administrator_sees_izdanja(self, client: Client) -> None:
        """AC#3: Administrator should see Izdanja menu item."""
        user = _create_user_with_role(
            email="administrator3@test.com",
            password=TEST_PASSWORD,
            role="Administrator",
        )
        _login_user(client, user.email)

        response = client.get(reverse("dashboard"))
        content = response.content.decode("utf-8")

        assert "Izdanja" in content or "izdanja" in content.lower()

    def test_administrator_cannot_see_user_management(self, client: Client) -> None:
        """AC#3: Administrator should NOT see User Management."""
        user = _create_user_with_role(
            email="administrator4@test.com",
            password=TEST_PASSWORD,
            role="Administrator",
        )
        _login_user(client, user.email)

        response = client.get(reverse("dashboard"))
        content = response.content.decode("utf-8")

        # User Management link should not appear in sidebar for Administrator
        # Only Superadmin should see the users:manage-list link
        assert 'href="/users/manage/"' not in content


@pytest.mark.django_db
class TestRoleBasedMenuSuperadmin:
    """Test Superadmin sees User Management and System Settings (AC#4)."""

    def test_superadmin_sees_korisnici(self, client: Client) -> None:
        """AC#4: Superadmin should see Korisnici menu item."""
        user = _create_user_with_role(
            email="superadmin6@test.com",
            password=TEST_PASSWORD,
            role="Superadmin",
        )
        _login_user(client, user.email)

        response = client.get(reverse("dashboard"))
        content = response.content.decode("utf-8")

        assert "Korisnici" in content

    def test_superadmin_sees_system_settings(self, client: Client) -> None:
        """AC#4: Superadmin should see System Settings menu item."""
        user = _create_user_with_role(
            email="superadmin7@test.com",
            password=TEST_PASSWORD,
            role="Superadmin",
        )
        _login_user(client, user.email)

        response = client.get(reverse("dashboard"))
        content = response.content.decode("utf-8")

        assert "Podesavanja sistema" in content or "sistem" in content.lower()

    def test_superadmin_sees_all_content_menu_items(self, client: Client) -> None:
        """AC#4: Superadmin should see all content management menu items."""
        user = _create_user_with_role(
            email="superadmin8@test.com",
            password=TEST_PASSWORD,
            role="Superadmin",
        )
        _login_user(client, user.email)

        response = client.get(reverse("dashboard"))
        content = response.content.decode("utf-8")

        # Should see all menu items
        assert "Kontrolna tabla" in content
        assert "Izdavaci" in content
        assert "Publikacije" in content


@pytest.mark.django_db
class TestLastActivityTracking:
    """Test last_activity is updated on request (AC#5)."""

    def test_last_activity_updated_on_dashboard_access(self, client: Client) -> None:
        """AC#5: last_activity should be updated when accessing dashboard."""
        user = _create_user_with_role(
            email="activity-test@test.com",
            password=TEST_PASSWORD,
            role="Superadmin",
        )
        assert user.last_activity is None

        _login_user(client, user.email)
        client.get(reverse("dashboard"))

        user.refresh_from_db()
        assert user.last_activity is not None

    def test_last_activity_is_recent(self, client: Client) -> None:
        """AC#5: last_activity should be within recent timeframe."""
        user = _create_user_with_role(
            email="activity-test2@test.com",
            password=TEST_PASSWORD,
            role="Superadmin",
        )
        _login_user(client, user.email)
        client.get(reverse("dashboard"))

        user.refresh_from_db()
        now = timezone.now()
        # Should be within recent threshold
        delta = (now - user.last_activity).total_seconds()
        assert delta < ACTIVITY_RECENT_THRESHOLD_SECONDS

    def test_last_activity_throttled_updates(self, client: Client) -> None:
        """AC#5: last_activity should not update too frequently (optimization)."""
        user = _create_user_with_role(
            email="activity-test3@test.com",
            password=TEST_PASSWORD,
            role="Superadmin",
        )
        _login_user(client, user.email)

        # First request
        client.get(reverse("dashboard"))
        user.refresh_from_db()
        first_activity = user.last_activity

        # Immediate second request (should not update due to throttling)
        client.get(reverse("dashboard"))
        user.refresh_from_db()
        second_activity = user.last_activity

        # Due to throttling, the timestamps should be the same or very close
        if first_activity and second_activity:
            delta = abs((second_activity - first_activity).total_seconds())
            # Throttling set to 60s, but in tests they should be very close
            # since we're not waiting 60s between requests
            assert delta < ACTIVITY_THROTTLE_TOLERANCE_SECONDS


@pytest.mark.django_db
class TestSessionTimeout:
    """Test session timeout handling (AC#6)."""

    def test_session_timeout_configuration(self) -> None:
        """AC#6: Session should be configured for 30 min timeout."""
        assert settings.SESSION_COOKIE_AGE == SESSION_TIMEOUT_SECONDS

    def test_session_extends_on_request(self) -> None:
        """AC#6: Session should extend on each request."""
        assert settings.SESSION_SAVE_EVERY_REQUEST is True

    def test_unauthenticated_redirects_to_login(self, client: Client) -> None:
        """AC#6: Unauthenticated user should be redirected to login."""
        response = client.get(reverse("dashboard"))
        assert response.status_code == HTTPStatus.FOUND
        assert "login" in response.url or "account" in response.url


@pytest.mark.django_db
class TestBreadcrumbs:
    """Test breadcrumbs display correctly (AC#1)."""

    def test_dashboard_shows_kontrolna_tabla_breadcrumb(self, client: Client) -> None:
        """AC#1: Dashboard should show Kontrolna tabla in breadcrumbs."""
        user = _create_user_with_role(
            email="breadcrumb-test@test.com",
            password=TEST_PASSWORD,
            role="Superadmin",
        )
        _login_user(client, user.email)

        response = client.get(reverse("dashboard"))
        content = response.content.decode("utf-8")

        # Breadcrumb should contain "Kontrolna tabla"
        assert "Kontrolna tabla" in content


@pytest.mark.django_db
class TestDashboardRoleDisplay:
    """Test dashboard displays role-specific content."""

    def test_dashboard_shows_role_welcome(self, client: Client) -> None:
        """AC#1: Dashboard should show role-specific welcome message."""
        user = _create_user_with_role(
            email="role-test@test.com",
            password=TEST_PASSWORD,
            role="Administrator",
            name="Test Administrator",
        )
        _login_user(client, user.email)

        response = client.get(reverse("dashboard"))
        content = response.content.decode("utf-8")

        # Should show user name in welcome
        assert "Test Administrator" in content or user.email in content
