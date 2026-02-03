"""
Validation data classes for pre-generation validation.

Story 5.2: Pre-Generation Validation & Warnings.
Provides ValidationResult and ValidationIssue for tracking validation issues.
"""

from __future__ import annotations

from dataclasses import dataclass
from dataclasses import field
from enum import Enum
from typing import Optional

__all__ = [
    "ValidationIssue",
    "ValidationResult",
    "ValidationSeverity",
]


class ValidationSeverity(Enum):
    """Severity levels for validation issues."""

    ERROR = "error"  # Blocking - cannot generate XML
    WARNING = "warning"  # Non-blocking - can generate but may have issues


@dataclass
class ValidationIssue:
    """
    Represents a single validation issue.

    Attributes:
        severity: ERROR (blocking) or WARNING (non-blocking)
        message: Human-readable description of the issue (Serbian)
        field_name: Name of the field with the issue
        article_id: Optional ID of the article with the issue
        fix_url: Optional URL to fix the issue
    """

    severity: ValidationSeverity
    message: str
    field_name: str
    article_id: Optional[int] = None
    fix_url: Optional[str] = None


@dataclass
class ValidationResult:
    """
    Container for validation results.

    Collects validation issues and provides helper methods
    to check validity and filter by severity.
    """

    issues: list[ValidationIssue] = field(default_factory=list)

    @property
    def is_valid(self) -> bool:
        """
        Check if validation passed (no errors).

        Returns:
            True if no ERROR severity issues exist
        """
        return not any(i.severity == ValidationSeverity.ERROR for i in self.issues)

    @property
    def errors(self) -> list[ValidationIssue]:
        """
        Get all ERROR severity issues.

        Returns:
            List of ValidationIssue with ERROR severity
        """
        return [i for i in self.issues if i.severity == ValidationSeverity.ERROR]

    @property
    def warnings(self) -> list[ValidationIssue]:
        """
        Get all WARNING severity issues.

        Returns:
            List of ValidationIssue with WARNING severity
        """
        return [i for i in self.issues if i.severity == ValidationSeverity.WARNING]

    def has_errors(self) -> bool:
        """
        Check if any errors exist.

        Returns:
            True if at least one ERROR severity issue exists
        """
        return len(self.errors) > 0

    def has_warnings(self) -> bool:
        """
        Check if any warnings exist.

        Returns:
            True if at least one WARNING severity issue exists
        """
        return len(self.warnings) > 0

    def all_issues(self) -> list[ValidationIssue]:
        """
        Get all issues regardless of severity.

        Returns:
            List of all ValidationIssue objects
        """
        return self.issues.copy()

    def add_error(
        self,
        message: str,
        field_name: str,
        article_id: Optional[int] = None,
        fix_url: Optional[str] = None,
    ) -> None:
        """
        Add an ERROR severity issue.

        Args:
            message: Human-readable description
            field_name: Name of the field with the issue
            article_id: Optional ID of the article
            fix_url: Optional URL to fix the issue
        """
        self.issues.append(
            ValidationIssue(
                severity=ValidationSeverity.ERROR,
                message=message,
                field_name=field_name,
                article_id=article_id,
                fix_url=fix_url,
            )
        )

    def add_warning(
        self,
        message: str,
        field_name: str,
        article_id: Optional[int] = None,
        fix_url: Optional[str] = None,
    ) -> None:
        """
        Add a WARNING severity issue.

        Args:
            message: Human-readable description
            field_name: Name of the field with the issue
            article_id: Optional ID of the article
            fix_url: Optional URL to fix the issue
        """
        self.issues.append(
            ValidationIssue(
                severity=ValidationSeverity.WARNING,
                message=message,
                field_name=field_name,
                article_id=article_id,
                fix_url=fix_url,
            )
        )

    def merge(self, other: ValidationResult) -> None:
        """
        Merge another ValidationResult into this one.

        Args:
            other: ValidationResult to merge issues from
        """
        self.issues.extend(other.issues)
