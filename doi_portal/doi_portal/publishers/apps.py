"""
Publishers app configuration.

Story 2.1: Register Publisher model with auditlog for audit trail.
"""

from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class PublishersConfig(AppConfig):
    """App configuration for publishers."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "doi_portal.publishers"
    verbose_name = _("Publishers")

    def ready(self):
        """Register models with auditlog for audit trail."""
        try:
            from auditlog.registry import auditlog

            from .models import Publisher, PublisherContact, PublisherNote

            auditlog.register(Publisher, exclude_fields=["crossref_password"])
            auditlog.register(PublisherContact)
            auditlog.register(PublisherNote)
        except ImportError:
            pass
