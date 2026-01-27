"""
Publication views.

Story 2.3 - Task 3: Publication admin CRUD views with HTMX support.
"""

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponse, HttpResponseRedirect
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

from doi_portal.publishers.mixins import AdministratorRequiredMixin

from .forms import PublicationForm
from .models import Publication, PublicationType


class PublicationListView(LoginRequiredMixin, AdministratorRequiredMixin, ListView):
    """
    List all publications with filtering by type/publisher.

    AC: #5 - Displays list of all publications with type icons.
    """

    model = Publication
    template_name = "publications/publication_list.html"
    context_object_name = "publications"
    paginate_by = 20

    def get_queryset(self):
        """Filter publications by type and publisher if specified."""
        queryset = super().get_queryset().select_related("publisher")

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

        return queryset

    def get_context_data(self, **kwargs):
        """Add breadcrumbs and filter options to context."""
        context = super().get_context_data(**kwargs)
        context["breadcrumbs"] = [
            {"label": "Kontrolna tabla", "url": reverse_lazy("dashboard")},
            {"label": "Publikacije", "url": None},
        ]
        context["publication_types"] = PublicationType.choices
        context["current_type"] = self.request.GET.get("type", "")
        context["current_publisher"] = self.request.GET.get("publisher", "")
        context["search_query"] = self.request.GET.get("search", "")
        return context


class PublicationCreateView(
    LoginRequiredMixin, AdministratorRequiredMixin, CreateView
):
    """
    Create new publication with dynamic HTMX form.

    AC: #5, #6 - Displays form with type-specific fields, creates publication.
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


class PublicationUpdateView(
    LoginRequiredMixin, AdministratorRequiredMixin, UpdateView
):
    """
    Update an existing publication.

    AC: #5, #6 - Updates publication data with dynamic type-specific fields.
    """

    model = Publication
    form_class = PublicationForm
    template_name = "publications/publication_form.html"
    success_url = reverse_lazy("publications:list")
    slug_url_kwarg = "slug"

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


class PublicationDetailView(
    LoginRequiredMixin, AdministratorRequiredMixin, DetailView
):
    """
    View publication details.

    AC: #5 - Displays publication information with type-specific fields.
    """

    model = Publication
    template_name = "publications/publication_detail.html"
    context_object_name = "publication"
    slug_url_kwarg = "slug"

    def get_context_data(self, **kwargs):
        """Add breadcrumbs to context."""
        context = super().get_context_data(**kwargs)
        context["breadcrumbs"] = [
            {"label": "Kontrolna tabla", "url": reverse_lazy("dashboard")},
            {"label": "Publikacije", "url": reverse_lazy("publications:list")},
            {"label": self.object.title, "url": None},
        ]
        return context


class PublicationDeleteView(
    LoginRequiredMixin, AdministratorRequiredMixin, DeleteView
):
    """
    Soft delete a publication.

    AC: #6 - Performs soft delete instead of actual deletion.
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
