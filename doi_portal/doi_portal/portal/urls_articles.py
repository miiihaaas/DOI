"""
Public portal URL configuration for articles.

Story 4.4: Article Landing Page.

These are PUBLIC routes - no authentication required.
"""

from django.urls import path

from doi_portal.portal import views

app_name = "portal-articles"

urlpatterns = [
    # Article detail - /articles/<pk>/
    path(
        "<int:pk>/",
        views.ArticleLandingView.as_view(),
        name="article-detail",
    ),
]
