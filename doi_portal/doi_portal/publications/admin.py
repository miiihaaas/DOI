"""
Django admin configuration for Publication model.

Story 2.3: Publication Model with Type-Specific Fields.
"""

from django.contrib import admin

from .models import Publication


@admin.register(Publication)
class PublicationAdmin(admin.ModelAdmin):
    """Admin configuration for Publication model."""

    list_display = [
        "title",
        "publication_type",
        "publisher",
        "access_type",
        "is_deleted",
        "created_at",
    ]
    list_filter = ["publication_type", "access_type", "is_deleted", "publisher"]
    search_fields = ["title", "description", "publisher__name"]
    prepopulated_fields = {"slug": ("title",)}
    readonly_fields = ["created_at", "updated_at", "deleted_at", "deleted_by"]
    ordering = ["title"]

    fieldsets = (
        (
            "Osnovne informacije",
            {
                "fields": (
                    "title",
                    "slug",
                    "publisher",
                    "publication_type",
                    "description",
                    "cover_image",
                )
            },
        ),
        (
            "Dodatne informacije",
            {
                "fields": ("language", "subject_area", "access_type"),
            },
        ),
        (
            "Polja za časopis",
            {
                "fields": ("issn_print", "issn_online", "abbreviation", "frequency"),
                "classes": ("collapse",),
            },
        ),
        (
            "Polja za konferenciju",
            {
                "fields": (
                    "conference_name",
                    "conference_acronym",
                    "conference_location",
                    "conference_date",
                    "conference_date_end",
                    "conference_number",
                    "series_issn",
                ),
                "classes": ("collapse",),
            },
        ),
        (
            "Polja za knjigu",
            {
                "fields": ("isbn_print", "isbn_online", "edition", "series_title"),
                "classes": ("collapse",),
            },
        ),
        (
            "Vremenske oznake",
            {
                "fields": ("created_at", "updated_at"),
                "classes": ("collapse",),
            },
        ),
        (
            "Brisanje",
            {
                "fields": ("is_deleted", "deleted_at", "deleted_by"),
                "classes": ("collapse",),
            },
        ),
    )
