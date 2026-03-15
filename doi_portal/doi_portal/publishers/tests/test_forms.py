"""
Tests for Publisher forms.

Story 2.1 - Task 2: Publisher form validation.
Task 7.2 (DOI), 7.4 (logo)
"""

import pytest
from io import BytesIO
from PIL import Image
from django.core.files.uploadedfile import SimpleUploadedFile

from doi_portal.publishers.forms import (
    PublisherContactForm,
    PublisherForm,
    PublisherNoteForm,
)
from doi_portal.publishers.models import Publisher


def create_test_image(format="PNG", size=(100, 100), file_size_kb=None):
    """
    Create a test image file.

    Args:
        format: Image format (PNG, JPEG, etc.)
        size: Image dimensions as (width, height)
        file_size_kb: Target file size in KB (approximate)

    Returns:
        SimpleUploadedFile with the image
    """
    image = Image.new("RGB", size, color="red")
    buffer = BytesIO()
    image.save(buffer, format=format)

    if file_size_kb:
        # Pad the buffer to reach target size
        current_size = buffer.tell()
        target_size = file_size_kb * 1024
        if target_size > current_size:
            buffer.write(b"\x00" * (target_size - current_size))

    buffer.seek(0)

    ext = format.lower()
    if format == "JPEG":
        ext = "jpg"
    content_type = f"image/{ext}"

    return SimpleUploadedFile(
        name=f"test_image.{ext}",
        content=buffer.read(),
        content_type=content_type,
    )


@pytest.mark.django_db
class TestPublisherFormValidation:
    """Test PublisherForm validation."""

    def test_form_valid_with_required_fields(self):
        """Test form is valid with required fields only."""
        data = {
            "name": "Test Izdavac",
            "doi_prefix": "10.1234",
        }
        form = PublisherForm(data=data)
        assert form.is_valid(), form.errors

    def test_form_valid_with_all_fields(self):
        """Test form is valid with all fields."""
        data = {
            "name": "Puni Izdavac",
            "doi_prefix": "10.9999",
            "description": "Opis izdavaca",
            "contact_email": "kontakt@izdavac.rs",
            "contact_phone": "+381 11 123 4567",
            "website": "https://www.izdavac.rs",
        }
        form = PublisherForm(data=data)
        assert form.is_valid(), form.errors

    def test_form_invalid_without_name(self):
        """Test form requires name."""
        data = {
            "doi_prefix": "10.1234",
        }
        form = PublisherForm(data=data)
        assert not form.is_valid()
        assert "name" in form.errors

    def test_form_invalid_without_doi_prefix(self):
        """Test form requires doi_prefix."""
        data = {
            "name": "Test",
        }
        form = PublisherForm(data=data)
        assert not form.is_valid()
        assert "doi_prefix" in form.errors


# =============================================================================
# Task 7.2: Test DOI prefix validation in form
# =============================================================================


@pytest.mark.django_db
class TestPublisherFormDOIPrefixValidation:
    """Test DOI prefix validation in PublisherForm."""

    def test_valid_doi_prefix(self):
        """Test valid DOI prefix passes validation."""
        data = {"name": "Test", "doi_prefix": "10.5678"}
        form = PublisherForm(data=data)
        assert form.is_valid(), form.errors

    def test_invalid_doi_prefix_format(self):
        """Test invalid DOI prefix format is rejected."""
        data = {"name": "Test", "doi_prefix": "invalid"}
        form = PublisherForm(data=data)
        assert not form.is_valid()
        assert "doi_prefix" in form.errors

    def test_doi_prefix_must_start_with_10(self):
        """Test DOI prefix must start with 10."""
        data = {"name": "Test", "doi_prefix": "11.1234"}
        form = PublisherForm(data=data)
        assert not form.is_valid()
        assert "doi_prefix" in form.errors

    def test_doi_prefix_minimum_4_digits(self):
        """Test DOI prefix requires minimum 4 digits after dot."""
        data = {"name": "Test", "doi_prefix": "10.123"}
        form = PublisherForm(data=data)
        assert not form.is_valid()
        assert "doi_prefix" in form.errors

    def test_doi_prefix_uniqueness_on_create(self):
        """Test DOI prefix uniqueness validation on create."""
        Publisher.objects.create(name="Existing", doi_prefix="10.1111")

        data = {"name": "New", "doi_prefix": "10.1111"}
        form = PublisherForm(data=data)
        assert not form.is_valid()
        assert "doi_prefix" in form.errors

    def test_doi_prefix_uniqueness_on_update(self):
        """Test DOI prefix uniqueness allows same value on update."""
        publisher = Publisher.objects.create(name="Test", doi_prefix="10.2222")

        data = {"name": "Updated", "doi_prefix": "10.2222"}
        form = PublisherForm(data=data, instance=publisher)
        assert form.is_valid(), form.errors


# =============================================================================
# Task 7.4: Test logo upload validation
# =============================================================================


@pytest.mark.django_db
class TestPublisherFormLogoValidation:
    """Test logo upload validation in PublisherForm."""

    def test_valid_png_logo(self):
        """Test PNG logo is accepted."""
        data = {"name": "Test", "doi_prefix": "10.3333"}
        logo = create_test_image(format="PNG")
        form = PublisherForm(data=data, files={"logo": logo})
        assert form.is_valid(), form.errors

    def test_valid_jpeg_logo(self):
        """Test JPEG logo is accepted."""
        data = {"name": "Test", "doi_prefix": "10.4444"}
        logo = create_test_image(format="JPEG")
        form = PublisherForm(data=data, files={"logo": logo})
        assert form.is_valid(), form.errors

    def test_logo_too_large_rejected(self):
        """Test logo larger than 2MB is rejected."""
        data = {"name": "Test", "doi_prefix": "10.5555"}
        # Create a file larger than 2MB
        logo = create_test_image(format="PNG", file_size_kb=2500)
        form = PublisherForm(data=data, files={"logo": logo})
        assert not form.is_valid()
        assert "logo" in form.errors

    def test_invalid_logo_format_rejected(self):
        """Test invalid file format is rejected."""
        data = {"name": "Test", "doi_prefix": "10.6666"}
        # Create a text file disguised as image
        invalid_file = SimpleUploadedFile(
            name="test.txt",
            content=b"This is not an image",
            content_type="text/plain",
        )
        form = PublisherForm(data=data, files={"logo": invalid_file})
        assert not form.is_valid()
        assert "logo" in form.errors


# =============================================================================
# Task 2.4: Test email validation
# =============================================================================


@pytest.mark.django_db
class TestPublisherFormEmailValidation:
    """Test contact_email validation in PublisherForm."""

    def test_valid_email(self):
        """Test valid email is accepted."""
        data = {
            "name": "Test",
            "doi_prefix": "10.7777",
            "contact_email": "valid@example.com",
        }
        form = PublisherForm(data=data)
        assert form.is_valid(), form.errors

    def test_invalid_email_rejected(self):
        """Test invalid email is rejected."""
        data = {
            "name": "Test",
            "doi_prefix": "10.8888",
            "contact_email": "invalid-email",
        }
        form = PublisherForm(data=data)
        assert not form.is_valid()
        assert "contact_email" in form.errors

    def test_empty_email_allowed(self):
        """Test empty email is allowed (optional field)."""
        data = {
            "name": "Test",
            "doi_prefix": "10.9999",
            "contact_email": "",
        }
        form = PublisherForm(data=data)
        assert form.is_valid(), form.errors


# =============================================================================
# Task 2.5: Test URL validation
# =============================================================================


@pytest.mark.django_db
class TestPublisherFormWebsiteValidation:
    """Test website URL validation in PublisherForm."""

    def test_valid_website_url(self):
        """Test valid website URL is accepted."""
        data = {
            "name": "Test",
            "doi_prefix": "10.1010",
            "website": "https://www.example.com",
        }
        form = PublisherForm(data=data)
        assert form.is_valid(), form.errors

    def test_invalid_website_url_rejected(self):
        """Test invalid website URL is rejected."""
        data = {
            "name": "Test",
            "doi_prefix": "10.1111",
            "website": "not-a-url",
        }
        form = PublisherForm(data=data)
        assert not form.is_valid()
        assert "website" in form.errors

    def test_empty_website_allowed(self):
        """Test empty website is allowed (optional field)."""
        data = {
            "name": "Test",
            "doi_prefix": "10.1212",
            "website": "",
        }
        form = PublisherForm(data=data)
        assert form.is_valid(), form.errors


# =============================================================================
# Test form widgets
# =============================================================================


@pytest.mark.django_db
class TestPublisherFormWidgets:
    """Test PublisherForm has correct widget classes."""

    def test_form_has_bootstrap_classes(self):
        """Test form widgets have Bootstrap form-control class."""
        form = PublisherForm()
        assert "form-control" in form.fields["name"].widget.attrs.get("class", "")
        assert "form-control" in form.fields["doi_prefix"].widget.attrs.get("class", "")
        assert "form-control" in form.fields["description"].widget.attrs.get("class", "")

    def test_form_has_placeholders(self):
        """Test form widgets have placeholders."""
        form = PublisherForm()
        assert form.fields["name"].widget.attrs.get("placeholder")
        assert form.fields["doi_prefix"].widget.attrs.get("placeholder")

    def test_logo_accepts_image_types(self):
        """Test logo input accepts correct image types."""
        form = PublisherForm()
        accept = form.fields["logo"].widget.attrs.get("accept", "")
        assert "image/jpeg" in accept or "image/png" in accept


# =============================================================================
# Test Crossref fields in PublisherForm
# =============================================================================


@pytest.mark.django_db
class TestPublisherFormCrossref:
    """Test Crossref fields in PublisherForm."""

    def test_crossref_username_in_form(self):
        """Test crossref_username field exists in form."""
        form = PublisherForm()
        assert "crossref_username" in form.fields

    def test_crossref_password_in_form(self):
        """Test crossref_password field exists in form."""
        form = PublisherForm()
        assert "crossref_password" in form.fields

    def test_crossref_password_is_password_input(self):
        """Test crossref_password uses PasswordInput widget."""
        form = PublisherForm()
        widget = form.fields["crossref_password"].widget
        assert widget.input_type == "password"

    def test_crossref_fields_optional(self):
        """Test crossref fields are not required."""
        data = {"name": "Test", "doi_prefix": "10.3030"}
        form = PublisherForm(data=data)
        assert form.is_valid(), form.errors

    def test_save_with_password(self):
        """Test saving form with crossref password."""
        data = {
            "name": "Crossref Test",
            "doi_prefix": "10.3031",
            "crossref_username": "myuser",
            "crossref_password": "mypass",
        }
        form = PublisherForm(data=data)
        assert form.is_valid(), form.errors
        publisher = form.save()
        publisher.refresh_from_db()
        assert publisher.crossref_username == "myuser"
        assert publisher.crossref_password == "mypass"

    def test_empty_password_preserves_existing(self):
        """Test empty password on update does not overwrite existing."""
        publisher = Publisher.objects.create(
            name="Preserve Test",
            doi_prefix="10.3032",
            crossref_password="original_pass",
        )
        data = {
            "name": "Preserve Test",
            "doi_prefix": "10.3032",
            "crossref_username": "user",
            "crossref_password": "",  # Empty = no change
        }
        form = PublisherForm(data=data, instance=publisher)
        assert form.is_valid(), form.errors
        form.save()
        publisher.refresh_from_db()
        assert publisher.crossref_password == "original_pass"


# =============================================================================
# Test PublisherContactForm
# =============================================================================


class TestPublisherContactForm:
    """Test PublisherContactForm validation."""

    def test_valid_with_required_fields(self):
        """Test form valid with only required fields."""
        data = {"first_name": "Petar", "last_name": "Petrović"}
        form = PublisherContactForm(data=data)
        assert form.is_valid(), form.errors

    def test_valid_with_all_fields(self):
        """Test form valid with all fields."""
        data = {
            "first_name": "Petar",
            "last_name": "Petrović",
            "email": "petar@test.rs",
            "phone": "+381111234567",
            "role": "direktor",
        }
        form = PublisherContactForm(data=data)
        assert form.is_valid(), form.errors

    def test_first_name_required(self):
        """Test first_name is required."""
        data = {"last_name": "Petrović"}
        form = PublisherContactForm(data=data)
        assert not form.is_valid()
        assert "first_name" in form.errors

    def test_last_name_required(self):
        """Test last_name is required."""
        data = {"first_name": "Petar"}
        form = PublisherContactForm(data=data)
        assert not form.is_valid()
        assert "last_name" in form.errors

    def test_invalid_email_rejected(self):
        """Test invalid email is rejected."""
        data = {
            "first_name": "Petar",
            "last_name": "Petrović",
            "email": "not-an-email",
        }
        form = PublisherContactForm(data=data)
        assert not form.is_valid()
        assert "email" in form.errors

    def test_widgets_have_bootstrap_class(self):
        """Test widgets have form-control class."""
        form = PublisherContactForm()
        for field_name in ["first_name", "last_name", "email", "phone", "role"]:
            assert "form-control" in form.fields[field_name].widget.attrs.get("class", "")

    def test_role_has_placeholder(self):
        """Test role field has placeholder with examples."""
        form = PublisherContactForm()
        placeholder = form.fields["role"].widget.attrs.get("placeholder", "")
        assert "direktor" in placeholder


# =============================================================================
# Test PublisherNoteForm
# =============================================================================


class TestPublisherNoteForm:
    """Test PublisherNoteForm validation."""

    def test_valid_with_text(self):
        """Test form valid with text."""
        data = {"text": "Ovo je napomena."}
        form = PublisherNoteForm(data=data)
        assert form.is_valid(), form.errors

    def test_text_required(self):
        """Test text is required."""
        data = {"text": ""}
        form = PublisherNoteForm(data=data)
        assert not form.is_valid()
        assert "text" in form.errors

    def test_widget_has_bootstrap_class(self):
        """Test textarea has form-control class."""
        form = PublisherNoteForm()
        assert "form-control" in form.fields["text"].widget.attrs.get("class", "")

    def test_widget_has_placeholder(self):
        """Test textarea has placeholder."""
        form = PublisherNoteForm()
        assert form.fields["text"].widget.attrs.get("placeholder")
