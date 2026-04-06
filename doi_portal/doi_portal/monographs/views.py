"""
Monograph views for DOI Portal.

Task 3.1-3.5: Monograph admin CRUD views with row-level permissions.
Task 4.1-4.5: HTMX FBV views for Contributors, Affiliations, Funding,
Relations, and Chapters at both monograph and chapter levels.
"""

import json
import logging

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.db import models
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy
from django.views.decorators.http import require_GET, require_POST
from django.views.generic import (
    CreateView,
    DeleteView,
    DetailView,
    ListView,
    UpdateView,
)

from .forms import (
    ChapterAffiliationForm,
    ChapterContributorForm,
    ChapterFundingForm,
    ChapterRelationForm,
    MonographAffiliationForm,
    MonographChapterForm,
    MonographContributorForm,
    MonographForm,
    MonographFundingForm,
    MonographRelationForm,
)
from .models import (
    ChapterAffiliation,
    ChapterContributor,
    ChapterFunding,
    ChapterRelation,
    Monograph,
    MonographAffiliation,
    MonographChapter,
    MonographContributor,
    MonographFunding,
    MonographRelation,
    MonographStatus,
)

logger = logging.getLogger(__name__)


# =============================================================================
# Permission helpers
# =============================================================================


def _get_user_group_names(user):
    """Get and cache user's group names to avoid redundant DB queries."""
    if not hasattr(user, "_cached_group_names"):
        user._cached_group_names = set(user.groups.values_list("name", flat=True))
    return user._cached_group_names


def _check_monograph_permission(user, monograph):
    """
    Check if user has permission to modify this monograph.

    Superadmin/Admin -> always OK; Urednik/Bibliotekar -> check publisher match.
    Raises PermissionDenied if not allowed.
    """
    if user.is_superuser:
        return
    group_names = _get_user_group_names(user)
    if "Administrator" in group_names or "Superadmin" in group_names:
        return
    # Urednik/Bibliotekar - check publisher scoping
    if hasattr(user, "publisher") and user.publisher:
        if monograph.publisher == user.publisher:
            return
    raise PermissionDenied


def _get_role_flags(user):
    """Return role flags dict for template context."""
    flags = {
        "is_admin": False,
        "is_urednik": False,
        "is_bibliotekar": False,
        "has_publisher": hasattr(user, "publisher") and user.publisher is not None,
    }
    if user.is_superuser:
        flags["is_admin"] = True
    else:
        group_names = _get_user_group_names(user)
        if "Administrator" in group_names or "Superadmin" in group_names:
            flags["is_admin"] = True
        if "Urednik" in group_names:
            flags["is_urednik"] = True
        if "Bibliotekar" in group_names:
            flags["is_bibliotekar"] = True
    return flags


# =============================================================================
# CBV views for Monograph CRUD (Task 3.1-3.5)
# =============================================================================


class MonographListView(LoginRequiredMixin, ListView):
    """List all monographs with filtering and role-based scoping."""

    model = Monograph
    template_name = "monographs/monograph_list.html"
    context_object_name = "monographs"
    paginate_by = 20

    def get_queryset(self):
        queryset = super().get_queryset().select_related("publisher", "created_by")
        user = self.request.user
        flags = _get_role_flags(user)

        if not flags["is_admin"]:
            if flags["has_publisher"]:
                queryset = queryset.filter(publisher=user.publisher)
            else:
                queryset = queryset.none()

        # Filter by status
        status = self.request.GET.get("status")
        if status and status in [c[0] for c in MonographStatus.choices]:
            queryset = queryset.filter(status=status)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        flags = _get_role_flags(self.request.user)
        context["breadcrumbs"] = [
            {"label": "Kontrolna tabla", "url": reverse_lazy("dashboard")},
            {"label": "Monografije", "url": None},
        ]
        context["status_choices"] = MonographStatus.choices
        context["current_status"] = self.request.GET.get("status", "")
        context["can_create"] = flags["is_admin"] or flags["is_urednik"] or flags["is_bibliotekar"]
        context["can_edit"] = flags["is_admin"] or flags["is_urednik"] or flags["is_bibliotekar"]
        context["can_delete"] = flags["is_admin"]
        return context


class MonographCreateView(LoginRequiredMixin, CreateView):
    """Create a new monograph."""

    model = Monograph
    form_class = MonographForm
    template_name = "monographs/monograph_form.html"

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["breadcrumbs"] = [
            {"label": "Kontrolna tabla", "url": reverse_lazy("dashboard")},
            {"label": "Monografije", "url": reverse_lazy("monographs:list")},
            {"label": "Nova monografija", "url": None},
        ]
        context["form_title"] = "Nova monografija"
        context["submit_text"] = "Kreiraj monografiju"
        return context

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        response = super().form_valid(form)
        messages.success(self.request, "Monografija je uspešno kreirana.")
        return response

    def get_success_url(self):
        return reverse("monographs:update", kwargs={"pk": self.object.pk})


class MonographDetailView(LoginRequiredMixin, DetailView):
    """View monograph details."""

    model = Monograph
    template_name = "monographs/monograph_detail.html"
    context_object_name = "monograph"

    def get_queryset(self):
        queryset = super().get_queryset().select_related("publisher", "created_by")
        user = self.request.user
        flags = _get_role_flags(user)
        if not flags["is_admin"]:
            if flags["has_publisher"]:
                queryset = queryset.filter(publisher=user.publisher)
            else:
                queryset = queryset.none()
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        flags = _get_role_flags(self.request.user)
        context["breadcrumbs"] = [
            {"label": "Kontrolna tabla", "url": reverse_lazy("dashboard")},
            {"label": "Monografije", "url": reverse_lazy("monographs:list")},
            {"label": str(self.object), "url": None},
        ]
        context["chapters"] = self.object.chapters.all()
        context["contributors"] = self.object.contributors.prefetch_related("affiliations").all()
        context["fundings"] = self.object.fundings.all()
        context["relations"] = self.object.relations.all()
        context["can_edit"] = (
            flags["is_admin"] or flags["is_urednik"] or flags["is_bibliotekar"]
        ) and self.object.status == MonographStatus.DRAFT
        context["can_delete"] = flags["is_admin"]
        return context


class MonographUpdateView(LoginRequiredMixin, UpdateView):
    """Update an existing monograph."""

    model = Monograph
    form_class = MonographForm
    template_name = "monographs/monograph_form.html"

    def get_queryset(self):
        queryset = super().get_queryset().select_related("publisher", "created_by")
        user = self.request.user
        flags = _get_role_flags(user)
        if not flags["is_admin"]:
            if flags["has_publisher"]:
                queryset = queryset.filter(publisher=user.publisher)
            else:
                queryset = queryset.none()
        return queryset.filter(status=MonographStatus.DRAFT)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["breadcrumbs"] = [
            {"label": "Kontrolna tabla", "url": reverse_lazy("dashboard")},
            {"label": "Monografije", "url": reverse_lazy("monographs:list")},
            {"label": str(self.object), "url": None},
        ]
        context["form_title"] = f"Izmeni monografiju: {self.object.title}"
        context["submit_text"] = "Sačuvaj izmene"
        context["is_edit"] = True
        context["contributors"] = self.object.contributors.prefetch_related("affiliations").all()
        context["fundings"] = self.object.fundings.all()
        context["relations"] = self.object.relations.all()
        context["chapters"] = self.object.chapters.all()
        return context

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, "Monografija je uspešno ažurirana.")
        return response

    def get_success_url(self):
        return reverse("monographs:update", kwargs={"pk": self.object.pk})


class MonographDeleteView(LoginRequiredMixin, DeleteView):
    """Soft delete a monograph. Only Administrator/Superadmin."""

    model = Monograph
    template_name = "monographs/monograph_confirm_delete.html"
    success_url = reverse_lazy("monographs:list")

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        flags = _get_role_flags(request.user)
        if not flags["is_admin"]:
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        return super().get_queryset().select_related("publisher")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["breadcrumbs"] = [
            {"label": "Kontrolna tabla", "url": reverse_lazy("dashboard")},
            {"label": "Monografije", "url": reverse_lazy("monographs:list")},
            {"label": str(self.object), "url": None},
        ]
        return context

    def form_valid(self, form):
        monograph = self.object
        messages.success(self.request, "Monografija je uspešno obrisana.")
        monograph.soft_delete(user=self.request.user)
        return HttpResponseRedirect(self.success_url)


# =============================================================================
# Monograph status transitions (Publish / Withdraw)
# =============================================================================


@login_required
@require_POST
def monograph_publish(request, pk):
    """Publish a monograph (DRAFT → PUBLISHED). Also publishes all DRAFT chapters."""
    monograph = get_object_or_404(Monograph.objects.select_related("publisher"), pk=pk)
    _check_monograph_permission(request.user, monograph)

    if monograph.status != MonographStatus.DRAFT:
        messages.error(request, "Samo monografije u statusu Nacrt mogu biti objavljene.")
        return redirect("monographs:detail", pk=pk)

    monograph.status = MonographStatus.PUBLISHED
    monograph.save(update_fields=["status", "updated_at"])

    # Also publish all DRAFT chapters
    updated = monograph.chapters.filter(status=MonographStatus.DRAFT).update(
        status=MonographStatus.PUBLISHED,
    )

    msg = "Monografija je objavljena."
    if updated:
        msg += f" {updated} poglavlje/a takođe objavljeno."
    messages.success(request, msg)
    return redirect("monographs:detail", pk=pk)


@login_required
@require_POST
def monograph_withdraw(request, pk):
    """Withdraw a published monograph (PUBLISHED → WITHDRAWN)."""
    monograph = get_object_or_404(Monograph.objects.select_related("publisher"), pk=pk)
    _check_monograph_permission(request.user, monograph)

    if monograph.status != MonographStatus.PUBLISHED:
        messages.error(request, "Samo objavljene monografije mogu biti povučene.")
        return redirect("monographs:detail", pk=pk)

    monograph.status = MonographStatus.WITHDRAWN
    monograph.save(update_fields=["status", "updated_at"])

    # Also withdraw all PUBLISHED chapters
    updated = monograph.chapters.filter(status=MonographStatus.PUBLISHED).update(
        status=MonographStatus.WITHDRAWN,
    )

    msg = "Monografija je povučena."
    if updated:
        msg += f" {updated} poglavlje/a takođe povučeno."
    messages.success(request, msg)
    return redirect("monographs:detail", pk=pk)


# =============================================================================
# HTMX FBV: Monograph-level Contributors
# =============================================================================


def _render_contributor_list(request, monograph):
    """Helper: render contributor list partial for a monograph."""
    contributors = monograph.contributors.prefetch_related("affiliations").all()
    return render(request, "monographs/partials/_contributor_list.html", {
        "monograph": monograph,
        "contributors": contributors,
    })


@login_required
@require_POST
def contributor_add(request, monograph_pk):
    """Add contributor to monograph via HTMX POST."""
    monograph = get_object_or_404(Monograph.objects.select_related("publisher"), pk=monograph_pk)
    _check_monograph_permission(request.user, monograph)

    form = MonographContributorForm(request.POST)
    if form.is_valid():
        contributor = form.save(commit=False)
        contributor.monograph = monograph
        max_order = monograph.contributors.aggregate(m=models.Max("order"))["m"] or 0
        contributor.order = max_order + 1
        if contributor.order == 1:
            from doi_portal.articles.models import AuthorSequence
            contributor.sequence = AuthorSequence.FIRST
        else:
            from doi_portal.articles.models import AuthorSequence
            contributor.sequence = AuthorSequence.ADDITIONAL
        contributor.save()
    else:
        response = render(request, "monographs/partials/_contributor_form.html", {
            "monograph": monograph,
            "contributor_form": form,
        })
        response["HX-Retarget"] = "#contributor-form-container"
        response["HX-Reswap"] = "innerHTML"
        return response

    return _render_contributor_list(request, monograph)


@login_required
@require_POST
def contributor_delete(request, pk):
    """Delete monograph contributor via HTMX POST, reorder remaining."""
    contributor = get_object_or_404(
        MonographContributor.objects.select_related("monograph", "monograph__publisher"),
        pk=pk,
    )
    _check_monograph_permission(request.user, contributor.monograph)

    monograph = contributor.monograph
    contributor.delete()

    # Reorder remaining
    from doi_portal.articles.models import AuthorSequence
    remaining = monograph.contributors.order_by("order")
    for index, c in enumerate(remaining, start=1):
        MonographContributor.objects.filter(pk=c.pk).update(
            order=index,
            sequence=AuthorSequence.FIRST if index == 1 else AuthorSequence.ADDITIONAL,
        )

    return _render_contributor_list(request, monograph)


@login_required
@require_POST
def contributor_reorder(request, monograph_pk):
    """Reorder monograph contributors via HTMX POST (drag & drop)."""
    monograph = get_object_or_404(Monograph.objects.select_related("publisher"), pk=monograph_pk)
    _check_monograph_permission(request.user, monograph)

    try:
        order_data = json.loads(request.body)
    except (json.JSONDecodeError, ValueError):
        order_data = {}

    order_list = order_data.get("order", [])
    if not isinstance(order_list, list):
        order_list = []

    from doi_portal.articles.models import AuthorSequence
    for index, cpk in enumerate(order_list, start=1):
        if not isinstance(cpk, int):
            continue
        MonographContributor.objects.filter(pk=cpk, monograph=monograph).update(
            order=index,
            sequence=AuthorSequence.FIRST if index == 1 else AuthorSequence.ADDITIONAL,
        )

    return _render_contributor_list(request, monograph)


@login_required
@require_GET
def contributor_form_view(request, monograph_pk):
    """Return empty contributor form for inline editing via HTMX GET."""
    monograph = get_object_or_404(Monograph.objects.select_related("publisher"), pk=monograph_pk)
    _check_monograph_permission(request.user, monograph)
    form = MonographContributorForm()
    return render(request, "monographs/partials/_contributor_form.html", {
        "monograph": monograph,
        "contributor_form": form,
    })


@login_required
@require_GET
def contributor_edit_form_view(request, pk):
    """Return pre-filled contributor form for editing via HTMX GET."""
    contributor = get_object_or_404(
        MonographContributor.objects.select_related("monograph", "monograph__publisher"),
        pk=pk,
    )
    _check_monograph_permission(request.user, contributor.monograph)
    form = MonographContributorForm(instance=contributor)
    return render(request, "monographs/partials/_contributor_form.html", {
        "monograph": contributor.monograph,
        "contributor_form": form,
        "contributor": contributor,
    })


@login_required
@require_POST
def contributor_update(request, pk):
    """Update monograph contributor via HTMX POST."""
    contributor = get_object_or_404(
        MonographContributor.objects.select_related("monograph", "monograph__publisher"),
        pk=pk,
    )
    _check_monograph_permission(request.user, contributor.monograph)

    form = MonographContributorForm(request.POST, instance=contributor)
    if form.is_valid():
        form.save()
    else:
        response = render(request, "monographs/partials/_contributor_form.html", {
            "monograph": contributor.monograph,
            "contributor_form": form,
            "contributor": contributor,
        })
        response["HX-Retarget"] = "#contributor-form-container"
        response["HX-Reswap"] = "innerHTML"
        return response

    return _render_contributor_list(request, contributor.monograph)


# =============================================================================
# HTMX FBV: Monograph-level Affiliations
# =============================================================================


@login_required
@require_POST
def affiliation_add(request, contributor_pk):
    """Add affiliation to monograph contributor via HTMX POST."""
    contributor = get_object_or_404(
        MonographContributor.objects.select_related("monograph", "monograph__publisher"),
        pk=contributor_pk,
    )
    _check_monograph_permission(request.user, contributor.monograph)

    form = MonographAffiliationForm(request.POST)
    if form.is_valid():
        affiliation = form.save(commit=False)
        affiliation.contributor = contributor
        max_order = contributor.affiliations.aggregate(m=models.Max("order"))["m"] or 0
        affiliation.order = max_order + 1
        affiliation.save()
    else:
        response = render(request, "monographs/partials/_affiliation_form.html", {
            "contributor": contributor,
            "affiliation_form": form,
        })
        response["HX-Retarget"] = "#contributor-form-container"
        response["HX-Reswap"] = "innerHTML"
        return response

    return _render_contributor_list(request, contributor.monograph)


@login_required
@require_POST
def affiliation_delete(request, pk):
    """Delete monograph affiliation via HTMX POST."""
    affiliation = get_object_or_404(
        MonographAffiliation.objects.select_related(
            "contributor", "contributor__monograph", "contributor__monograph__publisher"
        ),
        pk=pk,
    )
    _check_monograph_permission(request.user, affiliation.contributor.monograph)
    monograph = affiliation.contributor.monograph
    affiliation.delete()
    return _render_contributor_list(request, monograph)


@login_required
@require_GET
def affiliation_form_view(request, contributor_pk):
    """Return empty affiliation form via HTMX GET."""
    contributor = get_object_or_404(
        MonographContributor.objects.select_related("monograph", "monograph__publisher"),
        pk=contributor_pk,
    )
    _check_monograph_permission(request.user, contributor.monograph)
    form = MonographAffiliationForm()
    return render(request, "monographs/partials/_affiliation_form.html", {
        "contributor": contributor,
        "affiliation_form": form,
    })


@login_required
@require_GET
def affiliation_edit_form_view(request, pk):
    """Return pre-populated affiliation form for editing via HTMX GET."""
    affiliation = get_object_or_404(
        MonographAffiliation.objects.select_related(
            "contributor", "contributor__monograph", "contributor__monograph__publisher"
        ),
        pk=pk,
    )
    _check_monograph_permission(request.user, affiliation.contributor.monograph)
    form = MonographAffiliationForm(instance=affiliation)
    return render(request, "monographs/partials/_affiliation_form.html", {
        "contributor": affiliation.contributor,
        "affiliation_form": form,
        "affiliation": affiliation,
    })


@login_required
@require_POST
def affiliation_update(request, pk):
    """Update monograph affiliation via HTMX POST."""
    affiliation = get_object_or_404(
        MonographAffiliation.objects.select_related(
            "contributor", "contributor__monograph", "contributor__monograph__publisher"
        ),
        pk=pk,
    )
    _check_monograph_permission(request.user, affiliation.contributor.monograph)

    form = MonographAffiliationForm(request.POST, instance=affiliation)
    if form.is_valid():
        form.save()
    else:
        response = render(request, "monographs/partials/_affiliation_form.html", {
            "contributor": affiliation.contributor,
            "affiliation_form": form,
            "affiliation": affiliation,
        })
        response["HX-Retarget"] = "#contributor-form-container"
        response["HX-Reswap"] = "innerHTML"
        return response

    return _render_contributor_list(request, affiliation.contributor.monograph)


# =============================================================================
# HTMX FBV: Monograph-level Funding
# =============================================================================


def _render_funding_list(request, monograph):
    """Helper: render funding list partial for a monograph."""
    fundings = monograph.fundings.all()
    return render(request, "monographs/partials/_funding_list.html", {
        "monograph": monograph,
        "fundings": fundings,
    })


@login_required
@require_POST
def monograph_funding_add(request, monograph_pk):
    """Add funding to monograph via HTMX POST."""
    monograph = get_object_or_404(Monograph.objects.select_related("publisher"), pk=monograph_pk)
    _check_monograph_permission(request.user, monograph)

    form = MonographFundingForm(request.POST)
    if form.is_valid():
        funding = form.save(commit=False)
        funding.monograph = monograph
        max_order = monograph.fundings.aggregate(m=models.Max("order"))["m"] or 0
        funding.order = max_order + 1
        funding.save()
    else:
        response = render(request, "monographs/partials/_funding_form.html", {
            "monograph": monograph,
            "funding_form": form,
        })
        response["HX-Retarget"] = "#funding-form-container"
        response["HX-Reswap"] = "innerHTML"
        return response

    return _render_funding_list(request, monograph)


@login_required
@require_POST
def monograph_funding_delete(request, pk):
    """Delete monograph funding via HTMX POST."""
    funding = get_object_or_404(
        MonographFunding.objects.select_related("monograph", "monograph__publisher"),
        pk=pk,
    )
    _check_monograph_permission(request.user, funding.monograph)
    monograph = funding.monograph
    funding.delete()
    return _render_funding_list(request, monograph)


@login_required
@require_POST
def monograph_funding_reorder(request, monograph_pk):
    """Reorder monograph funding via HTMX POST."""
    monograph = get_object_or_404(Monograph.objects.select_related("publisher"), pk=monograph_pk)
    _check_monograph_permission(request.user, monograph)

    try:
        order_data = json.loads(request.body)
    except (json.JSONDecodeError, ValueError):
        order_data = {}

    order_list = order_data.get("order", [])
    if not isinstance(order_list, list):
        order_list = []

    for index, fpk in enumerate(order_list, start=1):
        if not isinstance(fpk, int):
            continue
        MonographFunding.objects.filter(pk=fpk, monograph=monograph).update(order=index)

    return _render_funding_list(request, monograph)


@login_required
@require_GET
def monograph_funding_form_view(request, monograph_pk):
    """Return empty funding form via HTMX GET."""
    monograph = get_object_or_404(Monograph.objects.select_related("publisher"), pk=monograph_pk)
    _check_monograph_permission(request.user, monograph)
    form = MonographFundingForm()
    return render(request, "monographs/partials/_funding_form.html", {
        "monograph": monograph,
        "funding_form": form,
    })


# =============================================================================
# HTMX FBV: Monograph-level Relations
# =============================================================================


def _render_relation_list(request, monograph):
    """Helper: render relation list partial for a monograph."""
    relations = monograph.relations.all()
    return render(request, "monographs/partials/_relation_list.html", {
        "monograph": monograph,
        "relations": relations,
    })


@login_required
@require_POST
def monograph_relation_add(request, monograph_pk):
    """Add relation to monograph via HTMX POST."""
    monograph = get_object_or_404(Monograph.objects.select_related("publisher"), pk=monograph_pk)
    _check_monograph_permission(request.user, monograph)

    form = MonographRelationForm(request.POST)
    if form.is_valid():
        relation = form.save(commit=False)
        relation.monograph = monograph
        max_order = monograph.relations.aggregate(m=models.Max("order"))["m"] or 0
        relation.order = max_order + 1
        relation.save()
    else:
        response = render(request, "monographs/partials/_relation_form.html", {
            "monograph": monograph,
            "relation_form": form,
        })
        response["HX-Retarget"] = "#relation-form-container"
        response["HX-Reswap"] = "innerHTML"
        return response

    return _render_relation_list(request, monograph)


@login_required
@require_POST
def monograph_relation_delete(request, pk):
    """Delete monograph relation via HTMX POST."""
    relation = get_object_or_404(
        MonographRelation.objects.select_related("monograph", "monograph__publisher"),
        pk=pk,
    )
    _check_monograph_permission(request.user, relation.monograph)
    monograph = relation.monograph
    relation.delete()
    return _render_relation_list(request, monograph)


@login_required
@require_POST
def monograph_relation_reorder(request, monograph_pk):
    """Reorder monograph relations via HTMX POST."""
    monograph = get_object_or_404(Monograph.objects.select_related("publisher"), pk=monograph_pk)
    _check_monograph_permission(request.user, monograph)

    try:
        order_data = json.loads(request.body)
    except (json.JSONDecodeError, ValueError):
        order_data = {}

    order_list = order_data.get("order", [])
    if not isinstance(order_list, list):
        order_list = []

    for index, rpk in enumerate(order_list, start=1):
        if not isinstance(rpk, int):
            continue
        MonographRelation.objects.filter(pk=rpk, monograph=monograph).update(order=index)

    return _render_relation_list(request, monograph)


@login_required
@require_GET
def monograph_relation_form_view(request, monograph_pk):
    """Return empty relation form via HTMX GET."""
    monograph = get_object_or_404(Monograph.objects.select_related("publisher"), pk=monograph_pk)
    _check_monograph_permission(request.user, monograph)
    form = MonographRelationForm()
    return render(request, "monographs/partials/_relation_form.html", {
        "monograph": monograph,
        "relation_form": form,
    })


# =============================================================================
# HTMX FBV: Chapters
# =============================================================================


def _render_chapter_list(request, monograph):
    """Helper: render chapter list partial for a monograph."""
    chapters = monograph.chapters.all()
    return render(request, "monographs/partials/_chapter_list.html", {
        "monograph": monograph,
        "chapters": chapters,
    })


@login_required
@require_POST
def chapter_add(request, monograph_pk):
    """Add chapter to monograph via HTMX POST."""
    monograph = get_object_or_404(Monograph.objects.select_related("publisher"), pk=monograph_pk)
    _check_monograph_permission(request.user, monograph)

    form = MonographChapterForm(request.POST)
    if form.is_valid():
        chapter = form.save(commit=False)
        chapter.monograph = monograph
        max_order = monograph.chapters.aggregate(m=models.Max("order"))["m"] or 0
        chapter.order = max_order + 1
        chapter.save()
    else:
        response = render(request, "monographs/partials/_chapter_form.html", {
            "monograph": monograph,
            "chapter_form": form,
        })
        response["HX-Retarget"] = "#chapter-form-container"
        response["HX-Reswap"] = "innerHTML"
        return response

    return _render_chapter_list(request, monograph)


@login_required
@require_POST
def chapter_delete(request, pk):
    """Delete chapter via HTMX POST, reorder remaining."""
    chapter = get_object_or_404(
        MonographChapter.objects.select_related("monograph", "monograph__publisher"),
        pk=pk,
    )
    _check_monograph_permission(request.user, chapter.monograph)
    monograph = chapter.monograph
    chapter.delete()

    # Reorder remaining chapters
    remaining = monograph.chapters.order_by("order")
    for index, ch in enumerate(remaining, start=1):
        MonographChapter.objects.filter(pk=ch.pk).update(order=index)

    return _render_chapter_list(request, monograph)


@login_required
@require_POST
def chapter_reorder(request, monograph_pk):
    """Reorder chapters via HTMX POST."""
    monograph = get_object_or_404(Monograph.objects.select_related("publisher"), pk=monograph_pk)
    _check_monograph_permission(request.user, monograph)

    try:
        order_data = json.loads(request.body)
    except (json.JSONDecodeError, ValueError):
        order_data = {}

    order_list = order_data.get("order", [])
    if not isinstance(order_list, list):
        order_list = []

    for index, cpk in enumerate(order_list, start=1):
        if not isinstance(cpk, int):
            continue
        MonographChapter.objects.filter(pk=cpk, monograph=monograph).update(order=index)

    return _render_chapter_list(request, monograph)


@login_required
@require_GET
def chapter_form_view(request, monograph_pk):
    """Return empty chapter form via HTMX GET."""
    monograph = get_object_or_404(Monograph.objects.select_related("publisher"), pk=monograph_pk)
    _check_monograph_permission(request.user, monograph)
    form = MonographChapterForm()
    return render(request, "monographs/partials/_chapter_form.html", {
        "monograph": monograph,
        "chapter_form": form,
    })


@login_required
@require_GET
def chapter_detail(request, pk):
    """Return chapter detail card via HTMX GET."""
    chapter = get_object_or_404(
        MonographChapter.objects.select_related("monograph", "monograph__publisher"),
        pk=pk,
    )
    _check_monograph_permission(request.user, chapter.monograph)
    contributors = chapter.contributors.prefetch_related("affiliations").all()
    fundings = chapter.fundings.all()
    relations = chapter.relations.all()
    return render(request, "monographs/partials/_chapter_detail.html", {
        "chapter": chapter,
        "monograph": chapter.monograph,
        "contributors": contributors,
        "fundings": fundings,
        "relations": relations,
    })


@login_required
@require_GET
def chapter_edit_form_view(request, pk):
    """Return pre-filled chapter form for editing via HTMX GET."""
    chapter = get_object_or_404(
        MonographChapter.objects.select_related("monograph", "monograph__publisher"),
        pk=pk,
    )
    _check_monograph_permission(request.user, chapter.monograph)
    form = MonographChapterForm(instance=chapter)
    return render(request, "monographs/partials/_chapter_form.html", {
        "monograph": chapter.monograph,
        "chapter_form": form,
        "chapter": chapter,
    })


@login_required
@require_POST
def chapter_update(request, pk):
    """Update chapter via HTMX POST."""
    chapter = get_object_or_404(
        MonographChapter.objects.select_related("monograph", "monograph__publisher"),
        pk=pk,
    )
    _check_monograph_permission(request.user, chapter.monograph)

    form = MonographChapterForm(request.POST, instance=chapter)
    if form.is_valid():
        form.save()
    else:
        response = render(request, "monographs/partials/_chapter_form.html", {
            "monograph": chapter.monograph,
            "chapter_form": form,
            "chapter": chapter,
        })
        response["HX-Retarget"] = "#chapter-form-container"
        response["HX-Reswap"] = "innerHTML"
        return response

    return _render_chapter_list(request, chapter.monograph)


# =============================================================================
# HTMX FBV: Chapter-level Contributors
# =============================================================================


def _render_chapter_contributor_list(request, chapter):
    """Helper: render chapter contributor list partial."""
    contributors = chapter.contributors.prefetch_related("affiliations").all()
    return render(request, "monographs/partials/_chapter_contributor_list.html", {
        "chapter": chapter,
        "contributors": contributors,
    })


@login_required
@require_POST
def chapter_contributor_add(request, chapter_pk):
    """Add contributor to chapter via HTMX POST."""
    chapter = get_object_or_404(
        MonographChapter.objects.select_related("monograph", "monograph__publisher"),
        pk=chapter_pk,
    )
    _check_monograph_permission(request.user, chapter.monograph)

    form = ChapterContributorForm(request.POST)
    if form.is_valid():
        contributor = form.save(commit=False)
        contributor.chapter = chapter
        max_order = chapter.contributors.aggregate(m=models.Max("order"))["m"] or 0
        contributor.order = max_order + 1
        if contributor.order == 1:
            from doi_portal.articles.models import AuthorSequence
            contributor.sequence = AuthorSequence.FIRST
        else:
            from doi_portal.articles.models import AuthorSequence
            contributor.sequence = AuthorSequence.ADDITIONAL
        contributor.save()
    else:
        response = render(request, "monographs/partials/_chapter_contributor_form.html", {
            "chapter": chapter,
            "contributor_form": form,
        })
        response["HX-Retarget"] = f"#chapter-{chapter.pk}-contributor-form-container"
        response["HX-Reswap"] = "innerHTML"
        return response

    return _render_chapter_contributor_list(request, chapter)


@login_required
@require_POST
def chapter_contributor_delete(request, pk):
    """Delete chapter contributor via HTMX POST, reorder remaining."""
    contributor = get_object_or_404(
        ChapterContributor.objects.select_related(
            "chapter", "chapter__monograph", "chapter__monograph__publisher"
        ),
        pk=pk,
    )
    _check_monograph_permission(request.user, contributor.chapter.monograph)
    chapter = contributor.chapter
    contributor.delete()

    from doi_portal.articles.models import AuthorSequence
    remaining = chapter.contributors.order_by("order")
    for index, c in enumerate(remaining, start=1):
        ChapterContributor.objects.filter(pk=c.pk).update(
            order=index,
            sequence=AuthorSequence.FIRST if index == 1 else AuthorSequence.ADDITIONAL,
        )

    return _render_chapter_contributor_list(request, chapter)


@login_required
@require_POST
def chapter_contributor_reorder(request, chapter_pk):
    """Reorder chapter contributors via HTMX POST."""
    chapter = get_object_or_404(
        MonographChapter.objects.select_related("monograph", "monograph__publisher"),
        pk=chapter_pk,
    )
    _check_monograph_permission(request.user, chapter.monograph)

    try:
        order_data = json.loads(request.body)
    except (json.JSONDecodeError, ValueError):
        order_data = {}

    order_list = order_data.get("order", [])
    if not isinstance(order_list, list):
        order_list = []

    from doi_portal.articles.models import AuthorSequence
    for index, cpk in enumerate(order_list, start=1):
        if not isinstance(cpk, int):
            continue
        ChapterContributor.objects.filter(pk=cpk, chapter=chapter).update(
            order=index,
            sequence=AuthorSequence.FIRST if index == 1 else AuthorSequence.ADDITIONAL,
        )

    return _render_chapter_contributor_list(request, chapter)


@login_required
@require_GET
def chapter_contributor_form_view(request, chapter_pk):
    """Return empty chapter contributor form via HTMX GET."""
    chapter = get_object_or_404(
        MonographChapter.objects.select_related("monograph", "monograph__publisher"),
        pk=chapter_pk,
    )
    _check_monograph_permission(request.user, chapter.monograph)
    form = ChapterContributorForm()
    return render(request, "monographs/partials/_chapter_contributor_form.html", {
        "chapter": chapter,
        "contributor_form": form,
    })


@login_required
@require_GET
def chapter_contributor_edit_form_view(request, pk):
    """Return pre-filled chapter contributor form via HTMX GET."""
    contributor = get_object_or_404(
        ChapterContributor.objects.select_related(
            "chapter", "chapter__monograph", "chapter__monograph__publisher"
        ),
        pk=pk,
    )
    _check_monograph_permission(request.user, contributor.chapter.monograph)
    form = ChapterContributorForm(instance=contributor)
    return render(request, "monographs/partials/_chapter_contributor_form.html", {
        "chapter": contributor.chapter,
        "contributor_form": form,
        "contributor": contributor,
    })


@login_required
@require_POST
def chapter_contributor_update(request, pk):
    """Update chapter contributor via HTMX POST."""
    contributor = get_object_or_404(
        ChapterContributor.objects.select_related(
            "chapter", "chapter__monograph", "chapter__monograph__publisher"
        ),
        pk=pk,
    )
    _check_monograph_permission(request.user, contributor.chapter.monograph)

    form = ChapterContributorForm(request.POST, instance=contributor)
    if form.is_valid():
        form.save()
    else:
        response = render(request, "monographs/partials/_chapter_contributor_form.html", {
            "chapter": contributor.chapter,
            "contributor_form": form,
            "contributor": contributor,
        })
        response["HX-Retarget"] = f"#chapter-{contributor.chapter.pk}-contributor-form-container"
        response["HX-Reswap"] = "innerHTML"
        return response

    return _render_chapter_contributor_list(request, contributor.chapter)


# =============================================================================
# HTMX FBV: Chapter-level Affiliations
# =============================================================================


@login_required
@require_POST
def chapter_affiliation_add(request, contributor_pk):
    """Add affiliation to chapter contributor via HTMX POST."""
    contributor = get_object_or_404(
        ChapterContributor.objects.select_related(
            "chapter", "chapter__monograph", "chapter__monograph__publisher"
        ),
        pk=contributor_pk,
    )
    _check_monograph_permission(request.user, contributor.chapter.monograph)

    form = ChapterAffiliationForm(request.POST)
    if form.is_valid():
        affiliation = form.save(commit=False)
        affiliation.contributor = contributor
        max_order = contributor.affiliations.aggregate(m=models.Max("order"))["m"] or 0
        affiliation.order = max_order + 1
        affiliation.save()
    else:
        response = render(request, "monographs/partials/_chapter_affiliation_form.html", {
            "contributor": contributor,
            "affiliation_form": form,
        })
        response["HX-Retarget"] = f"#chapter-{contributor.chapter.pk}-contributor-form-container"
        response["HX-Reswap"] = "innerHTML"
        return response

    return _render_chapter_contributor_list(request, contributor.chapter)


@login_required
@require_POST
def chapter_affiliation_delete(request, pk):
    """Delete chapter affiliation via HTMX POST."""
    affiliation = get_object_or_404(
        ChapterAffiliation.objects.select_related(
            "contributor", "contributor__chapter",
            "contributor__chapter__monograph", "contributor__chapter__monograph__publisher"
        ),
        pk=pk,
    )
    _check_monograph_permission(request.user, affiliation.contributor.chapter.monograph)
    chapter = affiliation.contributor.chapter
    affiliation.delete()
    return _render_chapter_contributor_list(request, chapter)


@login_required
@require_GET
def chapter_affiliation_form_view(request, contributor_pk):
    """Return empty chapter affiliation form via HTMX GET."""
    contributor = get_object_or_404(
        ChapterContributor.objects.select_related(
            "chapter", "chapter__monograph", "chapter__monograph__publisher"
        ),
        pk=contributor_pk,
    )
    _check_monograph_permission(request.user, contributor.chapter.monograph)
    form = ChapterAffiliationForm()
    return render(request, "monographs/partials/_chapter_affiliation_form.html", {
        "contributor": contributor,
        "affiliation_form": form,
    })


@login_required
@require_GET
def chapter_affiliation_edit_form_view(request, pk):
    """Return pre-filled chapter affiliation form via HTMX GET."""
    affiliation = get_object_or_404(
        ChapterAffiliation.objects.select_related(
            "contributor", "contributor__chapter",
            "contributor__chapter__monograph", "contributor__chapter__monograph__publisher"
        ),
        pk=pk,
    )
    _check_monograph_permission(request.user, affiliation.contributor.chapter.monograph)
    form = ChapterAffiliationForm(instance=affiliation)
    return render(request, "monographs/partials/_chapter_affiliation_form.html", {
        "contributor": affiliation.contributor,
        "affiliation_form": form,
        "affiliation": affiliation,
    })


@login_required
@require_POST
def chapter_affiliation_update(request, pk):
    """Update chapter affiliation via HTMX POST."""
    affiliation = get_object_or_404(
        ChapterAffiliation.objects.select_related(
            "contributor", "contributor__chapter",
            "contributor__chapter__monograph", "contributor__chapter__monograph__publisher"
        ),
        pk=pk,
    )
    _check_monograph_permission(request.user, affiliation.contributor.chapter.monograph)

    form = ChapterAffiliationForm(request.POST, instance=affiliation)
    if form.is_valid():
        form.save()
    else:
        response = render(request, "monographs/partials/_chapter_affiliation_form.html", {
            "contributor": affiliation.contributor,
            "affiliation_form": form,
            "affiliation": affiliation,
        })
        response["HX-Retarget"] = f"#chapter-{affiliation.contributor.chapter.pk}-contributor-form-container"
        response["HX-Reswap"] = "innerHTML"
        return response

    return _render_chapter_contributor_list(request, affiliation.contributor.chapter)


# =============================================================================
# HTMX FBV: Chapter-level Funding
# =============================================================================


def _render_chapter_funding_list(request, chapter):
    """Helper: render chapter funding list partial."""
    fundings = chapter.fundings.all()
    return render(request, "monographs/partials/_chapter_funding_list.html", {
        "chapter": chapter,
        "fundings": fundings,
    })


@login_required
@require_POST
def chapter_funding_add(request, chapter_pk):
    """Add funding to chapter via HTMX POST."""
    chapter = get_object_or_404(
        MonographChapter.objects.select_related("monograph", "monograph__publisher"),
        pk=chapter_pk,
    )
    _check_monograph_permission(request.user, chapter.monograph)

    form = ChapterFundingForm(request.POST)
    if form.is_valid():
        funding = form.save(commit=False)
        funding.chapter = chapter
        max_order = chapter.fundings.aggregate(m=models.Max("order"))["m"] or 0
        funding.order = max_order + 1
        funding.save()
    else:
        response = render(request, "monographs/partials/_chapter_funding_form.html", {
            "chapter": chapter,
            "funding_form": form,
        })
        response["HX-Retarget"] = f"#chapter-{chapter.pk}-funding-form-container"
        response["HX-Reswap"] = "innerHTML"
        return response

    return _render_chapter_funding_list(request, chapter)


@login_required
@require_POST
def chapter_funding_delete(request, pk):
    """Delete chapter funding via HTMX POST."""
    funding = get_object_or_404(
        ChapterFunding.objects.select_related(
            "chapter", "chapter__monograph", "chapter__monograph__publisher"
        ),
        pk=pk,
    )
    _check_monograph_permission(request.user, funding.chapter.monograph)
    chapter = funding.chapter
    funding.delete()
    return _render_chapter_funding_list(request, chapter)


@login_required
@require_POST
def chapter_funding_reorder(request, chapter_pk):
    """Reorder chapter funding via HTMX POST."""
    chapter = get_object_or_404(
        MonographChapter.objects.select_related("monograph", "monograph__publisher"),
        pk=chapter_pk,
    )
    _check_monograph_permission(request.user, chapter.monograph)

    try:
        order_data = json.loads(request.body)
    except (json.JSONDecodeError, ValueError):
        order_data = {}

    order_list = order_data.get("order", [])
    if not isinstance(order_list, list):
        order_list = []

    for index, fpk in enumerate(order_list, start=1):
        if not isinstance(fpk, int):
            continue
        ChapterFunding.objects.filter(pk=fpk, chapter=chapter).update(order=index)

    return _render_chapter_funding_list(request, chapter)


@login_required
@require_GET
def chapter_funding_form_view(request, chapter_pk):
    """Return empty chapter funding form via HTMX GET."""
    chapter = get_object_or_404(
        MonographChapter.objects.select_related("monograph", "monograph__publisher"),
        pk=chapter_pk,
    )
    _check_monograph_permission(request.user, chapter.monograph)
    form = ChapterFundingForm()
    return render(request, "monographs/partials/_chapter_funding_form.html", {
        "chapter": chapter,
        "funding_form": form,
    })


# =============================================================================
# HTMX FBV: Chapter-level Relations
# =============================================================================


def _render_chapter_relation_list(request, chapter):
    """Helper: render chapter relation list partial."""
    relations = chapter.relations.all()
    return render(request, "monographs/partials/_chapter_relation_list.html", {
        "chapter": chapter,
        "relations": relations,
    })


@login_required
@require_POST
def chapter_relation_add(request, chapter_pk):
    """Add relation to chapter via HTMX POST."""
    chapter = get_object_or_404(
        MonographChapter.objects.select_related("monograph", "monograph__publisher"),
        pk=chapter_pk,
    )
    _check_monograph_permission(request.user, chapter.monograph)

    form = ChapterRelationForm(request.POST)
    if form.is_valid():
        relation = form.save(commit=False)
        relation.chapter = chapter
        max_order = chapter.relations.aggregate(m=models.Max("order"))["m"] or 0
        relation.order = max_order + 1
        relation.save()
    else:
        response = render(request, "monographs/partials/_chapter_relation_form.html", {
            "chapter": chapter,
            "relation_form": form,
        })
        response["HX-Retarget"] = f"#chapter-{chapter.pk}-relation-form-container"
        response["HX-Reswap"] = "innerHTML"
        return response

    return _render_chapter_relation_list(request, chapter)


@login_required
@require_POST
def chapter_relation_delete(request, pk):
    """Delete chapter relation via HTMX POST."""
    relation = get_object_or_404(
        ChapterRelation.objects.select_related(
            "chapter", "chapter__monograph", "chapter__monograph__publisher"
        ),
        pk=pk,
    )
    _check_monograph_permission(request.user, relation.chapter.monograph)
    chapter = relation.chapter
    relation.delete()
    return _render_chapter_relation_list(request, chapter)


@login_required
@require_POST
def chapter_relation_reorder(request, chapter_pk):
    """Reorder chapter relations via HTMX POST."""
    chapter = get_object_or_404(
        MonographChapter.objects.select_related("monograph", "monograph__publisher"),
        pk=chapter_pk,
    )
    _check_monograph_permission(request.user, chapter.monograph)

    try:
        order_data = json.loads(request.body)
    except (json.JSONDecodeError, ValueError):
        order_data = {}

    order_list = order_data.get("order", [])
    if not isinstance(order_list, list):
        order_list = []

    for index, rpk in enumerate(order_list, start=1):
        if not isinstance(rpk, int):
            continue
        ChapterRelation.objects.filter(pk=rpk, chapter=chapter).update(order=index)

    return _render_chapter_relation_list(request, chapter)


@login_required
@require_GET
def chapter_relation_form_view(request, chapter_pk):
    """Return empty chapter relation form via HTMX GET."""
    chapter = get_object_or_404(
        MonographChapter.objects.select_related("monograph", "monograph__publisher"),
        pk=chapter_pk,
    )
    _check_monograph_permission(request.user, chapter.monograph)
    form = ChapterRelationForm()
    return render(request, "monographs/partials/_chapter_relation_form.html", {
        "chapter": chapter,
        "relation_form": form,
    })
