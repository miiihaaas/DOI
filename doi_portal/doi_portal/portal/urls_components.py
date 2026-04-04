"""
Public portal URL configuration for components.

These are PUBLIC routes - no authentication required.
"""

from django.urls import path

from doi_portal.portal.views import ComponentLandingView

app_name = "portal-components"

urlpatterns = [
    path(
        "<int:pk>/",
        ComponentLandingView.as_view(),
        name="component-detail",
    ),
]
