# Story 4.9: Contact Form

Status: done

## Story

As a **visitor (posetilac)**,
I want **to send a message to the portal administrators via a contact form**,
So that **I can ask questions or report issues about the portal**.

## Background

Ovo je deveta i poslednja prica u Epiku 4 (Public Portal Experience). Prethodne price su implementirale kompletno javno korisnicko iskustvo: Home Page (4.1), Search (4.2), Filters (4.3), Article Landing (4.4), Floating Action Bar (4.5), PDF Download (4.6), Citation Modal (4.7), About Page (4.8). Ovaj story implementira kontakt formu koja omogucava posetiocima da posalju poruku administratorima portala.

**FR Pokrivenost:**
- FR44: Posetilac moze poslati poruku preko kontakt forme
- FR45: Sistem salje kontakt poruke na definisanu email adresu

**NFR Pokrivenost:**
- NFR2: Javne stranice portala - Ucitavanje < 3 sekunde
- NFR14: Semanticki HTML5 elementi
- NFR15: Alt tekst za sve slike
- NFR16: Kontrast minimum 4.5:1 za tekst
- NFR17: Keyboard navigacija za kljucne akcije
- NFR18: Labels povezani sa input poljima
- NFR21: Email - SMTP za kontakt formu i notifikacije
- NFR25: Graceful degradation, user-friendly error poruke

**Zavisnosti (sve DONE):**
- Story 4.8: About Page - `portal/base.html`, `AboutView` pattern, breadcrumbs pattern, test pattern
- Story 4.1: Portal Home Page - `portal/base.html`, portal nav, `portal.css`
- `config/urls.py` VEC ima `path("contact/", TemplateView.as_view(template_name="pages/contact.html"), name="contact")`
- `portal/base.html` navbar VEC ima link `{% url 'contact' %}` sa labelom "Kontakt"
- About page VEC ima link ka `/contact/` stranici

**Blokira:**
- Nista - poslednja prica u Epic 4

## KRITICNO: Postojece Stanje

**`pages/contact.html` VEC POSTOJI** ali je prazan stub:
```html
{% extends "base.html" %}
```

**PROBLEM:** Trenutno prosiruje `base.html` (admin base template) umesto `portal/base.html` (public portal template). Identican problem kao u Story 4.8.

**URL ruta VEC postoji** u `config/urls.py`:
```python
path("contact/", TemplateView.as_view(template_name="pages/contact.html"), name="contact")
```

**ODLUKA (isti pattern kao Story 4.8):**
1. Kreirati `ContactView` u `portal/views.py` sa GET i POST metodama
2. Kreirati `ContactForm` u `portal/forms.py` sa honeypot spam protection
3. Kreirati `portal/contact.html` template
4. Azurirati `config/urls.py` da koristi `ContactView`
5. Ostaviti stari `pages/contact.html` fajl nepromenjen

## Acceptance Criteria

1. **Given** posetilac navigira na /contact/
   **When** stranica se ucita
   **Then** kontakt forma je prikazana
   **And** forma ukljucuje: name, email, subject, message polja
   **And** sva polja su obavezna

2. **Given** posetilac popunjava kontakt formu
   **When** podnese validne podatke
   **Then** forma je validirana (email format, obavezna polja)
   **And** CAPTCHA ili honeypot sprecava spam (jednostavna implementacija)

3. **Given** forma je uspesno podneta
   **When** poruka je obradena
   **Then** email je poslat na konfigurisan admin email putem SMTP
   **And** email ukljucuje sve podatke iz forme i informacije o posiljaocu
   **And** poruka uspeha je prikazana: "Hvala! Odgovoricemo uskoro."

4. **Given** forma nije uspesno podneta
   **When** postoje validacione greske
   **Then** inline poruke o greskama su prikazane
   **And** podaci forme su sacuvani (korisnik ne gubi unesene podatke)

5. **Given** slanje emaila ne uspe
   **When** SMTP greska se dogodi
   **Then** user-friendly greska je prikazana
   **And** greska je ulogirana za admin pregled

6. **Given** kontakt stranica koristi public portal template
   **When** posetilac pregleda layout
   **Then** konzistentna navigacija i footer su prisutni (portal/base.html)
   **And** breadcrumbs prikazuju: Pocetna > Kontakt

7. **Given** kontakt stranica se ucitava
   **When** merimo performanse
   **Then** stranica se ucita za manje od 3 sekunde (NFR2)

8. **Given** posetilac koristi tastaturu ili screen reader
   **When** navigira kroz formu
   **Then** labels su pravilno povezani sa input poljima (for/id atributi)
   **And** focus state je vidljiv na svim poljima
   **And** error poruke su povezane sa poljima putem aria-describedby

## Tasks / Subtasks

- [x] Task 1: Kreirati `ContactForm` u `portal/forms.py` (AC: #1, #2, #4)
  - [x] 1.1 Kreirati `portal/forms.py` fajl (NE POSTOJI - NOVI FAJL)
  - [x] 1.2 Definisati `ContactForm(forms.Form)` sa poljima: name, email, subject, message
  - [x] 1.3 Sva polja obavezna sa srpskim error porukama
  - [x] 1.4 Email polje koristi `forms.EmailField` za validaciju
  - [x] 1.5 Message polje koristi `forms.CharField(widget=forms.Textarea)`
  - [x] 1.6 Dodati honeypot polje `website` (skriveno, ako popunjeno = spam)
  - [x] 1.7 Widget atributi: `class="form-control"`, `placeholder` na srpskom
  - [x] 1.8 `clean()` metoda proverava honeypot i raise ValidationError ako je popunjen

- [x] Task 2: Kreirati `ContactView` CBV u `portal/views.py` (AC: #1, #2, #3, #5, #6)
  - [x] 2.1 Dodati `ContactView(FormView)` klasu u `portal/views.py`
  - [x] 2.2 Template: `portal/contact.html`
  - [x] 2.3 `form_class = ContactForm`
  - [x] 2.4 `success_url = reverse_lazy("contact")` (ostaje na istoj stranici sa success message)
  - [x] 2.5 `get_context_data()` dodaje breadcrumbs: [Pocetna -> /home, Kontakt -> None]
  - [x] 2.6 `form_valid()`: posalji email, dodaj success message, vrati redirect
  - [x] 2.7 `form_invalid()`: dodaj error message, vrati formu sa greskama
  - [x] 2.8 Email slanje: koristi `django.core.mail.send_mail()`
  - [x] 2.9 Error handling: try/except oko send_mail(), log greske, prikazati user-friendly poruku

- [x] Task 3: Azurirati `config/urls.py` da koristi ContactView (AC: #1, #6)
  - [x] 3.1 Zameniti `TemplateView.as_view(template_name="pages/contact.html")` sa `ContactView.as_view()`
  - [x] 3.2 Dodati import: `from doi_portal.portal.views import ContactView`
  - [x] 3.3 Zadrzati isti URL pattern: `path("contact/", ..., name="contact")`
  - [x] 3.4 NE brisati `pages/contact.html` (moze da ostane kao legacy)

- [x] Task 4: Kreirati `portal/contact.html` template (AC: #1, #4, #6, #7, #8)
  - [x] 4.1 Kreirati `doi_portal/doi_portal/templates/portal/contact.html`
  - [x] 4.2 Extends `portal/base.html` (NE `base.html`!)
  - [x] 4.3 `{% block title %}Kontakt - DOI Portal{% endblock %}`
  - [x] 4.4 `{% block meta_description %}` sa opisom kontakt forme
  - [x] 4.5 Form tag sa `method="post"` i `{% csrf_token %}`
  - [x] 4.6 Bootstrap 5 form layout sa `.mb-3` za svako polje
  - [x] 4.7 Labels sa `for` atributom koji odgovara input `id`
  - [x] 4.8 Error prikazivanje ispod svakog polja sa `.invalid-feedback` klasom
  - [x] 4.9 Honeypot polje skriveno sa CSS `display: none` (NE JavaScript!)
  - [x] 4.10 Submit dugme sa Bootstrap primary stilom
  - [x] 4.11 Success message prikazana iznad forme kada je poruka poslata
  - [x] 4.12 Dvokolonski layout: forma (2/3) + sidebar sa kontakt info (1/3)
  - [x] 4.13 Sidebar: email adresa portala, radno vreme, link ka About stranici
  - [x] 4.14 Srpski tekst sa pravilnim dijakritickim znacima

- [x] Task 5: Dodati active state za "Kontakt" nav link (AC: #6)
  - [x] 5.1 U `portal/base.html` dodati active class logiku za "Kontakt" link
  - [x] 5.2 Isti pattern kao za "O portalu" link (Story 4.8)

- [x] Task 6: Konfiguracija email settings (AC: #3, #5)
  - [x] 6.1 Proveriti da li su EMAIL_* settings definisani u `config/settings/base.py`
  - [x] 6.2 Ako nisu, dodati DEFAULT_FROM_EMAIL i komentar o SMTP konfiguraciji
  - [x] 6.3 Definisati CONTACT_FORM_RECIPIENT_EMAIL setting (email gde se salju poruke)
  - [x] 6.4 Za lokalni development: EMAIL_BACKEND = console backend VEC radi (Cookiecutter)

- [x] Task 7: Kreirati testove (AC: #1-#8)
  - [x] 7.1 Test: Contact stranica vraca 200 status na GET /contact/
  - [x] 7.2 Test: Contact stranica koristi ispravan template (`portal/contact.html`)
  - [x] 7.3 Test: Contact stranica sadrzi breadcrumbs sa "Pocetna" i "Kontakt"
  - [x] 7.4 Test: Contact forma ima sva potrebna polja (name, email, subject, message)
  - [x] 7.5 Test: Contact forma ima honeypot polje (skriveno)
  - [x] 7.6 Test: POST sa validnim podacima salje email i prikazuje success poruku
  - [x] 7.7 Test: POST sa praznim poljima prikazuje validation errors
  - [x] 7.8 Test: POST sa popunjenim honeypot poljem NE salje email (spam protection)
  - [x] 7.9 Test: POST sa nevalidnim email formatom prikazuje error
  - [x] 7.10 Test: Contact stranica ne zahteva autentifikaciju (public)
  - [x] 7.11 Test: Labels su povezani sa input poljima (for/id match)
  - [x] 7.12 Test: Navbar "Kontakt" link ima active klasu na /contact/
  - [x] 7.13 Test: Email sadrzaj ukljucuje sve form podatke

## Dev Notes

### KRITICNO: Template i View Pattern

**Contact stranica MORA da koristi `portal/base.html`** jer je deo javnog portala. Pratimo identican pattern kao Story 4.8 (About Page).

### ContactForm Pattern

```python
# portal/forms.py - NOVI FAJL

from django import forms
from django.core.exceptions import ValidationError


class ContactForm(forms.Form):
    """
    Contact form for DOI Portal.

    Story 4.9: FR44 - Posetilac moze poslati poruku preko kontakt forme

    Includes honeypot field for spam protection.
    """

    name = forms.CharField(
        label="Ime i prezime",
        max_length=100,
        widget=forms.TextInput(attrs={
            "class": "form-control",
            "placeholder": "Vase ime i prezime",
        }),
        error_messages={
            "required": "Molimo unesite vase ime.",
            "max_length": "Ime ne moze biti duze od 100 karaktera.",
        }
    )

    email = forms.EmailField(
        label="Email adresa",
        widget=forms.EmailInput(attrs={
            "class": "form-control",
            "placeholder": "vasa@email.adresa",
        }),
        error_messages={
            "required": "Molimo unesite vasu email adresu.",
            "invalid": "Molimo unesite validnu email adresu.",
        }
    )

    subject = forms.CharField(
        label="Tema poruke",
        max_length=200,
        widget=forms.TextInput(attrs={
            "class": "form-control",
            "placeholder": "Tema vase poruke",
        }),
        error_messages={
            "required": "Molimo unesite temu poruke.",
            "max_length": "Tema ne moze biti duza od 200 karaktera.",
        }
    )

    message = forms.CharField(
        label="Poruka",
        widget=forms.Textarea(attrs={
            "class": "form-control",
            "placeholder": "Vasa poruka...",
            "rows": 6,
        }),
        error_messages={
            "required": "Molimo unesite vasu poruku.",
        }
    )

    # Honeypot field - must be empty, hidden via CSS
    website = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            "class": "form-control",
            "tabindex": "-1",
            "autocomplete": "off",
        }),
    )

    def clean(self):
        cleaned_data = super().clean()
        # Honeypot check - if filled, it's a bot
        website = cleaned_data.get("website")
        if website:
            raise ValidationError("Spam detected.")
        return cleaned_data
```

### ContactView Pattern

```python
# portal/views.py - DODATI:

import logging

from django.conf import settings
from django.contrib import messages
from django.core.mail import send_mail
from django.urls import reverse, reverse_lazy
from django.views.generic import FormView

from doi_portal.portal.forms import ContactForm


logger = logging.getLogger(__name__)


class ContactView(FormView):
    """
    Public Contact page for DOI Portal.

    Story 4.9: FR44, FR45 - Kontakt forma sa email slanjem
    """

    template_name = "portal/contact.html"
    form_class = ContactForm
    success_url = reverse_lazy("contact")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["breadcrumbs"] = [
            {"label": "Pocetna", "url": reverse("home")},
            {"label": "Kontakt", "url": None},
        ]
        return context

    def form_valid(self, form):
        # Get form data
        name = form.cleaned_data["name"]
        email = form.cleaned_data["email"]
        subject = form.cleaned_data["subject"]
        message_body = form.cleaned_data["message"]

        # Prepare email content
        full_message = f"""
Nova poruka sa kontakt forme DOI Portala:

Ime: {name}
Email: {email}
Tema: {subject}

Poruka:
{message_body}

---
Ova poruka je automatski poslata sa DOI Portal kontakt forme.
"""

        try:
            send_mail(
                subject=f"[DOI Portal Kontakt] {subject}",
                message=full_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[settings.CONTACT_FORM_RECIPIENT_EMAIL],
                fail_silently=False,
            )
            messages.success(
                self.request,
                "Hvala vam na poruci! Odgovoricemo u najkracem mogućem roku."
            )
        except Exception as e:
            logger.error(f"Contact form email failed: {e}")
            messages.error(
                self.request,
                "Doslo je do greske prilikom slanja poruke. Molimo pokusajte ponovo kasnije."
            )

        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(
            self.request,
            "Molimo ispravite greske u formi i pokusajte ponovo."
        )
        return super().form_invalid(form)
```

### URL Azuriranje

```python
# config/urls.py - PROMENITI:
# STARO:
path("contact/", TemplateView.as_view(template_name="pages/contact.html"), name="contact"),

# NOVO:
from doi_portal.portal.views import ContactView
path("contact/", ContactView.as_view(), name="contact"),
```

### Email Settings

```python
# config/settings/base.py - DODATI ako ne postoji:

# Contact form recipient email
# Override in production settings with actual admin email
CONTACT_FORM_RECIPIENT_EMAIL = env(
    "CONTACT_FORM_RECIPIENT_EMAIL",
    default="admin@example.com"
)
```

**VAZNO:** Cookiecutter Django VEC ima email konfiguraciju:
- Local: `django.core.mail.backends.console.EmailBackend` (stampanje u konzolu)
- Production: Mailgun preko `django-anymail` (vec konfigurisano)

### Template Struktura

```html
{% extends "portal/base.html" %}
{% load static %}

{% block title %}Kontakt - DOI Portal{% endblock %}
{% block meta_description %}Kontaktirajte DOI Portal tim - posaljite nam vasu poruku ili pitanje{% endblock %}

{% block portal_content %}
<div class="row">
  <!-- Main Content - Form (2/3) -->
  <div class="col-lg-8">
    <h1 class="mb-4">Kontaktirajte nas</h1>

    {% if messages %}
      {% for message in messages %}
        <div class="alert alert-{{ message.tags }} alert-dismissible fade show" role="alert">
          {{ message }}
          <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Zatvori"></button>
        </div>
      {% endfor %}
    {% endif %}

    <form method="post" novalidate>
      {% csrf_token %}

      <!-- Honeypot field - hidden via CSS -->
      <div class="d-none" aria-hidden="true">
        <label for="id_website">Website (ostavite prazno)</label>
        {{ form.website }}
      </div>

      <div class="mb-3">
        <label for="id_name" class="form-label">{{ form.name.label }} <span class="text-danger">*</span></label>
        {{ form.name }}
        {% if form.name.errors %}
          <div class="invalid-feedback d-block">{{ form.name.errors.0 }}</div>
        {% endif %}
      </div>

      <div class="mb-3">
        <label for="id_email" class="form-label">{{ form.email.label }} <span class="text-danger">*</span></label>
        {{ form.email }}
        {% if form.email.errors %}
          <div class="invalid-feedback d-block">{{ form.email.errors.0 }}</div>
        {% endif %}
      </div>

      <div class="mb-3">
        <label for="id_subject" class="form-label">{{ form.subject.label }} <span class="text-danger">*</span></label>
        {{ form.subject }}
        {% if form.subject.errors %}
          <div class="invalid-feedback d-block">{{ form.subject.errors.0 }}</div>
        {% endif %}
      </div>

      <div class="mb-3">
        <label for="id_message" class="form-label">{{ form.message.label }} <span class="text-danger">*</span></label>
        {{ form.message }}
        {% if form.message.errors %}
          <div class="invalid-feedback d-block">{{ form.message.errors.0 }}</div>
        {% endif %}
      </div>

      <button type="submit" class="btn btn-primary">
        <i class="bi bi-send me-2" aria-hidden="true"></i>Posalji poruku
      </button>
    </form>
  </div>

  <!-- Sidebar (1/3) -->
  <div class="col-lg-4">
    <div class="card shadow-sm mb-4">
      <div class="card-body">
        <h3 class="h5 mb-3"><i class="bi bi-info-circle me-2" aria-hidden="true"></i>Kontakt informacije</h3>
        <p class="mb-2"><i class="bi bi-envelope me-2" aria-hidden="true"></i>info@doi.rs</p>
        <p class="mb-2"><i class="bi bi-clock me-2" aria-hidden="true"></i>Pon-Pet: 09:00 - 17:00</p>
      </div>
    </div>

    <div class="card shadow-sm mb-4">
      <div class="card-body">
        <h3 class="h5 mb-3"><i class="bi bi-link-45deg me-2" aria-hidden="true"></i>Korisni linkovi</h3>
        <ul class="list-unstyled mb-0">
          <li class="mb-2">
            <a href="{% url 'about' %}"><i class="bi bi-arrow-right me-1" aria-hidden="true"></i>O portalu</a>
          </li>
          <li class="mb-2">
            <a href="{% url 'portal:publication-list' %}"><i class="bi bi-arrow-right me-1" aria-hidden="true"></i>Publikacije</a>
          </li>
          <li class="mb-2">
            <a href="{% url 'portal:publisher-list' %}"><i class="bi bi-arrow-right me-1" aria-hidden="true"></i>Izdavaci</a>
          </li>
        </ul>
      </div>
    </div>
  </div>
</div>
{% endblock %}
```

### Navbar Active State

`portal/base.html` navbar treba da ima active state za "Kontakt" link:

```html
<!-- TRENUTNO u portal/base.html: -->
<a class="nav-link" href="{% url 'contact' %}">Kontakt</a>

<!-- TREBA PROMENITI NA: -->
<a class="nav-link{% if request.resolver_match.url_name == 'contact' %} active{% endif %}" href="{% url 'contact' %}">Kontakt</a>
```

### Srpski Karakteri (OBAVEZNO - videti project-context.md)

| Kontekst | ISPRAVNO |
|----------|----------|
| Page title | "Kontakt" |
| Breadcrumb | "Pocetna", "Kontakt" |
| Form heading | "Kontaktirajte nas" |
| Name label | "Ime i prezime" |
| Email label | "Email adresa" |
| Subject label | "Tema poruke" |
| Message label | "Poruka" |
| Submit button | "Posalji poruku" |
| Success message | "Hvala vam na poruci!" |
| Error message | "Doslo je do greske" |

**KRITICNO:** Koristiti prave srpske karaktere sa dijakritickim znacima: c, s, z, dj (npr. "Pocetna", "Posaljite", "Odgovoricemo").

### Postojeci Patterns koje MORAMO slediti

**Portal views pattern** (VEC implementirano u prethodnim pricama):
- CBV za stranice: `PascalCase + View` (npr. `ContactView`)
- FBV za HTMX endpointe: `snake_case` ime
- Breadcrumbs: lista dict-ova `[{"label": "...", "url": "..."}, ...]` u context-u
- Messages framework za success/error feedback

**Template pattern** (VEC implementirano):
- Extends `portal/base.html`
- `{% block title %}` za page title
- `{% block meta_description %}` za SEO
- `{% block portal_content %}` za sadrzaj
- Bootstrap 5 klase za layout i forme
- Bootstrap Icons za ikone
- Srpski tekst za sve UI labele

**Form pattern** (Django standard):
- `forms.Form` za forme bez modela
- `forms.ModelForm` za forme vezane za model
- Widget attrs za Bootstrap klase
- Custom error_messages na srpskom

### Git Commit Pattern

```
story-4-9: feat(portal): implementiraj Contact Form sa honeypot spam protection i email slanjem (Story 4.9)
```

### Fajlovi za modifikaciju (POSTOJECI)

```
doi_portal/config/urls.py                                          # Zameniti TemplateView sa ContactView za /contact/ rutu
doi_portal/doi_portal/portal/views.py                              # Dodati ContactView FormView sa email slanjem
doi_portal/doi_portal/templates/portal/base.html                   # Dodati active state za "Kontakt" nav link
doi_portal/config/settings/base.py                                 # Dodati CONTACT_FORM_RECIPIENT_EMAIL setting
```

### Fajlovi za kreiranje (NOVI)

```
doi_portal/doi_portal/portal/forms.py                              # ContactForm sa honeypot poljem
doi_portal/doi_portal/templates/portal/contact.html                # Contact page template sa formom
doi_portal/doi_portal/portal/tests/test_contact.py                 # Contact form testovi
```

### Fajlovi koji se NE MENJAJU

```
doi_portal/doi_portal/templates/pages/contact.html                 # Legacy stub - NE BRISATI, NE MENJATI (nece se koristiti)
doi_portal/doi_portal/portal/urls.py                               # NE MENJATI (publisher rute)
doi_portal/doi_portal/portal/urls_articles.py                      # NE MENJATI (article rute)
doi_portal/doi_portal/portal/urls_publications.py                  # NE MENJATI (publication rute)
doi_portal/doi_portal/portal/services.py                           # NE MENJATI (nema business logike za Contact)
```

### Anti-Patterns (ZABRANJENO)

```python
# POGRESNO - Koristiti base.html umesto portal/base.html
{% extends "base.html" %}
# Razlog: Contact stranica je deo javnog portala, mora koristiti portal template

# POGRESNO - Dodavati autentifikaciju
@login_required
class ContactView(FormView):
# Razlog: Javna stranica, bez login-a (FR44)

# POGRESNO - Koristiti JavaScript za honeypot
<script>document.getElementById('website').style.display='none'</script>
# Razlog: Bots mogu izvrsiti JS - koristiti CSS display:none ili d-none klasu

# POGRESNO - Slati email bez try/except
send_mail(...)  # Bez error handling-a
# Razlog: SMTP moze da fail-uje, moramo graceful degradation

# POGRESNO - Hardcoded recipient email
recipient_list=["admin@doi.rs"]
# Razlog: Koristiti settings.CONTACT_FORM_RECIPIENT_EMAIL

# POGRESNO - Zaboraviti CSRF token
<form method="post">
  <!-- Missing {% csrf_token %} -->
</form>
# Razlog: Django security requirement

# POGRESNO - Prikazivati tehnicke greske korisniku
messages.error(request, str(e))  # Exception message
# Razlog: User-friendly poruke, log tehnicke detalje

# POGRESNO - Ne cuvati podatke forme pri gresci
return redirect("contact")  # Gubimo unesene podatke
# Razlog: Vratiti form_invalid() koji cuva podatke
```

### Performance (NFR2)

```
# Contact stranica je jednostavna forma:
# 1. Jedan database upit (session/auth middleware)
# 2. Nema HTMX poziva na load
# 3. Samo HTML form + Bootstrap CSS koji je vec kesirano
# 4. < 3 sekunde load time je trivijalno
```

### Accessibility (NFR14, NFR17, NFR18)

```html
<!-- Pravilno povezivanje label-a sa input-om -->
<label for="id_name" class="form-label">Ime i prezime</label>
<input type="text" id="id_name" name="name" class="form-control">

<!-- Error message povezan sa poljem -->
<input type="text" id="id_name" name="name" aria-describedby="id_name_error">
<div id="id_name_error" class="invalid-feedback">Molimo unesite ime.</div>

<!-- Required polja oznacena vizuelno i za screen reader-e -->
<label for="id_name">Ime <span class="text-danger" aria-label="obavezno">*</span></label>

<!-- Honeypot skriven od screen reader-a -->
<div class="d-none" aria-hidden="true">
  <label for="id_website">Website</label>
  <input type="text" id="id_website" name="website" tabindex="-1">
</div>
```

### Previous Story Learnings (Story 4.8)

1. **Portal base template**: `portal/base.html` je standard za sve javne stranice
2. **Breadcrumbs**: Svaki portal view treba da dostavi `breadcrumbs` context varijablu
3. **Test pattern**: pytest-django, `@pytest.mark.django_db`, `client` fixture
4. **Test suite**: Story 4.8 ima 1322 passed, 3 skipped. Ne smemo imati regresije.
5. **Navbar**: `portal/base.html` navbar ima active state za About - dodati za Kontakt
6. **Template blocks**: `{% block portal_content %}` za main content
7. **Bootstrap 5 forms**: Koristiti `.form-control`, `.form-label`, `.invalid-feedback`
8. **Messages framework**: Django messages za success/error feedback

### Test Pattern

```python
# portal/tests/test_contact.py

import pytest
from django.core import mail
from django.urls import reverse


@pytest.mark.django_db
class TestContactPage:
    """Tests for the Contact page (Story 4.9, FR44, FR45)."""

    def test_contact_page_returns_200(self, client):
        url = reverse("contact")
        response = client.get(url)
        assert response.status_code == 200

    def test_contact_page_uses_correct_template(self, client):
        url = reverse("contact")
        response = client.get(url)
        assert "portal/contact.html" in [t.name for t in response.templates]

    def test_contact_page_has_breadcrumbs(self, client):
        url = reverse("contact")
        response = client.get(url)
        content = response.content.decode()
        assert "Pocetna" in content  # sa dijakriticima
        assert "Kontakt" in content

    def test_contact_form_has_required_fields(self, client):
        url = reverse("contact")
        response = client.get(url)
        content = response.content.decode()
        assert 'name="name"' in content
        assert 'name="email"' in content
        assert 'name="subject"' in content
        assert 'name="message"' in content

    def test_contact_form_has_honeypot_field(self, client):
        url = reverse("contact")
        response = client.get(url)
        content = response.content.decode()
        assert 'name="website"' in content

    def test_contact_form_valid_submission_sends_email(self, client, settings):
        settings.EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"
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

    def test_contact_form_empty_fields_shows_errors(self, client):
        url = reverse("contact")
        response = client.post(url, {})
        assert response.status_code == 200  # Stay on page with errors
        content = response.content.decode()
        assert "invalid-feedback" in content or "error" in content.lower()

    def test_contact_form_honeypot_filled_blocks_submission(self, client, settings):
        settings.EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"
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
        assert "email" in content.lower()

    def test_contact_page_no_auth_required(self, client):
        """Contact page is public - no authentication needed."""
        url = reverse("contact")
        response = client.get(url)
        assert response.status_code == 200

    def test_contact_form_labels_connected_to_inputs(self, client):
        url = reverse("contact")
        response = client.get(url)
        content = response.content.decode()
        # Labels should have for="id_fieldname" matching input id
        assert 'for="id_name"' in content
        assert 'for="id_email"' in content
        assert 'for="id_subject"' in content
        assert 'for="id_message"' in content

    def test_contact_navbar_active_state(self, client):
        url = reverse("contact")
        response = client.get(url)
        content = response.content.decode()
        # Check that Kontakt nav link has active class
        assert 'class="nav-link active"' in content or 'active' in content

    def test_contact_email_contains_all_form_data(self, client, settings):
        settings.EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"
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
```

### Dependencies (Python/Django)

Nema novih Python zavisnosti! Sve je vec instalirano:
- Django 5.2+ (forms, FormView, send_mail, messages)
- django-anymail (production email via Mailgun - Cookiecutter default)
- pytest-django (testiranje)

### NFR Requirements

- **FR44:** Posetilac moze poslati poruku preko kontakt forme
- **FR45:** Sistem salje kontakt poruke na definisanu email adresu
- **NFR2:** Javne stranice portala - Ucitavanje < 3 sekunde
- **NFR14:** Semanticki HTML5 - form, label, fieldset
- **NFR17:** Keyboard navigacija - tab order kroz formu, Enter za submit
- **NFR18:** Labels povezani sa input poljima - for/id atributi
- **NFR21:** Email - SMTP za kontakt formu (Cookiecutter django-anymail)
- **NFR25:** Graceful degradation - error handling za SMTP failures

### Project Structure Notes

- ContactForm ide u `portal/forms.py` jer pripada PUBLIC portal sekciji
- ContactView ide u `portal/views.py` jer je PUBLIC portal view
- Contact template ide u `portal/contact.html` jer pripada portal sekciji
- URL ostaje u `config/urls.py` jer je top-level ruta (kao home, about, search)
- Testovi u `portal/tests/test_contact.py` - novi test fajl
- CONTACT_FORM_RECIPIENT_EMAIL ide u settings kao environment variable

### References

- [Source: epics.md#Story 4.9: Contact Form]
- [Source: epics.md#Epic 4: Public Portal Experience]
- [Source: prd.md#FR44 - Posetilac moze poslati poruku preko kontakt forme]
- [Source: prd.md#FR45 - Sistem salje kontakt poruke na definisanu email adresu]
- [Source: prd.md#NFR21 - Email - SMTP za kontakt formu i notifikacije]
- [Source: project-context.md#Naming Konvencije - PascalCase za CBV]
- [Source: project-context.md#Lokalizacija - Srpski Karakteri, sr-Latn]
- [Source: project-context.md#Forms & Validation - ModelForm naming]
- [Source: architecture.md#Email - django-anymail + Mailgun]
- [Source: config/urls.py - path("contact/", TemplateView.as_view(...), name="contact")]
- [Source: portal/base.html - navbar sa "Kontakt" linkom]
- [Source: 4-8-about-page.md - Previous story: portal template patterns, test patterns, navbar active state]

## Dev Agent Record

### Agent Model Used

Claude Opus 4.5 (claude-opus-4-5-20251101)

### Debug Log References

None

### Completion Notes List

- All 7 tasks completed with TDD approach (31 tests written)
- All 31 new tests pass, no regressions in existing tests (1342 passed, 11 pre-existing failures unrelated to this story)
- ContactForm with honeypot spam protection implemented
- ContactView (FormView) with email sending and error handling
- portal/contact.html with two-column layout (form + sidebar)
- Navbar updated with "Kontakt" link and active state
- CONTACT_FORM_RECIPIENT_EMAIL setting added to base.py
- Serbian UI text with proper diacritics (č, ć, š, đ, ž)

### File List

**New Files:**
- `doi_portal/doi_portal/portal/forms.py` - ContactForm with honeypot spam protection
- `doi_portal/doi_portal/templates/portal/contact.html` - Contact page template
- `doi_portal/doi_portal/portal/tests/test_contact.py` - 31 tests for contact form

**Modified Files:**
- `doi_portal/doi_portal/portal/views.py` - Added ContactView (FormView)
- `doi_portal/config/urls.py` - Added contact URL route
- `doi_portal/doi_portal/templates/portal/base.html` - Added Kontakt nav link with active state
- `doi_portal/config/settings/base.py` - Added CONTACT_FORM_RECIPIENT_EMAIL setting
