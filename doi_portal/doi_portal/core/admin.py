"""
Core admin configuration for DOI Portal.

Registers global settings in Django Admin.
"""

from django.contrib import admin

from .models import SiteSettings


@admin.register(SiteSettings)
class SiteSettingsAdmin(admin.ModelAdmin):
    """Admin za globalna podesavanja portala."""

    fieldsets = (
        (
            "Crossref Depositor",
            {
                "fields": ("depositor_name", "depositor_email"),
                "description": (
                    "Podaci organizacije koja salje XML na Crossref. "
                    "Ovi podaci se koriste u XML <head> sekciji za sve izdavace."
                ),
            },
        ),
    )

    def has_add_permission(self, request):
        """Prevent adding more than one instance."""
        return not SiteSettings.objects.exists()

    def has_delete_permission(self, request, obj=None):
        """Prevent deletion."""
        return False
