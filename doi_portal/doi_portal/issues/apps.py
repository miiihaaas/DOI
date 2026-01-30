"""Issues app configuration."""

from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class IssuesConfig(AppConfig):
    """Configuration for Issues app."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "doi_portal.issues"
    verbose_name = _("Izdanja")

    def ready(self):
        """Register models with auditlog on app ready."""
        try:
            from auditlog.registry import auditlog

            from .models import Issue

            auditlog.register(Issue)
        except ImportError:
            pass
