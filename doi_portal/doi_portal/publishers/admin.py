"""
Publisher admin configuration.

Story 2.1: Admin interface for Publisher model with soft delete support.
"""

from django.contrib import admin

from .models import Publisher, PublisherContact, PublisherNote


class PublisherContactInline(admin.TabularInline):
    """Inline admin for publisher contact persons."""

    model = PublisherContact
    extra = 0
    fields = ["first_name", "last_name", "email", "phone", "role", "order"]


class PublisherNoteInline(admin.TabularInline):
    """Inline admin for publisher notes."""

    model = PublisherNote
    extra = 0
    fields = ["text", "author", "created_at"]
    readonly_fields = ["author", "created_at"]


@admin.register(Publisher)
class PublisherAdmin(admin.ModelAdmin):
    """
    Admin configuration for Publisher model.

    Includes:
    - List view with key fields
    - Soft delete management
    - Search and filtering
    """

    list_display = [
        "name",
        "doi_prefix",
        "publication_count",
        "is_deleted",
        "created_at",
    ]
    list_filter = ["is_deleted", "created_at"]
    search_fields = ["name", "doi_prefix", "contact_email"]
    readonly_fields = ["slug", "created_at", "updated_at", "deleted_at", "deleted_by"]
    inlines = [PublisherContactInline, PublisherNoteInline]

    fieldsets = [
        (None, {
            "fields": ["name", "slug", "description", "logo"]
        }),
        ("Kontakt", {
            "fields": ["contact_email", "contact_phone", "website"]
        }),
        ("DOI", {
            "fields": ["doi_prefix"]
        }),
        ("Crossref", {
            "fields": ["crossref_username"],
            "classes": ["collapse"],
            "description": "Crossref lozinka se ne prikazuje u admin panelu iz bezbednosnih razloga. Koristite dashboard za upravljanje lozinkom.",
        }),
        ("Status", {
            "fields": ["is_deleted", "deleted_at", "deleted_by"],
            "classes": ["collapse"]
        }),
        ("Datumi", {
            "fields": ["created_at", "updated_at"],
            "classes": ["collapse"]
        }),
    ]

    def get_queryset(self, request):
        """Show all publishers including soft-deleted in admin."""
        return Publisher.all_objects.all()

    def publication_count(self, obj):
        """Display publication count."""
        return obj.publication_count
    publication_count.short_description = "Publikacije"

    actions = ["restore_selected"]

    @admin.action(description="Vrati obrisane izdavače")
    def restore_selected(self, request, queryset):
        """Restore soft-deleted publishers."""
        count = 0
        for publisher in queryset.filter(is_deleted=True):
            publisher.restore()
            count += 1
        self.message_user(request, f"Vraćeno {count} izdavača.")
