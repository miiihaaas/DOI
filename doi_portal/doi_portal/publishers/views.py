"""
Publisher views.

Story 2.1 - Task 3: Publisher admin CRUD views.
"""

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404, render
from django.urls import reverse_lazy
from django.views.decorators.http import require_GET, require_POST
from django.views.generic import (
    CreateView,
    DeleteView,
    DetailView,
    ListView,
    UpdateView,
)

from .forms import PublisherContactForm, PublisherForm, PublisherNoteForm
from .mixins import AdministratorRequiredMixin
from .models import Publisher, PublisherContact, PublisherNote


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------


def _check_publisher_admin(user):
    """Check if user is Administrator or Superadmin. Raises PermissionDenied."""
    if user.is_superuser:
        return
    group_names = set(user.groups.values_list("name", flat=True))
    if "Administrator" in group_names or "Superadmin" in group_names:
        return
    raise PermissionDenied


# ---------------------------------------------------------------------------
# Publisher CRUD (CBV)
# ---------------------------------------------------------------------------


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
        """Add breadcrumbs, contacts, notes to context."""
        context = super().get_context_data(**kwargs)
        context["breadcrumbs"] = [
            {"label": "Kontrolna tabla", "url": reverse_lazy("dashboard")},
            {"label": "Izdavači", "url": reverse_lazy("publishers:list")},
            {"label": self.object.name, "url": None},
        ]
        context["contacts"] = self.object.contacts.all()
        context["notes"] = self.object.notes.select_related("author").all()
        context["note_form"] = PublisherNoteForm()
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


# ---------------------------------------------------------------------------
# Crossref password reveal/hide (HTMX FBV)
# ---------------------------------------------------------------------------


@login_required
@require_POST
def reveal_crossref_password(request, pk):
    """HTMX: prikaži dekriptovani crossref password."""
    _check_publisher_admin(request.user)
    if not request.headers.get("HX-Request"):
        raise PermissionDenied
    publisher = get_object_or_404(Publisher, pk=pk)
    return render(
        request,
        "publishers/partials/_crossref_password_revealed.html",
        {
            "publisher": publisher,
            "password": publisher.crossref_password or "",
        },
    )


@login_required
@require_POST
def hide_crossref_password(request, pk):
    """HTMX: sakrij crossref password (vrati masked view)."""
    _check_publisher_admin(request.user)
    publisher = get_object_or_404(Publisher, pk=pk)
    return render(
        request,
        "publishers/partials/_crossref_password_masked.html",
        {"publisher": publisher},
    )


# ---------------------------------------------------------------------------
# PublisherContact HTMX views (FBV)
# ---------------------------------------------------------------------------


@login_required
@require_GET
def contact_list(request, publisher_pk):
    """HTMX partial: lista kontakata za izdavača."""
    _check_publisher_admin(request.user)
    publisher = get_object_or_404(Publisher, pk=publisher_pk)
    contacts = publisher.contacts.all()
    return render(
        request,
        "publishers/partials/_contact_list.html",
        {"publisher": publisher, "contacts": contacts},
    )


@login_required
@require_GET
def contact_add_form(request, publisher_pk):
    """HTMX partial: prazna forma za dodavanje kontakta."""
    _check_publisher_admin(request.user)
    publisher = get_object_or_404(Publisher, pk=publisher_pk)
    form = PublisherContactForm()
    return render(
        request,
        "publishers/partials/_contact_form.html",
        {"publisher": publisher, "form": form},
    )


@login_required
@require_POST
def contact_add(request, publisher_pk):
    """HTMX partial: dodaj kontakt osobu."""
    _check_publisher_admin(request.user)
    publisher = get_object_or_404(Publisher, pk=publisher_pk)
    form = PublisherContactForm(request.POST)
    if form.is_valid():
        contact = form.save(commit=False)
        contact.publisher = publisher
        contact.save()
        contacts = publisher.contacts.all()
        return render(
            request,
            "publishers/partials/_contact_list.html",
            {"publisher": publisher, "contacts": contacts},
        )
    return render(
        request,
        "publishers/partials/_contact_form.html",
        {"publisher": publisher, "form": form},
    )


@login_required
@require_GET
def contact_edit_form(request, pk):
    """HTMX partial: forma za editovanje kontakta."""
    _check_publisher_admin(request.user)
    contact = get_object_or_404(PublisherContact, pk=pk)
    form = PublisherContactForm(instance=contact)
    return render(
        request,
        "publishers/partials/_contact_form.html",
        {"publisher": contact.publisher, "form": form, "contact": contact},
    )


@login_required
@require_POST
def contact_update(request, pk):
    """HTMX partial: ažuriraj kontakt osobu."""
    _check_publisher_admin(request.user)
    contact = get_object_or_404(PublisherContact, pk=pk)
    form = PublisherContactForm(request.POST, instance=contact)
    if form.is_valid():
        form.save()
        contacts = contact.publisher.contacts.all()
        return render(
            request,
            "publishers/partials/_contact_list.html",
            {"publisher": contact.publisher, "contacts": contacts},
        )
    return render(
        request,
        "publishers/partials/_contact_form.html",
        {"publisher": contact.publisher, "form": form, "contact": contact},
    )


@login_required
@require_POST
def contact_delete(request, pk):
    """HTMX partial: soft delete kontakta."""
    _check_publisher_admin(request.user)
    contact = get_object_or_404(PublisherContact, pk=pk)
    publisher = contact.publisher
    contact.soft_delete(user=request.user)
    contacts = publisher.contacts.all()
    return render(
        request,
        "publishers/partials/_contact_list.html",
        {"publisher": publisher, "contacts": contacts},
    )


# ---------------------------------------------------------------------------
# PublisherNote HTMX views (FBV)
# ---------------------------------------------------------------------------


@login_required
@require_GET
def note_list(request, publisher_pk):
    """HTMX partial: lista napomena za izdavača."""
    _check_publisher_admin(request.user)
    publisher = get_object_or_404(Publisher, pk=publisher_pk)
    notes = publisher.notes.select_related("author").all()
    note_form = PublisherNoteForm()
    return render(
        request,
        "publishers/partials/_note_list.html",
        {"publisher": publisher, "notes": notes, "note_form": note_form},
    )


@login_required
@require_POST
def note_add(request, publisher_pk):
    """HTMX partial: dodaj napomenu."""
    _check_publisher_admin(request.user)
    publisher = get_object_or_404(Publisher, pk=publisher_pk)
    form = PublisherNoteForm(request.POST)
    if form.is_valid():
        note = form.save(commit=False)
        note.publisher = publisher
        note.author = request.user
        note.save()
        notes = publisher.notes.select_related("author").all()
        note_form = PublisherNoteForm()
        return render(
            request,
            "publishers/partials/_note_list.html",
            {"publisher": publisher, "notes": notes, "note_form": note_form},
        )
    # On error, re-render list with the invalid form
    notes = publisher.notes.select_related("author").all()
    return render(
        request,
        "publishers/partials/_note_list.html",
        {"publisher": publisher, "notes": notes, "note_form": form},
    )


@login_required
@require_GET
def note_edit_form(request, pk):
    """HTMX partial: forma za editovanje napomene."""
    _check_publisher_admin(request.user)
    note = get_object_or_404(PublisherNote, pk=pk)
    form = PublisherNoteForm(instance=note)
    return render(
        request,
        "publishers/partials/_note_form.html",
        {"publisher": note.publisher, "form": form, "note": note},
    )


@login_required
@require_POST
def note_update(request, pk):
    """HTMX partial: ažuriraj napomenu."""
    _check_publisher_admin(request.user)
    note = get_object_or_404(PublisherNote, pk=pk)
    publisher = note.publisher
    form = PublisherNoteForm(request.POST, instance=note)
    if form.is_valid():
        updated_note = form.save(commit=False)
        updated_note.is_edited = True
        updated_note.save()
        notes = publisher.notes.select_related("author").all()
        note_form = PublisherNoteForm()
        return render(
            request,
            "publishers/partials/_note_list.html",
            {"publisher": publisher, "notes": notes, "note_form": note_form},
        )
    return render(
        request,
        "publishers/partials/_note_form.html",
        {"publisher": publisher, "form": form, "note": note},
    )


@login_required
@require_POST
def note_delete(request, pk):
    """HTMX partial: hard delete napomene."""
    _check_publisher_admin(request.user)
    note = get_object_or_404(PublisherNote, pk=pk)
    publisher = note.publisher
    note.delete()  # Hard delete
    notes = publisher.notes.select_related("author").all()
    note_form = PublisherNoteForm()
    return render(
        request,
        "publishers/partials/_note_list.html",
        {"publisher": publisher, "notes": notes, "note_form": note_form},
    )
