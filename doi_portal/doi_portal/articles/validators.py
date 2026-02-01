"""
Article validators for DOI Portal.

Story 3.2: ORCID format validator for Author model.
Story 3.3: PDF file validator for upload (type, size, extension).
"""

from __future__ import annotations

import re

from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

# PDF upload constraints
MAX_PDF_SIZE = 100 * 1024 * 1024  # 100 MB


def validate_orcid(value: str) -> None:
    """
    Validate ORCID format: 0000-0000-0000-000X

    Pattern: 4 groups of 4 digits separated by dashes,
    last character can be digit or uppercase X.

    Args:
        value: ORCID identifier string to validate.

    Raises:
        ValidationError: If the ORCID format is invalid.
    """
    if not value:
        return  # Empty is OK (field is optional/blank=True)

    pattern = r"^\d{4}-\d{4}-\d{4}-\d{3}[\dX]$"
    if not re.match(pattern, value):
        raise ValidationError(
            _("Neispravan ORCID format. Očekivani format: 0000-0000-0000-000X"),
            code="invalid_orcid",
        )


def validate_pdf_file(file) -> list[str]:
    """
    Validate uploaded PDF file.

    Checks:
    1. File extension is .pdf
    2. Content-Type is application/pdf
    3. File size <= 100 MB

    Args:
        file: Django UploadedFile instance.

    Returns:
        List of error strings (empty if valid).
    """
    errors = []

    # Check file extension
    if not file.name.lower().endswith(".pdf"):
        errors.append("Dozvoljeni su samo PDF fajlovi.")
        return errors

    # Check Content-Type
    if hasattr(file, "content_type") and file.content_type != "application/pdf":
        errors.append("Dozvoljeni su samo PDF fajlovi.")
        return errors

    # Check file size
    if file.size > MAX_PDF_SIZE:
        errors.append("Maksimalna veličina fajla je 100 MB.")
        return errors

    return errors
