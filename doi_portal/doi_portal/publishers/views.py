"""
Publisher views.

Story 2.1 - Task 3: Publisher admin CRUD views.
"""

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponseRedirect
from django.urls import reverse_lazy
from django.views.generic import (
    CreateView,
    DeleteView,
    DetailView,
    ListView,
    UpdateView,
)

from .forms import PublisherForm
from .mixins import AdministratorRequiredMixin
from .models import Publisher


class PublisherListView(LoginRequiredMixin, AdministratorRequiredMixin, ListView):
    """
    List all publishers with name, DOI prefix, publication count.

    AC: #2 - Displays list of all publishers.
    """

    model = Publisher
    template_name = "publishers/publisher_list.html"
    context_object_name = "publishers"

    def get_context_data(self, **kwargs):
        """Add breadcrumbs to context."""
        context = super().get_context_data(**kwargs)
        context["breadcrumbs"] = [
            {"label": "Kontrolna tabla", "url": reverse_lazy("dashboard")},
            {"label": "Izdavači", "url": None},
        ]
        return context


class PublisherCreateView(
    LoginRequiredMixin, AdministratorRequiredMixin, CreateView
):
    """
    Create a new publisher.

    AC: #3, #4 - Displays form with validation, creates publisher on submit.
    """

    model = Publisher
    form_class = PublisherForm
    template_name = "publishers/publisher_form.html"
    success_url = reverse_lazy("publishers:list")

    def get_context_data(self, **kwargs):
        """Add breadcrumbs and form metadata to context."""
        context = super().get_context_data(**kwargs)
        context["breadcrumbs"] = [
            {"label": "Kontrolna tabla", "url": reverse_lazy("dashboard")},
            {"label": "Izdavači", "url": reverse_lazy("publishers:list")},
            {"label": "Novi izdavač", "url": None},
        ]
        context["form_title"] = "Novi izdavač"
        context["submit_text"] = "Kreiraj izdavača"
        return context

    def form_valid(self, form):
        """Show success message on valid submission."""
        response = super().form_valid(form)
        messages.success(
            self.request,
            f"Izdavač '{self.object.name}' uspešno kreiran.",
        )
        return response


class PublisherUpdateView(
    LoginRequiredMixin, AdministratorRequiredMixin, UpdateView
):
    """
    Update an existing publisher.

    AC: #5 - Updates publisher data with audit logging.
    """

    model = Publisher
    form_class = PublisherForm
    template_name = "publishers/publisher_form.html"
    success_url = reverse_lazy("publishers:list")

    def get_context_data(self, **kwargs):
        """Add breadcrumbs and form metadata to context."""
        context = super().get_context_data(**kwargs)
        context["breadcrumbs"] = [
            {"label": "Kontrolna tabla", "url": reverse_lazy("dashboard")},
            {"label": "Izdavači", "url": reverse_lazy("publishers:list")},
            {"label": self.object.name, "url": None},
        ]
        context["form_title"] = f"Izmeni izdavača: {self.object.name}"
        context["submit_text"] = "Sačuvaj izmene"
        return context

    def form_valid(self, form):
        """Show success message on valid submission."""
        response = super().form_valid(form)
        messages.success(
            self.request,
            f"Izdavač '{self.object.name}' uspešno ažuriran.",
        )
        return response


class PublisherDetailView(
    LoginRequiredMixin, AdministratorRequiredMixin, DetailView
):
    """
    View publisher details.

    AC: #2 - Displays publisher information.
    """

    model = Publisher
    template_name = "publishers/publisher_detail.html"
    context_object_name = "publisher"

    def get_context_data(self, **kwargs):
        """Add breadcrumbs to context."""
        context = super().get_context_data(**kwargs)
        context["breadcrumbs"] = [
            {"label": "Kontrolna tabla", "url": reverse_lazy("dashboard")},
            {"label": "Izdavači", "url": reverse_lazy("publishers:list")},
            {"label": self.object.name, "url": None},
        ]
        return context


class PublisherDeleteView(
    LoginRequiredMixin, AdministratorRequiredMixin, DeleteView
):
    """
    Soft delete a publisher.

    AC: #6 - Performs soft delete, shows warning if has publications.
    """

    model = Publisher
    template_name = "publishers/publisher_confirm_delete.html"
    success_url = reverse_lazy("publishers:list")

    def get_context_data(self, **kwargs):
        """Add breadcrumbs and publication count to context."""
        context = super().get_context_data(**kwargs)
        context["breadcrumbs"] = [
            {"label": "Kontrolna tabla", "url": reverse_lazy("dashboard")},
            {"label": "Izdavači", "url": reverse_lazy("publishers:list")},
            {"label": self.object.name, "url": None},
        ]
        context["publication_count"] = self.object.publication_count
        return context

    def form_valid(self, form):
        """Perform soft delete instead of actual deletion."""
        publisher = self.get_object()
        pub_count = publisher.publication_count

        if pub_count > 0:
            messages.warning(
                self.request,
                f"Izdavač '{publisher.name}' ima {pub_count} publikacija. "
                "Izdavač je označen kao obrisan ali podaci su sačuvani.",
            )
        else:
            messages.success(
                self.request,
                f"Izdavač '{publisher.name}' uspešno obrisan.",
            )

        # Soft delete instead of actual delete
        publisher.soft_delete(user=self.request.user)
        return HttpResponseRedirect(self.success_url)
