"""
Monograph URL configuration.

Task 3.1-3.5: Monograph admin CRUD routes.
Task 4.1-4.5: HTMX routes for Contributors, Affiliations, Funding,
Relations, and Chapters at both monograph and chapter levels.
"""

from django.urls import path

from . import views

app_name = "monographs"

urlpatterns = [
    # Monograph CRUD
    path("", views.MonographListView.as_view(), name="list"),
    path("create/", views.MonographCreateView.as_view(), name="create"),
    path("<int:pk>/", views.MonographDetailView.as_view(), name="detail"),
    path("<int:pk>/edit/", views.MonographUpdateView.as_view(), name="update"),
    path("<int:pk>/publish/", views.monograph_publish, name="publish"),
    path("<int:pk>/withdraw/", views.monograph_withdraw, name="withdraw"),
    path("<int:pk>/delete/", views.MonographDeleteView.as_view(), name="delete"),
    # Monograph-level contributor HTMX endpoints
    path(
        "<int:monograph_pk>/contributors/add/",
        views.contributor_add,
        name="contributor-add",
    ),
    path(
        "<int:monograph_pk>/contributors/form/",
        views.contributor_form_view,
        name="contributor-form",
    ),
    path(
        "contributors/<int:pk>/update/",
        views.contributor_update,
        name="contributor-update",
    ),
    path(
        "contributors/<int:pk>/delete/",
        views.contributor_delete,
        name="contributor-delete",
    ),
    path(
        "contributors/<int:pk>/edit-form/",
        views.contributor_edit_form_view,
        name="contributor-edit-form",
    ),
    path(
        "<int:monograph_pk>/contributors/reorder/",
        views.contributor_reorder,
        name="contributor-reorder",
    ),
    # Monograph-level affiliation HTMX endpoints
    path(
        "contributors/<int:contributor_pk>/affiliations/add/",
        views.affiliation_add,
        name="affiliation-add",
    ),
    path(
        "contributors/<int:contributor_pk>/affiliations/form/",
        views.affiliation_form_view,
        name="affiliation-form",
    ),
    path(
        "affiliations/<int:pk>/delete/",
        views.affiliation_delete,
        name="affiliation-delete",
    ),
    path(
        "affiliations/<int:pk>/edit-form/",
        views.affiliation_edit_form_view,
        name="affiliation-edit-form",
    ),
    path(
        "affiliations/<int:pk>/update/",
        views.affiliation_update,
        name="affiliation-update",
    ),
    # Monograph-level funding HTMX endpoints
    path(
        "<int:monograph_pk>/funding/add/",
        views.monograph_funding_add,
        name="funding-add",
    ),
    path(
        "funding/<int:pk>/delete/",
        views.monograph_funding_delete,
        name="funding-delete",
    ),
    path(
        "<int:monograph_pk>/funding/reorder/",
        views.monograph_funding_reorder,
        name="funding-reorder",
    ),
    path(
        "<int:monograph_pk>/funding/form/",
        views.monograph_funding_form_view,
        name="funding-form",
    ),
    # Monograph-level relation HTMX endpoints
    path(
        "<int:monograph_pk>/relations/add/",
        views.monograph_relation_add,
        name="relation-add",
    ),
    path(
        "relations/<int:pk>/delete/",
        views.monograph_relation_delete,
        name="relation-delete",
    ),
    path(
        "<int:monograph_pk>/relations/reorder/",
        views.monograph_relation_reorder,
        name="relation-reorder",
    ),
    path(
        "<int:monograph_pk>/relations/form/",
        views.monograph_relation_form_view,
        name="relation-form",
    ),
    # Chapter HTMX endpoints
    path(
        "<int:monograph_pk>/chapters/add/",
        views.chapter_add,
        name="chapter-add",
    ),
    path(
        "<int:monograph_pk>/chapters/form/",
        views.chapter_form_view,
        name="chapter-form",
    ),
    path(
        "<int:monograph_pk>/chapters/reorder/",
        views.chapter_reorder,
        name="chapter-reorder",
    ),
    path(
        "chapters/<int:pk>/",
        views.chapter_detail,
        name="chapter-detail",
    ),
    path(
        "chapters/<int:pk>/delete/",
        views.chapter_delete,
        name="chapter-delete",
    ),
    path(
        "chapters/<int:pk>/edit-form/",
        views.chapter_edit_form_view,
        name="chapter-edit-form",
    ),
    path(
        "chapters/<int:pk>/update/",
        views.chapter_update,
        name="chapter-update",
    ),
    # Chapter-level contributor HTMX endpoints
    path(
        "chapters/<int:chapter_pk>/contributors/add/",
        views.chapter_contributor_add,
        name="chapter-contributor-add",
    ),
    path(
        "chapters/<int:chapter_pk>/contributors/form/",
        views.chapter_contributor_form_view,
        name="chapter-contributor-form",
    ),
    path(
        "chapters/<int:chapter_pk>/contributors/reorder/",
        views.chapter_contributor_reorder,
        name="chapter-contributor-reorder",
    ),
    path(
        "chapter-contributors/<int:pk>/update/",
        views.chapter_contributor_update,
        name="chapter-contributor-update",
    ),
    path(
        "chapter-contributors/<int:pk>/delete/",
        views.chapter_contributor_delete,
        name="chapter-contributor-delete",
    ),
    path(
        "chapter-contributors/<int:pk>/edit-form/",
        views.chapter_contributor_edit_form_view,
        name="chapter-contributor-edit-form",
    ),
    # Chapter-level affiliation HTMX endpoints
    path(
        "chapter-contributors/<int:contributor_pk>/affiliations/add/",
        views.chapter_affiliation_add,
        name="chapter-affiliation-add",
    ),
    path(
        "chapter-contributors/<int:contributor_pk>/affiliations/form/",
        views.chapter_affiliation_form_view,
        name="chapter-affiliation-form",
    ),
    path(
        "chapter-affiliations/<int:pk>/delete/",
        views.chapter_affiliation_delete,
        name="chapter-affiliation-delete",
    ),
    path(
        "chapter-affiliations/<int:pk>/edit-form/",
        views.chapter_affiliation_edit_form_view,
        name="chapter-affiliation-edit-form",
    ),
    path(
        "chapter-affiliations/<int:pk>/update/",
        views.chapter_affiliation_update,
        name="chapter-affiliation-update",
    ),
    # Chapter-level funding HTMX endpoints
    path(
        "chapters/<int:chapter_pk>/funding/add/",
        views.chapter_funding_add,
        name="chapter-funding-add",
    ),
    path(
        "chapters/<int:chapter_pk>/funding/form/",
        views.chapter_funding_form_view,
        name="chapter-funding-form",
    ),
    path(
        "chapters/<int:chapter_pk>/funding/reorder/",
        views.chapter_funding_reorder,
        name="chapter-funding-reorder",
    ),
    path(
        "chapter-funding/<int:pk>/delete/",
        views.chapter_funding_delete,
        name="chapter-funding-delete",
    ),
    # Chapter-level relation HTMX endpoints
    path(
        "chapters/<int:chapter_pk>/relations/add/",
        views.chapter_relation_add,
        name="chapter-relation-add",
    ),
    path(
        "chapters/<int:chapter_pk>/relations/form/",
        views.chapter_relation_form_view,
        name="chapter-relation-form",
    ),
    path(
        "chapters/<int:chapter_pk>/relations/reorder/",
        views.chapter_relation_reorder,
        name="chapter-relation-reorder",
    ),
    path(
        "chapter-relations/<int:pk>/delete/",
        views.chapter_relation_delete,
        name="chapter-relation-delete",
    ),
    # Monograph PDF HTMX endpoints
    path(
        "<int:pk>/pdf/upload/",
        views.monograph_pdf_upload,
        name="pdf-upload",
    ),
    path(
        "<int:pk>/pdf/status/",
        views.monograph_pdf_status,
        name="pdf-status",
    ),
    path(
        "<int:pk>/pdf/delete/",
        views.monograph_pdf_delete,
        name="pdf-delete",
    ),
    # Chapter PDF HTMX endpoints
    path(
        "chapters/<int:pk>/pdf/upload/",
        views.chapter_pdf_upload,
        name="chapter-pdf-upload",
    ),
    path(
        "chapters/<int:pk>/pdf/status/",
        views.chapter_pdf_status,
        name="chapter-pdf-status",
    ),
    path(
        "chapters/<int:pk>/pdf/delete/",
        views.chapter_pdf_delete,
        name="chapter-pdf-delete",
    ),
]
