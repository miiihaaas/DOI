"""
Component URL configuration.

Crossref sa_component support: CRUD routes for ComponentGroup, Component, Contributor.
"""

from django.urls import path

from . import views

app_name = "components"

urlpatterns = [
    # ComponentGroup CRUD
    path(
        "",
        views.ComponentGroupListView.as_view(),
        name="group-list",
    ),
    path(
        "groups/create/",
        views.ComponentGroupCreateView.as_view(),
        name="group-create",
    ),
    path(
        "groups/<int:pk>/",
        views.ComponentGroupDetailView.as_view(),
        name="group-detail",
    ),
    path(
        "groups/<int:pk>/edit/",
        views.ComponentGroupUpdateView.as_view(),
        name="group-update",
    ),
    path(
        "groups/<int:pk>/delete/",
        views.ComponentGroupDeleteView.as_view(),
        name="group-delete",
    ),
    # Component CRUD (within ComponentGroup)
    path(
        "groups/<int:group_pk>/components/create/",
        views.ComponentCreateView.as_view(),
        name="component-create",
    ),
    path(
        "groups/<int:group_pk>/components/<int:pk>/",
        views.ComponentDetailView.as_view(),
        name="component-detail",
    ),
    path(
        "groups/<int:group_pk>/components/<int:pk>/edit/",
        views.ComponentUpdateView.as_view(),
        name="component-update",
    ),
    path(
        "groups/<int:group_pk>/components/<int:pk>/delete/",
        views.ComponentDeleteView.as_view(),
        name="component-delete",
    ),
    # Contributor HTMX endpoints
    path(
        "components/<int:component_pk>/contributors/add/",
        views.contributor_add,
        name="contributor-add",
    ),
    path(
        "contributors/<int:contributor_pk>/update/",
        views.contributor_update,
        name="contributor-update",
    ),
    path(
        "contributors/<int:contributor_pk>/delete/",
        views.contributor_delete,
        name="contributor-delete",
    ),
    path(
        "components/<int:component_pk>/contributors/reorder/",
        views.contributor_reorder,
        name="contributor-reorder",
    ),
    path(
        "components/<int:component_pk>/contributors/form/",
        views.contributor_form_view,
        name="contributor-form",
    ),
    path(
        "contributors/<int:contributor_pk>/edit-form/",
        views.contributor_edit_form_view,
        name="contributor-edit-form",
    ),
]
