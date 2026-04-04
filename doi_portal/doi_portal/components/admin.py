"""
Django admin configuration for Component models.

Crossref sa_component support.
"""

from django.contrib import admin

from .models import Component, ComponentContributor, ComponentGroup


class ComponentInline(admin.TabularInline):
    """Inline for Components within ComponentGroup admin."""

    model = Component
    extra = 0
    fields = ["title", "doi_suffix", "format_mime_type", "order"]
    readonly_fields = ["created_at"]


@admin.register(ComponentGroup)
class ComponentGroupAdmin(admin.ModelAdmin):
    """Admin configuration for ComponentGroup model."""

    list_display = [
        "parent_doi",
        "title",
        "publisher",
        "component_count",
        "created_at",
    ]
    list_filter = ["publisher"]
    search_fields = ["parent_doi", "title"]
    readonly_fields = [
        "created_at",
        "updated_at",
        "deleted_at",
        "deleted_by",
        "xml_generated_at",
        "xsd_validated_at",
        "crossref_deposited_at",
        "crossref_deposited_by",
    ]
    inlines = [ComponentInline]


class ComponentContributorInline(admin.TabularInline):
    """Inline for ComponentContributors within Component admin."""

    model = ComponentContributor
    extra = 0
    fields = ["given_name", "surname", "sequence", "contributor_role", "order"]


@admin.register(Component)
class ComponentAdmin(admin.ModelAdmin):
    """Admin configuration for Component model."""

    list_display = [
        "title",
        "doi_suffix",
        "component_group",
        "format_mime_type",
        "order",
    ]
    list_filter = ["component_group__publisher"]
    search_fields = ["title", "doi_suffix"]
    readonly_fields = ["created_at", "updated_at", "deleted_at", "deleted_by"]
    inlines = [ComponentContributorInline]
