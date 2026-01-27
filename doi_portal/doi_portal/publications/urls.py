"""
Publication URL configuration.

Story 2.3 - Task 5: Publication admin routes + HTMX endpoints.
"""

from django.urls import path

from . import views

app_name = "publications"

urlpatterns = [
    # Admin CRUD routes (requires authentication)
    path("", views.PublicationListView.as_view(), name="list"),
    path("create/", views.PublicationCreateView.as_view(), name="create"),
    path("<slug:slug>/", views.PublicationDetailView.as_view(), name="detail"),
    path("<slug:slug>/edit/", views.PublicationUpdateView.as_view(), name="update"),
    path("<slug:slug>/delete/", views.PublicationDeleteView.as_view(), name="delete"),
    # HTMX endpoints
    path("htmx/type-fields/", views.htmx_type_fields, name="htmx-type-fields"),
]
