"""
Publisher URL configuration.

Story 2.1 - Task 3.6: URL patterns for Publisher CRUD.
"""

from django.urls import path

from . import views

app_name = "publishers"

urlpatterns = [
    path("", views.PublisherListView.as_view(), name="list"),
    path("create/", views.PublisherCreateView.as_view(), name="create"),
    path("<int:pk>/", views.PublisherDetailView.as_view(), name="detail"),
    path("<int:pk>/edit/", views.PublisherUpdateView.as_view(), name="update"),
    path("<int:pk>/delete/", views.PublisherDeleteView.as_view(), name="delete"),
]
