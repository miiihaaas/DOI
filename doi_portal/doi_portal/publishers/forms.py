"""
Publisher forms.

Story 2.1 - Task 2: Publisher form with validation.
"""

from django import forms
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from .models import Publisher, validate_doi_prefix


class PublisherForm(forms.ModelForm):
    """
    Form for creating and editing publishers.

    Includes validation for:
    - DOI prefix format (10.XXXX)
    - DOI prefix uniqueness
    - Logo file type (jpg, png, svg)
    - Logo file size (max 2MB)
    - Email format
    - Website URL format
    """

    class Meta:
        model = Publisher
        fields = [
            "name",
            "description",
            "logo",
            "contact_email",
            "contact_phone",
            "website",
            "doi_prefix",
        ]
        widgets = {
            "name": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Naziv izdavača",
                }
            ),
            "description": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 4,
                    "placeholder": "Opis izdavača",
                }
            ),
            "logo": forms.ClearableFileInput(
                attrs={
                    "class": "form-control",
                    "accept": "image/jpeg,image/png,image/svg+xml",
                }
            ),
            "contact_email": forms.EmailInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "kontakt@izdavač.rs",
                }
            ),
            "contact_phone": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "+381 11 123 4567",
                }
            ),
            "website": forms.URLInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "https://www.izdavač.rs",
                }
            ),
            "doi_prefix": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "10.1234",
                }
            ),
        }

    def clean_logo(self):
        """
        Validate logo file.

        - Accepted formats: jpg, jpeg, png, svg
        - Maximum size: 2MB
        """
        logo = self.cleaned_data.get("logo")
        if logo:
            # Check file size (2MB max)
            max_size = 2 * 1024 * 1024  # 2MB in bytes
            if logo.size > max_size:
                raise ValidationError(_("Logo ne sme biti veći od 2MB."))

            # Check file extension
            valid_extensions = [".jpg", ".jpeg", ".png", ".svg"]
            name = logo.name.lower()
            ext = None
            for valid_ext in valid_extensions:
                if name.endswith(valid_ext):
                    ext = valid_ext
                    break

            if not ext:
                raise ValidationError(_("Dozvoljeni formati su: JPG, PNG, SVG."))

        return logo

    def clean_doi_prefix(self):
        """
        Validate DOI prefix format and uniqueness.

        - Format: 10.XXXX (minimum 4 digits after 10.)
        - Must be unique (excluding current instance on update)
        """
        doi_prefix = self.cleaned_data.get("doi_prefix")
        if doi_prefix:
            # Run the format validator
            validate_doi_prefix(doi_prefix)

            # Check uniqueness (excluding current instance on update)
            qs = Publisher.all_objects.filter(doi_prefix=doi_prefix)
            if self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise ValidationError(
                    _("DOI prefiks '%(value)s' vec postoji."),
                    params={"value": doi_prefix},
                )

        return doi_prefix
