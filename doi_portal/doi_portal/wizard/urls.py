"""
URL configuration for Conference Registration Wizard.
"""

from django.urls import path

from . import views

app_name = "wizard"

urlpatterns = [
    # Start wizard (GET=empty form, POST=create Publication + redirect)
    path("conference/", views.wizard_start, name="conference-start"),
    # Step 1: Edit conference (back navigation only)
    path("conference/<int:pub_pk>/step-1/", views.wizard_step_1, name="conference-step-1"),
    # Step 2: Proceedings
    path("conference/<int:pub_pk>/step-2/", views.wizard_step_2, name="conference-step-2"),
    # Step 3: Papers
    path("conference/<int:pub_pk>/step-3/", views.wizard_step_3, name="conference-step-3"),
    # Step 3 HTMX: Paper CRUD
    path("conference/<int:pub_pk>/papers/add/", views.wizard_paper_add, name="paper-add"),
    path("conference/<int:pub_pk>/papers/<int:article_pk>/edit/", views.wizard_paper_edit, name="paper-edit"),
    path("conference/<int:pub_pk>/papers/<int:article_pk>/delete/", views.wizard_paper_delete, name="paper-delete"),
    # Step 3 HTMX: Wizard author CRUD (wrapper endpoints)
    path("papers/<int:article_pk>/authors/", views.wizard_author_list, name="author-list"),
    path("papers/<int:article_pk>/authors/form/", views.wizard_author_form, name="author-form"),
    path("papers/<int:article_pk>/authors/add/", views.wizard_author_add, name="author-add"),
    path("authors/<int:pk>/edit-form/", views.wizard_author_edit_form, name="author-edit-form"),
    path("authors/<int:pk>/update/", views.wizard_author_update, name="author-update"),
    path("authors/<int:pk>/delete/", views.wizard_author_delete, name="author-delete"),
    # Step 4: Review & XML
    path("conference/<int:pub_pk>/step-4/", views.wizard_step_4, name="conference-step-4"),
    path("conference/<int:pub_pk>/generate-xml/", views.wizard_generate_xml, name="generate-xml"),
]
