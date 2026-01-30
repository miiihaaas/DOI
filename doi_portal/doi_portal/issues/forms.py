"""
Issue forms for DOI Portal.

Story 2.6: Issue form with publication scoping and validation.
"""

import json

from django import forms
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from doi_portal.publications.models import Publication

from .models import Issue


class IssueForm(forms.ModelForm):
    """
    Form for creating and editing issues.

    Includes:
    - Publication queryset scoping based on user role
    - Unique constraint validation with user-friendly error messages
    - Conference-specific proceedings fields
    """

    class Meta:
        model = Issue
        fields = [
            "publication",
            "volume",
            "issue_number",
            "year",
            "title",
            "cover_image",
            "publication_date",
            "status",
            "proceedings_title",
            "proceedings_publisher_name",
            "proceedings_publisher_place",
        ]
        widgets = {
            "publication": forms.Select(
                attrs={
                    "class": "form-select",
                }
            ),
            "volume": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "npr. 1, Special",
                }
            ),
            "issue_number": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "npr. 1, Supplement",
                }
            ),
            "year": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "npr. 2026",
                    "min": "1900",
                    "max": "2100",
                }
            ),
            "title": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Opcioni naslov izdanja",
                }
            ),
            "cover_image": forms.ClearableFileInput(
                attrs={
                    "class": "form-control",
                    "accept": "image/*",
                }
            ),
            "publication_date": forms.DateInput(
                attrs={
                    "class": "form-control",
                    "type": "date",
                }
            ),
            "status": forms.Select(
                attrs={
                    "class": "form-select",
                }
            ),
            "proceedings_title": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Naslov zbornika",
                }
            ),
            "proceedings_publisher_name": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Naziv izdavača zbornika",
                }
            ),
            "proceedings_publisher_place": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Mesto izdavanja",
                }
            ),
        }
        labels = {
            "publication": _("Publikacija"),
            "volume": _("Volumen"),
            "issue_number": _("Broj izdanja"),
            "year": _("Godina"),
            "title": _("Naslov"),
            "cover_image": _("Naslovna slika"),
            "publication_date": _("Datum objave"),
            "status": _("Status"),
            "proceedings_title": _("Naslov zbornika"),
            "proceedings_publisher_name": _("Naziv izdavača zbornika"),
            "proceedings_publisher_place": _("Mesto izdavanja"),
        }

    def __init__(self, *args, user=None, **kwargs):
        """
        Initialize form with user-scoped publication queryset.

        Args:
            user: Current user for publication queryset filtering
        """
        super().__init__(*args, **kwargs)
        self._pub_type_map = {}
        if user:
            if user.is_superuser or user.groups.filter(
                name__in=["Administrator", "Superadmin"]
            ).exists():
                queryset = Publication.objects.select_related("publisher")
            elif hasattr(user, "publisher") and user.publisher:
                queryset = Publication.objects.filter(
                    publisher=user.publisher
                ).select_related("publisher")
            else:
                queryset = Publication.objects.none()
            self.fields["publication"].queryset = queryset
            # Build publication type map for Alpine.js toggle
            self._pub_type_map = dict(
                queryset.values_list("pk", "publication_type")
            )

    @property
    def publication_type_map_json(self):
        """Return JSON map of publication PK to publication_type for Alpine.js."""
        return json.dumps(
            {str(k): v for k, v in self._pub_type_map.items()}
        )

    # Maximum cover image file size: 5 MB
    MAX_COVER_IMAGE_SIZE = 5 * 1024 * 1024

    def clean_cover_image(self):
        """Validate cover image file size (max 5 MB)."""
        cover_image = self.cleaned_data.get("cover_image")
        if cover_image and hasattr(cover_image, "size"):
            if cover_image.size > self.MAX_COVER_IMAGE_SIZE:
                raise ValidationError(
                    _("Naslovna slika ne sme biti veća od 5 MB.")
                )
        return cover_image

    def clean(self):
        """
        Validate unique constraint for (publication, volume, issue_number).

        Shows user-friendly error message if combination already exists.
        Checks all combinations including both empty volume and issue_number.
        """
        cleaned_data = super().clean()
        publication = cleaned_data.get("publication")
        volume = cleaned_data.get("volume")
        issue_number = cleaned_data.get("issue_number")

        if publication is not None:
            qs = Issue.objects.filter(
                publication=publication,
                volume=volume or "",
                issue_number=issue_number or "",
            )
            # Exclude current instance when editing
            if self.instance and self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise ValidationError(
                    _(
                        "Izdanje sa ovom kombinacijom publikacije, volumena i broja "
                        "već postoji."
                    )
                )

        return cleaned_data

    def add_error_classes(self):
        """Add is-invalid class to fields with errors after validation."""
        for field_name in self.errors:
            if field_name in self.fields:
                css_class = self.fields[field_name].widget.attrs.get("class", "")
                if "is-invalid" not in css_class:
                    self.fields[field_name].widget.attrs["class"] = (
                        f"{css_class} is-invalid".strip()
                    )

    def is_valid(self):
        """Override to add error classes after validation."""
        result = super().is_valid()
        if not result:
            self.add_error_classes()
        return result
