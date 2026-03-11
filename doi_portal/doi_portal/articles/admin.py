"""
Article admin configuration for DOI Portal.

Story 3.1: Basic admin registration for Article model visibility and debugging.
Custom Bootstrap 5 views handle the main CRUD operations.
"""

from django.contrib import admin

from .models import Article, ArticleFunding


@admin.register(Article)
class ArticleAdmin(admin.ModelAdmin):
    """Article admin for visibility, debugging, and soft-delete inspection."""

    list_display = ("title", "issue", "status", "is_deleted", "created_by", "created_at")
    list_filter = ("status", "is_deleted", "language")
    search_fields = ("title", "doi_suffix")
    readonly_fields = ("created_at", "updated_at", "deleted_at", "deleted_by")
    raw_id_fields = ("issue", "created_by")

    def get_queryset(self, request):
        """Show all articles including soft-deleted ones."""
        return self.model.all_objects.select_related(
            "issue", "issue__publication", "created_by"
        )


@admin.register(ArticleFunding)
class ArticleFundingAdmin(admin.ModelAdmin):
    list_display = ("funder_name", "award_number", "article", "order")
    list_filter = ("funder_name",)
    search_fields = ("funder_name", "award_number")
    raw_id_fields = ("article",)
