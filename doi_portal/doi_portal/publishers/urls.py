"""
Publisher URL configuration.

Story 2.1 - Task 3.6: URL patterns for Publisher CRUD.
"""

from django.urls import path

from . import views

app_name = "publishers"

urlpatterns = [
    # Publisher CRUD (CBV)
    path("", views.PublisherListView.as_view(), name="list"),
    path("create/", views.PublisherCreateView.as_view(), name="create"),
    path("<int:pk>/", views.PublisherDetailView.as_view(), name="detail"),
    path("<int:pk>/edit/", views.PublisherUpdateView.as_view(), name="update"),
    path("<int:pk>/delete/", views.PublisherDeleteView.as_view(), name="delete"),
    # Crossref password reveal/hide (HTMX)
    path(
        "<int:pk>/reveal-password/",
        views.reveal_crossref_password,
        name="reveal-crossref-password",
    ),
    path(
        "<int:pk>/hide-password/",
        views.hide_crossref_password,
        name="hide-crossref-password",
    ),
    # Kontakt osobe (HTMX)
    path("<int:publisher_pk>/contacts/", views.contact_list, name="contact-list"),
    path(
        "<int:publisher_pk>/contacts/add-form/",
        views.contact_add_form,
        name="contact-add-form",
    ),
    path(
        "<int:publisher_pk>/contacts/add/", views.contact_add, name="contact-add"
    ),
    path(
        "contacts/<int:pk>/edit-form/",
        views.contact_edit_form,
        name="contact-edit-form",
    ),
    path(
        "contacts/<int:pk>/update/", views.contact_update, name="contact-update"
    ),
    path(
        "contacts/<int:pk>/delete/", views.contact_delete, name="contact-delete"
    ),
    # Napomene (HTMX)
    path("<int:publisher_pk>/notes/", views.note_list, name="note-list"),
    path("<int:publisher_pk>/notes/add/", views.note_add, name="note-add"),
    path("notes/<int:pk>/edit-form/", views.note_edit_form, name="note-edit-form"),
    path("notes/<int:pk>/update/", views.note_update, name="note-update"),
    path("notes/<int:pk>/delete/", views.note_delete, name="note-delete"),
]
