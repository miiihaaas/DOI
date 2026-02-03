"""
Crossref XML validators.

Story 5.1: Crossref Service Infrastructure.
XSD validation stubs - full implementation in Story 5.4.
"""

from __future__ import annotations

__all__ = ["validate_xml"]


def validate_xml(xml_string: str) -> tuple[bool, list[str]]:
    """
    Validate XML against Crossref XSD schema.

    Note: This is a stub implementation. Full XSD validation
    will be implemented in Story 5.4.

    Args:
        xml_string: XML string to validate

    Returns:
        Tuple of (is_valid, error_messages)
        - is_valid: True if XML is valid
        - error_messages: List of validation error strings
    """
    # Stub implementation - always returns valid
    # Full XSD validation will be implemented in Story 5.4
    return (True, [])
