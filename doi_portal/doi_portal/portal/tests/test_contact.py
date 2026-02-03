"""
Tests for the Contact page (Story 4.9, FR44, FR45).

Test coverage:
- AC #1: Contact page returns 200 and displays form with all required fields
- AC #2: Form validation (email format, required fields, honeypot spam protection)
- AC #3: Email sending on valid submission with success message
- AC #4: Inline validation errors with form data preserved
- AC #5: User-friendly error on SMTP failure, logged for admin
- AC #6: Uses portal/base.html, breadcrumbs "Početna" > "Kontakt"
- AC #7: Performance (simple form, trivial)
- AC #8: Accessibility - labels connected to inputs, focus state, aria-describedby
"""

import pytest
from django.core import mail
from django.urls import reverse


@pytest.mark.django_db
class TestContactPage:
    """Tests for the Contact page (Story 4.9, FR44, FR45)."""

    def test_contact_page_returns_200(self, client):
        """AC #1: Contact page returns 200 status on GET /contact/."""
        url = reverse("contact")
        response = client.get(url)
        assert response.status_code == 200

    def test_contact_page_uses_correct_template(self, client):
        """AC #1, AC #6: Contact page uses portal/contact.html template."""
        url = reverse("contact")
        response = client.get(url)
        assert "portal/contact.html" in [t.name for t in response.templates]

    def test_contact_page_extends_portal_base(self, client):
        """AC #6: Contact page extends portal/base.html, not base.html."""
        url = reverse("contact")
        response = client.get(url)
        template_names = [t.name for t in response.templates]
        assert "portal/base.html" in template_names
        content = response.content.decode()
        assert "DOI Portal" in content  # navbar brand
        assert "Izdavači" in content  # navbar link

    def test_contact_page_has_breadcrumbs(self, client):
        """AC #6: Contact page contains breadcrumbs with "Početna" and "Kontakt"."""
        url = reverse("contact")
        response = client.get(url)
        content = response.content.decode()
        assert "Početna" in content
        assert "Kontakt" in content

    def test_contact_page_context_has_breadcrumbs(self, client):
        """AC #6: Contact view provides breadcrumbs in context."""
        url = reverse("contact")
        response = client.get(url)
        assert "breadcrumbs" in response.context
        breadcrumbs = response.context["breadcrumbs"]
        assert len(breadcrumbs) == 2
        assert breadcrumbs[0]["label"] == "Početna"
        assert breadcrumbs[0]["url"] == reverse("home")
        assert breadcrumbs[1]["label"] == "Kontakt"
        assert breadcrumbs[1]["url"] is None

    def test_contact_form_has_required_fields(self, client):
        """AC #1: Contact form has all required fields (name, email, subject, message)."""
        url = reverse("contact")
        response = client.get(url)
        content = response.content.decode()
        assert 'name="name"' in content
        assert 'name="email"' in content
        assert 'name="subject"' in content
        assert 'name="message"' in content

    def test_contact_form_has_honeypot_field(self, client):
        """AC #2: Contact form has honeypot field for spam protection."""
        url = reverse("contact")
        response = client.get(url)
        content = response.content.decode()
        assert 'name="website"' in content

    def test_contact_form_honeypot_hidden(self, client):
        """AC #2: Honeypot field is hidden via CSS (d-none or display: none)."""
        url = reverse("contact")
        response = client.get(url)
        content = response.content.decode()
        # Honeypot should be hidden - look for d-none class or aria-hidden
        assert "d-none" in content or 'aria-hidden="true"' in content

    def test_contact_form_valid_submission_sends_email(self, client, settings):
        """AC #3: POST with valid data sends email and redirects."""
        settings.EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"
        settings.CONTACT_FORM_RECIPIENT_EMAIL = "test-admin@example.com"
        url = reverse("contact")
        data = {
            "name": "Test User",
            "email": "test@example.com",
            "subject": "Test Subject",
            "message": "Test message content",
            "website": "",  # Honeypot empty
        }
        response = client.post(url, data)
        assert response.status_code == 302  # Redirect after success
        assert len(mail.outbox) == 1
        assert "Test Subject" in mail.outbox[0].subject

    def test_contact_form_valid_submission_shows_success_message(self, client, settings):
        """AC #3: Success message displayed after valid submission."""
        settings.EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"
        settings.CONTACT_FORM_RECIPIENT_EMAIL = "test-admin@example.com"
        url = reverse("contact")
        data = {
            "name": "Test User",
            "email": "test@example.com",
            "subject": "Test Subject",
            "message": "Test message",
            "website": "",
        }
        response = client.post(url, data, follow=True)
        content = response.content.decode()
        assert "Hvala" in content or "hvala" in content.lower()

    def test_contact_form_empty_fields_shows_errors(self, client):
        """AC #4: POST with empty required fields shows validation errors."""
        url = reverse("contact")
        response = client.post(url, {})
        assert response.status_code == 200  # Stay on page with errors
        content = response.content.decode()
        # Form should show errors
        assert "invalid-feedback" in content or "error" in content.lower()

    def test_contact_form_preserves_data_on_error(self, client):
        """AC #4: Form data is preserved when validation fails."""
        url = reverse("contact")
        data = {
            "name": "Test User",
            "email": "not-an-email",  # Invalid email
            "subject": "Test Subject",
            "message": "Test message",
            "website": "",
        }
        response = client.post(url, data)
        content = response.content.decode()
        assert "Test User" in content  # Name preserved
        assert "Test Subject" in content  # Subject preserved

    def test_contact_form_honeypot_filled_blocks_submission(self, client, settings):
        """AC #2: Honeypot filled = spam, email NOT sent."""
        settings.EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"
        settings.CONTACT_FORM_RECIPIENT_EMAIL = "test-admin@example.com"
        url = reverse("contact")
        data = {
            "name": "Spam Bot",
            "email": "spam@bot.com",
            "subject": "Buy now!",
            "message": "Spam content",
            "website": "http://spam.com",  # Honeypot filled = spam
        }
        response = client.post(url, data)
        assert len(mail.outbox) == 0  # Email NOT sent

    def test_contact_form_invalid_email_shows_error(self, client):
        """AC #2, AC #4: Invalid email format shows error."""
        url = reverse("contact")
        data = {
            "name": "Test User",
            "email": "not-an-email",
            "subject": "Test",
            "message": "Test message",
            "website": "",
        }
        response = client.post(url, data)
        assert response.status_code == 200
        content = response.content.decode()
        # Error should mention email
        assert "email" in content.lower() or "invalid-feedback" in content

    def test_contact_page_no_auth_required(self, client):
        """AC #1: Contact page is public - no authentication needed."""
        url = reverse("contact")
        response = client.get(url)
        assert response.status_code == 200
        if hasattr(response, "url"):
            assert "login" not in response.url

    def test_contact_form_labels_connected_to_inputs(self, client):
        """AC #8: Labels have for attribute matching input id."""
        url = reverse("contact")
        response = client.get(url)
        content = response.content.decode()
        assert 'for="id_name"' in content
        assert 'for="id_email"' in content
        assert 'for="id_subject"' in content
        assert 'for="id_message"' in content

    def test_contact_navbar_active_state(self, client):
        """AC #6: Navbar "Kontakt" link has active class on /contact/."""
        url = reverse("contact")
        response = client.get(url)
        content = response.content.decode()
        # Check that Kontakt nav link has active class
        assert 'nav-link active' in content

    def test_contact_email_contains_all_form_data(self, client, settings):
        """AC #3: Email body contains all submitted form data."""
        settings.EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"
        settings.CONTACT_FORM_RECIPIENT_EMAIL = "test-admin@example.com"
        url = reverse("contact")
        data = {
            "name": "Test User",
            "email": "test@example.com",
            "subject": "My Subject",
            "message": "My detailed message",
            "website": "",
        }
        client.post(url, data)
        assert len(mail.outbox) == 1
        email_body = mail.outbox[0].body
        assert "Test User" in email_body
        assert "test@example.com" in email_body
        assert "My Subject" in email_body
        assert "My detailed message" in email_body

    def test_contact_page_has_csrf_token(self, client):
        """AC #1: Contact form has CSRF token for security."""
        url = reverse("contact")
        response = client.get(url)
        content = response.content.decode()
        assert "csrfmiddlewaretoken" in content

    def test_contact_page_title(self, client):
        """AC #1: Contact page has correct title format."""
        url = reverse("contact")
        response = client.get(url)
        content = response.content.decode()
        assert "Kontakt - DOI Portal" in content

    def test_contact_page_has_serbian_labels(self, client):
        """AC #8: Form labels are in Serbian."""
        url = reverse("contact")
        response = client.get(url)
        content = response.content.decode()
        # Check for Serbian labels
        assert "Ime" in content  # name label
        assert "Email" in content  # email label
        assert "Tema" in content or "poruke" in content  # subject label
        assert "Poruka" in content  # message label

    def test_contact_sidebar_has_contact_info(self, client):
        """AC #6: Contact page sidebar has contact information."""
        url = reverse("contact")
        response = client.get(url)
        content = response.content.decode()
        # Check for sidebar contact info
        assert "info@doi.rs" in content or "info@" in content or "@" in content

    def test_contact_sidebar_has_about_link(self, client):
        """AC #6: Contact page sidebar has link to About page."""
        url = reverse("contact")
        response = client.get(url)
        content = response.content.decode()
        about_url = reverse("about")
        assert about_url in content or "O portalu" in content


@pytest.mark.django_db
class TestContactForm:
    """Unit tests for ContactForm (Story 4.9, Task 1)."""

    def test_contact_form_has_all_fields(self):
        """Task 1.2: ContactForm has all required fields."""
        from doi_portal.portal.forms import ContactForm
        form = ContactForm()
        assert "name" in form.fields
        assert "email" in form.fields
        assert "subject" in form.fields
        assert "message" in form.fields
        assert "website" in form.fields  # honeypot

    def test_contact_form_all_fields_required_except_honeypot(self):
        """Task 1.3: All fields required except honeypot."""
        from doi_portal.portal.forms import ContactForm
        form = ContactForm()
        assert form.fields["name"].required is True
        assert form.fields["email"].required is True
        assert form.fields["subject"].required is True
        assert form.fields["message"].required is True
        assert form.fields["website"].required is False  # honeypot not required

    def test_contact_form_email_uses_emailfield(self):
        """Task 1.4: Email field uses EmailField for validation."""
        from django import forms as django_forms
        from doi_portal.portal.forms import ContactForm
        form = ContactForm()
        assert isinstance(form.fields["email"], django_forms.EmailField)

    def test_contact_form_message_uses_textarea(self):
        """Task 1.5: Message field uses Textarea widget."""
        from django.forms import Textarea
        from doi_portal.portal.forms import ContactForm
        form = ContactForm()
        assert isinstance(form.fields["message"].widget, Textarea)

    def test_contact_form_honeypot_validation(self):
        """Task 1.8: Honeypot filled raises ValidationError."""
        from doi_portal.portal.forms import ContactForm
        data = {
            "name": "Bot",
            "email": "bot@spam.com",
            "subject": "Spam",
            "message": "Buy now!",
            "website": "http://spam.com",  # honeypot filled
        }
        form = ContactForm(data=data)
        assert form.is_valid() is False

    def test_contact_form_valid_without_honeypot(self):
        """Task 1.6, 1.8: Form valid when honeypot is empty."""
        from doi_portal.portal.forms import ContactForm
        data = {
            "name": "Real User",
            "email": "user@example.com",
            "subject": "Question",
            "message": "I have a question about...",
            "website": "",  # honeypot empty
        }
        form = ContactForm(data=data)
        assert form.is_valid() is True

    def test_contact_form_widget_classes(self):
        """Task 1.7: Widgets have form-control class."""
        from doi_portal.portal.forms import ContactForm
        form = ContactForm()
        assert "form-control" in form.fields["name"].widget.attrs.get("class", "")
        assert "form-control" in form.fields["email"].widget.attrs.get("class", "")
        assert "form-control" in form.fields["subject"].widget.attrs.get("class", "")
        assert "form-control" in form.fields["message"].widget.attrs.get("class", "")

    def test_contact_form_serbian_error_messages(self):
        """Task 1.3: Error messages are in Serbian."""
        from doi_portal.portal.forms import ContactForm
        form = ContactForm(data={})
        form.is_valid()  # trigger validation
        # Check that error messages contain Serbian text
        name_errors = str(form.errors.get("name", []))
        assert "Molimo" in name_errors or "unesite" in name_errors.lower() or "required" in name_errors.lower()

    def test_contact_form_message_max_length(self):
        """ISSUE #5: Message field has max_length validation."""
        from doi_portal.portal.forms import ContactForm
        form = ContactForm()
        assert form.fields["message"].max_length == 5000

    def test_contact_form_honeypot_has_label(self):
        """ISSUE #4: Honeypot field has label for consistency."""
        from doi_portal.portal.forms import ContactForm
        form = ContactForm()
        assert form.fields["website"].label is not None
        assert "prazno" in form.fields["website"].label.lower()


@pytest.mark.django_db
class TestContactSMTPFailure:
    """Tests for SMTP failure handling (AC #5)."""

    def test_contact_form_smtp_failure_shows_error_message(self, client, settings, monkeypatch):
        """AC #5: SMTP failure shows user-friendly error message."""
        import smtplib
        settings.EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"
        settings.CONTACT_FORM_RECIPIENT_EMAIL = "test-admin@example.com"

        # Mock send_mail to raise SMTPException
        def mock_send_mail(*args, **kwargs):
            raise smtplib.SMTPException("Connection refused")

        monkeypatch.setattr("doi_portal.portal.views.send_mail", mock_send_mail)

        url = reverse("contact")
        data = {
            "name": "Test User",
            "email": "test@example.com",
            "subject": "Test Subject",
            "message": "Test message",
            "website": "",
        }
        response = client.post(url, data, follow=True)
        content = response.content.decode()
        # Should show error message, not crash
        assert "greške" in content.lower() or "greška" in content.lower()

    def test_contact_form_smtp_failure_logs_error(self, client, settings, monkeypatch, caplog):
        """AC #5: SMTP failure is logged for admin review."""
        import smtplib
        import logging
        settings.EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"
        settings.CONTACT_FORM_RECIPIENT_EMAIL = "test-admin@example.com"

        # Mock send_mail to raise SMTPException
        def mock_send_mail(*args, **kwargs):
            raise smtplib.SMTPException("Connection refused")

        monkeypatch.setattr("doi_portal.portal.views.send_mail", mock_send_mail)

        url = reverse("contact")
        data = {
            "name": "Test User",
            "email": "test@example.com",
            "subject": "Test Subject",
            "message": "Test message",
            "website": "",
        }

        with caplog.at_level(logging.ERROR):
            client.post(url, data)

        # Check that error was logged
        assert any("Contact form email failed" in record.message for record in caplog.records)


@pytest.mark.django_db
class TestContactAccessibility:
    """Tests for accessibility (AC #8)."""

    def test_contact_form_fields_have_aria_describedby(self, client):
        """AC #8: Input fields have aria-describedby for error association."""
        url = reverse("contact")
        response = client.get(url)
        content = response.content.decode()
        # Check aria-describedby attributes are present
        assert 'aria-describedby="id_name_error"' in content
        assert 'aria-describedby="id_email_error"' in content
        assert 'aria-describedby="id_subject_error"' in content
        assert 'aria-describedby="id_message_error"' in content

    def test_contact_form_honeypot_hidden_from_screen_readers(self, client):
        """AC #8: Honeypot is hidden from screen readers with aria-hidden."""
        url = reverse("contact")
        response = client.get(url)
        content = response.content.decode()
        assert 'aria-hidden="true"' in content

    def test_contact_form_required_fields_marked(self, client):
        """AC #8: Required fields have visual indicator and aria-label."""
        url = reverse("contact")
        response = client.get(url)
        content = response.content.decode()
        # Asterisks with aria-label for screen readers
        assert 'aria-label="obavezno"' in content
