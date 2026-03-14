"""
Core app configuration.

Story 6.4: Register GdprRequest model with auditlog for audit trail.
"""

from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class CoreConfig(AppConfig):
    """App configuration for core utilities."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "doi_portal.core"
    verbose_name = _("Core")

    def ready(self):
        """Register GdprRequest model with auditlog for audit trail."""
        try:
            from auditlog.registry import auditlog

            from .models import GdprRequest

            auditlog.register(GdprRequest)
        except ImportError:
            pass
