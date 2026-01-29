"""
Public portal URL configuration for publications.

Story 2.5: Public Publication List with Filters.

These are PUBLIC routes - no authentication required.
"""

from django.urls import path

from doi_portal.portal import views

app_name = "portal-publications"

urlpatterns = [
    # Publication list - /publications/
    path(
        "",
        views.PublicationPublicListView.as_view(),
        name="publication-list",
    ),
    # Publication detail - /publications/<slug>/
    path(
        "<slug:slug>/",
        views.PublicationPublicDetailView.as_view(),
        name="publication-detail",
    ),
]
