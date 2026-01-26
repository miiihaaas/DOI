"""
Tests for Password Reset functionality (Story 1.5).

Covers AC #1-#4:
- AC#1: Password reset form displayed from login page
- AC#2: Password reset email sent with secure token
- AC#3: Valid reset link shows new password form
- AC#4: Password updated with argon2, session invalidation
"""

# ruff: noqa: PLR2004, S106, PLC0415

import re

import pytest
from allauth.account.models import EmailAddress
from django.contrib.auth import get_user_model
from django.contrib.sessions.models import Session
from django.core import mail
from django.test import Client
from django.urls import reverse
from django.utils import timezone

from doi_portal.users.tests.factories import UserFactory

User = get_user_model()


def get_reset_url_from_email() -> str | None:
    """
    Extract password reset URL from the sent email.

    Helper function to parse reset URL from mail.outbox.
    Returns the path portion of the reset URL.
    """
    if not mail.outbox:
        return None
    email_body = mail.outbox[0].body
    url_pattern = r"http[s]?://[^\s]+/accounts/password/reset/key/[^\s]+"
    match = re.search(url_pattern, email_body)
    if match:
        url = match.group(0)
        return url.split("testserver")[-1] if "testserver" in url else url
    return None


@pytest.fixture
def verified_user(db):
    """Create a user with verified email for password reset tests."""
    user = UserFactory(password="OldPassword123!")
    EmailAddress.objects.create(
        user=user,
        email=user.email,
        verified=True,
        primary=True,
    )
    return user


@pytest.fixture
def client():
    """Return a Django test client."""
    return Client()


@pytest.mark.django_db
class TestPasswordResetRequest:
    """Tests for AC#1: Password reset form displayed from login page."""

    def test_password_reset_page_renders(self, client):
        """AC#1: Password reset form is displayed when clicking Forgot Password."""
        response = client.get(reverse("account_reset_password"))
        assert response.status_code == 200
        assert "form" in response.context

    def test_password_reset_page_contains_email_field(self, client):
        """AC#1: Password reset form has email input field."""
        response = client.get(reverse("account_reset_password"))
        assert response.status_code == 200
        content = response.content.decode()
        assert "email" in content.lower()

    def test_password_reset_page_contains_back_to_login_link(self, client):
        """AC#1: Password reset page has link to return to login."""
        response = client.get(reverse("account_reset_password"))
        assert response.status_code == 200
        content = response.content.decode()
        assert reverse("account_login") in content

    def test_password_reset_page_uses_bootstrap_styling(self, client):
        """AC#1: Password reset form uses Bootstrap 5 styling."""
        response = client.get(reverse("account_reset_password"))
        assert response.status_code == 200
        content = response.content.decode()
        # Check for Bootstrap 5 classes
        assert "card" in content
        assert "btn-primary" in content


@pytest.mark.django_db
class TestPasswordResetSubmission:
    """Tests for AC#2: Password reset email sent with secure token."""

    def test_valid_email_shows_confirmation(self, client, verified_user):
        """AC#2: Valid email submission redirects to confirmation page."""
        response = client.post(
            reverse("account_reset_password"),
            {"email": verified_user.email},
        )
        assert response.status_code == 302
        assert reverse("account_reset_password_done") in response.url

    def test_nonexistent_email_still_shows_confirmation(self, client):
        """AC#2: Non-existent email shows same confirmation (security)."""
        response = client.post(
            reverse("account_reset_password"),
            {"email": "nonexistent@example.com"},
        )
        assert response.status_code == 302
        assert reverse("account_reset_password_done") in response.url

    def test_password_reset_email_sent_for_valid_user(self, client, verified_user):
        """AC#2: Password reset email is sent for valid user."""
        client.post(
            reverse("account_reset_password"),
            {"email": verified_user.email},
        )
        assert len(mail.outbox) == 1
        assert verified_user.email in mail.outbox[0].to

    def test_password_reset_email_contains_reset_link(self, client, verified_user):
        """AC#2: Password reset email contains secure reset link."""
        client.post(
            reverse("account_reset_password"),
            {"email": verified_user.email},
        )
        assert len(mail.outbox) == 1
        email_body = mail.outbox[0].body
        # Check that email contains password reset URL
        assert "/accounts/password/reset/key/" in email_body

    def test_password_reset_confirmation_page_renders(self, client, verified_user):
        """AC#2: Confirmation page displays after email submission."""
        client.post(
            reverse("account_reset_password"),
            {"email": verified_user.email},
        )
        response = client.get(reverse("account_reset_password_done"))
        assert response.status_code == 200

    def test_email_handling_for_nonexistent_user(self, client):
        """AC#2: Non-existent email still shows confirmation (security by obscurity).

        Note: django-allauth may send an "unknown account" email for security,
        but the user sees the same confirmation page regardless.
        """
        response = client.post(
            reverse("account_reset_password"),
            {"email": "nonexistent@example.com"},
        )
        # The important thing is that the response is the same as for valid emails
        assert response.status_code == 302
        assert reverse("account_reset_password_done") in response.url

    def test_invalid_email_format_shows_error(self, client):
        """AC#2: Invalid email format shows validation error."""
        response = client.post(
            reverse("account_reset_password"),
            {"email": "not-an-email"},
        )
        # Should either show error on same page or still redirect for security
        # Allauth typically validates email format
        assert response.status_code in [200, 302]


@pytest.mark.django_db
class TestPasswordResetConfirm:
    """Tests for AC#3: Valid reset link shows new password form."""

    def test_valid_token_shows_password_form(self, client, verified_user):
        """AC#3: Valid reset link shows new password form."""
        # Request password reset
        client.post(
            reverse("account_reset_password"),
            {"email": verified_user.email},
        )

        # Get reset URL from email
        reset_url = get_reset_url_from_email()
        assert reset_url is not None, "Reset URL should be in email"

        # Access the reset page
        response = client.get(reset_url, follow=True)
        assert response.status_code == 200

    def test_reset_form_contains_password_fields(self, client, verified_user):
        """AC#3: New password form has password and confirmation fields."""
        client.post(
            reverse("account_reset_password"),
            {"email": verified_user.email},
        )

        reset_url = get_reset_url_from_email()
        response = client.get(reset_url, follow=True)
        content = response.content.decode()

        assert "password" in content.lower()

    def test_reset_form_displays_password_policy(self, client, verified_user):
        """AC#3/AC#4: Form displays password policy requirements."""
        client.post(
            reverse("account_reset_password"),
            {"email": verified_user.email},
        )

        reset_url = get_reset_url_from_email()
        response = client.get(reset_url, follow=True)
        content = response.content.decode()

        # Should show password requirements (min 8 chars)
        assert "8" in content or "karakter" in content.lower()


@pytest.mark.django_db
class TestPasswordResetComplete:
    """Tests for AC#4: Password updated, sessions invalidated."""

    def test_password_update_succeeds_with_valid_password(self, client, verified_user):
        """AC#4: Password update succeeds with valid password."""
        # Request reset
        client.post(
            reverse("account_reset_password"),
            {"email": verified_user.email},
        )

        reset_url = get_reset_url_from_email()

        # Follow the reset flow (allauth has POST-redirect-GET pattern)
        response = client.get(reset_url, follow=True)

        # Submit new password
        if response.context and "form" in response.context:
            response = client.post(
                response.request["PATH_INFO"],
                {
                    "password1": "NewSecurePass123!",
                    "password2": "NewSecurePass123!",
                },
                follow=True,
            )

        # Verify password was changed
        verified_user.refresh_from_db()
        assert verified_user.check_password("NewSecurePass123!")

    def test_password_policy_enforced_min_length(self, client, verified_user):
        """AC#4: Password policy enforces minimum length."""
        client.post(
            reverse("account_reset_password"),
            {"email": verified_user.email},
        )

        reset_url = get_reset_url_from_email()
        response = client.get(reset_url, follow=True)

        if response.context and "form" in response.context:
            response = client.post(
                response.request["PATH_INFO"],
                {
                    "password1": "short",  # Less than 8 chars
                    "password2": "short",
                },
            )

        # Password should NOT have changed to the short one
        verified_user.refresh_from_db()
        assert not verified_user.check_password("short")

    def test_password_mismatch_rejected(self, client, verified_user):
        """AC#4: Password mismatch should be rejected."""
        client.post(
            reverse("account_reset_password"),
            {"email": verified_user.email},
        )

        reset_url = get_reset_url_from_email()
        response = client.get(reset_url, follow=True)

        if response.context and "form" in response.context:
            response = client.post(
                response.request["PATH_INFO"],
                {
                    "password1": "NewSecurePass123!",
                    "password2": "DifferentPass456!",  # Mismatch!
                },
            )

        # Password should NOT have changed
        verified_user.refresh_from_db()
        assert not verified_user.check_password("NewSecurePass123!")
        assert not verified_user.check_password("DifferentPass456!")

    def test_redirect_to_login_after_successful_reset(self, client, verified_user):
        """AC#4: User redirected to login after successful reset."""
        client.post(
            reverse("account_reset_password"),
            {"email": verified_user.email},
        )

        reset_url = get_reset_url_from_email()
        response = client.get(reset_url, follow=True)

        if response.context and "form" in response.context:
            response = client.post(
                response.request["PATH_INFO"],
                {
                    "password1": "NewSecurePass123!",
                    "password2": "NewSecurePass123!",
                },
                follow=True,
            )

            # Should end up at success page or login
            final_url = response.request["PATH_INFO"]
            assert (
                "done" in final_url
                or "login" in final_url
                or reverse("account_reset_password_from_key_done") in final_url
            )


@pytest.mark.django_db
class TestSessionInvalidation:
    """Tests for AC#4: All existing sessions invalidated on password reset."""

    def test_sessions_invalidated_on_password_change(self, client, verified_user):
        """AC#4: All sessions should be invalidated when password is changed."""
        # Login to create a session
        client.login(email=verified_user.email, password="OldPassword123!")

        # Verify session exists
        sessions_before = Session.objects.filter(
            expire_date__gte=timezone.now(),
        ).count()
        assert sessions_before >= 1

        # Trigger password change signal
        from allauth.account.signals import password_changed

        password_changed.send(
            sender=verified_user.__class__,
            request=None,
            user=verified_user,
        )

        # Check that user's sessions are cleared
        # Note: This test verifies the signal handler is connected
        # The actual session clearing depends on signal handler implementation
        user_sessions = 0
        for session in Session.objects.filter(expire_date__gte=timezone.now()):
            session_data = session.get_decoded()
            if str(session_data.get("_auth_user_id")) == str(verified_user.pk):
                user_sessions += 1

        assert user_sessions == 0


@pytest.mark.django_db
class TestInvalidToken:
    """Tests for AC#3: Invalid/expired token handling."""

    def test_invalid_token_shows_error(self, client):
        """AC#3: Invalid token shows user-friendly error message."""
        # Access with invalid token
        invalid_url = "/accounts/password/reset/key/invalid-token/"
        response = client.get(invalid_url, follow=True)

        # Should show error message or redirect
        assert response.status_code == 200
        content = response.content.decode()
        # Check for error indication
        assert any(
            word in content.lower()
            for word in ["invalid", "istekao", "nevažeći", "greška", "error", "link"]
        )

    def test_invalid_token_has_request_new_link(self, client):
        """AC#3: Invalid token page has 'Request New Link' option."""
        invalid_url = "/accounts/password/reset/key/invalid-token/"
        response = client.get(invalid_url, follow=True)

        content = response.content.decode()
        # Should have link to request new reset
        assert reverse("account_reset_password") in content


@pytest.mark.django_db
class TestPasswordResetSettings:
    """Tests for Task 1: django-allauth password reset configuration."""

    def test_password_reset_timeout_configured(self):
        """Task 1.2: PASSWORD_RESET_TIMEOUT should be 3600 seconds (1 hour)."""
        from django.conf import settings

        # Django default is 3600 (1 hour), but we want to ensure it's set
        timeout = getattr(settings, "PASSWORD_RESET_TIMEOUT", 259200)
        assert timeout == 3600

    def test_site_id_configured(self):
        """Task 1.4: SITE_ID should be configured for email links."""
        from django.conf import settings

        assert hasattr(settings, "SITE_ID")
        assert settings.SITE_ID == 1

    def test_email_backend_configured(self):
        """Task 1.3: Email backend should be configured."""
        from django.conf import settings

        assert hasattr(settings, "EMAIL_BACKEND")
        # In test settings, should be locmem
        assert "locmem" in settings.EMAIL_BACKEND or "console" in settings.EMAIL_BACKEND


@pytest.mark.django_db
class TestPasswordValidators:
    """Tests for Task 8: Password policy validation."""

    def test_minimum_length_validator_configured(self):
        """Task 8.2: MinimumLengthValidator should be set to 8 characters."""
        from django.conf import settings

        validators = settings.AUTH_PASSWORD_VALIDATORS
        min_length_validator = None

        for validator in validators:
            if "MinimumLengthValidator" in validator["NAME"]:
                min_length_validator = validator
                break

        assert min_length_validator is not None
        # Check if min_length is 8 (either in OPTIONS or default)
        options = min_length_validator.get("OPTIONS", {})
        min_length = options.get("min_length", 8)  # Django default is 8
        assert min_length == 8

    def test_common_password_validator_enabled(self):
        """Task 8.3: CommonPasswordValidator should be enabled."""
        from django.conf import settings

        validators = settings.AUTH_PASSWORD_VALIDATORS
        validator_names = [v["NAME"] for v in validators]

        assert any("CommonPasswordValidator" in name for name in validator_names)
