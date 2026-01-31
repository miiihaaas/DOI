"""
Article views for DOI Portal.

Story 3.1: Article admin CRUD views with row-level permissions.
Story 3.2: HTMX FBV views for Author CRUD, reorder, ORCID validation.
"""

import json
import re

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db import models
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404, render
from django.urls import reverse, reverse_lazy
from django.views.decorators.http import require_GET, require_http_methods, require_POST
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

from .forms import AffiliationForm, ArticleForm, AuthorForm
from .models import (
    Affiliation,
    Article,
    ArticleStatus,
    Author,
    AuthorSequence,
)


# =============================================================================
# Publisher scoping helper for HTMX FBV views
# =============================================================================


def _check_article_permission(user, article):
    """
    Check if user has permission to modify authors on this article.

    Raises PermissionDenied if not allowed.
    Scoping: article.issue.publication.publisher (4-level chain).
    """
    if user.is_superuser:
        return
    if user.groups.filter(name__in=["Administrator", "Superadmin"]).exists():
        return
    # Urednik/Bibliotekar - check publisher scoping
    if hasattr(user, "publisher") and user.publisher:
        if article.issue.publication.publisher == user.publisher:
            return
    raise PermissionDenied


# =============================================================================
# CBV views for Article CRUD (Story 3.1)
# =============================================================================


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
        # Prefetch authors with affiliations to avoid N+1 queries (Story 3.2)
        context["authors"] = self.object.authors.prefetch_related("affiliations").all()
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

        # Author list for detail view (Story 3.2)
        context["authors"] = self.object.authors.prefetch_related("affiliations").all()

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


# =============================================================================
# HTMX FBV views for Author CRUD (Story 3.2)
# =============================================================================


@login_required
@require_POST
def author_add(request, article_pk):
    """Add author to article via HTMX POST."""
    article = get_object_or_404(
        Article.objects.select_related(
            "issue", "issue__publication", "issue__publication__publisher"
        ),
        pk=article_pk,
    )
    _check_article_permission(request.user, article)

    form = AuthorForm(request.POST)
    if form.is_valid():
        author = form.save(commit=False)
        author.article = article
        # Auto-set order to next available
        max_order = article.authors.aggregate(
            max_order=models.Max("order")
        )["max_order"] or 0
        author.order = max_order + 1
        # Auto-set sequence
        if author.order == 1:
            author.sequence = AuthorSequence.FIRST
        else:
            author.sequence = AuthorSequence.ADDITIONAL
        author.save()
    else:
        # Return form with errors, retarget to form container
        response = render(request, "articles/partials/_author_form.html", {
            "article": article,
            "author_form": form,
        })
        response["HX-Retarget"] = "#author-form-container"
        response["HX-Reswap"] = "innerHTML"
        return response

    # Return updated author list fragment
    authors = article.authors.prefetch_related("affiliations").all()
    return render(request, "articles/partials/_author_list.html", {
        "article": article,
        "authors": authors,
        "author_form": AuthorForm(),
    })


@login_required
@require_POST
def author_update(request, pk):
    """Update author via HTMX POST."""
    author = get_object_or_404(
        Author.objects.select_related(
            "article", "article__issue",
            "article__issue__publication",
            "article__issue__publication__publisher",
        ),
        pk=pk,
    )
    _check_article_permission(request.user, author.article)

    form = AuthorForm(request.POST, instance=author)
    if form.is_valid():
        form.save()
    else:
        # Return form with errors, retarget to form container
        response = render(request, "articles/partials/_author_form.html", {
            "article": author.article,
            "author_form": form,
            "author": author,
        })
        response["HX-Retarget"] = "#author-form-container"
        response["HX-Reswap"] = "innerHTML"
        return response

    article = author.article
    authors = article.authors.prefetch_related("affiliations").all()
    return render(request, "articles/partials/_author_list.html", {
        "article": article,
        "authors": authors,
        "author_form": AuthorForm(),
    })


@login_required
@require_POST
def author_delete(request, pk):
    """Delete author via HTMX POST, re-order remaining authors."""
    author = get_object_or_404(
        Author.objects.select_related(
            "article", "article__issue",
            "article__issue__publication",
            "article__issue__publication__publisher",
        ),
        pk=pk,
    )
    _check_article_permission(request.user, author.article)

    article = author.article
    author.delete()

    # Re-order remaining authors and recalculate sequence
    remaining = article.authors.order_by("order")
    for index, a in enumerate(remaining, start=1):
        Author.objects.filter(pk=a.pk).update(
            order=index,
            sequence=AuthorSequence.FIRST if index == 1 else AuthorSequence.ADDITIONAL,
        )

    authors = article.authors.prefetch_related("affiliations").all()
    return render(request, "articles/partials/_author_list.html", {
        "article": article,
        "authors": authors,
        "author_form": AuthorForm(),
    })


@login_required
@require_POST
def author_reorder(request, article_pk):
    """Reorder authors via HTMX POST (drag & drop)."""
    article = get_object_or_404(
        Article.objects.select_related(
            "issue", "issue__publication", "issue__publication__publisher"
        ),
        pk=article_pk,
    )
    _check_article_permission(request.user, article)

    try:
        order_data = json.loads(request.body)
    except (json.JSONDecodeError, ValueError):
        order_data = {}

    # order_data = {"order": [pk1, pk2, pk3, ...]}
    order_list = order_data.get("order", [])

    # Validate: only accept integer PKs
    if not isinstance(order_list, list):
        order_list = []

    for index, author_pk in enumerate(order_list, start=1):
        if not isinstance(author_pk, int):
            continue
        Author.objects.filter(pk=author_pk, article=article).update(
            order=index,
            sequence=AuthorSequence.FIRST if index == 1 else AuthorSequence.ADDITIONAL,
        )

    authors = article.authors.prefetch_related("affiliations").all()
    return render(request, "articles/partials/_author_list.html", {
        "article": article,
        "authors": authors,
        "author_form": AuthorForm(),
    })


@login_required
@require_GET
def validate_orcid_view(request):
    """Validate ORCID format via HTMX GET request."""
    orcid = request.GET.get("orcid", "").strip()
    is_valid = False
    if orcid:
        is_valid = bool(re.match(r"^\d{4}-\d{4}-\d{4}-\d{3}[\dX]$", orcid))

    return render(request, "articles/partials/_orcid_validation.html", {
        "orcid": orcid,
        "is_valid": is_valid,
        "has_value": bool(orcid),
    })


@login_required
@require_GET
def author_form_view(request, article_pk):
    """Return empty author form for inline editing via HTMX GET."""
    article = get_object_or_404(
        Article.objects.select_related(
            "issue", "issue__publication", "issue__publication__publisher"
        ),
        pk=article_pk,
    )
    _check_article_permission(request.user, article)

    form = AuthorForm()
    return render(request, "articles/partials/_author_form.html", {
        "article": article,
        "author_form": form,
    })


@login_required
@require_GET
def author_edit_form_view(request, pk):
    """Return pre-filled author form for editing via HTMX GET."""
    author = get_object_or_404(
        Author.objects.select_related(
            "article", "article__issue",
            "article__issue__publication",
            "article__issue__publication__publisher",
        ),
        pk=pk,
    )
    _check_article_permission(request.user, author.article)

    form = AuthorForm(instance=author)
    return render(request, "articles/partials/_author_form.html", {
        "article": author.article,
        "author_form": form,
        "author": author,
    })


@login_required
@require_POST
def affiliation_add(request, author_pk):
    """Add affiliation to author via HTMX POST."""
    author = get_object_or_404(
        Author.objects.select_related(
            "article", "article__issue",
            "article__issue__publication",
            "article__issue__publication__publisher",
        ),
        pk=author_pk,
    )
    _check_article_permission(request.user, author.article)

    form = AffiliationForm(request.POST)
    if form.is_valid():
        affiliation = form.save(commit=False)
        affiliation.author = author
        # Auto-set order to next available
        max_order = author.affiliations.aggregate(
            max_order=models.Max("order")
        )["max_order"] or 0
        affiliation.order = max_order + 1
        affiliation.save()
    else:
        # Return form with errors, retarget to form container
        response = render(request, "articles/partials/_affiliation_form.html", {
            "author": author,
            "affiliation_form": form,
        })
        response["HX-Retarget"] = "#author-form-container"
        response["HX-Reswap"] = "innerHTML"
        return response

    article = author.article
    authors = article.authors.prefetch_related("affiliations").all()
    return render(request, "articles/partials/_author_list.html", {
        "article": article,
        "authors": authors,
        "author_form": AuthorForm(),
    })


@login_required
@require_POST
def affiliation_delete(request, pk):
    """Delete affiliation via HTMX POST."""
    affiliation = get_object_or_404(
        Affiliation.objects.select_related(
            "author", "author__article",
            "author__article__issue",
            "author__article__issue__publication",
            "author__article__issue__publication__publisher",
        ),
        pk=pk,
    )
    _check_article_permission(request.user, affiliation.author.article)

    article = affiliation.author.article
    affiliation.delete()

    authors = article.authors.prefetch_related("affiliations").all()
    return render(request, "articles/partials/_author_list.html", {
        "article": article,
        "authors": authors,
        "author_form": AuthorForm(),
    })


@login_required
@require_GET
def affiliation_form_view(request, author_pk):
    """Return empty affiliation form for inline editing via HTMX GET."""
    author = get_object_or_404(
        Author.objects.select_related(
            "article", "article__issue",
            "article__issue__publication",
            "article__issue__publication__publisher",
        ),
        pk=author_pk,
    )
    _check_article_permission(request.user, author.article)

    form = AffiliationForm()
    return render(request, "articles/partials/_affiliation_form.html", {
        "author": author,
        "affiliation_form": form,
    })
