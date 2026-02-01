"""
Article URL configuration.

Story 3.1: Article admin routes.
Story 3.2: HTMX routes for Author CRUD, reorder, ORCID validation, affiliations.
Story 3.3: HTMX routes for PDF upload, status polling, delete.
"""

from django.urls import path

from . import views

app_name = "articles"

urlpatterns = [
    # Article CRUD (Story 3.1)
    path("", views.ArticleListView.as_view(), name="list"),
    path("create/", views.ArticleCreateView.as_view(), name="create"),
    path("<int:pk>/", views.ArticleDetailView.as_view(), name="detail"),
    path("<int:pk>/edit/", views.ArticleUpdateView.as_view(), name="update"),
    path("<int:pk>/delete/", views.ArticleDeleteView.as_view(), name="delete"),
    # Author HTMX endpoints (Story 3.2)
    path(
        "<int:article_pk>/authors/add/",
        views.author_add,
        name="author-add",
    ),
    path(
        "<int:article_pk>/authors/form/",
        views.author_form_view,
        name="author-form",
    ),
    path(
        "authors/<int:pk>/update/",
        views.author_update,
        name="author-update",
    ),
    path(
        "authors/<int:pk>/delete/",
        views.author_delete,
        name="author-delete",
    ),
    path(
        "authors/<int:pk>/edit-form/",
        views.author_edit_form_view,
        name="author-edit-form",
    ),
    path(
        "<int:article_pk>/authors/reorder/",
        views.author_reorder,
        name="author-reorder",
    ),
    # ORCID validation (Story 3.2)
    path(
        "validate-orcid/",
        views.validate_orcid_view,
        name="validate-orcid",
    ),
    # Affiliation HTMX endpoints (Story 3.2)
    path(
        "authors/<int:author_pk>/affiliations/add/",
        views.affiliation_add,
        name="affiliation-add",
    ),
    path(
        "authors/<int:author_pk>/affiliations/form/",
        views.affiliation_form_view,
        name="affiliation-form",
    ),
    path(
        "affiliations/<int:pk>/delete/",
        views.affiliation_delete,
        name="affiliation-delete",
    ),
    # PDF HTMX endpoints (Story 3.3)
    path(
        "<int:article_pk>/pdf/upload/",
        views.pdf_upload,
        name="pdf-upload",
    ),
    path(
        "<int:article_pk>/pdf/status/",
        views.pdf_status,
        name="pdf-status",
    ),
    path(
        "<int:article_pk>/pdf/delete/",
        views.pdf_delete,
        name="pdf-delete",
    ),
]
