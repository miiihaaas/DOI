"""URL configuration for the core app (Story 6.2: Audit Log Viewer)."""

from django.urls import path

from . import views

app_name = "core"

urlpatterns = [
    path("", views.AuditLogListView.as_view(), name="audit-log-list"),
    path("<int:pk>/", views.AuditLogDetailView.as_view(), name="audit-log-detail"),
]
