"""
Crossref XML validators.

Story 5.1: Crossref Service Infrastructure.
Story 5.4: XSD Validation.

Provides XSD validation for generated Crossref XML using lxml.etree.XMLSchema.
"""

from __future__ import annotations

from dataclasses import dataclass
from dataclasses import field
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING

from lxml import etree

if TYPE_CHECKING:
    from lxml.etree import _Element  # noqa: F401

__all__ = ["validate_xml", "XSDValidationResult", "XSDValidationError"]


@dataclass
class XSDValidationError:
    """
    Single XSD validation error.

    Represents a single error from XSD schema validation,
    including location information when available.
    """

    message: str
    line: int | None = None
    column: int | None = None
    element: str | None = None

    def to_dict(self) -> dict:
        """
        Convert to dictionary for JSON storage.

        Returns:
            Dictionary with error details
        """
        return {
            "message": self.message,
            "line": self.line,
            "column": self.column,
            "element": self.element,
        }


@dataclass
class XSDValidationResult:
    """
    XSD validation result container.

    Contains validation status, any errors, and timestamp.
    """

    is_valid: bool
    errors: list[XSDValidationError] = field(default_factory=list)
    validated_at: datetime | None = None

    def to_dict(self) -> dict:
        """
        Convert to dictionary for JSON storage.

        Returns:
            Dictionary with validation result
        """
        return {
            "is_valid": self.is_valid,
            "errors": [e.to_dict() for e in self.errors],
            "validated_at": self.validated_at.isoformat() if self.validated_at else None,
        }


# Schema cache (load once, reuse)
_SCHEMA_CACHE: etree.XMLSchema | None = None


def _get_schema() -> etree.XMLSchema:
    """
    Load and cache the Crossref XSD schema.

    Loads the Crossref 5.4.0 XSD schema from the bundled schema files.
    The schema is cached at module level for performance.

    Returns:
        Compiled XMLSchema object

    Raises:
        RuntimeError: If schema files cannot be loaded
    """
    global _SCHEMA_CACHE

    if _SCHEMA_CACHE is None:
        schema_path = Path(__file__).parent / "schemas" / "crossref5.4.0.xsd"

        if not schema_path.exists():
            raise RuntimeError(
                f"Crossref XSD schema not found at {schema_path}. "
                "Please download from https://www.crossref.org/schemas/"
            )

        try:
            schema_doc = etree.parse(str(schema_path))
            _SCHEMA_CACHE = etree.XMLSchema(schema_doc)
        except etree.XMLSchemaParseError as e:
            raise RuntimeError(f"Failed to parse XSD schema: {e}") from e

    return _SCHEMA_CACHE


def validate_xml(xml_string: str) -> XSDValidationResult:
    """
    Validate XML against Crossref XSD schema 5.4.0.

    Parses the XML string and validates it against the bundled
    Crossref XSD schema. Returns a structured result with
    validation status and any errors.

    Args:
        xml_string: XML string to validate

    Returns:
        XSDValidationResult with validation status and any errors
    """
    from django.utils import timezone

    result = XSDValidationResult(
        is_valid=False,
        validated_at=timezone.now(),
    )

    # Handle empty string
    if not xml_string or not xml_string.strip():
        result.errors.append(
            XSDValidationError(
                message="XML sintaksna greška: prazan sadržaj",
                line=1,
            )
        )
        return result

    # Parse XML string
    try:
        xml_doc = etree.fromstring(xml_string.encode("utf-8"))
    except etree.XMLSyntaxError as e:
        result.errors.append(
            XSDValidationError(
                message=f"XML sintaksna greška: {e.msg}",
                line=e.lineno,
                column=e.offset,
            )
        )
        return result

    # Get schema and validate
    try:
        schema = _get_schema()
    except RuntimeError as e:
        result.errors.append(
            XSDValidationError(
                message=str(e),
            )
        )
        return result

    # Run validation
    is_valid = schema.validate(xml_doc)
    result.is_valid = is_valid

    if not is_valid:
        for error in schema.error_log:
            result.errors.append(
                XSDValidationError(
                    message=error.message,
                    line=error.line,
                    column=error.column,
                    element=getattr(error, "path", None),
                )
            )

    return result
