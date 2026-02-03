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

if TYPE_CHECKING:
    from datetime import datetime

    from doi_portal.issues.models import Issue

__all__ = ["CrossrefService"]


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
            "issue": ["volume", "year", "publication_date"],
            "article": ["title", "doi_suffix"],
            "author": ["surname", "sequence", "contributor_role"],
        },
        "CONFERENCE": {
            "publication": ["title", "conference_name"],
            "issue": ["year", "publication_date"],
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
        for article in issue.articles.filter(is_deleted=False):
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
            articles_data.append({
                "title": article.title,
                "subtitle": article.subtitle,
                "abstract": article.abstract,
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
                "authors": authors_data,
            })

        # Build full context
        return {
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
                "publication_date": issue.publication_date,
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

