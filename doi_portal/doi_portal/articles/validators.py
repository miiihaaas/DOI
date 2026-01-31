"""
Article validators for DOI Portal.

Story 3.2: ORCID format validator for Author model.
"""

from __future__ import annotations

import re

from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _


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
