"""Components app configuration."""

from __future__ import annotations

from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class ComponentsConfig(AppConfig):
    """Configuration for Components app."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "doi_portal.components"
    verbose_name = _("Komponente")

    def ready(self):
        """Register models with auditlog on app ready."""
        try:
            from auditlog.registry import auditlog

            from .models import Component, ComponentContributor, ComponentGroup

            auditlog.register(ComponentGroup)
            auditlog.register(Component)
            auditlog.register(ComponentContributor)
        except ImportError:
            pass
