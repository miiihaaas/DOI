"""
Monograph forms for DOI Portal.

MonographForm with publisher scoping and validation.
Contributor, Affiliation, Funding, and Relation forms for inline HTMX editing
at both monograph and chapter levels.
"""

import json
from datetime import datetime

from django import forms
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from doi_portal.core.constants import LANGUAGE_CHOICES
from doi_portal.publishers.models import Publisher

from .models import (
    ChapterAffiliation,
    ChapterContributor,
    ChapterFunding,
    ChapterRelation,
    Monograph,
    MonographAffiliation,
    MonographChapter,
    MonographContributor,
    MonographFunding,
    MonographRelation,
)


class MonographForm(forms.ModelForm):
    """
    Form for creating and editing monographs.

    Includes:
    - Publisher queryset scoping based on user role
    - Bootstrap 5 widget styling
    - Keywords JSON field handling
    - Year validation
    """

    class Meta:
        model = Monograph
        fields = [
            "title",
            "subtitle",
            "doi_suffix",
            "year",
            "publisher",
            "publication_place",
            "isbn_print",
            "isbn_online",
            "language",
            "abstract",
            "keywords",
            "total_pages",
            "edition_number",
            "license_url",
            "license_applies_to",
            "free_to_read",
            "cover_image",
            "use_external_resource",
            "external_landing_url",
        ]
        widgets = {
            "title": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Unesite naslov monografije",
                    "data-check-spaces": "true",
                }
            ),
            "subtitle": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Opcioni podnaslov",
                    "data-check-spaces": "true",
                }
            ),
            "doi_suffix": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "npr. monograph.2026.001",
                }
            ),
            "year": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "npr. 2026",
                }
            ),
            "publisher": forms.Select(
                attrs={
                    "class": "form-select",
                }
            ),
            "publication_place": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "npr. Beograd",
                }
            ),
            "isbn_print": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "978-X-XXXX-XXXX-X",
                }
            ),
            "isbn_online": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "978-X-XXXX-XXXX-X",
                }
            ),
            "language": forms.Select(
                choices=LANGUAGE_CHOICES,
                attrs={
                    "class": "form-select",
                }
            ),
            "abstract": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 6,
                    "placeholder": "Unesite apstrakt monografije",
                }
            ),
            "keywords": forms.HiddenInput(),
            "total_pages": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "npr. 350",
                }
            ),
            "edition_number": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "npr. 1",
                }
            ),
            "license_url": forms.URLInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "https://creativecommons.org/licenses/by/4.0/",
                }
            ),
            "license_applies_to": forms.Select(
                attrs={
                    "class": "form-select",
                }
            ),
            "free_to_read": forms.CheckboxInput(
                attrs={
                    "class": "form-check-input",
                }
            ),
            "cover_image": forms.ClearableFileInput(
                attrs={
                    "class": "form-control",
                    "accept": "image/*",
                }
            ),
            "use_external_resource": forms.CheckboxInput(
                attrs={
                    "class": "form-check-input",
                    "role": "switch",
                }
            ),
            "external_landing_url": forms.URLInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "https://izdavac.example.com/monografija/123",
                }
            ),
        }
        labels = {
            "title": _("Naslov"),
            "subtitle": _("Podnaslov"),
            "doi_suffix": _("DOI sufiks"),
            "year": _("Godina izdanja"),
            "publisher": _("Izdavač"),
            "publication_place": _("Mesto izdanja"),
            "isbn_print": _("ISBN (štampano)"),
            "isbn_online": _("ISBN (online)"),
            "language": _("Jezik"),
            "abstract": _("Apstrakt"),
            "keywords": _("Ključne reči"),
            "total_pages": _("Ukupan broj strana"),
            "edition_number": _("Broj izdanja"),
            "license_url": _("URL licence"),
            "license_applies_to": _("Licenca se odnosi na"),
            "free_to_read": _("Slobodan pristup"),
            "cover_image": _("Naslovna slika"),
            "use_external_resource": _("Koristi eksterni URL za DOI"),
            "external_landing_url": _("Eksterna landing stranica"),
        }
        help_texts = {
            "language": "Jezik monografije (ISO 639 kod).",
        }

    def __init__(self, *args, user=None, **kwargs):
        """
        Initialize form with user-scoped publisher queryset.

        Args:
            user: Current user for publisher queryset filtering
        """
        super().__init__(*args, **kwargs)
        if user:
            if user.is_superuser or user.groups.filter(
                name__in=["Administrator", "Superadmin"]
            ).exists():
                queryset = Publisher.objects.all()
            elif hasattr(user, "publisher") and user.publisher:
                queryset = Publisher.objects.filter(pk=user.publisher.pk)
            else:
                queryset = Publisher.objects.none()
            self.fields["publisher"].queryset = queryset

    def clean(self):
        """Validate year and external resource fields."""
        cleaned_data = super().clean()

        # Validate year not > current_year + 1
        year = cleaned_data.get("year")
        if year is not None:
            current_year = datetime.now().year
            if year > current_year + 1:
                self.add_error(
                    "year",
                    _("Godina izdanja ne može biti veća od %(max_year)s.")
                    % {"max_year": current_year + 1},
                )

        # Validate external resource
        use_external = cleaned_data.get("use_external_resource")
        external_landing_url = (cleaned_data.get("external_landing_url") or "").strip()

        if use_external and not external_landing_url:
            self.add_error(
                "external_landing_url",
                _("Eksterna landing stranica je obavezna kada je uključen eksterni URL za DOI."),
            )

        return cleaned_data

    def clean_keywords(self):
        """Parse keywords from JSON string or return existing list."""
        keywords = self.cleaned_data.get("keywords")
        if isinstance(keywords, str):
            try:
                keywords = json.loads(keywords)
            except (json.JSONDecodeError, TypeError):
                keywords = []
        if not isinstance(keywords, list):
            keywords = []
        # Filter out empty strings
        return [kw.strip() for kw in keywords if isinstance(kw, str) and kw.strip()]

    def clean_language(self):
        """Validate language code is in allowed choices."""
        language = self.cleaned_data.get("language", "")
        if language:
            valid_codes = [code for code, _ in self.fields["language"].widget.choices]
            if language not in valid_codes:
                raise ValidationError(_("Izaberite jednu od ponuđenih vrednosti."))
        return language

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


class MonographChapterForm(forms.ModelForm):
    """
    Form for creating and editing monograph chapters.

    Bootstrap 5 styled form with Serbian labels.
    """

    class Meta:
        model = MonographChapter
        fields = [
            "title",
            "subtitle",
            "doi_suffix",
            "first_page",
            "last_page",
            "abstract",
            "language",
            "license_url",
            "license_applies_to",
            "free_to_read",
        ]
        widgets = {
            "title": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Unesite naslov poglavlja",
                    "data-check-spaces": "true",
                }
            ),
            "subtitle": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Opcioni podnaslov",
                    "data-check-spaces": "true",
                }
            ),
            "doi_suffix": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "npr. chapter.2026.001",
                }
            ),
            "first_page": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "npr. 1",
                }
            ),
            "last_page": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "npr. 25",
                }
            ),
            "abstract": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 6,
                    "placeholder": "Unesite apstrakt poglavlja",
                }
            ),
            "language": forms.Select(
                choices=LANGUAGE_CHOICES,
                attrs={
                    "class": "form-select",
                }
            ),
            "license_url": forms.URLInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "https://creativecommons.org/licenses/by/4.0/",
                }
            ),
            "license_applies_to": forms.Select(
                attrs={
                    "class": "form-select",
                }
            ),
            "free_to_read": forms.CheckboxInput(
                attrs={
                    "class": "form-check-input",
                }
            ),
        }
        labels = {
            "title": _("Naslov"),
            "subtitle": _("Podnaslov"),
            "doi_suffix": _("DOI sufiks"),
            "first_page": _("Prva stranica"),
            "last_page": _("Poslednja stranica"),
            "abstract": _("Apstrakt"),
            "language": _("Jezik"),
            "license_url": _("URL licence"),
            "license_applies_to": _("Licenca se odnosi na"),
            "free_to_read": _("Slobodan pristup"),
        }
        help_texts = {
            "language": "Jezik poglavlja (ISO 639 kod).",
        }


class MonographContributorForm(forms.ModelForm):
    """
    Form for creating and editing monograph-level contributors via HTMX inline editing.

    Bootstrap 5 styled form with Serbian labels.
    """

    class Meta:
        model = MonographContributor
        fields = [
            "given_name",
            "surname",
            "suffix",
            "email",
            "orcid",
            "contributor_role",
            "is_corresponding",
        ]
        widgets = {
            "given_name": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Ime autora",
                }
            ),
            "surname": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Prezime autora",
                }
            ),
            "suffix": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "npr. Jr., III",
                }
            ),
            "email": forms.EmailInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "email@primer.com",
                }
            ),
            "orcid": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "0000-0000-0000-0000",
                }
            ),
            "contributor_role": forms.Select(
                attrs={
                    "class": "form-select",
                }
            ),
            "is_corresponding": forms.CheckboxInput(
                attrs={
                    "class": "form-check-input",
                }
            ),
        }
        labels = {
            "given_name": _("Ime"),
            "surname": _("Prezime"),
            "suffix": _("Sufiks"),
            "email": _("Email"),
            "orcid": _("ORCID"),
            "contributor_role": _("Uloga kontributora"),
            "is_corresponding": _("Korespondentan autor"),
        }


class MonographAffiliationForm(forms.ModelForm):
    """
    Form for creating and editing monograph-level affiliations via HTMX inline editing.

    Bootstrap 5 styled form with Serbian labels.
    """

    class Meta:
        model = MonographAffiliation
        fields = [
            "institution_name",
            "institution_ror_id",
            "department",
            "city",
            "country",
        ]
        widgets = {
            "institution_name": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Naziv institucije",
                }
            ),
            "institution_ror_id": forms.URLInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "https://ror.org/...",
                }
            ),
            "department": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Departman (opciono)",
                }
            ),
            "city": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "npr. Beograd",
                }
            ),
            "country": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "npr. Srbija",
                }
            ),
        }
        labels = {
            "institution_name": _("Naziv institucije"),
            "institution_ror_id": _("ROR ID"),
            "department": _("Departman"),
            "city": _("Grad"),
            "country": _("Država"),
        }


class ChapterContributorForm(forms.ModelForm):
    """
    Form for creating and editing chapter-level contributors via HTMX inline editing.

    Bootstrap 5 styled form with Serbian labels.
    """

    class Meta:
        model = ChapterContributor
        fields = [
            "given_name",
            "surname",
            "suffix",
            "email",
            "orcid",
            "contributor_role",
            "is_corresponding",
        ]
        widgets = {
            "given_name": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Ime autora",
                }
            ),
            "surname": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Prezime autora",
                }
            ),
            "suffix": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "npr. Jr., III",
                }
            ),
            "email": forms.EmailInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "email@primer.com",
                }
            ),
            "orcid": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "0000-0000-0000-0000",
                }
            ),
            "contributor_role": forms.Select(
                attrs={
                    "class": "form-select",
                }
            ),
            "is_corresponding": forms.CheckboxInput(
                attrs={
                    "class": "form-check-input",
                }
            ),
        }
        labels = {
            "given_name": _("Ime"),
            "surname": _("Prezime"),
            "suffix": _("Sufiks"),
            "email": _("Email"),
            "orcid": _("ORCID"),
            "contributor_role": _("Uloga kontributora"),
            "is_corresponding": _("Korespondentan autor"),
        }


class ChapterAffiliationForm(forms.ModelForm):
    """
    Form for creating and editing chapter-level affiliations via HTMX inline editing.

    Bootstrap 5 styled form with Serbian labels.
    """

    class Meta:
        model = ChapterAffiliation
        fields = [
            "institution_name",
            "institution_ror_id",
            "department",
            "city",
            "country",
        ]
        widgets = {
            "institution_name": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Naziv institucije",
                }
            ),
            "institution_ror_id": forms.URLInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "https://ror.org/...",
                }
            ),
            "department": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Departman (opciono)",
                }
            ),
            "city": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "npr. Beograd",
                }
            ),
            "country": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "npr. Srbija",
                }
            ),
        }
        labels = {
            "institution_name": _("Naziv institucije"),
            "institution_ror_id": _("ROR ID"),
            "department": _("Departman"),
            "city": _("Grad"),
            "country": _("Država"),
        }


class MonographFundingForm(forms.ModelForm):
    """Form for monograph-level funding/grant information."""

    class Meta:
        model = MonographFunding
        fields = ["funder_name", "funder_doi", "funder_ror_id", "award_number"]
        widgets = {
            "funder_name": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Naziv finansijera",
            }),
            "funder_doi": forms.URLInput(attrs={
                "class": "form-control",
                "placeholder": "https://doi.org/10.13039/...",
                "readonly": "readonly",
            }),
            "funder_ror_id": forms.URLInput(attrs={
                "class": "form-control",
                "placeholder": "https://ror.org/...",
                "readonly": "readonly",
            }),
            "award_number": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Broj projekta/granta",
            }),
        }
        labels = {
            "funder_name": _("Naziv finansijera"),
            "funder_doi": _("Funder DOI"),
            "funder_ror_id": _("Funder ROR ID"),
            "award_number": _("Broj projekta"),
        }


class MonographRelationForm(forms.ModelForm):
    """Form for monograph-level relation metadata (Crossref Relations)."""

    class Meta:
        model = MonographRelation
        fields = ["relationship_type", "identifier_type", "target_identifier", "description"]
        widgets = {
            "relationship_type": forms.Select(attrs={"class": "form-select"}),
            "identifier_type": forms.Select(attrs={"class": "form-select"}),
            "target_identifier": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "10.5555/target_doi",
            }),
            "description": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Opcioni opis relacije",
            }),
        }
        labels = {
            "relationship_type": _("Tip relacije"),
            "identifier_type": _("Tip identifikatora"),
            "target_identifier": _("Identifikator cilja"),
            "description": _("Opis"),
        }


class ChapterFundingForm(forms.ModelForm):
    """Form for chapter-level funding/grant information."""

    class Meta:
        model = ChapterFunding
        fields = ["funder_name", "funder_doi", "funder_ror_id", "award_number"]
        widgets = {
            "funder_name": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Naziv finansijera",
            }),
            "funder_doi": forms.URLInput(attrs={
                "class": "form-control",
                "placeholder": "https://doi.org/10.13039/...",
                "readonly": "readonly",
            }),
            "funder_ror_id": forms.URLInput(attrs={
                "class": "form-control",
                "placeholder": "https://ror.org/...",
                "readonly": "readonly",
            }),
            "award_number": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Broj projekta/granta",
            }),
        }
        labels = {
            "funder_name": _("Naziv finansijera"),
            "funder_doi": _("Funder DOI"),
            "funder_ror_id": _("Funder ROR ID"),
            "award_number": _("Broj projekta"),
        }


class ChapterRelationForm(forms.ModelForm):
    """Form for chapter-level relation metadata (Crossref Relations)."""

    class Meta:
        model = ChapterRelation
        fields = ["relationship_type", "identifier_type", "target_identifier", "description"]
        widgets = {
            "relationship_type": forms.Select(attrs={"class": "form-select"}),
            "identifier_type": forms.Select(attrs={"class": "form-select"}),
            "target_identifier": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "10.5555/target_doi",
            }),
            "description": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Opcioni opis relacije",
            }),
        }
        labels = {
            "relationship_type": _("Tip relacije"),
            "identifier_type": _("Tip identifikatora"),
            "target_identifier": _("Identifikator cilja"),
            "description": _("Opis"),
        }
