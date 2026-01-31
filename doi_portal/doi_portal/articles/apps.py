"""Articles app configuration."""

from __future__ import annotations

from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class ArticlesConfig(AppConfig):
    """Configuration for Articles app."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "doi_portal.articles"
    verbose_name = _("Članci")

    def ready(self):
        """Register models with auditlog on app ready."""
        try:
            from auditlog.registry import auditlog

            from .models import Affiliation, Article, Author

            auditlog.register(Article)
            auditlog.register(Author)
            auditlog.register(Affiliation)
        except ImportError:
            pass
