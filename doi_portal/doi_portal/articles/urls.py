"""
Article URL configuration.

Story 3.1: Article admin routes.
"""

from django.urls import path

from . import views

app_name = "articles"

urlpatterns = [
    path("", views.ArticleListView.as_view(), name="list"),
    path("create/", views.ArticleCreateView.as_view(), name="create"),
    path("<int:pk>/", views.ArticleDetailView.as_view(), name="detail"),
    path("<int:pk>/edit/", views.ArticleUpdateView.as_view(), name="update"),
    path("<int:pk>/delete/", views.ArticleDeleteView.as_view(), name="delete"),
]
