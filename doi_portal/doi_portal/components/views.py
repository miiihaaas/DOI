"""
Component views for DOI Portal.

CRUD views for ComponentGroup, Component, and HTMX contributor management.
"""

import json
import logging

from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db import models
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, render
from django.urls import reverse, reverse_lazy
from django.views.decorators.http import require_GET, require_POST
from django.views.generic import (
    CreateView,
    DeleteView,
    DetailView,
    ListView,
    UpdateView,
)

from doi_portal.articles.models import AuthorSequence
from doi_portal.core.permissions import has_publisher_access
from doi_portal.publishers.mixins import (
    AdministratorRequiredMixin,
    PublisherScopedEditMixin,
    PublisherScopedMixin,
)

from .forms import ComponentContributorForm, ComponentForm, ComponentGroupForm
from .models import Component, ComponentContributor, ComponentGroup

logger = logging.getLogger(__name__)


# =============================================================================
# Publisher scoping helper for HTMX FBV views
# =============================================================================


def _check_component_permission(user, component):
    """Check if user has permission to modify this component."""
    if not has_publisher_access(user, component.component_group.publisher):
        raise PermissionDenied


def _check_contributor_permission(user, contributor):
    """Check if user has permission to modify this contributor."""
    if not has_publisher_access(user, contributor.component.component_group.publisher):
        raise PermissionDenied


# =============================================================================
# ComponentGroup CRUD Views
# =============================================================================


class ComponentGroupListView(PublisherScopedMixin, ListView):
    """List ComponentGroups for the current publisher."""

    model = ComponentGroup
    template_name = "component_groups/component_group_list.html"
    context_object_name = "component_groups"
    paginate_by = 20

    def get_queryset(self):
        return self.get_scoped_queryset(
            ComponentGroup.objects.select_related("publisher").all()
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["breadcrumbs"] = [
            {"label": "Komponente", "url": ""},
        ]
        return context


class ComponentGroupCreateView(PublisherScopedEditMixin, CreateView):
    """Create a new ComponentGroup."""

    model = ComponentGroup
    form_class = ComponentGroupForm
    template_name = "component_groups/component_group_form.html"

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def get_success_url(self):
        return reverse("components:group-detail", args=[self.object.pk])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["breadcrumbs"] = [
            {"label": "Komponente", "url": reverse("components:group-list")},
            {"label": "Nova grupa", "url": ""},
        ]
        context["form_title"] = "Nova grupa komponenti"
        return context


class ComponentGroupDetailView(PublisherScopedMixin, DetailView):
    """Display ComponentGroup details with component list."""

    model = ComponentGroup
    template_name = "component_groups/component_group_detail.html"
    context_object_name = "component_group"

    def get_queryset(self):
        return ComponentGroup.objects.select_related("publisher").all()

    def get_object(self, queryset=None):
        obj = super().get_object(queryset)
        if not has_publisher_access(self.request.user, obj.publisher):
            raise PermissionDenied
        return obj

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["components"] = self.object.components.filter(is_deleted=False).order_by("order")
        context["breadcrumbs"] = [
            {"label": "Komponente", "url": reverse("components:group-list")},
            {"label": str(self.object), "url": ""},
        ]
        return context


class ComponentGroupUpdateView(PublisherScopedEditMixin, UpdateView):
    """Edit ComponentGroup metadata."""

    model = ComponentGroup
    form_class = ComponentGroupForm
    template_name = "component_groups/component_group_form.html"

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def get_object(self, queryset=None):
        obj = super().get_object(queryset)
        if not has_publisher_access(self.request.user, obj.publisher):
            raise PermissionDenied
        return obj

    def get_success_url(self):
        return reverse("components:group-detail", args=[self.object.pk])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["breadcrumbs"] = [
            {"label": "Komponente", "url": reverse("components:group-list")},
            {"label": str(self.object), "url": reverse("components:group-detail", args=[self.object.pk])},
            {"label": "Izmena", "url": ""},
        ]
        context["form_title"] = "Izmena grupe komponenti"
        return context


class ComponentGroupDeleteView(AdministratorRequiredMixin, PublisherScopedEditMixin, DeleteView):
    """Soft delete a ComponentGroup."""

    model = ComponentGroup
    template_name = "component_groups/component_group_confirm_delete.html"
    success_url = reverse_lazy("components:group-list")

    def get_object(self, queryset=None):
        obj = super().get_object(queryset)
        if not has_publisher_access(self.request.user, obj.publisher):
            raise PermissionDenied
        return obj

    def form_valid(self, form):
        self.object = self.get_object()
        self.object.soft_delete(user=self.request.user)
        return HttpResponse(status=302, headers={"Location": self.success_url})


# =============================================================================
# Component CRUD Views (within ComponentGroup)
# =============================================================================


class ComponentCreateView(PublisherScopedEditMixin, CreateView):
    """Create a new Component within a ComponentGroup."""

    model = Component
    form_class = ComponentForm
    template_name = "component_groups/component_form.html"

    def dispatch(self, request, *args, **kwargs):
        self.component_group = get_object_or_404(
            ComponentGroup.objects.select_related("publisher"),
            pk=kwargs["group_pk"],
        )
        if not has_publisher_access(request.user, self.component_group.publisher):
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        form.instance.component_group = self.component_group
        return super().form_valid(form)

    def get_success_url(self):
        return reverse("components:group-detail", args=[self.component_group.pk])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["component_group"] = self.component_group
        context["breadcrumbs"] = [
            {"label": "Komponente", "url": reverse("components:group-list")},
            {"label": str(self.component_group), "url": reverse("components:group-detail", args=[self.component_group.pk])},
            {"label": "Nova komponenta", "url": ""},
        ]
        context["form_title"] = "Nova komponenta"
        return context


class ComponentDetailView(PublisherScopedMixin, DetailView):
    """Display Component details with contributor list."""

    model = Component
    template_name = "component_groups/component_detail.html"
    context_object_name = "component"

    def get_queryset(self):
        return Component.objects.select_related(
            "component_group", "component_group__publisher"
        ).all()

    def get_object(self, queryset=None):
        obj = super().get_object(queryset)
        if not has_publisher_access(self.request.user, obj.component_group.publisher):
            raise PermissionDenied
        return obj

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["component_group"] = self.object.component_group
        context["contributors"] = self.object.contributors.filter(is_deleted=False).order_by("order")
        context["contributor_form"] = ComponentContributorForm()
        context["breadcrumbs"] = [
            {"label": "Komponente", "url": reverse("components:group-list")},
            {"label": str(self.object.component_group), "url": reverse("components:group-detail", args=[self.object.component_group.pk])},
            {"label": str(self.object), "url": ""},
        ]
        return context


class ComponentUpdateView(PublisherScopedEditMixin, UpdateView):
    """Edit Component fields."""

    model = Component
    form_class = ComponentForm
    template_name = "component_groups/component_form.html"

    def get_queryset(self):
        return Component.objects.select_related(
            "component_group", "component_group__publisher"
        ).all()

    def get_object(self, queryset=None):
        obj = super().get_object(queryset)
        if not has_publisher_access(self.request.user, obj.component_group.publisher):
            raise PermissionDenied
        return obj

    def get_success_url(self):
        return reverse(
            "components:component-detail",
            args=[self.object.component_group.pk, self.object.pk],
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["component_group"] = self.object.component_group
        context["breadcrumbs"] = [
            {"label": "Komponente", "url": reverse("components:group-list")},
            {"label": str(self.object.component_group), "url": reverse("components:group-detail", args=[self.object.component_group.pk])},
            {"label": str(self.object), "url": reverse("components:component-detail", args=[self.object.component_group.pk, self.object.pk])},
            {"label": "Izmena", "url": ""},
        ]
        context["form_title"] = "Izmena komponente"
        return context


class ComponentDeleteView(PublisherScopedEditMixin, DeleteView):
    """Soft delete a Component."""

    model = Component
    template_name = "component_groups/component_confirm_delete.html"

    def get_queryset(self):
        return Component.objects.select_related(
            "component_group", "component_group__publisher"
        ).all()

    def get_object(self, queryset=None):
        obj = super().get_object(queryset)
        if not has_publisher_access(self.request.user, obj.component_group.publisher):
            raise PermissionDenied
        return obj

    def get_success_url(self):
        return reverse("components:group-detail", args=[self.object.component_group.pk])

    def form_valid(self, form):
        self.object = self.get_object()
        success_url = self.get_success_url()
        self.object.soft_delete(user=self.request.user)
        return HttpResponse(status=302, headers={"Location": success_url})


# =============================================================================
# HTMX Contributor Management (FBV)
# =============================================================================


@login_required
@require_POST
def contributor_add(request, component_pk):
    """Add contributor to component via HTMX POST."""
    component = get_object_or_404(
        Component.objects.select_related(
            "component_group", "component_group__publisher"
        ),
        pk=component_pk,
    )
    _check_component_permission(request.user, component)

    form = ComponentContributorForm(request.POST)
    if form.is_valid():
        contributor = form.save(commit=False)
        contributor.component = component
        # Auto-set order to next available
        max_order = component.contributors.aggregate(
            max_order=models.Max("order")
        )["max_order"] or 0
        contributor.order = max_order + 1
        # Auto-set sequence
        if contributor.order == 1:
            contributor.sequence = AuthorSequence.FIRST
        else:
            contributor.sequence = AuthorSequence.ADDITIONAL
        contributor.save()
    else:
        response = render(request, "component_groups/partials/_contributor_form.html", {
            "component": component,
            "contributor_form": form,
        })
        response["HX-Retarget"] = "#contributor-form-container"
        response["HX-Reswap"] = "innerHTML"
        return response

    contributors = component.contributors.filter(is_deleted=False).order_by("order")
    return render(request, "component_groups/partials/_contributor_list.html", {
        "component": component,
        "contributors": contributors,
        "contributor_form": ComponentContributorForm(),
    })


@login_required
@require_POST
def contributor_update(request, contributor_pk):
    """Update contributor via HTMX POST."""
    contributor = get_object_or_404(
        ComponentContributor.objects.select_related(
            "component", "component__component_group",
            "component__component_group__publisher",
        ),
        pk=contributor_pk,
    )
    _check_contributor_permission(request.user, contributor)

    form = ComponentContributorForm(request.POST, instance=contributor)
    if form.is_valid():
        form.save()
    else:
        response = render(request, "component_groups/partials/_contributor_form.html", {
            "component": contributor.component,
            "contributor_form": form,
            "contributor": contributor,
        })
        response["HX-Retarget"] = "#contributor-form-container"
        response["HX-Reswap"] = "innerHTML"
        return response

    component = contributor.component
    contributors = component.contributors.filter(is_deleted=False).order_by("order")
    return render(request, "component_groups/partials/_contributor_list.html", {
        "component": component,
        "contributors": contributors,
        "contributor_form": ComponentContributorForm(),
    })


@login_required
@require_POST
def contributor_delete(request, contributor_pk):
    """Delete contributor via HTMX POST."""
    contributor = get_object_or_404(
        ComponentContributor.objects.select_related(
            "component", "component__component_group",
            "component__component_group__publisher",
        ),
        pk=contributor_pk,
    )
    _check_contributor_permission(request.user, contributor)

    component = contributor.component
    contributor.delete()

    # Re-order remaining contributors
    remaining = component.contributors.filter(is_deleted=False).order_by("order")
    for index, c in enumerate(remaining, start=1):
        ComponentContributor.objects.filter(pk=c.pk).update(
            order=index,
            sequence=AuthorSequence.FIRST if index == 1 else AuthorSequence.ADDITIONAL,
        )

    contributors = component.contributors.filter(is_deleted=False).order_by("order")
    return render(request, "component_groups/partials/_contributor_list.html", {
        "component": component,
        "contributors": contributors,
        "contributor_form": ComponentContributorForm(),
    })


@login_required
@require_POST
def contributor_reorder(request, component_pk):
    """Reorder contributors via HTMX POST (drag & drop)."""
    component = get_object_or_404(
        Component.objects.select_related(
            "component_group", "component_group__publisher"
        ),
        pk=component_pk,
    )
    _check_component_permission(request.user, component)

    try:
        order_data = json.loads(request.body)
    except (json.JSONDecodeError, ValueError):
        order_data = {}

    order_list = order_data.get("order", [])
    if not isinstance(order_list, list):
        order_list = []

    for index, contributor_pk in enumerate(order_list, start=1):
        if not isinstance(contributor_pk, int):
            continue
        ComponentContributor.objects.filter(pk=contributor_pk, component=component).update(
            order=index,
            sequence=AuthorSequence.FIRST if index == 1 else AuthorSequence.ADDITIONAL,
        )

    contributors = component.contributors.filter(is_deleted=False).order_by("order")
    return render(request, "component_groups/partials/_contributor_list.html", {
        "component": component,
        "contributors": contributors,
        "contributor_form": ComponentContributorForm(),
    })


@login_required
@require_GET
def contributor_form_view(request, component_pk):
    """Return empty contributor form for inline editing via HTMX GET."""
    component = get_object_or_404(
        Component.objects.select_related(
            "component_group", "component_group__publisher"
        ),
        pk=component_pk,
    )
    _check_component_permission(request.user, component)

    form = ComponentContributorForm()
    return render(request, "component_groups/partials/_contributor_form.html", {
        "component": component,
        "contributor_form": form,
    })


@login_required
@require_GET
def contributor_edit_form_view(request, contributor_pk):
    """Return pre-filled contributor form for editing via HTMX GET."""
    contributor = get_object_or_404(
        ComponentContributor.objects.select_related(
            "component", "component__component_group",
            "component__component_group__publisher",
        ),
        pk=contributor_pk,
    )
    _check_contributor_permission(request.user, contributor)

    form = ComponentContributorForm(instance=contributor)
    return render(request, "component_groups/partials/_contributor_form.html", {
        "component": contributor.component,
        "contributor_form": form,
        "contributor": contributor,
    })
