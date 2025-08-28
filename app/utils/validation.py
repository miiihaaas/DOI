"""
Validation constants and patterns for data validation.
"""

# ISSN validation pattern (format: 1234-567X)
ISSN_PATTERN = r'^[0-9]{4}-[0-9]{3}[0-9X]$'

# ISBN validation patterns
ISBN_10_PATTERN = r'^[0-9]{9}[0-9X]$'
ISBN_13_PATTERN = r'^97[89][0-9]{10}$'
ISBN_PATTERN = r'^(97[89])?[0-9]{9}[0-9X]$'

# DOI pattern (format: 10.xxxx/xxxx)
DOI_PATTERN = r'^10\.[0-9]+/.+$'

# ORCID pattern (format: https://orcid.org/0000-0000-0000-0000)
ORCID_PATTERN = r'^https://orcid\.org/\d{4}-\d{4}-\d{4}-\d{3}[\dX]$'

# Language code pattern (ISO 639-1)
LANGUAGE_CODE_PATTERN = r'^[a-z]{2}$'

# Publication year range
MIN_PUBLICATION_YEAR = 1000
MAX_PUBLICATION_YEAR = 9999

# Month range
MIN_MONTH = 1
MAX_MONTH = 12

# Day range
MIN_DAY = 1
MAX_DAY = 31


def validate_issn(issn):
    """Validate ISSN format."""
    import re
    return bool(re.match(ISSN_PATTERN, issn))


def validate_isbn(isbn):
    """Validate ISBN format (both ISBN-10 and ISBN-13)."""
    import re
    return bool(re.match(ISBN_PATTERN, isbn))


def validate_doi(doi):
    """Validate DOI format."""
    import re
    return bool(re.match(DOI_PATTERN, doi))


def validate_orcid(orcid):
    """Validate ORCID format."""
    import re
    return bool(re.match(ORCID_PATTERN, orcid))


def validate_language_code(language_code):
    """Validate ISO 639-1 language code."""
    import re
    return bool(re.match(LANGUAGE_CODE_PATTERN, language_code.lower()))


def validate_publication_year(year):
    """Validate publication year range."""
    return MIN_PUBLICATION_YEAR <= year <= MAX_PUBLICATION_YEAR


def validate_month(month):
    """Validate month range."""
    return MIN_MONTH <= month <= MAX_MONTH


def validate_day(day):
    """Validate day range."""
    return MIN_DAY <= day <= MAX_DAY