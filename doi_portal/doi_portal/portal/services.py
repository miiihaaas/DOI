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
from slugify import slugify

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
    "generate_chapter_citation",
    "generate_monograph_citation",
    "get_article_for_landing",
    "get_chapter_pdf_download_filename",
    "get_monograph_pdf_download_filename",
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


# =============================================================================
# Monograph Citation Formatting Functions
# =============================================================================


def _get_monograph_contributors_ordered(monograph) -> list:
    """Get ordered list of contributors for a monograph."""
    return list(monograph.contributors.order_by("order"))


def _get_monograph_full_title(monograph) -> str:
    """Build full title with subtitle if available."""
    if monograph.subtitle:
        return f"{monograph.title}: {monograph.subtitle}"
    return monograph.title


def _get_chapter_full_title(chapter) -> str:
    """Build full chapter title with subtitle if available."""
    if chapter.subtitle:
        return f"{chapter.title}: {chapter.subtitle}"
    return chapter.title


def generate_monograph_citation(monograph, fmt="apa"):
    """Generate citation for a monograph in the specified format."""
    formatters = {
        "apa": format_monograph_citation_apa,
        "mla": format_monograph_citation_mla,
        "chicago": format_monograph_citation_chicago,
        "bibtex": format_monograph_citation_bibtex,
        "ris": format_monograph_citation_ris,
    }
    formatter = formatters.get(fmt, format_monograph_citation_apa)
    return formatter(monograph)


def format_monograph_citation_apa(monograph) -> str:
    """
    Format monograph citation in APA 7th edition style.

    Format: Surname, I. I., & Surname2, I. I. (Year). *Title: Subtitle*. Publisher. DOI
    """
    contributors = _get_monograph_contributors_ordered(monograph)
    full_title = _get_monograph_full_title(monograph)

    # Format authors: Surname, I.
    author_parts = []
    for c in contributors:
        if c.given_name:
            name_parts = c.given_name.strip().split()
            initials = " ".join(f"{p[0]}." for p in name_parts if p)
            author_parts.append(f"{c.surname}, {initials}")
        else:
            author_parts.append(c.surname)

    if len(author_parts) == 0:
        author_str = ""
    elif len(author_parts) == 1:
        author_str = author_parts[0]
    elif len(author_parts) == 2:
        author_str = f"{author_parts[0]} & {author_parts[1]}"
    else:
        author_str = ", ".join(author_parts[:-1]) + ", & " + author_parts[-1]

    year = monograph.year or ""

    # Publisher name
    try:
        publisher = monograph.publisher.name
    except AttributeError:
        publisher = ""

    doi = monograph.full_doi

    # Build citation
    parts = []
    if author_str:
        parts.append(author_str)
    if year:
        parts.append(f"({year})")
    if full_title:
        parts.append(f"*{full_title}*.")
    if publisher:
        parts.append(f"{publisher}.")
    if doi:
        parts.append(f"https://doi.org/{doi}")

    return " ".join(parts)


def format_monograph_citation_mla(monograph) -> str:
    """
    Format monograph citation in MLA 9th edition style.

    Format: Surname, GivenName. *Title: Subtitle*. Publisher, Year.
    2 authors: Surname, GivenName, and GivenName2 Surname2.
    3+ authors: Surname, GivenName, et al.
    """
    contributors = _get_monograph_contributors_ordered(monograph)
    full_title = _get_monograph_full_title(monograph)

    if len(contributors) == 0:
        author_str = ""
    elif len(contributors) == 1:
        c = contributors[0]
        author_str = f"{c.surname}, {c.given_name}" if c.given_name else c.surname
    elif len(contributors) == 2:
        c1 = contributors[0]
        c2 = contributors[1]
        first = f"{c1.surname}, {c1.given_name}" if c1.given_name else c1.surname
        second = f"{c2.given_name} {c2.surname}" if c2.given_name else c2.surname
        author_str = f"{first}, and {second}"
    else:
        c = contributors[0]
        author_str = f"{c.surname}, {c.given_name}, et al." if c.given_name else f"{c.surname}, et al."

    year = monograph.year or ""

    try:
        publisher = monograph.publisher.name
    except AttributeError:
        publisher = ""

    # Build citation
    parts = []
    if author_str:
        parts.append(f"{author_str}.")

    if full_title:
        parts.append(f"*{full_title}*.")

    # Publisher, Year.
    pub_parts = []
    if publisher:
        pub_parts.append(publisher)
    if year:
        pub_parts.append(str(year))
    if pub_parts:
        parts.append(", ".join(pub_parts) + ".")

    return " ".join(parts)


def format_monograph_citation_chicago(monograph) -> str:
    """
    Format monograph citation in Chicago 17th edition style.

    Format: Surname, GivenName. *Title: Subtitle*. Place: Publisher, Year.
    """
    contributors = _get_monograph_contributors_ordered(monograph)
    full_title = _get_monograph_full_title(monograph)

    # Format authors (same pattern as Chicago article)
    if len(contributors) == 0:
        author_str = ""
    elif len(contributors) == 1:
        c = contributors[0]
        author_str = f"{c.surname}, {c.given_name}" if c.given_name else c.surname
    elif len(contributors) == 2:
        c1 = contributors[0]
        c2 = contributors[1]
        first = f"{c1.surname}, {c1.given_name}" if c1.given_name else c1.surname
        second = f"{c2.given_name} {c2.surname}" if c2.given_name else c2.surname
        author_str = f"{first}, and {second}"
    else:
        c1 = contributors[0]
        first = f"{c1.surname}, {c1.given_name}" if c1.given_name else c1.surname
        rest = []
        for c in contributors[1:-1]:
            rest.append(f"{c.given_name} {c.surname}" if c.given_name else c.surname)
        last = contributors[-1]
        last_str = f"{last.given_name} {last.surname}" if last.given_name else last.surname
        author_str = first + ", " + ", ".join(rest) + ", and " + last_str if rest else f"{first}, and {last_str}"

    year = monograph.year or ""
    place = getattr(monograph, "publication_place", "") or ""

    try:
        publisher = monograph.publisher.name
    except AttributeError:
        publisher = ""

    # Build citation
    parts = []
    if author_str:
        parts.append(f"{author_str}.")

    if full_title:
        parts.append(f"*{full_title}*.")

    # Place: Publisher, Year.
    pub_parts = []
    if place and publisher:
        pub_parts.append(f"{place}: {publisher}")
    elif publisher:
        pub_parts.append(publisher)
    elif place:
        pub_parts.append(place)
    if year:
        pub_parts.append(str(year))
    if pub_parts:
        parts.append(", ".join(pub_parts) + ".")

    return " ".join(parts)


def format_monograph_citation_bibtex(monograph) -> str:
    """
    Format monograph citation as BibTeX @book entry.
    """
    contributors = _get_monograph_contributors_ordered(monograph)
    full_title = _get_monograph_full_title(monograph)

    # BibTeX key from doi_suffix
    key = monograph.doi_suffix.replace("/", "_").replace(".", "_") if monograph.doi_suffix else "book"

    # Authors: "Surname, GivenName and Surname2, GivenName2"
    author_parts = []
    for c in contributors:
        if c.given_name:
            author_parts.append(f"{c.surname}, {c.given_name}")
        else:
            author_parts.append(c.surname)
    author_str = " and ".join(author_parts)

    year = str(monograph.year) if monograph.year else ""

    try:
        publisher = monograph.publisher.name
    except AttributeError:
        publisher = ""

    isbn = monograph.isbn_print or monograph.isbn_online or ""
    doi = monograph.full_doi

    # Build BibTeX entry fields
    fields = []
    if author_str:
        fields.append(f"  author = {{{author_str}}}")
    fields.append(f"  title = {{{full_title}}}")
    if publisher:
        fields.append(f"  publisher = {{{publisher}}}")
    if year:
        fields.append(f"  year = {{{year}}}")
    if isbn:
        fields.append(f"  isbn = {{{isbn}}}")
    if doi:
        fields.append(f"  doi = {{{doi}}}")
        fields.append(f"  url = {{https://doi.org/{doi}}}")

    lines = [f"@book{{{key},"]
    lines.append(",\n".join(fields))
    lines.append("}")

    return "\n".join(lines)


def format_monograph_citation_ris(monograph) -> str:
    """
    Format monograph citation in RIS format.
    """
    contributors = _get_monograph_contributors_ordered(monograph)
    doi = monograph.full_doi

    lines = ["TY  - BOOK"]

    for c in contributors:
        name = f"{c.surname}, {c.given_name}" if c.given_name else c.surname
        lines.append(f"AU  - {name}")

    full_title = _get_monograph_full_title(monograph)
    if full_title:
        lines.append(f"TI  - {full_title}")

    try:
        publisher = monograph.publisher.name
        if publisher:
            lines.append(f"PB  - {publisher}")
    except AttributeError:
        pass

    place = getattr(monograph, "publication_place", "") or ""
    if place:
        lines.append(f"CY  - {place}")

    if monograph.year:
        lines.append(f"PY  - {monograph.year}")

    isbn = monograph.isbn_print or monograph.isbn_online or ""
    if isbn:
        lines.append(f"SN  - {isbn}")

    if doi:
        lines.append(f"DO  - {doi}")
        lines.append(f"UR  - https://doi.org/{doi}")

    lines.append("ER  -")

    return "\n".join(lines)


# =============================================================================
# Chapter Citation Formatting Functions
# =============================================================================


def _get_chapter_contributors_ordered(chapter) -> list:
    """Get ordered list of contributors for a chapter."""
    return list(chapter.contributors.order_by("order"))


def _get_monograph_editors(monograph) -> list:
    """Get editors from monograph contributors."""
    return list(
        monograph.contributors.filter(contributor_role="editor").order_by("order")
    )


def _format_editors_apa(editors) -> str:
    """Format editor names for APA 'In' clause."""
    parts = []
    for e in editors:
        initials = " ".join(f"{p[0]}." for p in e.given_name.strip().split() if p) if e.given_name else ""
        parts.append(f"{initials} {e.surname}" if initials else e.surname)

    if len(parts) == 0:
        return ""
    elif len(parts) == 1:
        return f"{parts[0]} (Ed.)"
    elif len(parts) == 2:
        return f"{parts[0]} & {parts[1]} (Eds.)"
    else:
        return ", ".join(parts[:-1]) + ", & " + parts[-1] + " (Eds.)"


def generate_chapter_citation(chapter, fmt="apa"):
    """Generate citation for a monograph chapter in the specified format."""
    formatters = {
        "apa": format_chapter_citation_apa,
        "mla": format_chapter_citation_mla,
        "chicago": format_chapter_citation_chicago,
        "bibtex": format_chapter_citation_bibtex,
        "ris": format_chapter_citation_ris,
    }
    formatter = formatters.get(fmt, format_chapter_citation_apa)
    return formatter(chapter)


def format_chapter_citation_apa(chapter) -> str:
    """
    Format chapter citation in APA 7th edition style.

    Format: Author, I. I. (Year). Chapter title. In E. Editor (Ed.),
    *Book title* (pp. first-last). Publisher. DOI
    """
    contributors = _get_chapter_contributors_ordered(chapter)
    monograph = chapter.monograph

    # Chapter author formatting
    author_parts = []
    for c in contributors:
        if c.given_name:
            name_parts = c.given_name.strip().split()
            initials = " ".join(f"{p[0]}." for p in name_parts if p)
            author_parts.append(f"{c.surname}, {initials}")
        else:
            author_parts.append(c.surname)

    if len(author_parts) == 0:
        author_str = ""
    elif len(author_parts) == 1:
        author_str = author_parts[0]
    elif len(author_parts) == 2:
        author_str = f"{author_parts[0]} & {author_parts[1]}"
    else:
        author_str = ", ".join(author_parts[:-1]) + ", & " + author_parts[-1]

    year = monograph.year or ""
    chapter_title = _get_chapter_full_title(chapter)
    book_title = _get_monograph_full_title(monograph)

    # Editors
    editors = _get_monograph_editors(monograph)
    if not editors:
        # Fall back to monograph contributors as authors
        editors = _get_monograph_contributors_ordered(monograph)
    editor_str = _format_editors_apa(editors) if editors else ""

    # Pages
    pages = ""
    if chapter.first_page:
        if chapter.last_page:
            pages = f"pp. {chapter.first_page}-{chapter.last_page}"
        else:
            pages = f"p. {chapter.first_page}"

    try:
        publisher = monograph.publisher.name
    except AttributeError:
        publisher = ""

    doi = chapter.full_doi

    # Build citation
    parts = []
    if author_str:
        parts.append(author_str)
    if year:
        parts.append(f"({year}).")
    elif parts:
        # Close author with period if no year
        parts[-1] = parts[-1] + "."

    if chapter_title:
        parts.append(f"{chapter_title}.")

    # In Editor (Ed.), *Book title* (pp. X-Y).
    in_part = "In"
    if editor_str:
        in_part += f" {editor_str},"
    in_part += f" *{book_title}*"
    if pages:
        in_part += f" ({pages})"
    in_part += "."
    parts.append(in_part)

    if publisher:
        parts.append(f"{publisher}.")
    if doi:
        parts.append(f"https://doi.org/{doi}")

    return " ".join(parts)


def format_chapter_citation_mla(chapter) -> str:
    """
    Format chapter citation in MLA 9th edition style.

    Format: Author. "Chapter Title." *Book Title*, edited by Editor,
    Publisher, Year, pp. first-last.
    """
    contributors = _get_chapter_contributors_ordered(chapter)
    monograph = chapter.monograph

    # Author formatting
    if len(contributors) == 0:
        author_str = ""
    elif len(contributors) == 1:
        c = contributors[0]
        author_str = f"{c.surname}, {c.given_name}" if c.given_name else c.surname
    elif len(contributors) == 2:
        c1 = contributors[0]
        c2 = contributors[1]
        first = f"{c1.surname}, {c1.given_name}" if c1.given_name else c1.surname
        second = f"{c2.given_name} {c2.surname}" if c2.given_name else c2.surname
        author_str = f"{first}, and {second}"
    else:
        c = contributors[0]
        author_str = f"{c.surname}, {c.given_name}, et al." if c.given_name else f"{c.surname}, et al."

    chapter_title = _get_chapter_full_title(chapter)
    book_title = _get_monograph_full_title(monograph)
    year = monograph.year or ""

    # Editors
    editors = _get_monograph_editors(monograph)
    if editors:
        editor_parts = []
        for e in editors:
            editor_parts.append(f"{e.given_name} {e.surname}" if e.given_name else e.surname)
        editor_str = " and ".join(editor_parts) if len(editor_parts) <= 2 else editor_parts[0] + ", et al."
    else:
        editor_str = ""

    try:
        publisher = monograph.publisher.name
    except AttributeError:
        publisher = ""

    pages = ""
    if chapter.first_page:
        if chapter.last_page:
            pages = f"pp. {chapter.first_page}-{chapter.last_page}"
        else:
            pages = f"p. {chapter.first_page}"

    # Build citation
    parts = []
    if author_str:
        parts.append(f"{author_str}.")
    if chapter_title:
        parts.append(f'"{chapter_title}."')

    # *Book Title*, edited by Editor, Publisher, Year, pp. X-Y.
    detail_parts = []
    if book_title:
        detail_parts.append(f"*{book_title}*")
    if editor_str:
        detail_parts.append(f"edited by {editor_str}")
    if publisher:
        detail_parts.append(publisher)
    if year:
        detail_parts.append(str(year))
    if pages:
        detail_parts.append(pages)
    if detail_parts:
        parts.append(", ".join(detail_parts) + ".")

    return " ".join(parts)


def format_chapter_citation_chicago(chapter) -> str:
    """
    Format chapter citation in Chicago 17th edition style.

    Format: Author. "Chapter Title." In *Book Title*, edited by Editor,
    pp. first-last. Place: Publisher, Year.
    """
    contributors = _get_chapter_contributors_ordered(chapter)
    monograph = chapter.monograph

    # Author formatting
    if len(contributors) == 0:
        author_str = ""
    elif len(contributors) == 1:
        c = contributors[0]
        author_str = f"{c.surname}, {c.given_name}" if c.given_name else c.surname
    elif len(contributors) == 2:
        c1 = contributors[0]
        c2 = contributors[1]
        first = f"{c1.surname}, {c1.given_name}" if c1.given_name else c1.surname
        second = f"{c2.given_name} {c2.surname}" if c2.given_name else c2.surname
        author_str = f"{first}, and {second}"
    else:
        c1 = contributors[0]
        first = f"{c1.surname}, {c1.given_name}" if c1.given_name else c1.surname
        rest = []
        for c in contributors[1:-1]:
            rest.append(f"{c.given_name} {c.surname}" if c.given_name else c.surname)
        last = contributors[-1]
        last_str = f"{last.given_name} {last.surname}" if last.given_name else last.surname
        author_str = first + ", " + ", ".join(rest) + ", and " + last_str if rest else f"{first}, and {last_str}"

    chapter_title = _get_chapter_full_title(chapter)
    book_title = _get_monograph_full_title(monograph)
    year = monograph.year or ""
    place = getattr(monograph, "publication_place", "") or ""

    # Editors
    editors = _get_monograph_editors(monograph)
    if editors:
        editor_parts = []
        for e in editors:
            editor_parts.append(f"{e.given_name} {e.surname}" if e.given_name else e.surname)
        editor_str = " and ".join(editor_parts) if len(editor_parts) <= 2 else editor_parts[0] + ", et al."
    else:
        editor_str = ""

    try:
        publisher = monograph.publisher.name
    except AttributeError:
        publisher = ""

    pages = ""
    if chapter.first_page:
        if chapter.last_page:
            pages = f"{chapter.first_page}-{chapter.last_page}"
        else:
            pages = chapter.first_page

    # Build citation
    parts = []
    if author_str:
        parts.append(f"{author_str}.")
    if chapter_title:
        parts.append(f'"{chapter_title}."')

    # In *Book Title*, edited by Editor, pp. X-Y.
    in_part = f"In *{book_title}*"
    if editor_str:
        in_part += f", edited by {editor_str}"
    if pages:
        in_part += f", {pages}"
    in_part += "."
    parts.append(in_part)

    # Place: Publisher, Year.
    pub_parts = []
    if place and publisher:
        pub_parts.append(f"{place}: {publisher}")
    elif publisher:
        pub_parts.append(publisher)
    elif place:
        pub_parts.append(place)
    if year:
        pub_parts.append(str(year))
    if pub_parts:
        parts.append(", ".join(pub_parts) + ".")

    return " ".join(parts)


def format_chapter_citation_bibtex(chapter) -> str:
    """
    Format chapter citation as BibTeX @incollection entry.
    """
    contributors = _get_chapter_contributors_ordered(chapter)
    monograph = chapter.monograph
    chapter_title = _get_chapter_full_title(chapter)
    book_title = _get_monograph_full_title(monograph)

    # BibTeX key from doi_suffix
    key = chapter.doi_suffix.replace("/", "_").replace(".", "_") if chapter.doi_suffix else "chapter"

    # Chapter authors
    author_parts = []
    for c in contributors:
        if c.given_name:
            author_parts.append(f"{c.surname}, {c.given_name}")
        else:
            author_parts.append(c.surname)
    author_str = " and ".join(author_parts)

    # Book editors
    editors = _get_monograph_editors(monograph)
    editor_parts = []
    for e in editors:
        if e.given_name:
            editor_parts.append(f"{e.surname}, {e.given_name}")
        else:
            editor_parts.append(e.surname)
    editor_str = " and ".join(editor_parts)

    year = str(monograph.year) if monograph.year else ""

    try:
        publisher = monograph.publisher.name
    except AttributeError:
        publisher = ""

    pages = ""
    if chapter.first_page:
        if chapter.last_page:
            pages = f"{chapter.first_page}--{chapter.last_page}"
        else:
            pages = chapter.first_page

    doi = chapter.full_doi

    # Build BibTeX entry fields
    fields = []
    if author_str:
        fields.append(f"  author = {{{author_str}}}")
    fields.append(f"  title = {{{chapter_title}}}")
    fields.append(f"  booktitle = {{{book_title}}}")
    if editor_str:
        fields.append(f"  editor = {{{editor_str}}}")
    if publisher:
        fields.append(f"  publisher = {{{publisher}}}")
    if year:
        fields.append(f"  year = {{{year}}}")
    if pages:
        fields.append(f"  pages = {{{pages}}}")
    if doi:
        fields.append(f"  doi = {{{doi}}}")
        fields.append(f"  url = {{https://doi.org/{doi}}}")

    lines = [f"@incollection{{{key},"]
    lines.append(",\n".join(fields))
    lines.append("}")

    return "\n".join(lines)


def format_chapter_citation_ris(chapter) -> str:
    """
    Format chapter citation in RIS format.
    """
    contributors = _get_chapter_contributors_ordered(chapter)
    monograph = chapter.monograph
    doi = chapter.full_doi

    lines = ["TY  - CHAP"]

    for c in contributors:
        name = f"{c.surname}, {c.given_name}" if c.given_name else c.surname
        lines.append(f"AU  - {name}")

    chapter_title = _get_chapter_full_title(chapter)
    if chapter_title:
        lines.append(f"TI  - {chapter_title}")

    book_title = _get_monograph_full_title(monograph)
    if book_title:
        lines.append(f"T2  - {book_title}")

    # Editors
    editors = _get_monograph_editors(monograph)
    for e in editors:
        name = f"{e.surname}, {e.given_name}" if e.given_name else e.surname
        lines.append(f"ED  - {name}")

    try:
        publisher = monograph.publisher.name
        if publisher:
            lines.append(f"PB  - {publisher}")
    except AttributeError:
        pass

    place = getattr(monograph, "publication_place", "") or ""
    if place:
        lines.append(f"CY  - {place}")

    if monograph.year:
        lines.append(f"PY  - {monograph.year}")

    if chapter.first_page:
        lines.append(f"SP  - {chapter.first_page}")
    if chapter.last_page:
        lines.append(f"EP  - {chapter.last_page}")

    isbn = monograph.isbn_print or monograph.isbn_online or ""
    if isbn:
        lines.append(f"SN  - {isbn}")

    if doi:
        lines.append(f"DO  - {doi}")
        lines.append(f"UR  - https://doi.org/{doi}")

    lines.append("ER  -")

    return "\n".join(lines)


# =============================================================================
# Monograph/Chapter PDF Download Filename Helpers
# =============================================================================


def get_monograph_pdf_download_filename(monograph) -> str:
    """Generate download filename for monograph PDF."""
    doi_slug = slugify(monograph.doi_suffix)
    title_slug = slugify(monograph.title)[:50]
    if not title_slug:
        return f"{doi_slug}.pdf"
    return f"{doi_slug}_{title_slug}.pdf"


def get_chapter_pdf_download_filename(chapter) -> str:
    """Generate download filename for chapter PDF."""
    doi_slug = slugify(chapter.doi_suffix)
    title_slug = slugify(chapter.title)[:50]
    if not title_slug:
        return f"{doi_slug}.pdf"
    return f"{doi_slug}_{title_slug}.pdf"
