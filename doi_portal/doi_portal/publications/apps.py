"""Publications app configuration."""

from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class PublicationsConfig(AppConfig):
    """Configuration for Publications app."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "doi_portal.publications"
    verbose_name = _("Publikacije")

    def ready(self):
        """Register models with auditlog on app ready."""
        try:
            from auditlog.registry import auditlog

            from . import models  # noqa: F401

            auditlog.register(models.Publication)
        except ImportError:
            pass
