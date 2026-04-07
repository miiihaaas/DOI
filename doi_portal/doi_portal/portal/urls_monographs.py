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
    # Monograph PDF & citation (must precede <int:pk>/ detail route)
    path(
        "<int:pk>/pdf/",
        views.monograph_pdf_download,
        name="monograph-pdf-download",
    ),
    path(
        "<int:pk>/cite/",
        views.monograph_citation,
        name="monograph-citation",
    ),
    path(
        "<int:pk>/cite/download/",
        views.monograph_citation_download,
        name="monograph-citation-download",
    ),
    # Chapter PDF & citation (must precede chapter detail route)
    path(
        "<int:monograph_pk>/chapters/<int:pk>/pdf/",
        views.chapter_pdf_download,
        name="chapter-pdf-download",
    ),
    path(
        "<int:monograph_pk>/chapters/<int:pk>/cite/",
        views.chapter_citation,
        name="chapter-citation",
    ),
    path(
        "<int:monograph_pk>/chapters/<int:pk>/cite/download/",
        views.chapter_citation_download,
        name="chapter-citation-download",
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
