"""
Portal service functions for DOI Portal.

Story 4.1: Portal Home Page.
Story 4.2: Article Search Functionality.
Story 4.6: PDF Download.
Story 4.7: Citation Modal.
Provides portal-wide statistics, recent publications, article search,
PDF download helpers, and citation formatting.
All business logic for portal data retrieval is centralized here.
"""

from __future__ import annotations

from django.db.models import Count, Q, QuerySet
from django.utils.text import slugify

from doi_portal.articles.models import Article, ArticleStatus, Author
from doi_portal.publications.models import Publication
from doi_portal.publishers.models import Publisher

__all__ = [
    "format_citation_apa",
    "format_citation_bibtex",
    "format_citation_chicago",
    "format_citation_mla",
    "format_citation_ris",
    "generate_citation",
    "get_article_for_landing",
    "get_pdf_download_filename",
    "get_portal_statistics",
    "get_recent_publications",
    "search_articles",
]


def get_article_for_landing(article_pk: int) -> Article | None:
    """
    Get article for public landing page display.

    FR41: Posetilac moze videti landing stranicu clanka sa svim metapodacima.
    Only PUBLISHED and WITHDRAWN articles are visible on public portal.

    Args:
        article_pk: Primary key of the article.

    Returns:
        Article with related data or None if not found/not public.
    """
    try:
        return (
            Article.objects.filter(
                pk=article_pk,
                status__in=[ArticleStatus.PUBLISHED, ArticleStatus.WITHDRAWN],
            )
            .select_related("issue__publication__publisher")
            .prefetch_related("authors__affiliations")
            .get()
        )
    except Article.DoesNotExist:
        return None


def get_portal_statistics() -> dict[str, int]:
    """
    Get portal-wide statistics for home page.

    Uses aggregate() for single SQL query (same pattern as dashboard/services.py).

    Returns:
        Dict with total_publications, total_articles, published_articles_count,
        total_publishers.
    """
    article_counts = Article.objects.aggregate(
        total=Count("id"),
        published=Count("id", filter=Q(status=ArticleStatus.PUBLISHED)),
    )
    return {
        "total_publications": Publication.objects.count(),
        "total_articles": article_counts["total"],
        "published_articles_count": article_counts["published"],
        "total_publishers": Publisher.objects.count(),
    }


def search_articles(
    query: str,
    filters: dict | None = None,
) -> QuerySet[Article]:
    """
    Search published articles by title, author names, keywords, and abstract.

    FR39: Posetilac moze pretrazivati clanke po nazivu, autoru i kljucnim recima.
    FR40: Filtriranje po vrsti, oblasti, pristupu, jeziku.
    NFR5: Rezultati < 2 sekunde.

    Only PUBLISHED articles are searched.
    SoftDeleteManager already excludes is_deleted=True records.

    Args:
        query: Search term (minimum 3 characters expected, caller validates).
        filters: Optional dict with filter criteria:
            - types: list of PublicationType values
            - subjects: list of subject area strings
            - languages: list of language strings
            - access_types: list of AccessType values
            - year_from: int minimum year
            - year_to: int maximum year

    Returns:
        QuerySet of matching Article objects with related data pre-fetched.
    """
    if not query or len(query.strip()) < 3:
        return Article.objects.none()

    q = query.strip()[:200]  # Cap query length to prevent oversized SQL

    # Find author IDs matching the search query
    matching_author_article_ids = (
        Author.objects.filter(
            Q(given_name__icontains=q) | Q(surname__icontains=q)
        )
        .values_list("article_id", flat=True)
        .distinct()
    )

    queryset = (
        Article.objects.filter(
            Q(status=ArticleStatus.PUBLISHED),
            Q(title__icontains=q)
            | Q(abstract__icontains=q)
            | Q(keywords__icontains=q)
            | Q(id__in=matching_author_article_ids),
        )
        .select_related("issue__publication__publisher")
        .prefetch_related("authors")
        .order_by("-published_at", "-created_at")
        .distinct()
    )

    # Apply filters (AND logic - all must be satisfied)
    if filters:
        if filters.get("types"):
            queryset = queryset.filter(
                issue__publication__publication_type__in=filters["types"]
            )
        if filters.get("subjects"):
            queryset = queryset.filter(
                issue__publication__subject_area__in=filters["subjects"]
            )
        if filters.get("languages"):
            queryset = queryset.filter(
                issue__publication__language__in=filters["languages"]
            )
        if filters.get("access_types"):
            queryset = queryset.filter(
                issue__publication__access_type__in=filters["access_types"]
            )
        if filters.get("year_from"):
            queryset = queryset.filter(
                issue__year__gte=filters["year_from"]
            )
        if filters.get("year_to"):
            queryset = queryset.filter(
                issue__year__lte=filters["year_to"]
            )

    return queryset


def get_recent_publications(limit: int = 6) -> QuerySet[Publication]:
    """
    Get most recent active publications for home page.

    SoftDeleteManager already excludes is_deleted=True records.

    Args:
        limit: Maximum number of publications to return (default 6).

    Returns:
        QuerySet of Publication objects ordered by created_at descending.
    """
    return (
        Publication.objects.select_related("publisher")
        .order_by("-created_at")[:limit]
    )


# =============================================================================
# Story 4.7: Citation Formatting Functions
# =============================================================================


def _get_full_doi(article: Article) -> str:
    """Build full DOI string from publisher prefix and article suffix."""
    try:
        prefix = article.issue.publication.publisher.doi_prefix
    except AttributeError:
        prefix = ""
    return f"{prefix}/{article.doi_suffix}" if prefix else article.doi_suffix


def _get_authors_ordered(article: Article) -> list:
    """Get ordered list of authors for citation formatting."""
    return list(article.authors.all().order_by("order"))


def generate_citation(article: Article, fmt: str) -> str:
    """
    Generate a formatted citation for the given article.

    Dispatches to format-specific functions based on fmt parameter.
    Falls back to APA for unknown formats.

    Args:
        article: Article instance with prefetch-ed authors and issue/publication/publisher.
        fmt: Citation format identifier (apa, mla, chicago, bibtex, ris).

    Returns:
        Formatted citation string.
    """
    formatters = {
        "apa": format_citation_apa,
        "mla": format_citation_mla,
        "chicago": format_citation_chicago,
        "bibtex": format_citation_bibtex,
        "ris": format_citation_ris,
    }
    formatter = formatters.get(fmt, format_citation_apa)
    return formatter(article)


def format_citation_apa(article: Article) -> str:
    """
    Format citation in APA 7th edition style.

    Format: Surname, I., Surname2, I2., & Surname3, I3. (Year). Title. Journal, Vol(Issue), Pages. DOI
    Gracefully omits missing fields.

    Args:
        article: Article instance with related data.

    Returns:
        APA formatted citation string.
    """
    authors = _get_authors_ordered(article)
    doi = _get_full_doi(article)

    # Format authors: Surname, I.
    author_parts = []
    for a in authors:
        initials = f"{a.given_name[0]}." if a.given_name else ""
        author_parts.append(f"{a.surname}, {initials}" if initials else a.surname)

    if len(author_parts) == 0:
        author_str = ""
    elif len(author_parts) == 1:
        author_str = author_parts[0]
    elif len(author_parts) == 2:
        author_str = f"{author_parts[0]} & {author_parts[1]}"
    else:
        author_str = ", ".join(author_parts[:-1]) + ", & " + author_parts[-1]

    # Year
    try:
        year = article.issue.year
    except AttributeError:
        year = ""

    # Title
    title = article.title or ""

    # Journal name
    try:
        journal = article.issue.publication.title
    except AttributeError:
        journal = ""

    # Volume and issue
    try:
        volume = article.issue.volume
        issue_number = article.issue.issue_number
    except AttributeError:
        volume = ""
        issue_number = ""

    # Pages
    pages = ""
    if article.first_page:
        pages = article.first_page
        if article.last_page:
            pages = f"{article.first_page}-{article.last_page}"

    # Build citation
    parts = []
    if author_str:
        parts.append(author_str)

    if year:
        parts.append(f"({year})")

    if title:
        parts.append(f"{title}.")

    # Journal, Volume(Issue), Pages
    journal_part = ""
    if journal:
        journal_part = journal
        if volume:
            journal_part += f", {volume}"
            if issue_number:
                journal_part += f"({issue_number})"
        if pages:
            journal_part += f", {pages}"
        journal_part += "."
        parts.append(journal_part)

    if doi:
        parts.append(f"https://doi.org/{doi}")

    return " ".join(parts)


def format_citation_mla(article: Article) -> str:
    """
    Format citation in MLA 9th edition style.

    Format: Surname, GivenName, et al. "Title." Journal, vol. V, no. N, Year, pp. Pages. DOI: doi.
    Gracefully omits missing fields.

    Args:
        article: Article instance with related data.

    Returns:
        MLA formatted citation string.
    """
    authors = _get_authors_ordered(article)
    doi = _get_full_doi(article)

    # Format authors: first author "Surname, GivenName", rest "et al." if >2
    if len(authors) == 0:
        author_str = ""
    elif len(authors) == 1:
        a = authors[0]
        author_str = f"{a.surname}, {a.given_name}" if a.given_name else a.surname
    elif len(authors) == 2:
        a1 = authors[0]
        a2 = authors[1]
        first = f"{a1.surname}, {a1.given_name}" if a1.given_name else a1.surname
        second = f"{a2.given_name} {a2.surname}" if a2.given_name else a2.surname
        author_str = f"{first}, and {second}"
    else:
        a = authors[0]
        author_str = f"{a.surname}, {a.given_name}, et al." if a.given_name else f"{a.surname}, et al."

    title = article.title or ""
    try:
        journal = article.issue.publication.title
    except AttributeError:
        journal = ""
    try:
        volume = article.issue.volume
        issue_number = article.issue.issue_number
        year = article.issue.year
    except AttributeError:
        volume = ""
        issue_number = ""
        year = ""

    pages = ""
    if article.first_page:
        pages = article.first_page
        if article.last_page:
            pages = f"{article.first_page}-{article.last_page}"

    # Build citation
    parts = []
    if author_str:
        parts.append(f"{author_str}.")

    if title:
        parts.append(f'"{title}."')

    # Journal details
    journal_details = []
    if journal:
        journal_details.append(journal)
    if volume:
        journal_details.append(f"vol. {volume}")
    if issue_number:
        journal_details.append(f"no. {issue_number}")
    if year:
        journal_details.append(str(year))
    if pages:
        journal_details.append(f"pp. {pages}")

    if journal_details:
        parts.append(", ".join(journal_details) + ".")

    if doi:
        parts.append(f"DOI: {doi}.")

    return " ".join(parts)


def format_citation_chicago(article: Article) -> str:
    """
    Format citation in Chicago 17th edition (author-date) style.

    Format: Surname, GivenName, and GivenName2 Surname2. Year. "Title." Journal V (N): Pages. DOI.
    Gracefully omits missing fields.

    Args:
        article: Article instance with related data.

    Returns:
        Chicago formatted citation string.
    """
    authors = _get_authors_ordered(article)
    doi = _get_full_doi(article)

    # Format authors: first "Surname, GivenName", rest "GivenName Surname"
    if len(authors) == 0:
        author_str = ""
    elif len(authors) == 1:
        a = authors[0]
        author_str = f"{a.surname}, {a.given_name}" if a.given_name else a.surname
    elif len(authors) == 2:
        a1 = authors[0]
        a2 = authors[1]
        first = f"{a1.surname}, {a1.given_name}" if a1.given_name else a1.surname
        second = f"{a2.given_name} {a2.surname}" if a2.given_name else a2.surname
        author_str = f"{first}, and {second}"
    else:
        a1 = authors[0]
        first = f"{a1.surname}, {a1.given_name}" if a1.given_name else a1.surname
        rest = []
        for a in authors[1:-1]:
            rest.append(f"{a.given_name} {a.surname}" if a.given_name else a.surname)
        last = authors[-1]
        last_str = f"{last.given_name} {last.surname}" if last.given_name else last.surname
        author_str = first + ", " + ", ".join(rest) + ", and " + last_str if rest else f"{first}, and {last_str}"

    try:
        year = article.issue.year
    except AttributeError:
        year = ""

    title = article.title or ""
    try:
        journal = article.issue.publication.title
    except AttributeError:
        journal = ""
    try:
        volume = article.issue.volume
        issue_number = article.issue.issue_number
    except AttributeError:
        volume = ""
        issue_number = ""

    pages = ""
    if article.first_page:
        pages = article.first_page
        if article.last_page:
            pages = f"{article.first_page}-{article.last_page}"

    # Build citation
    parts = []
    if author_str:
        parts.append(f"{author_str}.")

    if year:
        parts.append(f"{year}.")

    if title:
        parts.append(f'"{title}."')

    # Journal Volume (Issue): Pages
    journal_part = ""
    if journal:
        journal_part = journal
        if volume:
            journal_part += f" {volume}"
            if issue_number:
                journal_part += f" ({issue_number})"
        if pages:
            journal_part += f": {pages}"
        journal_part += "."
        parts.append(journal_part)

    if doi:
        parts.append(f"https://doi.org/{doi}.")

    return " ".join(parts)


def format_citation_bibtex(article: Article) -> str:
    """
    Format citation as BibTeX @article entry.

    Gracefully omits missing fields.

    Args:
        article: Article instance with related data.

    Returns:
        BibTeX formatted citation string.
    """
    authors = _get_authors_ordered(article)
    doi = _get_full_doi(article)

    # BibTeX key from doi_suffix (sanitize for BibTeX key)
    key = article.doi_suffix.replace("/", "_").replace(".", "_") if article.doi_suffix else "article"

    # Authors: "Surname, GivenName and Surname2, GivenName2"
    author_parts = []
    for a in authors:
        if a.given_name:
            author_parts.append(f"{a.surname}, {a.given_name}")
        else:
            author_parts.append(a.surname)
    author_str = " and ".join(author_parts)

    try:
        journal = article.issue.publication.title
    except AttributeError:
        journal = ""
    try:
        year = str(article.issue.year) if article.issue.year else ""
        volume = article.issue.volume or ""
        issue_number = article.issue.issue_number or ""
    except AttributeError:
        year = ""
        volume = ""
        issue_number = ""

    pages = ""
    if article.first_page:
        pages = article.first_page
        if article.last_page:
            pages = f"{article.first_page}--{article.last_page}"

    # Build BibTeX entry fields
    fields = []
    if author_str:
        fields.append(f"  author = {{{author_str}}}")
    fields.append(f"  title = {{{article.title or ''}}}")
    if journal:
        fields.append(f"  journal = {{{journal}}}")
    if year:
        fields.append(f"  year = {{{year}}}")
    if volume:
        fields.append(f"  volume = {{{volume}}}")
    if issue_number:
        fields.append(f"  number = {{{issue_number}}}")
    if pages:
        fields.append(f"  pages = {{{pages}}}")
    if doi:
        fields.append(f"  doi = {{{doi}}}")

    # Join fields with commas, no trailing comma on last field
    lines = [f"@article{{{key},"]
    lines.append(",\n".join(fields))
    lines.append("}")

    return "\n".join(lines)


def format_citation_ris(article: Article) -> str:
    """
    Format citation in RIS format.

    Gracefully omits missing fields.

    Args:
        article: Article instance with related data.

    Returns:
        RIS formatted citation string.
    """
    authors = _get_authors_ordered(article)
    doi = _get_full_doi(article)

    lines = ["TY  - JOUR"]

    for a in authors:
        name = f"{a.surname}, {a.given_name}" if a.given_name else a.surname
        lines.append(f"AU  - {name}")

    if article.title:
        lines.append(f"TI  - {article.title}")

    try:
        journal = article.issue.publication.title
        if journal:
            lines.append(f"JO  - {journal}")
    except AttributeError:
        pass

    try:
        volume = article.issue.volume
        if volume:
            lines.append(f"VL  - {volume}")
        issue_number = article.issue.issue_number
        if issue_number:
            lines.append(f"IS  - {issue_number}")
    except AttributeError:
        pass

    if article.first_page:
        lines.append(f"SP  - {article.first_page}")
    if article.last_page:
        lines.append(f"EP  - {article.last_page}")

    try:
        year = article.issue.year
        if year:
            lines.append(f"PY  - {year}")
    except AttributeError:
        pass

    if doi:
        lines.append(f"DO  - {doi}")

    lines.append("ER  -")

    return "\n".join(lines)


def get_pdf_download_filename(article: Article) -> str:
    """
    Generate descriptive PDF filename for download attribute.

    FR42: Posetilac može preuzeti PDF članka.
    Format: {doi_suffix}_{title_slug}.pdf
    Example: "test-001_some-article-title.pdf"

    Note: Used for the HTML download attribute on the <a> tag,
    not for server-side Content-Disposition header.
    The download attribute is ignored by browsers for cross-origin URLs (S3),
    but works for same-origin (local development).

    Args:
        article: Article instance with doi_suffix and title.

    Returns:
        Descriptive filename string ending in .pdf.
    """
    title_slug = slugify(article.title)[:100]
    doi_slug = article.doi_suffix.replace("/", "-")
    if not title_slug:
        return f"{doi_slug}.pdf"
    return f"{doi_slug}_{title_slug}.pdf"
