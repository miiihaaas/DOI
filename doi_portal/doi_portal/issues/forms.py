"""
Issue forms for DOI Portal.

Story 2.6: Issue form with publication scoping and validation.
"""

import calendar
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
            "publication_month",
            "publication_day",
            "doi_suffix",
            "pdf_file",
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
                    "data-check-spaces": "true",
                }
            ),
            "cover_image": forms.ClearableFileInput(
                attrs={
                    "class": "form-control",
                    "accept": "image/*",
                }
            ),
            "publication_month": forms.Select(
                choices=[("", "—")] + [
                    (i, name) for i, name in enumerate(
                        ["januar", "februar", "mart", "april", "maj", "jun",
                         "jul", "avgust", "septembar", "oktobar", "novembar", "decembar"],
                        start=1,
                    )
                ],
                attrs={"class": "form-select"},
            ),
            "publication_day": forms.Select(
                choices=[("", "—")] + [(i, str(i)) for i in range(1, 32)],
                attrs={"class": "form-select"},
            ),
            "status": forms.Select(
                attrs={
                    "class": "form-select",
                }
            ),
            "doi_suffix": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "npr. zbornik-2025-vol1",
                }
            ),
            "pdf_file": forms.ClearableFileInput(
                attrs={
                    "class": "form-control",
                    "accept": "application/pdf",
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
            "publication_month": _("Mesec objave"),
            "publication_day": _("Dan objave"),
            "status": _("Status"),
            "doi_suffix": _("DOI sufiks izdanja"),
            "pdf_file": _("PDF publikacije"),
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
        self._pub_doi_prefix_map = {}
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
            # Build publication DOI prefix map for Alpine.js
            self._pub_doi_prefix_map = {
                str(pk): prefix
                for pk, prefix in queryset.values_list("pk", "publisher__doi_prefix")
            }

    @property
    def publication_type_map_json(self):
        """Return JSON map of publication PK to publication_type for Alpine.js."""
        return json.dumps(
            {str(k): v for k, v in self._pub_type_map.items()}
        )

    @property
    def pub_doi_prefix_map_json(self):
        """Return JSON map of publication PK to publisher DOI prefix for Alpine.js."""
        return json.dumps(self._pub_doi_prefix_map)

    # Maximum cover image file size: 5 MB
    MAX_COVER_IMAGE_SIZE = 5 * 1024 * 1024
    # Maximum PDF file size: 50 MB
    MAX_PDF_FILE_SIZE = 50 * 1024 * 1024

    def clean_cover_image(self):
        """Validate cover image file size (max 5 MB)."""
        cover_image = self.cleaned_data.get("cover_image")
        if cover_image and hasattr(cover_image, "size"):
            if cover_image.size > self.MAX_COVER_IMAGE_SIZE:
                raise ValidationError(
                    _("Naslovna slika ne sme biti veća od 5 MB.")
                )
        return cover_image

    def clean_pdf_file(self):
        """Validate PDF file: content type and size (max 50 MB)."""
        pdf_file = self.cleaned_data.get("pdf_file")
        # Only validate newly uploaded files (UploadedFile has content_type)
        if pdf_file and hasattr(pdf_file, "content_type"):
            if pdf_file.content_type != "application/pdf":
                raise ValidationError(
                    _("Dozvoljeni su samo PDF fajlovi.")
                )
            if pdf_file.size > self.MAX_PDF_FILE_SIZE:
                raise ValidationError(
                    _("PDF fajl ne sme biti veći od 50 MB.")
                )
        return pdf_file

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

        # Validate publication_month / publication_day consistency
        pub_month = cleaned_data.get("publication_month")
        pub_day = cleaned_data.get("publication_day")
        year = cleaned_data.get("year")

        if pub_day and not pub_month:
            self.add_error(
                "publication_month",
                _("Morate izabrati mesec ako birate dan."),
            )
        elif pub_month and pub_day and year:
            _weekday, max_day = calendar.monthrange(year, pub_month)
            if pub_day > max_day:
                self.add_error(
                    "publication_day",
                    _(f"Mesec {pub_month} u godini {year} ima samo {max_day} dana."),
                )

        # Validate doi_suffix format
        doi_suffix = cleaned_data.get("doi_suffix")
        if doi_suffix:
            if doi_suffix.startswith("/"):
                self.add_error(
                    "doi_suffix",
                    _("DOI sufiks ne sme počinjati sa '/'."),
                )
            if " " in doi_suffix:
                self.add_error(
                    "doi_suffix",
                    _("DOI sufiks ne sme sadržati razmake."),
                )

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

    def save(self, commit=True):
        """Override save to populate pdf_original_filename from uploaded file."""
        instance = super().save(commit=False)
        pdf_file = self.cleaned_data.get("pdf_file")
        # Only update filename for newly uploaded files (UploadedFile has content_type)
        if pdf_file and hasattr(pdf_file, "content_type"):
            instance.pdf_original_filename = pdf_file.name
        elif not instance.pdf_file:
            # PDF was cleared
            instance.pdf_original_filename = ""
        if commit:
            instance.save()
        return instance

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
