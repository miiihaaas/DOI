"""
Article views for DOI Portal.

Story 3.1: Article admin CRUD views with row-level permissions.
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

from .forms import ArticleForm
from .models import Article, ArticleStatus


class ArticleListView(PublisherScopedMixin, ListView):
    """
    List all articles with filtering and role-based scoping.

    AC: #5 - Displays list with title, issue, status, created date.
    Publisher scoping via issue__publication__publisher.
    """

    model = Article
    template_name = "articles/article_list.html"
    context_object_name = "articles"
    paginate_by = 20

    def get_scoped_queryset(self, queryset):
        """Override to scope via issue__publication__publisher (three-level relation)."""
        flags = self._get_user_role_flags()
        if flags["is_admin"]:
            return queryset
        if flags["has_publisher"]:
            return queryset.filter(
                issue__publication__publisher=self.request.user.publisher
            )
        return queryset.none()

    def get_queryset(self):
        """Filter articles by issue, status; apply scoping."""
        queryset = super().get_queryset().select_related(
            "issue", "issue__publication", "issue__publication__publisher", "created_by"
        )

        # Scope by publisher
        queryset = self.get_scoped_queryset(queryset)

        # Filter by issue
        issue_id = self.request.GET.get("issue")
        if issue_id:
            queryset = queryset.filter(issue_id=issue_id)

        # Filter by status
        status = self.request.GET.get("status")
        if status and status in [choice[0] for choice in ArticleStatus.choices]:
            queryset = queryset.filter(status=status)

        return queryset

    def get_context_data(self, **kwargs):
        """Add breadcrumbs, filter options to context."""
        context = super().get_context_data(**kwargs)

        context["breadcrumbs"] = [
            {"label": "Kontrolna tabla", "url": reverse_lazy("dashboard")},
            {"label": "Članci", "url": None},
        ]

        context["status_choices"] = ArticleStatus.choices
        context["current_status"] = self.request.GET.get("status", "")
        context["current_issue"] = self.request.GET.get("issue", "")

        # Role-based action visibility
        flags = self._get_user_role_flags()
        context["can_create"] = flags["is_admin"] or flags["is_urednik"] or flags["is_bibliotekar"]
        context["can_edit"] = flags["is_admin"] or flags["is_urednik"] or flags["is_bibliotekar"]
        context["can_delete"] = flags["is_admin"]

        return context


class ArticleCreateView(PublisherScopedEditMixin, CreateView):
    """
    Create a new article.

    AC: #2, #4 - Form with issue pre-selection, DRAFT default status, created_by auto-set.
    """

    model = Article
    form_class = ArticleForm
    template_name = "articles/article_form.html"

    def test_func(self):
        """Allow Bibliotekar to create articles (override PublisherScopedEditMixin)."""
        user = self.request.user
        if not user.is_authenticated:
            return False

        flags = self._get_user_role_flags()

        # Superuser/Administrator/Superadmin - full access
        if flags["is_admin"]:
            return True

        # Urednik can create
        if flags["is_urednik"]:
            return flags["has_publisher"]

        # Bibliotekar can also create articles
        if flags["is_bibliotekar"]:
            return flags["has_publisher"]

        return False

    def get_form_kwargs(self):
        """Pass user to form for issue queryset scoping."""
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def get_initial(self):
        """Pre-select issue if issue_id in query params."""
        initial = super().get_initial()
        issue_id = self.request.GET.get("issue")
        if issue_id:
            initial["issue"] = issue_id
        return initial

    def get_context_data(self, **kwargs):
        """Add breadcrumbs and form metadata to context."""
        context = super().get_context_data(**kwargs)
        context["breadcrumbs"] = [
            {"label": "Kontrolna tabla", "url": reverse_lazy("dashboard")},
            {"label": "Članci", "url": reverse_lazy("articles:list")},
            {"label": "Novi članak", "url": None},
        ]
        context["form_title"] = "Novi članak"
        context["submit_text"] = "Kreiraj članak"
        return context

    def form_valid(self, form):
        """Set created_by and show success message."""
        form.instance.created_by = self.request.user
        response = super().form_valid(form)
        messages.success(
            self.request,
            "Članak uspešno kreiran.",
        )
        return response

    def get_success_url(self):
        """Redirect to article edit page after creation."""
        return reverse("articles:update", kwargs={"pk": self.object.pk})


class ArticleUpdateView(PublisherScopedEditMixin, UpdateView):
    """
    Update an existing article.

    AC: #4 - Only DRAFT status allows edit.
    Bibliotekar can edit their own publisher's DRAFT articles.
    """

    model = Article
    form_class = ArticleForm
    template_name = "articles/article_form.html"

    def test_func(self):
        """Allow Bibliotekar to edit DRAFT articles (same as create permission)."""
        user = self.request.user
        if not user.is_authenticated:
            return False

        flags = self._get_user_role_flags()

        if flags["is_admin"]:
            return True

        if flags["is_urednik"]:
            return flags["has_publisher"]

        # Bibliotekar can edit DRAFT articles (queryset enforces DRAFT + scoping)
        if flags["is_bibliotekar"]:
            return flags["has_publisher"]

        return False

    def get_scoped_queryset(self, queryset):
        """Override to scope via issue__publication__publisher."""
        flags = self._get_user_role_flags()
        if flags["is_admin"]:
            return queryset
        if flags["has_publisher"]:
            return queryset.filter(
                issue__publication__publisher=self.request.user.publisher
            )
        return queryset.none()

    def get_queryset(self):
        """Scope queryset and restrict to DRAFT status for editing (AC #4)."""
        queryset = super().get_queryset().select_related(
            "issue", "issue__publication", "issue__publication__publisher"
        ).filter(status=ArticleStatus.DRAFT)
        return self.get_scoped_queryset(queryset)

    def get_form_kwargs(self):
        """Pass user to form for issue queryset scoping."""
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def get_context_data(self, **kwargs):
        """Add breadcrumbs and form metadata to context."""
        context = super().get_context_data(**kwargs)
        context["breadcrumbs"] = [
            {"label": "Kontrolna tabla", "url": reverse_lazy("dashboard")},
            {"label": "Članci", "url": reverse_lazy("articles:list")},
            {"label": str(self.object), "url": None},
        ]
        context["form_title"] = f"Izmeni članak: {self.object.title}"
        context["submit_text"] = "Sačuvaj izmene"
        context["is_edit"] = True
        return context

    def form_valid(self, form):
        """Show success message on valid submission."""
        response = super().form_valid(form)
        messages.success(
            self.request,
            "Članak uspešno ažuriran.",
        )
        return response

    def get_success_url(self):
        """Redirect to article edit page."""
        return reverse("articles:update", kwargs={"pk": self.object.pk})


class ArticleDetailView(PublisherScopedMixin, DetailView):
    """
    View article details.

    AC: #4 - Displays all metadata with status badge.
    """

    model = Article
    template_name = "articles/article_detail.html"
    context_object_name = "article"

    def get_scoped_queryset(self, queryset):
        """Override to scope via issue__publication__publisher."""
        flags = self._get_user_role_flags()
        if flags["is_admin"]:
            return queryset
        if flags["has_publisher"]:
            return queryset.filter(
                issue__publication__publisher=self.request.user.publisher
            )
        return queryset.none()

    def get_queryset(self):
        """Scope queryset to user's publisher for non-admin roles."""
        queryset = super().get_queryset().select_related(
            "issue", "issue__publication", "issue__publication__publisher", "created_by"
        )
        return self.get_scoped_queryset(queryset)

    def get_context_data(self, **kwargs):
        """Add breadcrumbs and role-based action flags to context."""
        context = super().get_context_data(**kwargs)
        context["breadcrumbs"] = [
            {"label": "Kontrolna tabla", "url": reverse_lazy("dashboard")},
            {"label": "Članci", "url": reverse_lazy("articles:list")},
            {"label": str(self.object), "url": None},
        ]

        # Role-based action visibility
        flags = self._get_user_role_flags()
        context["can_edit"] = (
            flags["is_admin"] or flags["is_urednik"] or flags["is_bibliotekar"]
        ) and self.object.status == ArticleStatus.DRAFT
        context["can_delete"] = flags["is_admin"]
        context["can_submit"] = (
            flags["is_admin"] or flags["is_urednik"] or flags["is_bibliotekar"]
        ) and self.object.status == ArticleStatus.DRAFT

        return context


class ArticleDeleteView(AdministratorRequiredMixin, DeleteView):
    """
    Soft delete an article.

    AC: #5 - Only Administrator/Superadmin can delete.
    """

    model = Article
    template_name = "articles/article_confirm_delete.html"
    success_url = reverse_lazy("articles:list")

    def get_queryset(self):
        """Include related data for display."""
        return super().get_queryset().select_related(
            "issue", "issue__publication", "issue__publication__publisher"
        )

    def get_context_data(self, **kwargs):
        """Add breadcrumbs to context."""
        context = super().get_context_data(**kwargs)
        context["breadcrumbs"] = [
            {"label": "Kontrolna tabla", "url": reverse_lazy("dashboard")},
            {"label": "Članci", "url": reverse_lazy("articles:list")},
            {"label": str(self.object), "url": None},
        ]
        return context

    def form_valid(self, form):
        """Perform soft delete instead of actual deletion."""
        article = self.object
        messages.success(
            self.request,
            "Članak uspešno obrisan.",
        )
        article.soft_delete(user=self.request.user)
        return HttpResponseRedirect(self.success_url)
