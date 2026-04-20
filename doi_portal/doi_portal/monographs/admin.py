from django.contrib import admin

from .models import Monograph, MonographChapter


@admin.register(Monograph)
class MonographAdmin(admin.ModelAdmin):
    list_display = ("id", "title", "status", "doi_suffix", "created_at")
    list_filter = ("status",)
    list_editable = ("status",)
    search_fields = ("title", "doi_suffix")
    fields = ("title", "status")
    readonly_fields = ("title",)


@admin.register(MonographChapter)
class MonographChapterAdmin(admin.ModelAdmin):
    list_display = ("id", "title", "monograph", "status", "doi_suffix", "created_at")
    list_filter = ("status", "monograph")
    list_editable = ("status",)
    search_fields = ("title", "doi_suffix")
    fields = ("title", "status")
    readonly_fields = ("title",)
