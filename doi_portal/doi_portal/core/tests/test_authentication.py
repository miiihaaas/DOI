"""
Authentication tests for DOI Portal (Story 1.3).

Tests cover:
- AC#1: Login page renders with Bootstrap form
- AC#2: Successful login redirects to dashboard, session created, last_activity updated
- AC#3: Logout terminates session, redirects to login
- AC#4: Invalid credentials show error message
"""

from http import HTTPStatus

import pytest
from allauth.account.models import EmailAddress
from django.conf import settings
from django.contrib.auth import get_user_model
from django.test import Client
from django.urls import reverse

User = get_user_model()

# Test constants
TEST_EMAIL = "test@example.com"
TEST_PASSWORD = "testpass123!"  # noqa: S105
WRONG_EMAIL = "wrong@example.com"
WRONG_PASSWORD = "wrongpass"  # noqa: S105
SESSION_TIMEOUT_SECONDS = 1800  # 30 minutes


def _create_verified_user(
    email: str = TEST_EMAIL,
    password: str = TEST_PASSWORD,
    name: str = "",
) -> "User":
    """Create a user with verified email for testing."""
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
    return user


def _login_user(
    client: Client,
    email: str = TEST_EMAIL,
    password: str = TEST_PASSWORD,
) -> None:
    """Login a user via POST request."""
    client.post(
        reverse("account_login"),
        {"login": email, "password": password},
    )


@pytest.mark.django_db
class TestLoginConfiguration:
    """Test django-allauth and session configuration (Task 1, 2)."""

    def test_login_redirect_url_is_dashboard(self) -> None:
        """AC#2: LOGIN_REDIRECT_URL should point to dashboard."""
        assert settings.LOGIN_REDIRECT_URL == "dashboard"

    def test_logout_redirect_url_is_login(self) -> None:
        """AC#3: LOGOUT_REDIRECT_URL should point to login page."""
        assert settings.LOGOUT_REDIRECT_URL == "account_login"

    def test_session_cookie_age_is_30_minutes(self) -> None:
        """AC#2: Session should timeout after 30 minutes of inactivity."""
        assert settings.SESSION_COOKIE_AGE == SESSION_TIMEOUT_SECONDS

    def test_session_save_every_request(self) -> None:
        """AC#2: Session should extend on each request."""
        assert settings.SESSION_SAVE_EVERY_REQUEST is True

    def test_account_login_methods_is_email(self) -> None:
        """AC#1: Login should use email, not username."""
        assert "email" in settings.ACCOUNT_LOGIN_METHODS

    def test_account_logout_on_get_is_false(self) -> None:
        """AC#3: Logout should require POST for security."""
        assert settings.ACCOUNT_LOGOUT_ON_GET is False


@pytest.mark.django_db
class TestLoginPage:
    """Test login page rendering (Task 3)."""

    def test_login_page_renders(self, client: Client) -> None:
        """AC#1: Login page should render with status 200."""
        response = client.get(reverse("account_login"))
        assert response.status_code == HTTPStatus.OK

    def test_login_page_has_form(self, client: Client) -> None:
        """AC#1: Login page should contain a form."""
        response = client.get(reverse("account_login"))
        assert "form" in response.context or b"<form" in response.content

    def test_login_page_has_email_field(self, client: Client) -> None:
        """AC#1: Login page should have email input field."""
        response = client.get(reverse("account_login"))
        content_lower = response.content.lower()
        assert b"email" in content_lower or b"login" in content_lower

    def test_login_page_has_password_field(self, client: Client) -> None:
        """AC#1: Login page should have password input field."""
        response = client.get(reverse("account_login"))
        assert b"password" in response.content.lower()

    def test_login_page_has_forgot_password_link(self, client: Client) -> None:
        """AC#1: Login page should have forgot password link."""
        response = client.get(reverse("account_login"))
        content = response.content.decode("utf-8").lower()
        # Check for password reset link (various language variants)
        assert "password" in content
        has_reset_link = (
            "reset" in content or "forgot" in content or "zaborav" in content
        )
        assert has_reset_link


@pytest.mark.django_db
class TestSuccessfulLogin:
    """Test successful login flow (Task 1, 2)."""

    def test_successful_login_redirects_to_dashboard(self, client: Client) -> None:
        """AC#2: Valid credentials should redirect to dashboard."""
        _create_verified_user()

        response = client.post(
            reverse("account_login"),
            {"login": TEST_EMAIL, "password": TEST_PASSWORD},
        )
        assert response.status_code == HTTPStatus.FOUND
        assert response.url == reverse("dashboard")

    def test_login_creates_session(self, client: Client) -> None:
        """AC#2: Login should create a session."""
        _create_verified_user()

        _login_user(client)
        assert "_auth_user_id" in client.session


@pytest.mark.django_db
class TestLastActivityMiddleware:
    """Test LastActivityMiddleware (Task 2)."""

    def test_authenticated_request_updates_last_activity(self, client: Client) -> None:
        """AC#2: Authenticated request should update last_activity."""
        user = _create_verified_user()

        # Login
        _login_user(client)

        # Make another request to trigger middleware
        client.get(reverse("dashboard"))

        # Check last_activity was updated
        user.refresh_from_db()
        assert user.last_activity is not None


@pytest.mark.django_db
class TestInvalidLogin:
    """Test invalid login handling (Task 3)."""

    def test_invalid_login_returns_200(self, client: Client) -> None:
        """AC#4: Invalid credentials should stay on login page."""
        response = client.post(
            reverse("account_login"),
            {"login": WRONG_EMAIL, "password": WRONG_PASSWORD},
        )
        assert response.status_code == HTTPStatus.OK

    def test_invalid_login_shows_error(self, client: Client) -> None:
        """AC#4: Invalid credentials should show error message."""
        response = client.post(
            reverse("account_login"),
            {"login": WRONG_EMAIL, "password": WRONG_PASSWORD},
        )
        content = response.content.decode("utf-8").lower()
        # Check for error indication (form errors or alert)
        error_indicators = ["error", "alert", "invalid", "incorrect", "neisprav"]
        has_error = any(indicator in content for indicator in error_indicators)
        assert has_error


@pytest.mark.django_db
class TestLogout:
    """Test logout functionality (Task 4)."""

    def test_logout_terminates_session(self, client: Client) -> None:
        """AC#3: Logout should terminate the session."""
        _create_verified_user()

        # Login first
        _login_user(client)
        assert "_auth_user_id" in client.session

        # Logout
        client.post(reverse("account_logout"))
        assert "_auth_user_id" not in client.session

    def test_logout_redirects_to_login(self, client: Client) -> None:
        """AC#3: After logout, user should be redirected to login page."""
        _create_verified_user()

        _login_user(client)

        response = client.post(reverse("account_logout"))
        assert response.status_code == HTTPStatus.FOUND
        assert "login" in response.url or "account_login" in response.url


@pytest.mark.django_db
class TestDashboard:
    """Test dashboard access control (Task 6)."""

    def test_dashboard_requires_login(self, client: Client) -> None:
        """AC#2: Unauthenticated user cannot access dashboard."""
        response = client.get(reverse("dashboard"))
        assert response.status_code == HTTPStatus.FOUND
        assert "login" in response.url

    def test_authenticated_user_can_access_dashboard(self, client: Client) -> None:
        """AC#2: Authenticated user can access dashboard."""
        _create_verified_user()

        _login_user(client)

        response = client.get(reverse("dashboard"))
        assert response.status_code == HTTPStatus.OK

    def test_dashboard_shows_welcome_message(self, client: Client) -> None:
        """AC#2: Dashboard should display welcome message with user name."""
        _create_verified_user(name="Test User")

        _login_user(client)

        response = client.get(reverse("dashboard"))
        content = response.content.decode("utf-8")
        # Should contain welcome message with user's name or email
        assert "Test User" in content or TEST_EMAIL in content
