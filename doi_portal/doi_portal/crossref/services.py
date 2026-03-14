"""
Crossref service layer for XML generation.

Story 5.1: Crossref Service Infrastructure.
Provides the CrossrefService class for generating Crossref XML.
"""

from __future__ import annotations

import uuid
from pathlib import Path
from typing import TYPE_CHECKING
from typing import Any

from django.utils import timezone
from jinja2 import Environment
from jinja2 import FileSystemLoader
from jinja2 import select_autoescape
from markupsafe import Markup

if TYPE_CHECKING:
    from datetime import datetime

    from doi_portal.articles.models import Article
    from doi_portal.articles.models import Author
    from doi_portal.issues.models import Issue

from doi_portal.core.markup import markup_to_crossref_xml, markup_to_jats_xml
from doi_portal.crossref.validation import ValidationResult

__all__ = ["CrossrefService", "PreValidationService"]


def xml_escape(value: str | None) -> str:
    """
    Escape XML special characters.

    Args:
        value: String to escape

    Returns:
        XML-safe string
    """
    if value is None:
        return ""
    replacements = [
        ("&", "&amp;"),
        ("<", "&lt;"),
        (">", "&gt;"),
        ('"', "&quot;"),
        ("'", "&apos;"),
    ]
    result = str(value)
    for old, new in replacements:
        result = result.replace(old, new)
    return result


def format_date(date_value: datetime | None, fmt: str = "%Y%m%d") -> str:
    """
    Format a date for Crossref XML.

    Args:
        date_value: Date to format
        fmt: strftime format string

    Returns:
        Formatted date string or empty string if None
    """
    if date_value is None:
        return ""
    return date_value.strftime(fmt)


def format_month(value: int | None) -> str:
    """Format month number as two-digit string (e.g., 3 → '03')."""
    if value is None:
        return ""
    return f"{int(value):02d}"


def format_day(value: int | None) -> str:
    """Format day number as two-digit string (e.g., 5 → '05')."""
    if value is None:
        return ""
    return f"{int(value):02d}"


def format_orcid_url(orcid: str | None) -> str:
    """
    Format ORCID as full URL.

    Args:
        orcid: ORCID identifier (0000-0000-0000-0000)

    Returns:
        Full ORCID URL or empty string
    """
    if not orcid:
        return ""
    # Remove any existing URL prefix
    orcid_clean = orcid.replace("https://orcid.org/", "")
    orcid_clean = orcid_clean.replace("http://orcid.org/", "")
    return f"https://orcid.org/{orcid_clean}"


class CrossrefService:
    """
    Service class for generating Crossref XML.

    Handles XML generation for all publication types:
    - Journal articles
    - Conference papers
    - Book chapters
    """

    # Template mapping by publication type
    TEMPLATE_MAP = {
        "JOURNAL": "journal_article.xml.j2",
        "CONFERENCE": "conference_paper.xml.j2",
        "BOOK": "book_chapter.xml.j2",
        "OTHER": "journal_article.xml.j2",  # Default to journal format
    }

    # Required fields by publication type
    REQUIRED_FIELDS = {
        "JOURNAL": {
            "publication": ["title", "issn_print", "issn_online"],
            "issue": ["volume", "year"],
            "article": ["title", "doi_suffix"],
            "author": ["surname", "sequence", "contributor_role"],
        },
        "CONFERENCE": {
            "publication": ["title", "conference_name"],
            "issue": ["year"],
            "article": ["title", "doi_suffix"],
            "author": ["surname", "sequence", "contributor_role"],
        },
        "BOOK": {
            "publication": ["title"],
            "issue": ["year"],
            "article": ["title", "doi_suffix"],
            "author": ["surname", "sequence", "contributor_role"],
        },
    }

    def __init__(self) -> None:
        """Initialize the CrossrefService with Jinja2 environment."""
        # Template directory
        template_dir = Path(__file__).parent / "templates" / "crossref"

        # Configure Jinja2 environment for XML
        self.env = Environment(
            loader=FileSystemLoader(str(template_dir)),
            autoescape=select_autoescape(
                enabled_extensions=("xml", "j2"),
                default_for_string=True,
            ),
            trim_blocks=True,
            lstrip_blocks=True,
        )

        # Add custom filters
        self.env.filters["xml_escape"] = xml_escape
        self.env.filters["format_date"] = format_date
        self.env.filters["format_orcid_url"] = format_orcid_url
        self.env.filters["format_month"] = format_month
        self.env.filters["format_day"] = format_day

    def generate_doi_batch_id(self) -> str:
        """
        Generate a unique DOI batch ID.

        Format: UUID_TIMESTAMP (e.g., "a1b2c3d4_20260203123045")

        Returns:
            Unique batch ID string
        """
        uuid_part = uuid.uuid4().hex[:8]
        timestamp = timezone.now().strftime("%Y%m%d%H%M%S")
        return f"{uuid_part}_{timestamp}"

    def generate_head(self, issue: Issue) -> dict[str, Any]:
        """
        Generate head metadata context for Crossref XML.

        Args:
            issue: Issue model instance

        Returns:
            Dictionary with head context data
        """
        from doi_portal.core.models import SiteSettings

        # Get site settings for depositor info
        settings = SiteSettings.get_settings()

        # Get publisher from publication
        publisher = issue.publication.publisher

        return {
            "doi_batch_id": self.generate_doi_batch_id(),
            "timestamp": timezone.now().strftime("%Y%m%d%H%M%S"),
            "depositor_name": settings.depositor_name or "DOI Portal",
            "depositor_email": settings.depositor_email or "admin@example.com",
            "registrant": publisher.name,
        }

    def get_required_fields(self, publication_type: str) -> dict[str, list[str]]:
        """
        Get required fields for a given publication type.

        Args:
            publication_type: Publication type (JOURNAL, CONFERENCE, BOOK, OTHER)

        Returns:
            Dictionary mapping entity types to lists of required field names
        """
        return self.REQUIRED_FIELDS.get(
            publication_type,
            self.REQUIRED_FIELDS["JOURNAL"],  # Default
        )

    def _get_template_name(self, publication_type: str) -> str:
        """
        Get the template filename for a publication type.

        Args:
            publication_type: Publication type string

        Returns:
            Template filename
        """
        return self.TEMPLATE_MAP.get(publication_type, self.TEMPLATE_MAP["JOURNAL"])

    @staticmethod
    def _normalize_funder_doi(doi_url: str) -> str:
        """Normalize funder DOI to Crossref FundRef expected format.

        Crossref expects http://dx.doi.org/10.13039/... format.
        """
        if not doi_url:
            return ""
        # Extract the DOI from various URL formats
        for prefix in ("https://doi.org/", "http://doi.org/", "https://dx.doi.org/", "http://dx.doi.org/"):
            if doi_url.startswith(prefix):
                bare_doi = doi_url[len(prefix):]
                return f"http://dx.doi.org/{bare_doi}"
        # If it's already a bare DOI like 10.13039/...
        if doi_url.startswith("10."):
            return f"http://dx.doi.org/{doi_url}"
        return doi_url

    def _get_site_url(self) -> str:
        """
        Get the site URL for resource links in Crossref XML.

        Uses Django Sites framework to construct the base URL.
        Protocol is controlled by CROSSREF_SITE_PROTOCOL setting (default: "https").

        Returns:
            Site URL without trailing slash (e.g., 'https://publikacije.doi.rs')

        Raises:
            ValueError: If Site is not configured or domain is the default 'example.com'.
        """
        if hasattr(self, "_cached_site_url"):
            return self._cached_site_url

        from django.conf import settings
        from django.contrib.sites.models import Site

        try:
            site = Site.objects.get_current()
        except Site.DoesNotExist:
            raise ValueError(
                "Django Site is not configured. "
                "Please add a Site via admin or run: "
                "Site.objects.create(domain='your-domain.com', name='Your Site')"
            )

        if site.domain == "example.com":
            raise ValueError(
                "Django Site domain is still the default 'example.com'. "
                "Please update it to your actual domain."
            )

        protocol = getattr(settings, "CROSSREF_SITE_PROTOCOL", "https")
        domain = site.domain.strip("/")
        result = f"{protocol}://{domain}"
        self._cached_site_url = result
        return result

    def _build_context(self, issue: Issue) -> dict[str, Any]:
        """
        Build the full template context from an Issue.

        Args:
            issue: Issue model instance

        Returns:
            Context dictionary for template rendering
        """
        publication = issue.publication
        publisher = publication.publisher

        # Build articles context with authors and affiliations
        articles_data = []
        for article in issue.articles.filter(is_deleted=False).prefetch_related(
            "authors__affiliations", "fundings"
        ):
            authors_data = []
            for author in article.authors.all().order_by("order"):
                affiliations_data = [
                    {
                        "institution_name": aff.institution_name,
                        "institution_ror_id": aff.institution_ror_id,
                        "department": aff.department,
                    }
                    for aff in author.affiliations.all().order_by("order")
                ]
                authors_data.append({
                    "given_name": author.given_name,
                    "surname": author.surname,
                    "suffix": author.suffix,
                    "orcid": author.orcid,
                    "orcid_authenticated": author.orcid_authenticated,
                    "sequence": author.sequence,
                    "contributor_role": author.contributor_role,
                    "affiliations": affiliations_data,
                })
            # Markup() prevents Jinja2 autoescape from double-escaping face markup tags
            articles_data.append({
                "pk": article.pk,
                "title": Markup(markup_to_crossref_xml(article.title)),
                "subtitle": Markup(markup_to_crossref_xml(article.subtitle)),
                "original_language_title": Markup(markup_to_crossref_xml(article.original_language_title)),
                "original_language_subtitle": Markup(markup_to_crossref_xml(article.original_language_subtitle)),
                "original_language_title_language": article.original_language_title_language,
                "abstract": Markup(markup_to_jats_xml(article.abstract)),
                "doi_suffix": article.doi_suffix,
                "first_page": article.first_page,
                "last_page": article.last_page,
                "article_number": article.article_number,
                "language": article.language,
                "publication_type": article.publication_type,
                "license_url": article.license_url,
                "license_applies_to": article.license_applies_to,
                "free_to_read": article.free_to_read,
                "free_to_read_start_date": article.free_to_read_start_date,
                "use_external_resource": article.use_external_resource,
                "external_landing_url": article.external_landing_url,
                "external_pdf_url": article.external_pdf_url,
                "authors": authors_data,
                "fundings": [
                    {
                        "funder_name": f.funder_name,
                        "funder_doi": self._normalize_funder_doi(f.funder_doi),
                        "award_number": f.award_number,
                    }
                    for f in article.fundings.order_by("order")
                ],
            })

        # Build full context
        return {
            "site_url": self._get_site_url(),
            "head": self.generate_head(issue),
            "publisher": {
                "name": publisher.name,
                "doi_prefix": publisher.doi_prefix,
            },
            "publication": {
                "title": publication.title,
                "publication_type": publication.publication_type,
                "language": publication.language,
                # Journal fields
                "issn_print": publication.issn_print,
                "issn_online": publication.issn_online,
                "abbreviation": publication.abbreviation,
                # Conference fields
                "conference_name": publication.conference_name,
                "conference_acronym": publication.conference_acronym,
                "conference_location": publication.conference_location,
                "conference_date": publication.conference_date,
                "conference_date_end": publication.conference_date_end,
                "conference_number": publication.conference_number,
                # Book fields
                "isbn_print": publication.isbn_print,
                "isbn_online": publication.isbn_online,
                "edition": publication.edition,
                "series_title": publication.series_title,
            },
            "issue": {
                "volume": issue.volume,
                "issue_number": issue.issue_number,
                "year": issue.year,
                "title": issue.title,
                "publication_month": issue.publication_month,
                "publication_day": issue.publication_day,
                # Conference proceedings fields
                "proceedings_title": issue.proceedings_title,
                "proceedings_publisher_name": issue.proceedings_publisher_name,
                "proceedings_publisher_place": issue.proceedings_publisher_place,
            },
            "articles": articles_data,
        }


    def generate_xml(self, issue: Issue) -> str:
        """
        Generate Crossref XML for all articles in an issue.

        Args:
            issue: Issue model instance with related articles

        Returns:
            XML string ready for Crossref deposit
        """
        # Determine template based on publication type
        publication_type = issue.publication.publication_type
        template_name = self._get_template_name(publication_type)

        # Build context
        context = self._build_context(issue)

        # Render template
        template = self.env.get_template(template_name)
        return template.render(**context)

    def generate_and_store_xml(self, issue: Issue) -> tuple[bool, str]:
        """
        Generate, store, and validate XML for an issue.

        Story 5.3: XML Generation for All Publication Types.
        Story 5.4: XSD Validation.

        Generates XML using the existing generate_xml() method,
        stores result in Issue model fields, records timestamp,
        and runs XSD validation.

        Uses transaction.atomic to ensure database consistency.

        Args:
            issue: Issue model instance

        Returns:
            Tuple of (success, xml_or_error_message)
        """
        from django.db import transaction

        from doi_portal.crossref.validators import validate_xml

        try:
            xml = self.generate_xml(issue)

            # Run XSD validation (Story 5.4)
            validation_result = validate_xml(xml)

            with transaction.atomic():
                issue.crossref_xml = xml
                issue.xml_generated_at = timezone.now()
                issue.xml_generation_status = "completed"

                # Store XSD validation results (Story 5.4)
                issue.xsd_valid = validation_result.is_valid
                issue.xsd_errors = [e.to_dict() for e in validation_result.errors]
                issue.xsd_validated_at = validation_result.validated_at

                issue.save(update_fields=[
                    "crossref_xml",
                    "xml_generated_at",
                    "xml_generation_status",
                    "xsd_valid",
                    "xsd_errors",
                    "xsd_validated_at",
                ])
            return (True, xml)
        except Exception as e:
            # Use separate transaction for failure status update
            with transaction.atomic():
                issue.xml_generation_status = "failed"
                issue.save(update_fields=["xml_generation_status"])
            return (False, str(e))


class PreValidationService:
    """
    Service for pre-generation validation of Crossref XML data.

    Story 5.2: Pre-Generation Validation & Warnings.
    Validates all required fields before XML generation to ensure
    valid Crossref submissions.
    """

    def validate_issue(self, issue: Issue) -> ValidationResult:
        """
        Run all pre-generation validations for an issue.

        Args:
            issue: Issue model instance to validate

        Returns:
            ValidationResult with all errors and warnings
        """
        from doi_portal.articles.models import ArticleStatus

        result = ValidationResult()

        # Check depositor settings first (blocking)
        result.merge(self._validate_depositor_settings())

        # Check common fields
        result.merge(self._validate_common_fields(issue))

        # Check type-specific fields
        pub_type = issue.publication.publication_type
        if pub_type == "JOURNAL":
            result.merge(self._validate_journal_fields(issue))
        elif pub_type == "CONFERENCE":
            result.merge(self._validate_conference_fields(issue))
        elif pub_type == "BOOK":
            result.merge(self._validate_book_fields(issue))

        # Validate all PUBLISHED articles only
        for article in issue.articles.filter(
            status=ArticleStatus.PUBLISHED,
            is_deleted=False,
        ):
            result.merge(self._validate_article(article))

        return result

    def _validate_depositor_settings(self) -> ValidationResult:
        """
        Validate depositor settings in SiteSettings (AC5).

        Returns:
            ValidationResult with depositor errors
        """
        from doi_portal.core.models import SiteSettings

        result = ValidationResult()
        settings = SiteSettings.get_settings()

        if not settings.depositor_name:
            result.add_error(
                message="Nedostaju depositor podaci: naziv deponenta",
                field_name="depositor_name",
                fix_url="/admin/core/sitesettings/1/change/",
            )

        if not settings.depositor_email:
            result.add_error(
                message="Nedostaju depositor podaci: email deponenta",
                field_name="depositor_email",
                fix_url="/admin/core/sitesettings/1/change/",
            )

        return result

    def _validate_common_fields(self, issue: Issue) -> ValidationResult:
        """
        Validate fields required for all publication types.

        Args:
            issue: Issue to validate

        Returns:
            ValidationResult with common field errors
        """
        result = ValidationResult()
        return result

    def _validate_journal_fields(self, issue: Issue) -> ValidationResult:
        """
        Validate journal-specific fields (AC2).

        Args:
            issue: Issue to validate

        Returns:
            ValidationResult with journal field errors
        """
        result = ValidationResult()
        publication = issue.publication

        # ISSN (print or online) is required for journals
        if not publication.issn_print and not publication.issn_online:
            result.add_error(
                message="Nedostaje ISSN (štampani ili online)",
                field_name="issn",
                fix_url=f"/dashboard/publications/{publication.slug}/edit/",
            )

        return result

    def _validate_conference_fields(self, issue: Issue) -> ValidationResult:
        """
        Validate conference-specific fields (AC3).

        Args:
            issue: Issue to validate

        Returns:
            ValidationResult with conference field errors/warnings
        """
        result = ValidationResult()
        publication = issue.publication

        # Conference name is required
        if not publication.conference_name:
            result.add_error(
                message="Nedostaje naziv konferencije",
                field_name="conference_name",
                fix_url=f"/dashboard/publications/{publication.slug}/edit/",
            )

        # Conference date is recommended (warning)
        if not publication.conference_date:
            result.add_warning(
                message="Nedostaje datum konferencije",
                field_name="conference_date",
                fix_url=f"/dashboard/publications/{publication.slug}/edit/",
            )

        # Conference location is recommended (warning)
        if not publication.conference_location:
            result.add_warning(
                message="Nedostaje lokacija konferencije",
                field_name="conference_location",
                fix_url=f"/dashboard/publications/{publication.slug}/edit/",
            )

        # Proceedings title is required (from Issue or Publication)
        if not issue.proceedings_title and not publication.title:
            result.add_error(
                message="Nedostaje naslov zbornika",
                field_name="proceedings_title",
                fix_url=f"/dashboard/issues/{issue.pk}/edit/",
            )

        return result

    def _validate_book_fields(self, issue: Issue) -> ValidationResult:
        """
        Validate book-specific fields (AC4).

        Args:
            issue: Issue to validate

        Returns:
            ValidationResult with book field errors
        """
        result = ValidationResult()
        publication = issue.publication

        # ISBN (print or online) is required for books
        if not publication.isbn_print and not publication.isbn_online:
            result.add_error(
                message="Nedostaje ISBN (štampani ili online)",
                field_name="isbn",
                fix_url=f"/dashboard/publications/{publication.slug}/edit/",
            )

        # Book title is required
        if not publication.title:
            result.add_error(
                message="Nedostaje naslov knjige",
                field_name="book_title",
                fix_url=f"/dashboard/publications/{publication.slug}/edit/",
            )

        return result

    def _validate_article(self, article: Article) -> ValidationResult:
        """
        Validate article-level fields.

        Args:
            article: Article to validate

        Returns:
            ValidationResult with article errors
        """
        result = ValidationResult()

        # Title is required
        if not article.title:
            result.add_error(
                message=f"Nedostaje naslov članka (ID: {article.pk})",
                field_name="title",
                article_id=article.pk,
                fix_url=f"/dashboard/articles/{article.pk}/edit/",
            )

        # DOI suffix is required
        if not article.doi_suffix:
            result.add_error(
                message=f"Nedostaje DOI sufiks (članak: {article.title or article.pk})",
                field_name="doi_suffix",
                article_id=article.pk,
                fix_url=f"/dashboard/articles/{article.pk}/edit/",
            )

        # At least one author is required
        authors = list(article.authors.all().order_by("order"))
        if not authors:
            result.add_error(
                message=f"Članak nema autore ({article.title or article.pk})",
                field_name="authors",
                article_id=article.pk,
                fix_url=f"/dashboard/articles/{article.pk}/edit/",
            )
        else:
            # Validate each author (determine first author once to avoid N+1 queries)
            first_author = authors[0] if authors else None
            for author in authors:
                is_first = (author == first_author)
                result.merge(self._validate_author(author, article, is_first))

        # Check external resource consistency
        if article.use_external_resource and not article.external_landing_url:
            result.add_warning(
                message=f"Eksterni URL je uključen ali landing URL nije popunjen (članak: {article.title or article.pk})",
                field_name="external_landing_url",
                article_id=article.pk,
                fix_url=f"/dashboard/articles/{article.pk}/edit/",
            )

        # Validate original language title consistency
        if article.original_language_title and not article.original_language_title_language:
            result.add_warning(
                message=f"Naslov na originalnom jeziku je popunjen ali jezik nije izabran (članak: {article.title or article.pk})",
                field_name="original_language_title_language",
                article_id=article.pk,
                fix_url=f"/dashboard/articles/{article.pk}/edit/",
            )
        if article.original_language_title_language and not article.original_language_title:
            result.add_warning(
                message=f"Jezik originalnog naslova je izabran ali naslov nije popunjen (članak: {article.title or article.pk})",
                field_name="original_language_title",
                article_id=article.pk,
                fix_url=f"/dashboard/articles/{article.pk}/edit/",
            )
        if article.original_language_subtitle and not article.original_language_title:
            result.add_warning(
                message=f"Podnaslov na originalnom jeziku je popunjen ali naslov nije (članak: {article.title or article.pk})",
                field_name="original_language_title",
                article_id=article.pk,
                fix_url=f"/dashboard/articles/{article.pk}/edit/",
            )

        return result

    def _validate_author(
        self,
        author: Author,
        article: Article,
        is_first_author: bool,
    ) -> ValidationResult:
        """
        Validate author-level fields.

        Args:
            author: Author to validate
            article: Parent article for context
            is_first_author: Whether this is the first author (by order)

        Returns:
            ValidationResult with author errors/warnings
        """
        result = ValidationResult()

        # Surname is required
        if not author.surname:
            result.add_error(
                message=f"Autor nema prezime (članak: {article.title or article.pk})",
                field_name="surname",
                article_id=article.pk,
                fix_url=f"/dashboard/articles/{article.pk}/edit/",
            )

        # Given name is recommended (warning)
        if not author.given_name:
            result.add_warning(
                message=f"Autor nema ime (članak: {article.title or article.pk})",
                field_name="given_name",
                article_id=article.pk,
                fix_url=f"/dashboard/articles/{article.pk}/edit/",
            )

        # First author must have sequence='first'
        if is_first_author and author.sequence != "first":
            result.add_error(
                message=f"Prvi autor mora imati sequence='first' (članak: {article.title or article.pk})",
                field_name="sequence",
                article_id=article.pk,
                fix_url=f"/dashboard/articles/{article.pk}/edit/",
            )

        # Contributor role is required
        if not author.contributor_role:
            result.add_error(
                message=f"Autor nema definisanu ulogu (članak: {article.title or article.pk})",
                field_name="contributor_role",
                article_id=article.pk,
                fix_url=f"/dashboard/articles/{article.pk}/edit/",
            )

        return result

