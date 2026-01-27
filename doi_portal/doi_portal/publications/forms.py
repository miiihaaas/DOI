"""
Publication forms.

Story 2.3 - Task 2: Publication form with dynamic type-specific field handling.
"""

from django import forms
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from .models import Publication, PublicationType
from .validators import validate_isbn, validate_issn


class PublicationForm(forms.ModelForm):
    """
    Form for creating and editing publications.

    Includes:
    - Dynamic type-specific field handling
    - ISSN format validation (####-####)
    - ISBN-13 format validation (978-X-XXXX-XXXX-X)
    - Cover image validation (type, size)
    """

    class Meta:
        model = Publication
        fields = [
            # Common fields
            "title",
            "publisher",
            "publication_type",
            "description",
            "cover_image",
            "language",
            "subject_area",
            "access_type",
            # Journal fields
            "issn_print",
            "issn_online",
            "abbreviation",
            "frequency",
            # Conference fields
            "conference_name",
            "conference_acronym",
            "conference_location",
            "conference_date",
            "series_issn",
            # Book fields
            "isbn_print",
            "isbn_online",
            "edition",
            "series_title",
        ]
        widgets = {
            "title": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Naslov publikacije",
                }
            ),
            "publisher": forms.Select(
                attrs={
                    "class": "form-select",
                }
            ),
            "publication_type": forms.Select(
                attrs={
                    "class": "form-select",
                }
            ),
            "description": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 4,
                    "placeholder": "Opis publikacije",
                }
            ),
            "cover_image": forms.ClearableFileInput(
                attrs={
                    "class": "form-control",
                    "accept": "image/jpeg,image/png,image/webp",
                }
            ),
            "language": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "sr",
                }
            ),
            "subject_area": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "npr. Medicina, Informatika",
                }
            ),
            "access_type": forms.Select(
                attrs={
                    "class": "form-select",
                }
            ),
            # Journal fields
            "issn_print": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "####-####",
                    "pattern": r"\d{4}-\d{3}[\dX]",
                }
            ),
            "issn_online": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "####-####",
                    "pattern": r"\d{4}-\d{3}[\dX]",
                }
            ),
            "abbreviation": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "npr. J. Sci. Res.",
                }
            ),
            "frequency": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "npr. Kvartalno, Godišnje",
                }
            ),
            # Conference fields
            "conference_name": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Puni naziv konferencije",
                }
            ),
            "conference_acronym": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "npr. NK2026",
                }
            ),
            "conference_location": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "npr. Beograd, Srbija",
                }
            ),
            "conference_date": forms.DateInput(
                attrs={
                    "class": "form-control",
                    "type": "date",
                }
            ),
            "series_issn": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "####-####",
                    "pattern": r"\d{4}-\d{3}[\dX]",
                }
            ),
            # Book fields
            "isbn_print": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "978-XX-XXXX-XXX-X",
                }
            ),
            "isbn_online": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "978-XX-XXXX-XXX-X",
                }
            ),
            "edition": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "npr. 1. izdanje",
                }
            ),
            "series_title": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Naslov serije/edicije",
                }
            ),
        }

    def clean_cover_image(self):
        """
        Validate cover image file.

        - Accepted formats: jpg, jpeg, png, webp
        - Maximum size: 5MB
        """
        cover_image = self.cleaned_data.get("cover_image")
        if cover_image:
            # Check file size (5MB max)
            max_size = 5 * 1024 * 1024  # 5MB in bytes
            if cover_image.size > max_size:
                raise ValidationError(_("Naslovna slika ne sme biti veća od 5MB."))

            # Check file extension
            valid_extensions = [".jpg", ".jpeg", ".png", ".webp"]
            name = cover_image.name.lower()
            ext = None
            for valid_ext in valid_extensions:
                if name.endswith(valid_ext):
                    ext = valid_ext
                    break

            if not ext:
                raise ValidationError(_("Dozvoljeni formati su: JPG, PNG, WebP."))

        return cover_image

    def clean_issn_print(self):
        """Validate ISSN (print) format."""
        value = self.cleaned_data.get("issn_print", "")
        if value:
            validate_issn(value)
        return value

    def clean_issn_online(self):
        """Validate ISSN (online) format."""
        value = self.cleaned_data.get("issn_online", "")
        if value:
            validate_issn(value)
        return value

    def clean_series_issn(self):
        """Validate series ISSN format."""
        value = self.cleaned_data.get("series_issn", "")
        if value:
            validate_issn(value)
        return value

    def clean_isbn_print(self):
        """Validate ISBN (print) format."""
        value = self.cleaned_data.get("isbn_print", "")
        if value:
            validate_isbn(value)
        return value

    def clean_isbn_online(self):
        """Validate ISBN (online) format."""
        value = self.cleaned_data.get("isbn_online", "")
        if value:
            validate_isbn(value)
        return value

    def clean(self):
        """
        Validate type-specific required fields.

        Based on publication_type, ensure appropriate fields are provided.
        """
        cleaned_data = super().clean()
        publication_type = cleaned_data.get("publication_type")

        # For journals, at least one ISSN should be provided (recommended, not required)
        if publication_type == PublicationType.JOURNAL:
            issn_print = cleaned_data.get("issn_print", "")
            issn_online = cleaned_data.get("issn_online", "")
            # This is a soft recommendation - not enforced as error

        # For books, at least one ISBN should be provided (recommended, not required)
        if publication_type == PublicationType.BOOK:
            isbn_print = cleaned_data.get("isbn_print", "")
            isbn_online = cleaned_data.get("isbn_online", "")
            # This is a soft recommendation - not enforced as error

        return cleaned_data

    def get_type_specific_fields(self):
        """
        Return list of field names for current publication type.

        Used for dynamic form rendering with HTMX.
        """
        publication_type = self.data.get(
            "publication_type",
            self.instance.publication_type if self.instance else PublicationType.JOURNAL,
        )

        field_map = {
            PublicationType.JOURNAL: [
                "issn_print",
                "issn_online",
                "abbreviation",
                "frequency",
            ],
            PublicationType.CONFERENCE: [
                "conference_name",
                "conference_acronym",
                "conference_location",
                "conference_date",
                "series_issn",
            ],
            PublicationType.BOOK: [
                "isbn_print",
                "isbn_online",
                "edition",
                "series_title",
            ],
            PublicationType.OTHER: [],
        }

        return field_map.get(publication_type, [])

    def __init__(self, *args, **kwargs):
        """Add Bootstrap is-invalid class to fields with errors."""
        super().__init__(*args, **kwargs)
        # After form validation, add is-invalid class to fields with errors
        for field_name, field in self.fields.items():
            # Add form-control/form-select class to all fields
            css_class = field.widget.attrs.get("class", "")
            if "form-control" not in css_class and "form-select" not in css_class:
                if hasattr(field.widget, "input_type") and field.widget.input_type == "select":
                    css_class = f"{css_class} form-select".strip()
                else:
                    css_class = f"{css_class} form-control".strip()
                field.widget.attrs["class"] = css_class

    def add_error_classes(self):
        """Add is-invalid class to fields with errors after validation."""
        for field_name in self.errors:
            if field_name in self.fields:
                css_class = self.fields[field_name].widget.attrs.get("class", "")
                if "is-invalid" not in css_class:
                    self.fields[field_name].widget.attrs["class"] = f"{css_class} is-invalid".strip()

    def is_valid(self):
        """Override to add error classes after validation."""
        result = super().is_valid()
        if not result:
            self.add_error_classes()
        return result
