"""
Public portal URL configuration for monographs.

These are PUBLIC routes - no authentication required.
"""

from django.urls import path

from doi_portal.portal import views

app_name = "portal-monographs"

urlpatterns = [
    # Monograph list - /monographs/
    path(
        "",
        views.MonographPublicListView.as_view(),
        name="monograph-list",
    ),
    # Monograph detail - /monographs/<pk>/
    path(
        "<int:pk>/",
        views.MonographPublicDetailView.as_view(),
        name="monograph-detail",
    ),
    # Chapter detail - /monographs/<monograph_pk>/chapters/<pk>/
    path(
        "<int:monograph_pk>/chapters/<int:pk>/",
        views.ChapterLandingView.as_view(),
        name="chapter-detail",
    ),
]
