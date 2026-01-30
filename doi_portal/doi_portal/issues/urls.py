"""
Issue URL configuration.

Story 2.6: Issue admin routes.
"""

from django.urls import path

from . import views

app_name = "issues"

urlpatterns = [
    path("", views.IssueListView.as_view(), name="list"),
    path("create/", views.IssueCreateView.as_view(), name="create"),
    path("<int:pk>/", views.IssueDetailView.as_view(), name="detail"),
    path("<int:pk>/edit/", views.IssueUpdateView.as_view(), name="update"),
    path("<int:pk>/delete/", views.IssueDeleteView.as_view(), name="delete"),
]
