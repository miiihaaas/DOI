"""
Public portal URL configuration.

Story 2.2: Public Publisher Page

These are PUBLIC routes - no authentication required.
"""

from django.urls import path

from doi_portal.portal import views

app_name = "portal"

urlpatterns = [
    # Publisher list - /publishers/
    path(
        "",
        views.PublisherPublicListView.as_view(),
        name="publisher-list",
    ),
    # Publisher detail - /publishers/<slug>/
    path(
        "<slug:slug>/",
        views.PublisherPublicDetailView.as_view(),
        name="publisher-detail",
    ),
]
