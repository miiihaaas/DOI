"""URL configuration for the core app (Story 6.2: Audit Log Viewer, Story 6.3: Deleted Items)."""

from django.urls import path

from . import views

app_name = "core"

urlpatterns = [
    # Story 6.2: Audit Log Viewer
    path("", views.AuditLogListView.as_view(), name="audit-log-list"),
    path("<int:pk>/", views.AuditLogDetailView.as_view(), name="audit-log-detail"),
    # Story 6.3: Deleted Items Management
    path("deleted/", views.DeletedItemsView.as_view(), name="deleted-items"),
    path(
        "deleted/<str:model_type>/<int:pk>/restore/",
        views.deleted_item_restore,
        name="deleted-item-restore",
    ),
    path(
        "deleted/<str:model_type>/<int:pk>/permanent-delete/",
        views.deleted_item_permanent_delete,
        name="deleted-item-permanent-delete",
    ),
]
