"""
Issue views for DOI Portal.

Story 2.6: Issue admin CRUD views with row-level permissions.
"""

from django.contrib import messages
from django.http import HttpResponseRedirect
from django.urls import reverse, reverse_lazy
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

from doi_portal.core.terminology import get_issue_delete_warning, get_term
from doi_portal.publications.models import Publication, PublicationType

from .forms import IssueForm
from .models import Issue, IssueStatus


def _get_pub_type_from_publication_id(publication_id):
    """Get publication_type from publication_id query param. Returns JOURNAL as fallback."""
    if publication_id:
        try:
            pub = Publication.objects.get(pk=publication_id)
            return pub.publication_type
        except Publication.DoesNotExist:
            pass
    return PublicationType.JOURNAL


# Whitelist of allowed sort fields
ALLOWED_SORT_FIELDS = {
    "volume": "volume",
    "year": "year",
    "status": "status",
    "issue_number": "issue_number",
}


class IssueListView(PublisherScopedMixin, ListView):
    """
    List all issues with filtering, sorting, and role-based scoping.

    AC: #3 - Displays list with columns: volume, issue_number, year, status badge,
    article count, cover thumbnail.
    AC: #7, #8 - Publisher scoping for Urednik/Bibliotekar, full access for Admin.
    """

    model = Issue
    template_name = "issues/issue_list.html"
    context_object_name = "issues"
    paginate_by = 20

    def get_scoped_queryset(self, queryset):
        """Override to scope via publication__publisher (Issue has no direct publisher FK)."""
        flags = self._get_user_role_flags()
        if flags["is_admin"]:
            return queryset
        if flags["has_publisher"]:
            return queryset.filter(
                publication__publisher=self.request.user.publisher
            )
        return queryset.none()

    def get_queryset(self):
        """Filter issues by publication, status; apply sorting and scoping."""
        queryset = super().get_queryset().select_related(
            "publication", "publication__publisher"
        )

        # Scope by publisher
        queryset = self.get_scoped_queryset(queryset)

        # Filter by publication
        publication_id = self.request.GET.get("publication")
        if publication_id:
            queryset = queryset.filter(publication_id=publication_id)

        # Filter by status
        status = self.request.GET.get("status")
        if status and status in [choice[0] for choice in IssueStatus.choices]:
            queryset = queryset.filter(status=status)

        # Sorting
        sort_field = self.request.GET.get("sort", "year")
        order = self.request.GET.get("order", "desc")
        db_field = ALLOWED_SORT_FIELDS.get(sort_field, "year")
        if order == "desc":
            db_field = f"-{db_field}"
        queryset = queryset.order_by(db_field)

        return queryset

    def get_context_data(self, **kwargs):
        """Add breadcrumbs, filter options, sort state to context."""
        context = super().get_context_data(**kwargs)

        # Determine if filtered by publication
        publication_id = self.request.GET.get("publication")
        publication = None
        if publication_id:
            try:
                publication = Publication.objects.select_related("publisher").get(
                    pk=publication_id
                )
            except (Publication.DoesNotExist, ValueError):
                pass

        if publication:
            pub_type = publication.publication_type
        else:
            pub_type = PublicationType.JOURNAL
        context["pub_type"] = pub_type

        if publication:
            context["breadcrumbs"] = [
                {"label": "Kontrolna tabla", "url": reverse_lazy("dashboard")},
                {"label": "Publikacije", "url": reverse_lazy("publications:list")},
                {
                    "label": publication.title,
                    "url": reverse(
                        "publications:detail", kwargs={"slug": publication.slug}
                    ),
                },
                {"label": get_term("issue_plural", pub_type), "url": None},
            ]
        else:
            context["breadcrumbs"] = [
                {"label": "Kontrolna tabla", "url": reverse_lazy("dashboard")},
                {"label": get_term("issue_plural", pub_type), "url": None},
            ]

        context["publication"] = publication
        context["status_choices"] = IssueStatus.choices
        context["current_status"] = self.request.GET.get("status", "")
        context["current_publication"] = self.request.GET.get("publication", "")
        context["current_sort"] = self.request.GET.get("sort", "year")
        context["current_order"] = self.request.GET.get("order", "desc")

        # Role-based action visibility
        flags = self._get_user_role_flags()
        context["can_create"] = flags["is_admin"] or flags["is_urednik"]
        context["can_edit"] = flags["is_admin"] or flags["is_urednik"]
        context["can_delete"] = flags["is_admin"]

        return context


class IssueCreateView(PublisherScopedEditMixin, CreateView):
    """
    Create a new issue.

    AC: #4, #5 - Form with publication scoping, DRAFT default status.
    AC: #7 - Urednik can create only for assigned publisher's publications.
    AC: #8 - Administrator can create for any publication.
    """

    model = Issue
    form_class = IssueForm
    template_name = "issues/issue_form.html"
    success_url = reverse_lazy("issues:list")

    def get_scoped_queryset(self, queryset):
        """Override to scope via publication__publisher."""
        flags = self._get_user_role_flags()
        if flags["is_admin"]:
            return queryset
        if flags["has_publisher"]:
            return queryset.filter(
                publication__publisher=self.request.user.publisher
            )
        return queryset.none()

    def get_form_kwargs(self):
        """Pass user to form for publication queryset scoping."""
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def get_initial(self):
        """Pre-select publication if publication_id in query params."""
        initial = super().get_initial()
        publication_id = self.request.GET.get("publication")
        if publication_id:
            initial["publication"] = publication_id
        return initial

    def get_context_data(self, **kwargs):
        """Add breadcrumbs and form metadata to context."""
        context = super().get_context_data(**kwargs)
        publication_id = self.request.GET.get("publication")
        pub_type = _get_pub_type_from_publication_id(publication_id)
        context["pub_type"] = pub_type
        context["breadcrumbs"] = [
            {"label": "Kontrolna tabla", "url": reverse_lazy("dashboard")},
            {"label": get_term("issue_plural", pub_type), "url": reverse_lazy("issues:list")},
            {"label": get_term("new_issue", pub_type), "url": None},
        ]
        context["form_title"] = get_term("new_issue", pub_type)
        context["submit_text"] = get_term("create_issue", pub_type)
        context["pub_doi_prefix_map_json"] = context["form"].pub_doi_prefix_map_json
        return context

    def form_valid(self, form):
        """Show success message on valid submission."""
        response = super().form_valid(form)
        messages.success(
            self.request,
            get_term("issue_created", self.object.publication.publication_type),
        )
        return response

    def get_success_url(self):
        """Redirect to issue list, optionally filtered by publication."""
        publication_id = self.object.publication_id
        return f"{reverse('issues:list')}?publication={publication_id}"


class IssueUpdateView(PublisherScopedEditMixin, UpdateView):
    """
    Update an existing issue.

    AC: #6 - Status changes are recorded in audit log.
    AC: #7 - Urednik can edit only their publisher's issues.
    AC: #8 - Administrator can edit all issues.
    """

    model = Issue
    form_class = IssueForm
    template_name = "issues/issue_form.html"
    success_url = reverse_lazy("issues:list")

    def get_scoped_queryset(self, queryset):
        """Override to scope via publication__publisher."""
        flags = self._get_user_role_flags()
        if flags["is_admin"]:
            return queryset
        if flags["has_publisher"]:
            return queryset.filter(
                publication__publisher=self.request.user.publisher
            )
        return queryset.none()

    def get_queryset(self):
        """Scope queryset to user's publisher for non-admin roles."""
        queryset = super().get_queryset().select_related(
            "publication", "publication__publisher"
        )
        return self.get_scoped_queryset(queryset)

    def get_form_kwargs(self):
        """Pass user to form for publication queryset scoping."""
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def get_context_data(self, **kwargs):
        """Add breadcrumbs and form metadata to context."""
        context = super().get_context_data(**kwargs)
        pub_type = self.object.publication.publication_type
        context["pub_type"] = pub_type
        context["breadcrumbs"] = [
            {"label": "Kontrolna tabla", "url": reverse_lazy("dashboard")},
            {"label": get_term("issue_plural", pub_type), "url": reverse_lazy("issues:list")},
            {"label": str(self.object), "url": None},
        ]
        context["form_title"] = f"{get_term('edit_issue', pub_type)}: {self.object}"
        context["submit_text"] = "Sačuvaj izmene"
        context["pub_doi_prefix_map_json"] = context["form"].pub_doi_prefix_map_json
        # For edit, also provide publisher_doi_prefix directly
        context["publisher_doi_prefix"] = self.object.publication.publisher.doi_prefix
        return context

    def form_valid(self, form):
        """Show success message on valid submission."""
        response = super().form_valid(form)
        messages.success(
            self.request,
            get_term("issue_updated", self.object.publication.publication_type),
        )
        return response

    def get_success_url(self):
        """Redirect to issue list filtered by publication."""
        publication_id = self.object.publication_id
        return f"{reverse('issues:list')}?publication={publication_id}"


class IssueDetailView(PublisherScopedMixin, DetailView):
    """
    View issue details.

    AC: #3 - Displays all issue data with status badge.
    AC: #7, #8 - Scoped by publisher for Urednik/Bibliotekar.
    """

    model = Issue
    template_name = "issues/issue_detail.html"
    context_object_name = "issue"

    def get_scoped_queryset(self, queryset):
        """Override to scope via publication__publisher."""
        flags = self._get_user_role_flags()
        if flags["is_admin"]:
            return queryset
        if flags["has_publisher"]:
            return queryset.filter(
                publication__publisher=self.request.user.publisher
            )
        return queryset.none()

    def get_queryset(self):
        """Scope queryset to user's publisher for non-admin roles."""
        queryset = super().get_queryset().select_related(
            "publication", "publication__publisher"
        ).prefetch_related(
            "articles__authors"  # Prefetch articles and their authors to avoid N+1
        )
        return self.get_scoped_queryset(queryset)

    def get_context_data(self, **kwargs):
        """Add breadcrumbs and role-based action flags to context."""
        context = super().get_context_data(**kwargs)
        pub_type = self.object.publication.publication_type
        context["pub_type"] = pub_type
        context["breadcrumbs"] = [
            {"label": "Kontrolna tabla", "url": reverse_lazy("dashboard")},
            {"label": get_term("issue_plural", pub_type), "url": reverse_lazy("issues:list")},
            {"label": str(self.object), "url": None},
        ]

        # Role-based action visibility
        flags = self._get_user_role_flags()
        context["can_edit"] = flags["is_admin"] or flags["is_urednik"]
        context["can_delete"] = flags["is_admin"]
        return context


class IssueDeleteView(AdministratorRequiredMixin, DeleteView):
    """
    Soft delete an issue.

    AC: #8 - Only Administrator/Superadmin can delete.
    """

    model = Issue
    template_name = "issues/issue_confirm_delete.html"
    success_url = reverse_lazy("issues:list")

    def get_queryset(self):
        """Include publication data for display."""
        return super().get_queryset().select_related(
            "publication", "publication__publisher"
        )

    def get_context_data(self, **kwargs):
        """Add breadcrumbs and article count to context."""
        context = super().get_context_data(**kwargs)
        pub_type = self.object.publication.publication_type
        context["pub_type"] = pub_type
        context["breadcrumbs"] = [
            {"label": "Kontrolna tabla", "url": reverse_lazy("dashboard")},
            {"label": get_term("issue_plural", pub_type), "url": reverse_lazy("issues:list")},
            {"label": str(self.object), "url": None},
        ]
        context["article_count"] = self.object.article_count
        return context

    def form_valid(self, form):
        """Perform soft delete instead of actual deletion."""
        issue = self.object
        article_count = issue.article_count
        pub_type = self.object.publication.publication_type

        if article_count > 0:
            messages.warning(
                self.request,
                get_issue_delete_warning(article_count, pub_type),
            )
        else:
            messages.success(
                self.request,
                get_term("issue_deleted", pub_type),
            )

        # Soft delete instead of actual delete
        issue.soft_delete(user=self.request.user)
        return HttpResponseRedirect(self.success_url)
