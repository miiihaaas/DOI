"""
Crossref app configuration.

Story 5.1: Crossref Service Infrastructure.
"""

from django.apps import AppConfig


class CrossrefConfig(AppConfig):
    """Configuration for the crossref app."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "doi_portal.crossref"
    verbose_name = "Crossref"
