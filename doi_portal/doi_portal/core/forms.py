"""
Core forms for DOI Portal.

Story 6.4: GdprRequestForm for creating GDPR data requests.
"""

from django import forms
from django.utils.translation import gettext_lazy as _

from doi_portal.core.models import GdprRequest

__all__ = ["GdprRequestForm"]


class GdprRequestForm(forms.ModelForm):
    """Form for creating a new GDPR data request."""

    class Meta:
        model = GdprRequest
        fields = ["requester_email", "request_type", "notes", "received_date"]
        labels = {
            "requester_email": _("Email podnosioca"),
            "request_type": _("Tip zahteva"),
            "notes": _("Napomene"),
            "received_date": _("Datum prijema"),
        }
        widgets = {
            "received_date": forms.DateInput(attrs={"type": "date"}),
        }
