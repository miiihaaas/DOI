"""
Forms for the public portal.

Story 4.9: Contact Form (FR44, FR45)
"""

from django import forms
from django.core.exceptions import ValidationError


class ContactForm(forms.Form):
    """
    Contact form for DOI Portal.

    Story 4.9: FR44 - Posetilac može poslati poruku preko kontakt forme.

    Includes honeypot field for spam protection.
    All fields are required except honeypot.
    """

    name = forms.CharField(
        label="Ime i prezime",
        max_length=100,
        widget=forms.TextInput(attrs={
            "class": "form-control",
            "placeholder": "Vaše ime i prezime",
            "aria-describedby": "id_name_error",
        }),
        error_messages={
            "required": "Molimo unesite vaše ime.",
            "max_length": "Ime ne može biti duže od 100 karaktera.",
        }
    )

    email = forms.EmailField(
        label="Email adresa",
        widget=forms.EmailInput(attrs={
            "class": "form-control",
            "placeholder": "vaša@email.adresa",
            "aria-describedby": "id_email_error",
        }),
        error_messages={
            "required": "Molimo unesite vašu email adresu.",
            "invalid": "Molimo unesite validnu email adresu.",
        }
    )

    subject = forms.CharField(
        label="Tema poruke",
        max_length=200,
        widget=forms.TextInput(attrs={
            "class": "form-control",
            "placeholder": "Tema vaše poruke",
            "aria-describedby": "id_subject_error",
        }),
        error_messages={
            "required": "Molimo unesite temu poruke.",
            "max_length": "Tema ne može biti duža od 200 karaktera.",
        }
    )

    message = forms.CharField(
        label="Poruka",
        max_length=5000,
        widget=forms.Textarea(attrs={
            "class": "form-control",
            "placeholder": "Vaša poruka...",
            "rows": 6,
            "aria-describedby": "id_message_error",
        }),
        error_messages={
            "required": "Molimo unesite vašu poruku.",
            "max_length": "Poruka ne može biti duža od 5000 karaktera.",
        }
    )

    # Honeypot field - must be empty, hidden via CSS
    website = forms.CharField(
        label="Website (ostavite prazno)",
        required=False,
        widget=forms.TextInput(attrs={
            "class": "form-control",
            "tabindex": "-1",
            "autocomplete": "off",
        }),
    )

    def clean(self):
        """Validate form including honeypot spam protection."""
        cleaned_data = super().clean()
        # Honeypot check - if filled, it's a bot
        website = cleaned_data.get("website")
        if website:
            raise ValidationError("Spam detected.")
        return cleaned_data
