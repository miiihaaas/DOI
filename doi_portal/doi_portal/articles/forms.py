"""
Article forms for DOI Portal.

Story 3.1: ArticleForm with issue scoping and validation.
Story 3.2: AuthorForm and AffiliationForm for inline HTMX editing.
"""

import json

from django import forms
from django.utils.translation import gettext_lazy as _

from doi_portal.issues.models import Issue

from .models import Affiliation, Article, Author


class ArticleForm(forms.ModelForm):
    """
    Form for creating and editing articles.

    Includes:
    - Issue queryset scoping based on user role
    - Bootstrap 5 widget styling
    - Keywords JSON field handling
    """

    class Meta:
        model = Article
        fields = [
            "issue",
            "title",
            "subtitle",
            "abstract",
            "keywords",
            "doi_suffix",
            "first_page",
            "last_page",
            "article_number",
            "language",
            "publication_type",
            "license_url",
            "license_applies_to",
            "free_to_read",
            "free_to_read_start_date",
        ]
        widgets = {
            "issue": forms.Select(
                attrs={
                    "class": "form-select",
                }
            ),
            "title": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Unesite naslov članka",
                }
            ),
            "subtitle": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Opcioni podnaslov",
                }
            ),
            "abstract": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 6,
                    "placeholder": "Unesite apstrakt članka",
                }
            ),
            "keywords": forms.HiddenInput(),
            "doi_suffix": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "npr. article.2026.001",
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
                    "placeholder": "npr. 15",
                }
            ),
            "article_number": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Za online-only članke",
                }
            ),
            "language": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "npr. sr, en",
                }
            ),
            "publication_type": forms.Select(
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
            "free_to_read_start_date": forms.DateInput(
                attrs={
                    "class": "form-control",
                    "type": "date",
                }
            ),
        }
        labels = {
            "issue": _("Izdanje"),
            "title": _("Naslov"),
            "subtitle": _("Podnaslov"),
            "abstract": _("Apstrakt"),
            "keywords": _("Ključne reči"),
            "doi_suffix": _("DOI sufiks"),
            "first_page": _("Prva stranica"),
            "last_page": _("Poslednja stranica"),
            "article_number": _("Broj članka"),
            "language": _("Jezik"),
            "publication_type": _("Tip sadržaja"),
            "license_url": _("URL licence"),
            "license_applies_to": _("Licenca se odnosi na"),
            "free_to_read": _("Slobodan pristup"),
            "free_to_read_start_date": _("Datum početka slobodnog pristupa"),
        }

    def __init__(self, *args, user=None, **kwargs):
        """
        Initialize form with user-scoped issue queryset.

        Args:
            user: Current user for issue queryset filtering
        """
        super().__init__(*args, **kwargs)
        if user:
            if user.is_superuser or user.groups.filter(
                name__in=["Administrator", "Superadmin"]
            ).exists():
                queryset = Issue.objects.select_related(
                    "publication", "publication__publisher"
                )
            elif hasattr(user, "publisher") and user.publisher:
                queryset = Issue.objects.filter(
                    publication__publisher=user.publisher
                ).select_related("publication", "publication__publisher")
            else:
                queryset = Issue.objects.none()
            self.fields["issue"].queryset = queryset

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


class AuthorForm(forms.ModelForm):
    """
    Form for creating and editing authors via HTMX inline editing.

    Story 3.2: Bootstrap 5 styled form with Serbian labels.
    """

    class Meta:
        model = Author
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


class AffiliationForm(forms.ModelForm):
    """
    Form for creating and editing affiliations via HTMX inline editing.

    Story 3.2: Bootstrap 5 styled form with Serbian labels.
    """

    class Meta:
        model = Affiliation
        fields = [
            "institution_name",
            "institution_ror_id",
            "department",
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
        }
        labels = {
            "institution_name": _("Naziv institucije"),
            "institution_ror_id": _("ROR ID"),
            "department": _("Departman"),
        }
