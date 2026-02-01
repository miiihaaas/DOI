"""
Article URL configuration.

Story 3.1: Article admin routes.
Story 3.2: HTMX routes for Author CRUD, reorder, ORCID validation, affiliations.
Story 3.3: HTMX routes for PDF upload, status polling, delete.
Story 3.4: HTMX route for auto-save endpoint.
Story 3.5: HTMX routes for Submit Article for Review.
Story 3.6: HTMX routes for Editorial Review Process.
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
    # Auto-save HTMX endpoint (Story 3.4)
    path(
        "<int:pk>/autosave/",
        views.article_autosave,
        name="article-autosave",
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
    # Submit for Review HTMX endpoints (Story 3.5)
    path(
        "<int:pk>/submit-check/",
        views.article_submit_check,
        name="article-submit-check",
    ),
    path(
        "<int:pk>/submit/",
        views.article_submit_for_review,
        name="article-submit",
    ),
    # Editorial Review HTMX endpoints (Story 3.6)
    path(
        "<int:pk>/approve-check/",
        views.article_approve_check,
        name="article-approve-check",
    ),
    path(
        "<int:pk>/approve/",
        views.article_approve,
        name="article-approve",
    ),
    path(
        "<int:pk>/return-check/",
        views.article_return_check,
        name="article-return-check",
    ),
    path(
        "<int:pk>/return/",
        views.article_return_for_revision,
        name="article-return",
    ),
]
