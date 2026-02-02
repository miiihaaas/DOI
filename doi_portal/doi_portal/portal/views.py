"""
Public portal views for DOI Portal.

Story 2.2: Public Publisher Page
Story 2.5: Public Publication List with Filters
Story 2.7: Public Issue List & Detail
Story 4.1: Portal Home Page
Story 4.2: Article Search Functionality
Story 4.3: Advanced Filtering for Articles
Story 4.4: Article Landing Page
Story 4.5: Floating Action Bar
Story 4.6: PDF Download

These are PUBLIC views - no authentication required.
CSRF protection is handled by Django middleware for GET requests (safe methods).
"""

from django.db import models
from django.http import Http404, HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.views.decorators.http import require_GET
from django.views.generic import DetailView
from django.views.generic import ListView
from django.views.generic import TemplateView

from doi_portal.articles.models import Article, ArticleStatus
from doi_portal.portal.services import get_pdf_download_filename
from doi_portal.portal.services import get_portal_statistics
from doi_portal.portal.services import get_recent_publications
from doi_portal.portal.services import search_articles

from doi_portal.issues.models import Issue
from doi_portal.issues.models import IssueStatus
from doi_portal.publications.models import AccessType
from doi_portal.publications.models import Publication
from doi_portal.publications.models import PublicationType
from doi_portal.publishers.models import Publisher


class PublisherPublicListView(ListView):
    """
    Public listing of all active publishers.

    AC: #2 - Lists all active publishers with logos and names.
    Each publisher links to their detail page.
    """

    model = Publisher
    template_name = "portal/publishers/publisher_list.html"
    context_object_name = "publishers"

    def get_queryset(self):
        """
        Return all active (non-deleted) publishers.

        SoftDeleteManager already excludes is_deleted=True records.
        """
        return Publisher.objects.all().order_by("name")

    def get_context_data(self, **kwargs):
        """Add breadcrumbs to context."""
        context = super().get_context_data(**kwargs)
        context["breadcrumbs"] = [
            {"label": "Početna", "url": reverse("home")},
            {"label": "Izdavači", "url": None},
        ]
        return context


class PublisherPublicDetailView(DetailView):
    """
    Public view of a single publisher with their publications.

    AC: #1, #3, #4 - Shows publisher details and publications.
    Returns 404 for deleted or non-existent publishers.
    """

    model = Publisher
    template_name = "portal/publishers/publisher_detail.html"
    context_object_name = "publisher"
    slug_url_kwarg = "slug"

    def get_queryset(self):
        """
        Return queryset of active publishers.

        SoftDeleteManager excludes deleted publishers - will raise 404.
        """
        return Publisher.objects.all()

    def get_context_data(self, **kwargs):
        """Add breadcrumbs and publications placeholder to context."""
        context = super().get_context_data(**kwargs)
        context["breadcrumbs"] = [
            {"label": "Početna", "url": reverse("home")},
            {"label": "Izdavači", "url": reverse("portal:publisher-list")},
            {"label": self.object.name, "url": None},
        ]
        # Story 2.5: Real publications for this publisher
        context["publications"] = (
            Publication.objects.filter(publisher=self.object)
            .select_related("publisher")
            .order_by("title")
        )
        return context


# =============================================================================
# Story 2.5: Public Publication Views
# =============================================================================


class PublicationPublicListView(ListView):
    """
    Public listing of all active publications with filters.

    FR17: Posetilac moze pregledati listu svih publikacija sa filterima.
    FR40: Posetilac moze filtrirati publikacije po vrsti, oblasti, pristupu, jeziku.
    """

    model = Publication
    template_name = "portal/publications/publication_list.html"
    context_object_name = "publications"
    paginate_by = 12

    def get_queryset(self):
        """Return filtered queryset of active publications."""
        queryset = Publication.objects.select_related("publisher").order_by("title")

        # Filter by type (multi-select checkboxes - AC #2)
        pub_types = self.request.GET.getlist("type")
        valid_types = [t for t in pub_types if t in [c[0] for c in PublicationType.choices]]
        if valid_types:
            queryset = queryset.filter(publication_type__in=valid_types)

        # Filter by subject area (multi-select checkboxes)
        subjects = self.request.GET.getlist("subject")
        if subjects:
            queryset = queryset.filter(subject_area__in=subjects)

        # Filter by access type (multi-select checkboxes)
        access_values = self.request.GET.getlist("access")
        valid_access = [a for a in access_values if a in [c[0] for c in AccessType.choices]]
        if valid_access:
            queryset = queryset.filter(access_type__in=valid_access)

        # Filter by language (multi-select checkboxes)
        languages = self.request.GET.getlist("language")
        if languages:
            queryset = queryset.filter(language__in=languages)

        # Search by title
        search = self.request.GET.get("search")
        if search:
            queryset = queryset.filter(title__icontains=search)

        return queryset

    def get_template_names(self):
        """Return partial template for HTMX requests."""
        if self.request.headers.get("HX-Request"):
            return ["portal/publications/partials/_publication_grid.html"]
        return [self.template_name]

    def get_context_data(self, **kwargs):
        """Add breadcrumbs, filter choices, and active filter values to context."""
        context = super().get_context_data(**kwargs)
        context["breadcrumbs"] = [
            {"label": "Početna", "url": reverse("home")},
            {"label": "Publikacije", "url": None},
        ]
        context["publication_types"] = PublicationType.choices
        context["access_types"] = AccessType.choices

        # Dynamic filter options from database
        context["subject_areas"] = (
            Publication.objects.exclude(subject_area="")
            .values_list("subject_area", flat=True)
            .distinct()
            .order_by("subject_area")
        )
        context["languages"] = (
            Publication.objects.exclude(language="")
            .values_list("language", flat=True)
            .distinct()
            .order_by("language")
        )

        # Active filters for UI state (multi-select checkboxes - AC #2)
        context["current_types"] = self.request.GET.getlist("type")
        context["current_subjects"] = self.request.GET.getlist("subject")
        context["current_access"] = self.request.GET.getlist("access")
        context["current_languages"] = self.request.GET.getlist("language")
        context["search_query"] = self.request.GET.get("search", "")

        # Convenience: any filter active?
        context["has_active_filters"] = bool(
            context["current_types"]
            or context["current_subjects"]
            or context["current_access"]
            or context["current_languages"]
            or context["search_query"]
        )

        return context


class PublicationPublicDetailView(DetailView):
    """
    Public view of a single publication with its details.

    AC: #5 - Shows publication detail with type-specific fields.
    Returns 404 for deleted or non-existent publications.
    """

    model = Publication
    template_name = "portal/publications/publication_detail.html"
    context_object_name = "publication"
    slug_url_kwarg = "slug"

    def get_queryset(self):
        """
        Return queryset of active publications.

        SoftDeleteManager excludes deleted publications - will raise 404.
        """
        return Publication.objects.select_related("publisher")

    def get_context_data(self, **kwargs):
        """Add breadcrumbs and issues placeholder to context."""
        context = super().get_context_data(**kwargs)
        context["breadcrumbs"] = [
            {"label": "Početna", "url": reverse("home")},
            {
                "label": "Publikacije",
                "url": reverse("portal-publications:publication-list"),
            },
            {"label": self.object.title, "url": None},
        ]
        # Story 2.6: Real published issues list
        context["issues"] = (
            self.object.issues.filter(status=IssueStatus.PUBLISHED)
            .order_by("-year", "-volume", "-issue_number")
        )
        return context


# =============================================================================
# Story 2.7: Public Issue Detail View
# =============================================================================


class IssuePublicDetailView(DetailView):
    """
    Public view of a single published issue with its articles.

    FR21: Posetilac moze pregledati sva izdanja publikacije.
    Only PUBLISHED issues are visible to the public.
    """

    model = Issue
    template_name = "portal/publications/issue_detail.html"
    context_object_name = "issue"

    def get_queryset(self):
        """
        Return queryset of published, non-deleted issues.

        Only PUBLISHED status issues are visible to the public.
        SoftDeleteManager already excludes is_deleted=True records.
        Additional filter for publication slug to ensure URL consistency.
        """
        slug = self.kwargs.get("slug")
        return (
            Issue.objects.filter(
                status=IssueStatus.PUBLISHED,
                publication__slug=slug,
                publication__is_deleted=False,
            ).select_related("publication", "publication__publisher")
        )

    def get_context_data(self, **kwargs):
        """Add breadcrumbs and articles placeholder to context."""
        context = super().get_context_data(**kwargs)
        issue = self.object
        publication = issue.publication

        context["breadcrumbs"] = [
            {"label": "Početna", "url": reverse("home")},
            {
                "label": "Publikacije",
                "url": reverse("portal-publications:publication-list"),
            },
            {
                "label": publication.title,
                "url": reverse(
                    "portal-publications:publication-detail",
                    kwargs={"slug": publication.slug},
                ),
            },
            {
                "label": f"Vol. {issue.volume}, No. {issue.issue_number} ({issue.year})",
                "url": None,
            },
        ]
        # Story 4.4: Real articles for this issue (only PUBLISHED/WITHDRAWN)
        context["articles"] = (
            Article.objects.filter(
                issue=self.object,
                status__in=[ArticleStatus.PUBLISHED, ArticleStatus.WITHDRAWN],
            )
            .select_related("issue__publication__publisher")
            .prefetch_related("authors")
            .order_by("first_page", "title")
        )
        return context


# =============================================================================
# Story 4.1: Portal Home Page
# =============================================================================


class PortalHomeView(TemplateView):
    """
    Portal home page view.

    FR38: Posetilac moze videti pocetnu stranu portala.
    Public view - no authentication required.
    """

    template_name = "portal/home.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["stats"] = get_portal_statistics()
        context["recent_publications"] = get_recent_publications()
        # No breadcrumbs on home page (it IS the root)
        return context


# =============================================================================
# Story 4.2: Article Search Functionality
# =============================================================================


class ArticleSearchView(ListView):
    """
    Public article search view with advanced filtering.

    FR39: Posetilac moze pretrazivati clanke po nazivu, autoru i kljucnim recima.
    FR40: Posetilac moze filtrirati publikacije po vrsti, oblasti, pristupu, jeziku.
    Public view - no authentication required.
    """

    template_name = "portal/search_results.html"
    context_object_name = "articles"
    paginate_by = 20

    def _parse_filters(self) -> dict:
        """Parse and validate filter parameters from GET request."""
        filters = {}

        pub_types = self.request.GET.getlist("type")
        valid_types = [t for t in pub_types if t in [c[0] for c in PublicationType.choices]]
        if valid_types:
            filters["types"] = valid_types

        subjects = self.request.GET.getlist("subject")
        # Validate against actual subject areas in database
        valid_subjects = list(
            Publication.objects.exclude(subject_area="")
            .values_list("subject_area", flat=True)
            .distinct()
        )
        filtered_subjects = [s for s in subjects if s in valid_subjects]
        if filtered_subjects:
            filters["subjects"] = filtered_subjects

        languages = self.request.GET.getlist("language")
        # Validate against actual languages in database
        valid_languages = list(
            Publication.objects.exclude(language="")
            .values_list("language", flat=True)
            .distinct()
        )
        filtered_languages = [lg for lg in languages if lg in valid_languages]
        if filtered_languages:
            filters["languages"] = filtered_languages

        access_values = self.request.GET.getlist("access")
        valid_access = [a for a in access_values if a in [c[0] for c in AccessType.choices]]
        if valid_access:
            filters["access_types"] = valid_access

        year_from = self.request.GET.get("year_from")
        if year_from and year_from.isdigit():
            filters["year_from"] = int(year_from)

        year_to = self.request.GET.get("year_to")
        if year_to and year_to.isdigit():
            filters["year_to"] = int(year_to)

        return filters

    def get_queryset(self):
        """Return filtered search results."""
        query = self.request.GET.get("q", "").strip()[:200]
        if len(query) < 3:
            return Article.objects.none()
        filters = self._parse_filters()
        return search_articles(query, filters=filters)

    def get_template_names(self):
        """Return partial template for HTMX requests."""
        if self.request.headers.get("HX-Request"):
            return ["portal/partials/_search_results.html"]
        return [self.template_name]

    def get_context_data(self, **kwargs):
        """Add search-specific context with filter choices and active state."""
        context = super().get_context_data(**kwargs)
        query = self.request.GET.get("q", "").strip()[:200]
        context["query"] = query
        context["result_count"] = (
            context["paginator"].count if context.get("paginator") else 0
        )
        context["min_query_length"] = 3
        context["breadcrumbs"] = [
            {"label": "Početna", "url": reverse("home")},
            {"label": "Pretraga", "url": None},
        ]

        # Filter choices
        context["publication_types"] = PublicationType.choices
        context["access_types"] = AccessType.choices
        context["subject_areas"] = (
            Publication.objects.exclude(subject_area="")
            .values_list("subject_area", flat=True)
            .distinct()
            .order_by("subject_area")
        )
        context["languages"] = (
            Publication.objects.exclude(language="")
            .values_list("language", flat=True)
            .distinct()
            .order_by("language")
        )

        # Year range from published issues
        year_agg = Issue.objects.filter(
            status=IssueStatus.PUBLISHED
        ).aggregate(
            min_year=models.Min("year"),
            max_year=models.Max("year"),
        )
        context["year_range"] = {
            "min": year_agg["min_year"],
            "max": year_agg["max_year"],
        }

        # Active filter state
        context["current_types"] = self.request.GET.getlist("type")
        context["current_subjects"] = self.request.GET.getlist("subject")
        context["current_languages"] = self.request.GET.getlist("language")
        context["current_access"] = self.request.GET.getlist("access")

        # Year filter state: only show if valid digit
        year_from_raw = self.request.GET.get("year_from", "")
        year_to_raw = self.request.GET.get("year_to", "")
        context["current_year_from"] = year_from_raw if year_from_raw.isdigit() else ""
        context["current_year_to"] = year_to_raw if year_to_raw.isdigit() else ""

        context["has_active_filters"] = bool(
            context["current_types"]
            or context["current_subjects"]
            or context["current_languages"]
            or context["current_access"]
            or context["current_year_from"]
            or context["current_year_to"]
        )

        return context


# =============================================================================
# Story 4.4: Article Landing Page
# =============================================================================


class ArticleLandingView(DetailView):
    """
    Public article landing page.

    FR41: Posetilac moze videti landing stranicu clanka sa svim metapodacima.
    NFR1: First Contentful Paint < 3 sekunde.
    Only PUBLISHED and WITHDRAWN articles are visible.
    """

    model = Article
    template_name = "portal/article_detail.html"
    context_object_name = "article"

    def get_queryset(self):
        """Return only PUBLISHED and WITHDRAWN articles with related data."""
        return (
            Article.objects.filter(
                status__in=[ArticleStatus.PUBLISHED, ArticleStatus.WITHDRAWN],
            )
            .select_related("issue__publication__publisher")
            .prefetch_related("authors__affiliations")
        )

    def get_context_data(self, **kwargs):
        """Add article-specific context."""
        context = super().get_context_data(**kwargs)
        article = self.object
        issue = article.issue
        publication = issue.publication
        publisher = publication.publisher

        # Breadcrumbs: Home > Publications > Publication > Issue > Article
        context["breadcrumbs"] = [
            {"label": "Početna", "url": reverse("home")},
            {
                "label": "Publikacije",
                "url": reverse("portal-publications:publication-list"),
            },
            {
                "label": publication.title,
                "url": reverse(
                    "portal-publications:publication-detail",
                    kwargs={"slug": publication.slug},
                ),
            },
            {
                "label": f"Vol. {issue.volume}, No. {issue.issue_number} ({issue.year})",
                "url": reverse(
                    "portal-publications:issue-detail",
                    kwargs={"slug": publication.slug, "pk": issue.pk},
                ),
            },
            {"label": article.title[:80], "url": None},
        ]

        context["is_withdrawn"] = article.status == ArticleStatus.WITHDRAWN
        context["full_doi"] = f"{publisher.doi_prefix}/{article.doi_suffix}"
        context["doi_url"] = f"https://doi.org/{publisher.doi_prefix}/{article.doi_suffix}"

        # Story 4.5: Floating Action Bar context
        context["has_pdf"] = bool(article.pdf_file) and article.status != ArticleStatus.WITHDRAWN
        context["share_url"] = self.request.build_absolute_uri(
            reverse("portal-articles:article-detail", kwargs={"pk": article.pk})
        )

        # Story 4.6: PDF Download URL and filename for download attribute
        if context["has_pdf"]:
            context["pdf_download_url"] = reverse(
                "portal-articles:article-pdf-download",
                kwargs={"pk": article.pk},
            )
            context["pdf_download_filename"] = get_pdf_download_filename(article)
        else:
            context["pdf_download_url"] = None
            context["pdf_download_filename"] = None

        return context


# =============================================================================
# Story 4.6: PDF Download
# =============================================================================


@require_GET
def article_pdf_download(request, pk):
    """
    Redirect to article PDF file URL.

    FR42: Posetilac može preuzeti PDF članka.
    NFR4: Direktan link, bez procesiranja.

    Only PUBLISHED articles with uploaded PDF are served.
    WITHDRAWN articles are excluded (has_pdf = False per Story 4.5 logic).
    Infected or in-progress PDFs are excluded via pdf_status check.
    """
    article = get_object_or_404(
        Article,
        pk=pk,
        status=ArticleStatus.PUBLISHED,
    )
    if not article.pdf_file:
        raise Http404("PDF nije dostupan za ovaj članak.")

    # Security: Do not serve infected or in-progress PDF files
    from doi_portal.articles.models import PdfStatus

    if article.pdf_status in (PdfStatus.INFECTED, PdfStatus.SCANNING, PdfStatus.UPLOADING):
        raise Http404("PDF nije dostupan za ovaj članak.")

    return HttpResponseRedirect(article.pdf_file.url)
