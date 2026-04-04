"""
Wizard forms for Conference Registration Wizard.

WizardConferenceForm - Step 1: Conference (Publication) creation/editing.
WizardProceedingsForm - Step 2: Proceedings (Issue) creation/editing.
WizardPaperForm - Step 3: Paper (Article) creation/editing.
"""

from django import forms
from django.core.exceptions import ValidationError

from doi_portal.core.constants import LANGUAGE_CHOICES
from doi_portal.articles.models import Article
from doi_portal.issues.models import Issue
from doi_portal.publications.models import Publication, PublicationType


class WizardConferenceForm(forms.ModelForm):
    """
    Step 1 form: Conference (Publication) creation.

    Does NOT include 'title' field - auto-populated from conference_name in save().
    """

    class Meta:
        model = Publication
        fields = [
            "publisher",
            "conference_name",
            "conference_acronym",
            "conference_number",
            "conference_location",
            "conference_date",
            "conference_date_end",
            "language",
        ]
        widgets = {
            "publisher": forms.Select(
                attrs={"class": "form-select"}
            ),
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
            "conference_number": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "npr. 15",
                    "min": "1",
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
            "conference_date_end": forms.DateInput(
                attrs={
                    "class": "form-control",
                    "type": "date",
                }
            ),
            "language": forms.Select(
                choices=LANGUAGE_CHOICES,
                attrs={"class": "form-select"}
            ),
        }

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self._user = user
        if user:
            if user.is_superuser or user.groups.filter(
                name__in=["Administrator", "Superadmin"]
            ).exists():
                from doi_portal.publishers.models import Publisher
                self.fields["publisher"].queryset = Publisher.objects.all()
            elif hasattr(user, "publisher") and user.publisher:
                self.fields["publisher"].widget = forms.HiddenInput()
                self.fields["publisher"].initial = user.publisher.pk
                from doi_portal.publishers.models import Publisher
                self.fields["publisher"].queryset = Publisher.objects.filter(
                    pk=user.publisher.pk
                )
            else:
                from doi_portal.publishers.models import Publisher
                self.fields["publisher"].queryset = Publisher.objects.none()

    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.publication_type = PublicationType.CONFERENCE
        instance.title = instance.conference_name
        if commit:
            instance.save()
        return instance


class WizardProceedingsForm(forms.ModelForm):
    """
    Step 2 form: Proceedings (Issue) creation/editing.

    Includes DOI suffix validation replicated from IssueForm.
    """

    class Meta:
        model = Issue
        fields = [
            "proceedings_title",
            "proceedings_publisher_name",
            "proceedings_publisher_place",
            "year",
            "doi_suffix",
        ]
        widgets = {
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
            "year": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "npr. 2026",
                    "min": "1900",
                    "max": "2100",
                }
            ),
            "doi_suffix": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "npr. zbornik-2025-vol1",
                }
            ),
        }

    def __init__(self, *args, publication=None, **kwargs):
        super().__init__(*args, **kwargs)
        self._publication = publication
        # Prefill logic when creating new (no instance pk)
        if publication and not (self.instance and self.instance.pk):
            if not self.initial.get("proceedings_title"):
                self.initial["proceedings_title"] = publication.conference_name or ""
            if not self.initial.get("proceedings_publisher_name"):
                self.initial["proceedings_publisher_name"] = (
                    publication.publisher.name if publication.publisher else ""
                )
            if not self.initial.get("year"):
                if publication.conference_date:
                    self.initial["year"] = publication.conference_date.year

    def clean_doi_suffix(self):
        value = self.cleaned_data.get("doi_suffix", "").strip()
        if not value:
            return value
        if value.startswith("/"):
            raise ValidationError("DOI sufiks ne sme počinjati sa '/'.")
        if " " in value:
            raise ValidationError("DOI sufiks ne sme sadržati razmake.")
        return value

    def save(self, commit=True):
        instance = super().save(commit=False)
        if self._publication:
            instance.publication = self._publication
        if commit:
            instance.save()
        return instance


class WizardPaperForm(forms.ModelForm):
    """
    Step 3 form: Paper (Article) creation/editing.
    """

    class Meta:
        model = Article
        fields = [
            "title",
            "subtitle",
            "abstract",
            "doi_suffix",
            "first_page",
            "last_page",
            "language",
            "license_url",
            "free_to_read",
        ]
        widgets = {
            "title": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Naslov rada",
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
                    "rows": 4,
                    "placeholder": "Apstrakt rada",
                }
            ),
            "doi_suffix": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "npr. rad.2026.001",
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
            "language": forms.Select(
                choices=LANGUAGE_CHOICES,
                attrs={"class": "form-select"}
            ),
            "license_url": forms.URLInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "https://creativecommons.org/licenses/by/4.0/",
                }
            ),
            "free_to_read": forms.CheckboxInput(
                attrs={"class": "form-check-input"}
            ),
        }

    def __init__(self, *args, issue=None, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self._issue = issue
        self._user = user

    def save(self, commit=True):
        instance = super().save(commit=False)
        if self._issue:
            instance.issue = self._issue
        if self._user and not instance.pk:
            instance.created_by = self._user
        if commit:
            instance.save()
        return instance
