"""
Component forms for DOI Portal.

Crossref sa_component support: ComponentGroup, Component, ComponentContributor forms.
"""

from django import forms
from django.utils.translation import gettext_lazy as _

from .models import Component, ComponentContributor, ComponentGroup


MIME_TYPE_CHOICES = [
    ("", _("--- Izaberite ---")),
    ("audio/mpeg", "audio/mpeg"),
    ("video/mp4", "video/mp4"),
    ("application/pdf", "application/pdf"),
    ("image/jpeg", "image/jpeg"),
    ("image/png", "image/png"),
    ("text/html", "text/html"),
    ("application/zip", "application/zip"),
]


class ComponentGroupForm(forms.ModelForm):
    """Form for creating and editing ComponentGroups."""

    class Meta:
        model = ComponentGroup
        fields = ["publisher", "parent_doi", "title"]
        widgets = {
            "publisher": forms.HiddenInput(),
            "parent_doi": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "npr. 10.66117/emce_zapisi.2026.1",
                }
            ),
            "title": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Opcioni naslov za prikaz u listi",
                }
            ),
        }

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        if user and not user.is_superuser:
            # Scope publisher to user's publisher
            if hasattr(user, "publisher") and user.publisher:
                self.fields["publisher"].initial = user.publisher.pk


class ComponentForm(forms.ModelForm):
    """Form for creating and editing Components."""

    format_mime_type = forms.CharField(
        label=_("MIME tip"),
        max_length=100,
        required=False,
        widget=forms.Select(
            attrs={"class": "form-select"},
            choices=MIME_TYPE_CHOICES,
        ),
    )

    class Meta:
        model = Component
        fields = [
            "title",
            "description",
            "format_mime_type",
            "doi_suffix",
            "resource_url",
            "publication_year",
            "publication_month",
            "publication_day",
            "parent_relation",
            "order",
        ]
        widgets = {
            "title": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Naslov komponente",
                }
            ),
            "description": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 3,
                    "placeholder": "Opis komponente",
                }
            ),
            "doi_suffix": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "npr. component.audio.001",
                }
            ),
            "resource_url": forms.URLInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "https://... (opciono, auto-generiše se)",
                }
            ),
            "publication_year": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "npr. 2026",
                }
            ),
            "publication_month": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "1-12",
                    "min": "1",
                    "max": "12",
                }
            ),
            "publication_day": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "1-31",
                    "min": "1",
                    "max": "31",
                }
            ),
            "parent_relation": forms.TextInput(
                attrs={
                    "class": "form-control",
                }
            ),
            "order": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "min": "0",
                }
            ),
        }


class ComponentContributorForm(forms.ModelForm):
    """Form for creating and editing ComponentContributors."""

    class Meta:
        model = ComponentContributor
        fields = [
            "given_name",
            "surname",
            "suffix",
            "email",
            "orcid",
            "orcid_authenticated",
            "sequence",
            "contributor_role",
            "order",
        ]
        widgets = {
            "given_name": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Ime",
                }
            ),
            "surname": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Prezime",
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
            "orcid_authenticated": forms.CheckboxInput(
                attrs={
                    "class": "form-check-input",
                }
            ),
            "sequence": forms.Select(
                attrs={
                    "class": "form-select",
                }
            ),
            "contributor_role": forms.Select(
                attrs={
                    "class": "form-select",
                }
            ),
            "order": forms.HiddenInput(),
        }
