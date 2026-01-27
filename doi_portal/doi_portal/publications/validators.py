"""
Publication validators.

Story 2.3: ISSN and ISBN format validators for Publication model.
"""

import re

from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

__all__ = [
    "validate_issn",
    "validate_isbn",
]


def validate_issn(value: str) -> None:
    """
    Validate ISSN format: ####-#### or ####-###X.

    ISSN (International Standard Serial Number) has 8 characters:
    4 digits, hyphen, 3 digits, check character (digit or X).

    Args:
        value: ISSN string to validate

    Raises:
        ValidationError: If format is invalid
    """
    if not value:
        return  # Blank is allowed

    pattern = r"^\d{4}-\d{3}[\dX]$"
    if not re.match(pattern, value):
        raise ValidationError(
            _("ISSN mora biti u formatu '####-####' (npr. '1234-5678')"),
            code="invalid_issn",
        )


def validate_isbn(value: str) -> None:
    """
    Validate ISBN-13 format.

    ISBN-13 has 13 digits and must start with 978 or 979.
    Can be with or without hyphens.

    Args:
        value: ISBN string to validate

    Raises:
        ValidationError: If format is invalid
    """
    if not value:
        return  # Blank is allowed

    # Remove hyphens for validation
    clean_isbn = value.replace("-", "")

    # Must be 13 digits
    if not re.match(r"^\d{13}$", clean_isbn):
        raise ValidationError(
            _("ISBN mora imati 13 cifara (npr. '978-86-7549-123-4')"),
            code="invalid_isbn",
        )

    # Must start with 978 or 979
    if not clean_isbn.startswith(("978", "979")):
        raise ValidationError(
            _("ISBN-13 mora početi sa '978' ili '979'"),
            code="invalid_isbn_prefix",
        )
