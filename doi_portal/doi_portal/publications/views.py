"""
Publication views.

Story 2.3 - Task 3: Publication admin CRUD views with HTMX support.
Story 2.4 - Tasks 1-3: Sorting, issue_count, row-level permissions.
"""

from django.contrib import messages
from django.db.models import Count, Value
from django.db.models.fields import IntegerField
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse_lazy
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_GET
from django.views.generic import (
    CreateView,
    DeleteView,
    DetailView,
    ListView,
    UpdateView,
)

from doi_portal.publishers.mixins import (
    AdministratorRequiredMixin,
    PublisherScopedEditMixin,
    PublisherScopedMixin,
)

from .forms import PublicationForm
from .models import Publication, PublicationType


# Whitelist of allowed sort fields (Story 2.4 - Task 1.2)
ALLOWED_SORT_FIELDS = {
    "title": "title",
    "type": "publication_type",
    "publisher": "publisher__name",
    "created": "created_at",
}

# Cache whether Issue model relation exists (checked once at module load)
# Will become True when Story 2.6 creates the Issue model with related_name="issues"
_HAS_ISSUES_RELATION = any(
    rel.get_accessor_name() == "issues"
    for rel in Publication._meta.related_objects
)


class PublicationListView(PublisherScopedMixin, ListView):
    """
    List all publications with filtering, sorting, and role-based scoping.

    AC: #1 - Displays list with sortable columns, type icons, issue count.
    AC: #4 - Urednik sees only own publisher's publications.
    AC: #6 - Bibliotekar sees only own publisher's publications (read-only).
    """

    model = Publication
    template_name = "publications/publication_list.html"
    context_object_name = "publications"
    paginate_by = 20

    def get_queryset(self):
        """Filter publications by type, publisher, search; apply sorting and scoping."""
        queryset = super().get_queryset().select_related("publisher")

        # Scope by publisher for Urednik/Bibliotekar (Story 2.4 - Task 3)
        queryset = self.get_scoped_queryset(queryset)

        # Annotate issue_count (Story 2.4 - Task 2.1)
        # Issue model doesn't exist yet (Story 2.6) - use Value(0) as placeholder
        # When Issue model is created with related_name="issues", replace with Count("issues")
        if _HAS_ISSUES_RELATION:
            queryset = queryset.annotate(issue_count_annotation=Count("issues"))
        else:
            queryset = queryset.annotate(
                issue_count_annotation=Value(0, output_field=IntegerField())
            )

        # Filter by publication type
        pub_type = self.request.GET.get("type")
        if pub_type and pub_type in [choice[0] for choice in PublicationType.choices]:
            queryset = queryset.filter(publication_type=pub_type)

        # Filter by publisher
        publisher_id = self.request.GET.get("publisher")
        if publisher_id:
            queryset = queryset.filter(publisher_id=publisher_id)

        # Search by title
        search = self.request.GET.get("search")
        if search:
            queryset = queryset.filter(title__icontains=search)

        # Sorting (Story 2.4 - Task 1)
        sort_field = self.request.GET.get("sort", "title")
        order = self.request.GET.get("order", "asc")
        db_field = ALLOWED_SORT_FIELDS.get(sort_field, "title")
        if order == "desc":
            db_field = f"-{db_field}"
        queryset = queryset.order_by(db_field)

        return queryset

    def get_context_data(self, **kwargs):
        """Add breadcrumbs, filter options, sort state to context."""
        context = super().get_context_data(**kwargs)
        context["breadcrumbs"] = [
            {"label": "Kontrolna tabla", "url": reverse_lazy("dashboard")},
            {"label": "Publikacije", "url": None},
        ]
        context["publication_types"] = PublicationType.choices
        context["current_type"] = self.request.GET.get("type", "")
        context["current_publisher"] = self.request.GET.get("publisher", "")
        context["search_query"] = self.request.GET.get("search", "")

        # Sort context (Story 2.4 - Task 1.4)
        context["current_sort"] = self.request.GET.get("sort", "title")
        context["current_order"] = self.request.GET.get("order", "asc")

        # Role-based action visibility (uses cached role flags from mixin)
        flags = self._get_user_role_flags()
        context["can_create"] = flags["is_admin"]
        context["can_edit"] = flags["is_admin"] or flags["is_urednik"]
        context["can_delete"] = flags["is_admin"]

        return context


class PublicationCreateView(AdministratorRequiredMixin, CreateView):
    """
    Create new publication with dynamic HTMX form.

    AC: #5, #6 - Displays form with type-specific fields, creates publication.
    Only Administrator/Superadmin can create publications (Story 2.4 - Task 3.4).
    """

    model = Publication
    form_class = PublicationForm
    template_name = "publications/publication_form.html"
    success_url = reverse_lazy("publications:list")

    def get_context_data(self, **kwargs):
        """Add breadcrumbs and form metadata to context."""
        context = super().get_context_data(**kwargs)
        context["breadcrumbs"] = [
            {"label": "Kontrolna tabla", "url": reverse_lazy("dashboard")},
            {"label": "Publikacije", "url": reverse_lazy("publications:list")},
            {"label": "Nova publikacija", "url": None},
        ]
        context["form_title"] = "Nova publikacija"
        context["submit_text"] = "Kreiraj publikaciju"
        context["publication_types"] = PublicationType.choices
        return context

    def form_valid(self, form):
        """Show success message on valid submission."""
        response = super().form_valid(form)
        messages.success(
            self.request,
            f"Publikacija '{self.object.title}' uspešno kreirana.",
        )
        return response


class PublicationUpdateView(PublisherScopedEditMixin, UpdateView):
    """
    Update an existing publication.

    Story 2.4 - Task 3.5: Urednik can edit own publisher's, Admin can edit all.
    Bibliotekar cannot edit (PublisherScopedEditMixin blocks).
    """

    model = Publication
    form_class = PublicationForm
    template_name = "publications/publication_form.html"
    success_url = reverse_lazy("publications:list")
    slug_url_kwarg = "slug"

    def get_queryset(self):
        """Scope queryset to user's publisher for non-admin roles."""
        queryset = super().get_queryset().select_related("publisher")
        return self.get_scoped_queryset(queryset)

    def get_context_data(self, **kwargs):
        """Add breadcrumbs and form metadata to context."""
        context = super().get_context_data(**kwargs)
        context["breadcrumbs"] = [
            {"label": "Kontrolna tabla", "url": reverse_lazy("dashboard")},
            {"label": "Publikacije", "url": reverse_lazy("publications:list")},
            {"label": self.object.title, "url": None},
        ]
        context["form_title"] = f"Izmeni publikaciju: {self.object.title}"
        context["submit_text"] = "Sačuvaj izmene"
        context["publication_types"] = PublicationType.choices
        return context

    def form_valid(self, form):
        """Show success message on valid submission."""
        response = super().form_valid(form)
        messages.success(
            self.request,
            f"Publikacija '{self.object.title}' uspešno ažurirana.",
        )
        return response


class PublicationDetailView(PublisherScopedMixin, DetailView):
    """
    View publication details.

    Story 2.4 - Task 3.3: Scoped by publisher for Urednik/Bibliotekar.
    AC: #2 - Displays all fields including conference_date_end, conference_number.
    """

    model = Publication
    template_name = "publications/publication_detail.html"
    context_object_name = "publication"
    slug_url_kwarg = "slug"

    def get_queryset(self):
        """Scope queryset to user's publisher for non-admin roles."""
        queryset = super().get_queryset().select_related("publisher")
        return self.get_scoped_queryset(queryset)

    def get_context_data(self, **kwargs):
        """Add breadcrumbs and role-based action flags to context."""
        context = super().get_context_data(**kwargs)
        context["breadcrumbs"] = [
            {"label": "Kontrolna tabla", "url": reverse_lazy("dashboard")},
            {"label": "Publikacije", "url": reverse_lazy("publications:list")},
            {"label": self.object.title, "url": None},
        ]

        # Role-based action visibility (uses cached role flags from mixin)
        flags = self._get_user_role_flags()
        context["can_edit"] = flags["is_admin"] or flags["is_urednik"]
        context["can_delete"] = flags["is_admin"]
        return context


class PublicationDeleteView(AdministratorRequiredMixin, DeleteView):
    """
    Soft delete a publication.

    Only Administrator/Superadmin can delete (Story 2.4 - Task 3.4).
    """

    model = Publication
    template_name = "publications/publication_confirm_delete.html"
    success_url = reverse_lazy("publications:list")
    slug_url_kwarg = "slug"

    def get_context_data(self, **kwargs):
        """Add breadcrumbs to context."""
        context = super().get_context_data(**kwargs)
        context["breadcrumbs"] = [
            {"label": "Kontrolna tabla", "url": reverse_lazy("dashboard")},
            {"label": "Publikacije", "url": reverse_lazy("publications:list")},
            {"label": self.object.title, "url": None},
        ]
        context["issue_count"] = self.object.issue_count
        return context

    def form_valid(self, form):
        """Perform soft delete instead of actual deletion."""
        publication = self.get_object()
        issue_count = publication.issue_count

        if issue_count > 0:
            messages.warning(
                self.request,
                f"Publikacija '{publication.title}' ima {issue_count} izdanja. "
                "Publikacija je označena kao obrisana ali podaci su sačuvani.",
            )
        else:
            messages.success(
                self.request,
                f"Publikacija '{publication.title}' uspešno obrisana.",
            )

        # Soft delete instead of actual delete
        publication.soft_delete(user=self.request.user)
        return HttpResponseRedirect(self.success_url)


# =============================================================================
# HTMX Endpoints
# =============================================================================


@login_required
@require_GET
def htmx_type_fields(request):
    """
    HTMX endpoint for dynamic type-specific fields.

    Called when publication_type select changes.
    Returns appropriate partial template for the selected type.

    AC: #5 - HTMX is used for dynamic form updates.
    """
    # Accept both 'type' (legacy) and 'publication_type' (from hx-include)
    publication_type = request.GET.get("publication_type") or request.GET.get("type", PublicationType.JOURNAL)

    template_map = {
        PublicationType.JOURNAL: "publications/partials/_type_fields_journal.html",
        PublicationType.CONFERENCE: "publications/partials/_type_fields_conference.html",
        PublicationType.BOOK: "publications/partials/_type_fields_book.html",
        PublicationType.OTHER: "publications/partials/_type_fields_other.html",
    }

    template = template_map.get(
        publication_type, "publications/partials/_type_fields_other.html"
    )

    # Create an empty form for context (provides widgets and labels)
    form = PublicationForm()

    context = {
        "publication_type": publication_type,
        "form": form,
    }

    # HTMX and non-HTMX both get the partial (for debugging)
    return render(request, template, context)
