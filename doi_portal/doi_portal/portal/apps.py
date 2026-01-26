"""
Portal app configuration.

Story 2.2: Public Publisher Page
"""

from django.apps import AppConfig


class PortalConfig(AppConfig):
    """Configuration for the Portal app."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "doi_portal.portal"
    verbose_name = "Portal"
