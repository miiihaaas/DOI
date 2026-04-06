"""Monographs app configuration."""

from __future__ import annotations

from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class MonographsConfig(AppConfig):
    """Configuration for Monographs app."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "doi_portal.monographs"
    verbose_name = _("Monografije")

    def ready(self):
        """Register models with auditlog on app ready."""
        try:
            from auditlog.registry import auditlog

            from .models import (
                ChapterContributor,
                ChapterFunding,
                ChapterRelation,
                Monograph,
                MonographChapter,
                MonographContributor,
                MonographFunding,
                MonographRelation,
            )

            auditlog.register(Monograph)
            auditlog.register(MonographChapter)
            auditlog.register(MonographContributor)
            auditlog.register(ChapterContributor)
            auditlog.register(ChapterFunding)
            auditlog.register(ChapterRelation)
            auditlog.register(MonographFunding)
            auditlog.register(MonographRelation)
        except ImportError:
            pass
