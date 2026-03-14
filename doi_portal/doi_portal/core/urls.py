"""URL configuration for the core app (Story 6.2, 6.3, 6.4)."""

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
    # Story 6.4: GDPR Data Request Handling
    path("gdpr/", views.GdprRequestListView.as_view(), name="gdpr-request-list"),
    path("gdpr/create/", views.GdprRequestCreateView.as_view(), name="gdpr-request-create"),
    path("gdpr/<int:pk>/", views.GdprRequestDetailView.as_view(), name="gdpr-request-detail"),
    path("gdpr/<int:pk>/process/", views.gdpr_request_process, name="gdpr-request-process"),
    path("gdpr/<int:pk>/cancel/", views.gdpr_request_cancel, name="gdpr-request-cancel"),
    path("gdpr/<int:pk>/report/", views.gdpr_request_download_report, name="gdpr-request-report"),
]
