"""
Tests for Publication forms.

Story 2-4a: Language Select widget tests.
"""

import pytest
from django import forms

from doi_portal.core.constants import LANGUAGE_CHOICES
from doi_portal.publications.forms import PublicationForm

from .factories import PublicationFactory


# =============================================================================
# Story 2-4a: Test language Select widget
# =============================================================================


@pytest.mark.django_db
class TestPublicationFormLanguageWidget:
    """Test PublicationForm language field uses Select widget."""

    def test_language_field_is_select_widget(self):
        """2-4a: Language field renders as Select widget, not TextInput."""
        form = PublicationForm()
        widget = form.fields["language"].widget
        assert isinstance(widget, forms.Select)

    def test_language_widget_has_form_select_class(self):
        """2-4a: Language Select widget has Bootstrap form-select class."""
        form = PublicationForm()
        css_class = form.fields["language"].widget.attrs.get("class", "")
        assert "form-select" in css_class

    def test_language_widget_has_correct_choices(self):
        """2-4a: Language Select widget has all LANGUAGE_CHOICES options."""
        form = PublicationForm()
        widget_choices = list(form.fields["language"].widget.choices)
        for code, label in LANGUAGE_CHOICES:
            assert (code, label) in widget_choices

    def test_language_help_text(self):
        """2-4a: Language field has correct help text."""
        form = PublicationForm()
        help_text = form.fields["language"].help_text
        assert help_text == "Primarni jezik publikacije. Članci/radovi mogu biti na različitim jezicima."

    def test_existing_language_sr_selected(self):
        """2-4a: Existing publication with language='sr' correctly selects that option."""
        publication = PublicationFactory(language="sr")
        form = PublicationForm(instance=publication)
        assert form.initial["language"] == "sr"
        # Fix #5: verify rendered HTML contains selected option
        rendered = str(form["language"])
        assert 'selected' in rendered
        assert '"sr"' in rendered

    def test_existing_language_en_selected(self):
        """2-4a: Existing publication with language='en' correctly selects that option."""
        publication = PublicationFactory(language="en")
        form = PublicationForm(instance=publication)
        assert form.initial["language"] == "en"
        # Fix #5: verify rendered HTML contains selected option
        rendered = str(form["language"])
        assert 'selected' in rendered
        assert '"en"' in rendered

    def test_invalid_language_code_rejected(self):
        """2-4a: Submitting a language code not in LANGUAGE_CHOICES is rejected."""
        from .factories import PublisherFactory

        publisher = PublisherFactory()
        form = PublicationForm(
            data={
                "title": "Test publikacija",
                "publisher": publisher.pk,
                "publication_type": "JOURNAL",
                "language": "xx",
                "access_type": "OPEN",
            }
        )
        assert not form.is_valid()
        assert "language" in form.errors

    def test_unlisted_language_preserved_for_existing_instance(self):
        """2-4a: Existing publication with unlisted language code gets it injected into choices."""
        publication = PublicationFactory(language="pt")
        form = PublicationForm(instance=publication)
        widget_choices = list(form.fields["language"].widget.choices)
        choice_codes = [code for code, _ in widget_choices]
        assert "pt" in choice_codes
