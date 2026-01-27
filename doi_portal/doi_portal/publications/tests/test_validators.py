"""
Tests for Publication validators.

Story 2.3 - Task 7.3, 7.4: ISSN and ISBN format validation.
"""

import pytest
from django.core.exceptions import ValidationError

from doi_portal.publications.validators import validate_isbn, validate_issn


# =============================================================================
# Task 7.3: Test ISSN format validation
# =============================================================================


class TestValidateISSN:
    """Test validate_issn function."""

    def test_valid_issn_numeric(self):
        """Test valid ISSN with all numeric digits."""
        # Should not raise
        validate_issn("1234-5678")

    def test_valid_issn_with_x_check_digit(self):
        """Test valid ISSN with X as check digit."""
        validate_issn("0000-000X")

    def test_valid_issn_real_example(self):
        """Test valid real-world ISSN examples."""
        validate_issn("0378-5955")  # Hearing Research
        validate_issn("2049-3630")  # Real ISSN

    def test_blank_issn_allowed(self):
        """Test blank ISSN passes validation (field is optional)."""
        validate_issn("")
        validate_issn(None)  # type: ignore

    def test_invalid_issn_missing_hyphen(self):
        """Test ISSN without hyphen raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            validate_issn("12345678")
        assert exc_info.value.code == "invalid_issn"

    def test_invalid_issn_too_short(self):
        """Test ISSN with too few digits raises ValidationError."""
        with pytest.raises(ValidationError):
            validate_issn("1234-567")

    def test_invalid_issn_too_long(self):
        """Test ISSN with too many digits raises ValidationError."""
        with pytest.raises(ValidationError):
            validate_issn("1234-56789")

    def test_invalid_issn_letters(self):
        """Test ISSN with letters (except X) raises ValidationError."""
        with pytest.raises(ValidationError):
            validate_issn("ABCD-5678")

    def test_invalid_issn_wrong_hyphen_position(self):
        """Test ISSN with hyphen in wrong position raises ValidationError."""
        with pytest.raises(ValidationError):
            validate_issn("12-345678")

    def test_invalid_issn_lowercase_x(self):
        """Test ISSN with lowercase x in check digit raises ValidationError."""
        with pytest.raises(ValidationError):
            validate_issn("0000-000x")


# =============================================================================
# Task 7.4: Test ISBN format validation
# =============================================================================


class TestValidateISBN:
    """Test validate_isbn function."""

    def test_valid_isbn_with_hyphens(self):
        """Test valid ISBN-13 with hyphens."""
        validate_isbn("978-86-7549-123-4")

    def test_valid_isbn_without_hyphens(self):
        """Test valid ISBN-13 without hyphens."""
        validate_isbn("9788675491234")

    def test_valid_isbn_979_prefix(self):
        """Test valid ISBN-13 with 979 prefix."""
        validate_isbn("979-10-1234-567-8")
        validate_isbn("9791012345678")

    def test_valid_isbn_real_example(self):
        """Test valid real-world ISBN examples."""
        validate_isbn("978-0-13-468599-1")  # Clean Code
        validate_isbn("978-0-596-51774-8")  # JavaScript: The Good Parts

    def test_blank_isbn_allowed(self):
        """Test blank ISBN passes validation (field is optional)."""
        validate_isbn("")
        validate_isbn(None)  # type: ignore

    def test_invalid_isbn_wrong_length(self):
        """Test ISBN with wrong length raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            validate_isbn("978-86-7549-12")  # Too short
        assert exc_info.value.code == "invalid_isbn"

    def test_invalid_isbn_too_long(self):
        """Test ISBN with too many digits raises ValidationError."""
        with pytest.raises(ValidationError):
            validate_isbn("978-86-7549-1234-56")  # Too long

    def test_invalid_isbn_wrong_prefix(self):
        """Test ISBN not starting with 978/979 raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            validate_isbn("123-45-6789-012-3")
        assert exc_info.value.code == "invalid_isbn_prefix"

    def test_invalid_isbn_letters(self):
        """Test ISBN with letters raises ValidationError."""
        with pytest.raises(ValidationError):
            validate_isbn("978-XX-7549-123-4")

    def test_invalid_isbn_10_digit(self):
        """Test old ISBN-10 format raises ValidationError (we only support ISBN-13)."""
        with pytest.raises(ValidationError):
            validate_isbn("0-596-51774-8")  # ISBN-10 format
