"""
Sentry before_send callback for scrubbing sensitive data (Story 6.5, AC#5).

This module provides a before_send callback that filters sensitive information
from Sentry events before they are transmitted.
"""

SENSITIVE_FIELDS = frozenset({
    "password",
    "token",
    "secret",
    "dsn",
    "api_key",
    "credit_card",
    "authorization",
})

SENSITIVE_COOKIES = frozenset({
    "sessionid",
    "csrftoken",
    "__Secure-sessionid",
    "__Secure-csrftoken",
})

SENSITIVE_HEADERS = frozenset({"Authorization", "Cookie", "X-CSRFToken"})

# Precomputed lowercase set for O(1) header lookups - avoids rebuilding on every call
_SENSITIVE_HEADERS_LOWER = frozenset(h.lower() for h in SENSITIVE_HEADERS)


def _scrub_dict_recursive(data):
    """Scrub sensitive fields from a dict, including nested dicts.

    Args:
        data: Dict to scrub in-place.
    """
    for key in list(data.keys()):
        if any(s in key.lower() for s in SENSITIVE_FIELDS):
            data[key] = "[Filtered]"
        elif isinstance(data[key], dict):
            _scrub_dict_recursive(data[key])


def before_send(event, hint):
    """Scrub sensitive data from Sentry events before sending.

    Filters:
    - Authorization, Cookie, X-CSRFToken headers
    - Session and CSRF cookies
    - Request body fields containing password, token, secret, dsn, api_key, credit_card
    - Nested dicts within request body are scrubbed recursively

    Args:
        event: Sentry event dict.
        hint: Sentry hint dict (unused).

    Returns:
        The scrubbed event dict.
    """
    request_data = event.get("request", {})

    # Scrub headers - handle both dict and list-of-pairs formats
    headers = request_data.get("headers", {})
    if headers:
        if isinstance(headers, dict):
            for key in list(headers.keys()):
                if key.lower() in _SENSITIVE_HEADERS_LOWER:
                    headers[key] = "[Filtered]"
        elif isinstance(headers, list):
            for i, pair in enumerate(headers):
                if isinstance(pair, (list, tuple)) and len(pair) == 2:
                    if pair[0].lower() in _SENSITIVE_HEADERS_LOWER:
                        headers[i] = [pair[0], "[Filtered]"]

    # Scrub cookies
    cookies = request_data.get("cookies", {})
    if cookies:
        if isinstance(cookies, dict):
            for key in list(cookies.keys()):
                if key in SENSITIVE_COOKIES:
                    cookies[key] = "[Filtered]"
        elif isinstance(cookies, list):
            for i, pair in enumerate(cookies):
                if isinstance(pair, (list, tuple)) and len(pair) == 2:
                    if pair[0] in SENSITIVE_COOKIES:
                        cookies[i] = [pair[0], "[Filtered]"]

    # Scrub request body (form data) - recursive for nested dicts
    data = request_data.get("data", {})
    if isinstance(data, dict):
        _scrub_dict_recursive(data)

    return event
