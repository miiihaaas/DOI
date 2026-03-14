"""Tests for Sentry before_send callback and SentryTestView (Story 6.5)."""

import pytest
from django.urls import reverse

from doi_portal.core.sentry import before_send


class TestBeforeSendCallback:
    """Tests for before_send callback that scrubs sensitive data (AC#5)."""

    def test_scrubs_password_from_request_body(self):
        """before_send should filter password fields from request body."""
        event = {
            "request": {
                "data": {
                    "username": "testuser",
                    "password": "secret123",
                    "password_confirm": "secret123",
                },
            },
        }
        result = before_send(event, {})
        assert result["request"]["data"]["username"] == "testuser"
        assert result["request"]["data"]["password"] == "[Filtered]"
        assert result["request"]["data"]["password_confirm"] == "[Filtered]"

    def test_scrubs_authorization_header(self):
        """before_send should filter Authorization header."""
        event = {
            "request": {
                "headers": {
                    "Authorization": "Bearer eyJ...",
                    "Content-Type": "application/json",
                },
            },
        }
        result = before_send(event, {})
        assert result["request"]["headers"]["Authorization"] == "[Filtered]"
        assert result["request"]["headers"]["Content-Type"] == "application/json"

    def test_scrubs_session_cookies(self):
        """before_send should filter session and CSRF cookies."""
        event = {
            "request": {
                "cookies": {
                    "sessionid": "abc123",
                    "csrftoken": "token456",
                    "__Secure-sessionid": "secabc",
                    "__Secure-csrftoken": "sectok",
                    "theme": "dark",
                },
            },
        }
        result = before_send(event, {})
        assert result["request"]["cookies"]["sessionid"] == "[Filtered]"
        assert result["request"]["cookies"]["csrftoken"] == "[Filtered]"
        assert result["request"]["cookies"]["__Secure-sessionid"] == "[Filtered]"
        assert result["request"]["cookies"]["__Secure-csrftoken"] == "[Filtered]"
        assert result["request"]["cookies"]["theme"] == "dark"

    def test_does_not_modify_event_without_sensitive_data(self):
        """before_send should pass through events without sensitive data."""
        event = {
            "request": {
                "headers": {
                    "Content-Type": "text/html",
                    "Accept": "*/*",
                },
                "cookies": {
                    "theme": "dark",
                },
                "data": {
                    "title": "Test Article",
                    "abstract": "Some text",
                },
            },
        }
        result = before_send(event, {})
        assert result["request"]["headers"]["Content-Type"] == "text/html"
        assert result["request"]["cookies"]["theme"] == "dark"
        assert result["request"]["data"]["title"] == "Test Article"

    def test_handles_event_without_request(self):
        """before_send should handle events without request data (e.g., Celery task errors)."""
        event = {
            "exception": {
                "values": [{"type": "ValueError", "value": "test"}],
            },
        }
        result = before_send(event, {})
        assert result == event

    def test_scrubs_token_fields(self):
        """before_send should filter fields containing 'token'."""
        event = {
            "request": {
                "data": {
                    "api_token": "tok_123",
                    "name": "test",
                },
            },
        }
        result = before_send(event, {})
        assert result["request"]["data"]["api_token"] == "[Filtered]"
        assert result["request"]["data"]["name"] == "test"

    def test_scrubs_secret_fields(self):
        """before_send should filter fields containing 'secret'."""
        event = {
            "request": {
                "data": {
                    "client_secret": "sec_abc",
                },
            },
        }
        result = before_send(event, {})
        assert result["request"]["data"]["client_secret"] == "[Filtered]"

    def test_scrubs_dsn_fields(self):
        """before_send should filter fields containing 'dsn'."""
        event = {
            "request": {
                "data": {
                    "sentry_dsn": "https://key@sentry.io/123",
                },
            },
        }
        result = before_send(event, {})
        assert result["request"]["data"]["sentry_dsn"] == "[Filtered]"

    def test_scrubs_api_key_fields(self):
        """before_send should filter fields containing 'api_key'."""
        event = {
            "request": {
                "data": {
                    "api_key": "key_xyz",
                },
            },
        }
        result = before_send(event, {})
        assert result["request"]["data"]["api_key"] == "[Filtered]"

    def test_scrubs_credit_card_fields(self):
        """before_send should filter fields containing 'credit_card'."""
        event = {
            "request": {
                "data": {
                    "credit_card": "4111111111111111",
                },
            },
        }
        result = before_send(event, {})
        assert result["request"]["data"]["credit_card"] == "[Filtered]"

    def test_scrubs_cookie_header(self):
        """before_send should filter Cookie header."""
        event = {
            "request": {
                "headers": {
                    "Cookie": "sessionid=abc; csrftoken=xyz",
                },
            },
        }
        result = before_send(event, {})
        assert result["request"]["headers"]["Cookie"] == "[Filtered]"

    def test_scrubs_x_csrftoken_header(self):
        """before_send should filter X-CSRFToken header."""
        event = {
            "request": {
                "headers": {
                    "X-CSRFToken": "csrf_value",
                },
            },
        }
        result = before_send(event, {})
        assert result["request"]["headers"]["X-CSRFToken"] == "[Filtered]"

    def test_handles_non_dict_request_body(self):
        """before_send should handle non-dict request body (e.g., string body)."""
        event = {
            "request": {
                "data": "raw body string",
            },
        }
        result = before_send(event, {})
        assert result["request"]["data"] == "raw body string"

    def test_handles_empty_request(self):
        """before_send should handle empty request dict."""
        event = {"request": {}}
        result = before_send(event, {})
        assert result == {"request": {}}

    def test_scrubs_nested_sensitive_fields(self):
        """before_send should scrub sensitive fields in nested dicts."""
        event = {
            "request": {
                "data": {
                    "user": {
                        "password": "secret123",
                        "email": "test@test.com",
                    },
                    "settings": {
                        "api_key": "key_abc",
                        "name": "test",
                    },
                    "title": "Article",
                },
            },
        }
        result = before_send(event, {})
        assert result["request"]["data"]["user"]["password"] == "[Filtered]"
        assert result["request"]["data"]["user"]["email"] == "test@test.com"
        assert result["request"]["data"]["settings"]["api_key"] == "[Filtered]"
        assert result["request"]["data"]["settings"]["name"] == "test"
        assert result["request"]["data"]["title"] == "Article"

    def test_scrubs_headers_as_list_of_pairs(self):
        """before_send should scrub headers when represented as list of [key, value] pairs."""
        event = {
            "request": {
                "headers": [
                    ["Authorization", "Bearer eyJ..."],
                    ["Content-Type", "application/json"],
                    ["Cookie", "sessionid=abc"],
                ],
            },
        }
        result = before_send(event, {})
        assert result["request"]["headers"][0] == ["Authorization", "[Filtered]"]
        assert result["request"]["headers"][1] == ["Content-Type", "application/json"]
        assert result["request"]["headers"][2] == ["Cookie", "[Filtered]"]

    def test_scrubs_cookies_as_list_of_pairs(self):
        """before_send should scrub cookies when represented as list of [key, value] pairs."""
        event = {
            "request": {
                "cookies": [
                    ["sessionid", "abc123"],
                    ["theme", "dark"],
                    ["csrftoken", "tok456"],
                ],
            },
        }
        result = before_send(event, {})
        assert result["request"]["cookies"][0] == ["sessionid", "[Filtered]"]
        assert result["request"]["cookies"][1] == ["theme", "dark"]
        assert result["request"]["cookies"][2] == ["csrftoken", "[Filtered]"]


@pytest.mark.django_db
class TestSentryTestView:
    """Tests for SentryTestView (AC#7)."""

    @pytest.fixture(autouse=True)
    def _setup(self, client):
        """Set up test fixtures."""
        from django.contrib.auth.models import Group

        from doi_portal.users.models import User

        self.superadmin = User.objects.create_user(
            email="superadmin@test.com",
            password="testpass123",
            is_superuser=True,
        )
        self.regular_user = User.objects.create_user(
            email="regular@test.com",
            password="testpass123",
        )
        self.client = client

    def test_superadmin_can_access_sentry_test_page(self):
        """AC#7: Superadmin can access Sentry test page (200)."""
        self.client.force_login(self.superadmin)
        response = self.client.get(reverse("core:sentry-test"))
        assert response.status_code == 200

    def test_non_superadmin_gets_403(self):
        """AC#7: Non-superadmin users get 403."""
        self.client.force_login(self.regular_user)
        response = self.client.get(reverse("core:sentry-test"))
        assert response.status_code == 403

    def test_anonymous_user_redirected_to_login(self):
        """Anonymous users should be redirected to login."""
        response = self.client.get(reverse("core:sentry-test"))
        assert response.status_code == 302

    def test_page_shows_sentry_status_info(self):
        """AC#7: Page should display Sentry status information."""
        self.client.force_login(self.superadmin)
        response = self.client.get(reverse("core:sentry-test"))
        assert response.status_code == 200
        content = response.content.decode()
        # Should contain status info - either configured or not configured
        assert "Sentry" in content

    def test_page_uses_correct_template(self):
        """Sentry test page should use core/sentry_test.html template."""
        self.client.force_login(self.superadmin)
        response = self.client.get(reverse("core:sentry-test"))
        assert "core/sentry_test.html" in [t.name for t in response.templates]


@pytest.mark.django_db
class TestSentryMenuVisibility:
    """Tests for sidebar menu visibility (Task 10.2)."""

    def test_sentry_test_menu_visible_for_superadmin(self):
        """Sentry test menu item should be visible for Superadmin."""
        from doi_portal.core.menu import get_menu_for_user
        from doi_portal.users.models import User

        superadmin = User.objects.create_user(
            email="super@test.com",
            password="testpass123",
            is_superuser=True,
        )
        menu = get_menu_for_user(superadmin)
        menu_keys = [item["key"] for item in menu]
        assert "sentry_test" in menu_keys

    def test_sentry_test_menu_not_visible_for_regular_user(self):
        """Sentry test menu item should not be visible for non-Superadmin."""
        from django.contrib.auth.models import Group

        from doi_portal.core.menu import get_menu_for_user
        from doi_portal.users.models import User

        user = User.objects.create_user(
            email="urednik@test.com",
            password="testpass123",
        )
        group, _ = Group.objects.get_or_create(name="Urednik")
        user.groups.add(group)
        menu = get_menu_for_user(user)
        menu_keys = [item["key"] for item in menu]
        assert "sentry_test" not in menu_keys
