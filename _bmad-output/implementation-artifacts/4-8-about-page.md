# Story 4.8: About Page

Status: done

## Story

As a **visitor (posetilac)**,
I want **to learn about the portal and its purpose on a dedicated About page**,
So that **I understand the context and credibility of the content available on the portal**.

## Background

Ovo je osma prica u Epiku 4 (Public Portal Experience). Prethodne price su implementirale kompletno javno korisnicko iskustvo: Home Page (4.1), Search (4.2), Filters (4.3), Article Landing (4.4), Floating Action Bar (4.5), PDF Download (4.6), Citation Modal (4.7). Ovaj story implementira staticku About stranicu ("O portalu") sa informacijama o misiji portala, organizaciji i kontakt podacima.

**FR Pokrivenost:**
- FR43: Posetilac moze videti stranicu "O portalu"

**NFR Pokrivenost:**
- NFR2: Javne stranice portala - Ucitavanje < 3 sekunde
- NFR14: Semanticki HTML5 elementi
- NFR15: Alt tekst za sve slike
- NFR16: Kontrast minimum 4.5:1 za tekst
- NFR17: Keyboard navigacija za kljucne akcije
- NFR25: Graceful degradation, user-friendly error poruke

**Zavisnosti (sve DONE):**
- Story 4.1: Portal Home Page - `portal/base.html`, portal nav sa "O portalu" linkom, `portal.css`, `home` URL name
- `config/urls.py` VEC ima `path("about/", TemplateView.as_view(template_name="pages/about.html"), name="about")`
- `portal/base.html` navbar VEC ima link `{% url 'about' %}` sa labelom "O portalu"
- `portal/home.html` quick links sekcija VEC ima link na "O portalu"

**Blokira:**
- Story 4.9: Contact Form (kontakt forma moze imati link sa About stranice)

## KRITICNO: Postojece Stanje

**`pages/about.html` VEC POSTOJI** ali je prazan stub:
```html
{% extends "base.html" %}
```

**PROBLEM:** Trenutno prosiruje `base.html` (admin base template) umesto `portal/base.html` (public portal template). Ovo znaci da:
1. Nema portal navigacije (header sa "Izdavaci", "Publikacije", "O portalu")
2. Nema portal footer-a
3. Nema portal CSS stilova
4. Nema breadcrumbs podrske

**URL ruta VEC postoji** u `config/urls.py`:
```python
path("about/", TemplateView.as_view(template_name="pages/about.html"), name="about")
```

**ODLUKA:** Potrebno je ili:
- (A) Promeniti TemplateView na pravi CBV koji prolazi breadcrumbs context i promeniti template da koristi `portal/base.html`, ILI
- (B) Premestiti template u `portal/about.html`, kreirati AboutView CBV sa breadcrumbs, azurirati URL

**PREPORUKA: Opcija (B)** - Kreirati `AboutView` CBV u `portal/views.py` sa template-om u `portal/about.html` i breadcrumbs. Azurirati `config/urls.py` da koristi `AboutView` umesto generickog `TemplateView`. Ostaviti stari `pages/about.html` fajl nepromenjen (nece se koristiti).

## Acceptance Criteria

1. **Given** posetilac navigira na /about/
   **When** stranica se ucita
   **Then** About stranica je prikazana sa informacijama o portalu
   **And** stranica koristi `portal/base.html` template (portal nav, footer, CSS)

2. **Given** About stranica prikazuje sadrzaj
   **When** posetilac pregleda stranicu
   **Then** misija/svrha portala je objasnjenja
   **And** informacije o organizaciji su prikazane
   **And** kontakt informacije su vidljive
   **And** linkovi ka pravilima (ako postoje) su dostupni

3. **Given** About stranica koristi public portal template
   **When** posetilac pregleda layout
   **Then** konzistentna navigacija i footer su prisutni (portal/base.html)
   **And** breadcrumbs prikazuju: Početna > O portalu

4. **Given** About stranica se ucitava
   **When** merimo performanse
   **Then** stranica se ucita za manje od 3 sekunde (NFR2)
   **And** nema blocking JS ili CSS resursa

5. **Given** posetilac koristi tastaturu ili screen reader
   **When** navigira kroz stranicu
   **Then** semanticki HTML5 elementi su korisceni (section, article, nav)
   **And** headings su pravilno hijerarhijski organizovani (h1 > h2 > h3)
   **And** kontrast je minimum 4.5:1 za tekst (NFR16)

6. **Given** posetilac je na mobilnom uredjaju
   **When** gleda About stranicu
   **Then** responsive layout se pravilno adaptira
   **And** touch targets su minimum 44px

## Tasks / Subtasks

- [x] Task 1: Kreirati `AboutView` CBV u `portal/views.py` (AC: #1, #3)
  - [x] 1.1 Dodati `AboutView(TemplateView)` klasu u `portal/views.py`
  - [x] 1.2 Template: `portal/about.html`
  - [x] 1.3 `get_context_data()` dodaje breadcrumbs: [Početna -> /home, O portalu -> None]

- [x] Task 2: Azurirati `config/urls.py` da koristi AboutView (AC: #1)
  - [x] 2.1 Zameniti `TemplateView.as_view(template_name="pages/about.html")` sa `AboutView.as_view()`
  - [x] 2.2 Dodati import: `from doi_portal.portal.views import AboutView`
  - [x] 2.3 Zadrzati isti URL pattern: `path("about/", ..., name="about")`
  - [x] 2.4 NE brisati `pages/about.html` (moze da ostane kao legacy, ne koristi se)

- [x] Task 3: Kreirati `portal/about.html` template (AC: #1, #2, #3, #5, #6)
  - [x] 3.1 Kreirati `doi_portal/doi_portal/templates/portal/about.html`
  - [x] 3.2 Extends `portal/base.html` (NE `base.html`!), uključiti `{% load static %}` ako se koriste static fajlovi
  - [x] 3.3 `{% block title %}O portalu - DOI Portal{% endblock %}`
  - [x] 3.4 `{% block meta_description %}` sa opisom portala
  - [x] 3.5 Sekcija: Misija portala - objasniti svrhu DOI portala za naucno izdavastvo
  - [x] 3.6 Sekcija: O nama / Organizacija - informacije o timu/organizaciji
  - [x] 3.7 Sekcija: Kontakt informacije - email, adresa, link ka kontakt formi
  - [x] 3.8 Sekcija: Korisni linkovi - linkovi ka publikacijama, izdavacima, (buduci) pravilima
  - [x] 3.9 Semanticki HTML5: `<section>` sa `aria-labelledby`, pravilna h1/h2 hijerarhija
  - [x] 3.10 Bootstrap 5 klase za layout (row, col, card)
  - [x] 3.11 Responsive dizajn: jednokolonski na mobilnom, dvokolonski na desktopu za sidebar sekciju
  - [x] 3.12 Bootstrap Icons za vizuelni stil (bi-info-circle, bi-building, bi-envelope, itd.)
  - [x] 3.13 Srpski tekst sa pravilnim dijakritickim znacima (c, s, z, dj, itd.)

- [x] Task 4: Dodati minimalne CSS stilove za About stranicu (AC: #5, #6)
  - [x] 4.1 U `portal.css` dodati `.about-section` i `.about-card` stilove (minimalno)
  - [x] 4.2 Koristiti postojece Bootstrap 5 klase koliko je moguce - NE preterivati sa custom CSS
  - [x] 4.3 Osigurati kontrast 4.5:1 (koristi vec definisane CSS varijable iz portal.css)

- [x] Task 5: Kreirati testove (AC: #1-#6)
  - [x] 5.1 Test: About stranica vraca 200 status na GET /about/
  - [x] 5.2 Test: About stranica koristi ispravan template (`portal/about.html`)
  - [x] 5.3 Test: About stranica sadrzi breadcrumbs sa "Početna" i "O portalu"
  - [x] 5.4 Test: About stranica sadrzi kljucne sekcije (misija, organizacija, kontakt)
  - [x] 5.5 Test: About stranica sadrzi srpski tekst
  - [x] 5.6 Test: About stranica ne zahteva autentifikaciju (public)
  - [x] 5.7 Test: About stranica sadrzi navigacione linkove ka publikacijama i izdavacima
  - [x] 5.8 Test: Navbar "O portalu" link ima active klasu kada je korisnik na /about/

## Dev Notes

### KRITICNO: Template Odluka

**About stranica MORA da koristi `portal/base.html`** jer je deo javnog portala. Trenutni stub `pages/about.html` koristi `base.html` (admin template) sto je POGRESNO. Kreiramo novi template `portal/about.html` i azuriramo URL config.

### View Pattern

```python
# portal/views.py - DODATI:
class AboutView(TemplateView):
    """
    Public About page for DOI Portal.

    Story 4.8: FR43 - Posetilac moze videti stranicu "O portalu"
    """
    template_name = "portal/about.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["breadcrumbs"] = [
            {"label": "Početna", "url": reverse("home")},
            {"label": "O portalu", "url": None},
        ]
        return context
```

### URL Azuriranje

```python
# config/urls.py - PROMENITI:
# STARO:
path("about/", TemplateView.as_view(template_name="pages/about.html"), name="about"),

# NOVO:
from doi_portal.portal.views import AboutView
path("about/", AboutView.as_view(), name="about"),
```

**VAZNO:** `TemplateView` import iz `django.views.generic` u `config/urls.py` moze da ostane jer se ne koristi nigde drugde u tom fajlu. Ili ga mozete ukloniti za cist kod.

### Navbar Active State

`portal/base.html` navbar VEC ima linkove ali NEMA active state za "O portalu" (za razliku od "Izdavaci" i "Publikacije"). Treba dodati active class logiku:

```html
<!-- TRENUTNO u portal/base.html: -->
<a class="nav-link" href="{% url 'about' %}">O portalu</a>

<!-- TREBA PROMENITI NA: -->
<a class="nav-link{% if request.resolver_match.url_name == 'about' %} active{% endif %}" href="{% url 'about' %}">O portalu</a>
```

### Template Struktura

```html
{% extends "portal/base.html" %}
{% load static %}

{% block title %}O portalu - DOI Portal{% endblock %}
{% block meta_description %}Saznajte vise o DOI Portalu za registraciju DOI identifikatora naucnih publikacija{% endblock %}

{% block portal_content %}
<div class="row">
  <!-- Main Content (2/3) -->
  <div class="col-lg-8">
    <h1 class="mb-4">O portalu</h1>

    <section aria-labelledby="mission-title" class="mb-5">
      <h2 id="mission-title">Misija portala</h2>
      <p>...</p>
    </section>

    <section aria-labelledby="about-org-title" class="mb-5">
      <h2 id="about-org-title">O nama</h2>
      <p>...</p>
    </section>

    <section aria-labelledby="services-title" class="mb-5">
      <h2 id="services-title">Nase usluge</h2>
      <p>...</p>
    </section>
  </div>

  <!-- Sidebar (1/3) -->
  <div class="col-lg-4">
    <div class="card shadow-sm mb-4">
      <div class="card-body">
        <h3 class="h5">Kontakt</h3>
        <p>Email, adresa, link ka kontakt formi</p>
      </div>
    </div>
    <div class="card shadow-sm mb-4">
      <div class="card-body">
        <h3 class="h5">Korisni linkovi</h3>
        <ul>...</ul>
      </div>
    </div>
  </div>
</div>
{% endblock %}
```

### Sadrzaj Stranice (Srpski Tekst)

Sadrzaj About stranice treba da bude na srpskom jeziku. Dev agent treba da napravi smislen placeholder sadrzaj koji odgovara DOI portalu za naucno izdavastvo u Srbiji. Kljucne teme:

1. **Misija portala** - DOI Portal za registraciju digitalnih identifikatora naucnih publikacija
2. **O nama** - Portal za podrsku naucnom izdavastvu, DOI registracija
3. **Nase usluge** - Registracija DOI identifikatora, upravljanje metapodacima, Crossref integracija
4. **Kontakt informacije** - Email, link ka buducoj kontakt formi (Story 4.9)
5. **Korisni linkovi** - Publikacije, Izdavaci, Crossref sajt

**Napomena za kontakt formu:** Story 4.9 implementira kontakt formu. Na About stranici staviti link ka `/contact/` sa napomenom da ce forma biti uskoro dostupna, ILI staviti samo email adresu. Dev agent treba da koristi `{% url 'contact' %}` samo ako ruta vec postoji - inace koristiti hardcoded link ili samo email.

### Srpski Karakteri (OBAVEZNO - videti project-context.md)

| Kontekst | ISPRAVNO |
|----------|----------|
| Page title | "O portalu" |
| Breadcrumb | "Početna", "O portalu" |
| Mission heading | "Misija portala" |
| About heading | "O nama" |
| Contact heading | "Kontakt" |
| Links heading | "Korisni linkovi" |
| Services heading | "Nase usluge" |
| Publications link | "Publikacije" |
| Publishers link | "Izdavaci" |

**KRITICNO:** Koristiti prave srpske karaktere sa dijakritickim znacima: č, š, ž, đ (Početna, Izdavači, Pretraživanje).

**NAPOMENA O DIJAKRITICIMA:** Pogledati vec implementirane template-ove za tacan nacin pisanja srpskih reci sa dijakriticima. Na primer `portal/base.html` koristi "Izdavaci" (sa c), "Publikacije", "O portalu", "Pretrazite" (sa z). Pratiti isti pattern za konzistentnost.

### Postojeci Patterns koje MORAMO slediti

**Portal views pattern** (VEC implementirano u prethodnim pricama):
- CBV za stranice sa template-om: `PascalCase + View` (npr. `PortalHomeView`, `ArticleLandingView`)
- FBV za HTMX endpointe: `snake_case` ime
- Breadcrumbs: lista dict-ova `[{"label": "...", "url": "..."}, ...]` u context-u
- `get_context_data()` za dodavanje breadcrumbs

**Template pattern** (VEC implementirano):
- Extends `portal/base.html`
- `{% block title %}` za page title
- `{% block meta_description %}` za SEO
- `{% block portal_content %}` za sadrzaj
- Bootstrap 5 klase za layout
- Bootstrap Icons za ikone
- Srpski tekst za sve UI labele
- `aria-labelledby` za section accessibility

**URL pattern** (VEC implementirano):
- `config/urls.py` za top-level rute (home, about, search, dashboard)
- `name="about"` VEC postoji - NE menjati ime rute

### Git Commit Pattern

```
story-4-8: feat(portal): implementiraj About Page sa misijom portala, organizacijom i kontakt informacijama (Story 4.8)
```

### Fajlovi za modifikaciju (POSTOJECI)

```
doi_portal/config/urls.py                                          # Zameniti TemplateView sa AboutView za /about/ rutu
doi_portal/doi_portal/portal/views.py                              # Dodati AboutView CBV sa breadcrumbs
doi_portal/doi_portal/templates/portal/base.html                   # Dodati active state za "O portalu" nav link
doi_portal/doi_portal/static/css/portal.css                        # Dodati minimalne about-page stilove (opcionalno)
```

### Fajlovi za kreiranje (NOVI)

```
doi_portal/doi_portal/templates/portal/about.html                  # About page template sa svim sekcijama
doi_portal/doi_portal/portal/tests/test_about.py                   # About page testovi
```

### Fajlovi koji se NE MENJAJU

```
doi_portal/doi_portal/templates/pages/about.html                   # Legacy stub - NE BRISATI, NE MENJATI (nece se koristiti)
doi_portal/doi_portal/templates/portal/base.html (struktura)       # NE menjati opstu strukturu - SAMO dodati active class za "O portalu" link
doi_portal/doi_portal/portal/urls.py                               # NE MENJATI (publisher rute)
doi_portal/doi_portal/portal/urls_articles.py                      # NE MENJATI (article rute)
doi_portal/doi_portal/portal/urls_publications.py                  # NE MENJATI (publication rute)
doi_portal/doi_portal/portal/services.py                           # NE MENJATI (nema business logike za About stranicu)
```

### Anti-Patterns (ZABRANJENO)

```python
# POGRESNO - Koristiti base.html umesto portal/base.html
{% extends "base.html" %}
# Razlog: About stranica je deo javnog portala, mora koristiti portal template

# POGRESNO - Dodavati autentifikaciju
@login_required
class AboutView(TemplateView):
# Razlog: Javna stranica, bez login-a (FR43)

# POGRESNO - Kreirati About stranicu kao FBV
def about_view(request):
# Razlog: CBV pattern za stranice sa template-om (project-context.md)

# POGRESNO - Hardcodovati URL-ove u template-u
<a href="/publishers/">Izdavaci</a>
# Razlog: Koristiti {% url 'portal:publisher-list' %}

# POGRESNO - Koristiti inline stilove umesto CSS klasa
<div style="background: #f0f0f0; padding: 20px;">
# Razlog: Koristiti Bootstrap klase i portal.css

# POGRESNO - Zaboraviti srpske karaktere sa dijakriticima
"Clanci" -> POGRESNO!
"Clanci" -> ISPRAVNO! (sa c)

# POGRESNO - Kreirati slozenu logiku u view-u
class AboutView(TemplateView):
    def get_context_data(self, **kwargs):
        # Ne treba nikakav database query!
        context["articles_count"] = Article.objects.count()
# Razlog: About je staticka stranica, nema potrebe za DB upitima

# POGRESNO - Menjati URL name "about"
path("about/", AboutView.as_view(), name="about-page"),
# Razlog: Postojeci linkovi koriste {% url 'about' %} - NE menjati
```

### Performance (NFR2)

```
# About stranica je staticka - izuzetno brza:
# 1. Nema database upita (osim session/auth middleware)
# 2. Nema HTMX poziva
# 3. Nema JavaScript logike
# 4. Samo HTML + Bootstrap CSS koji je vec kesirano
# 5. < 3 sekunde load time je trivijalno za staticki sadrzaj
```

### Accessibility (NFR14, NFR15, NFR16, NFR17)

```html
<!-- Pravilna hijerarhija headings-a -->
<h1>O portalu</h1>
  <h2>Misija portala</h2>
  <h2>O nama</h2>
  <h2>Nase usluge</h2>
  <h3>Kontakt</h3> <!-- u sidebar card-u -->
  <h3>Korisni linkovi</h3> <!-- u sidebar card-u -->

<!-- Section sa aria-labelledby -->
<section aria-labelledby="mission-title">
  <h2 id="mission-title">Misija portala</h2>
</section>

<!-- Bootstrap Icons sa aria-hidden -->
<i class="bi bi-info-circle" aria-hidden="true"></i>
```

### Previous Story Learnings (Story 4.7)

1. **Portal base template**: `portal/base.html` je standard za sve javne stranice - NE koristiti `base.html`
2. **Breadcrumbs**: Svaki portal view treba da dostavi `breadcrumbs` context varijablu
3. **Bootstrap 5 VEC dostupan**: CDN u `base.html`, Bootstrap Icons u `portal/base.html`
4. **Alpine.js VEC dostupan**: CDN u `base.html` sa `defer` - ali About stranica NE treba Alpine.js
5. **Portal CSS**: `static/css/portal.css` VEC ucitan u `portal/base.html`
6. **Test pattern**: pytest-django, `@pytest.mark.django_db`, `client` fixture za HTTP testove
7. **Test suite**: Story 4.7 ima 1284 passed, 3 skipped. Ne smemo imati regresije.
8. **Navbar**: `portal/base.html` navbar vec ima active state logiku za "Izdavaci" i "Publikacije" ali NE za "O portalu" - treba dodati.
9. **CSS varijable**: `portal.css` definise `--portal-primary`, `--portal-secondary`, itd. - koristiti za konzistentan stil.
10. **Template block-ovi**: `{% block portal_content %}` za main content, `{% block title %}` za title, `{% block meta_description %}` za SEO.

### Test Pattern

```python
# portal/tests/test_about.py

import pytest
from django.urls import reverse


@pytest.mark.django_db
class TestAboutPage:
    """Tests for the About page (Story 4.8, FR43)."""

    def test_about_page_returns_200(self, client):
        url = reverse("about")
        response = client.get(url)
        assert response.status_code == 200

    def test_about_page_uses_correct_template(self, client):
        url = reverse("about")
        response = client.get(url)
        assert "portal/about.html" in [t.name for t in response.templates]

    def test_about_page_has_breadcrumbs(self, client):
        url = reverse("about")
        response = client.get(url)
        content = response.content.decode()
        assert "Početna" in content  # sa dijakriticima
        assert "O portalu" in content

    def test_about_page_has_key_sections(self, client):
        url = reverse("about")
        response = client.get(url)
        content = response.content.decode()
        # Proveriti kljucne sekcije
        assert "misij" in content.lower() or "Misija" in content
        assert "kontakt" in content.lower() or "Kontakt" in content

    def test_about_page_no_auth_required(self, client):
        """About page is public - no authentication needed."""
        url = reverse("about")
        response = client.get(url)
        assert response.status_code == 200
        # Ne redirectuje na login
        assert "login" not in response.url if hasattr(response, "url") else True

    def test_about_page_has_portal_nav_links(self, client):
        url = reverse("about")
        response = client.get(url)
        content = response.content.decode()
        assert "Publikacije" in content
        assert "Izdavaci" in content  # sa c
```

### Dependencies (Python/Django)

Nema novih Python zavisnosti! Sve je vec instalirano:
- Django 5.2+ (TemplateView, reverse)
- Bootstrap 5.3+ (cards, grid, nav - CDN u base.html)
- pytest-django (testiranje)

### NFR Requirements

- **FR43:** Posetilac moze videti stranicu "O portalu"
- **NFR2:** Javne stranice portala - Ucitavanje < 3 sekunde (trivijalno za staticki sadrzaj)
- **NFR14:** Semanticki HTML5 - section, article, heading hijerarhija
- **NFR15:** Alt tekst za sve slike (ako se dodaju ikone/slike)
- **NFR16:** Kontrast minimum 4.5:1 - koristiti portal CSS varijable
- **NFR17:** Keyboard navigacija - standardni tab order, skip-to-content link (vec u base.html)
- **NFR25:** Graceful degradation - staticka stranica, nema sta da padne

### Project Structure Notes

- About view ide u `portal/views.py` jer je PUBLIC portal view
- About template ide u `portal/about.html` jer pripada portal sekciji
- URL ostaje u `config/urls.py` jer je top-level ruta (kao home i search)
- Testovi u `portal/tests/test_about.py` - novi test fajl za about-specifricne testove
- NE treba `services.py` izmena jer je About staticka stranica bez business logike

### References

- [Source: epics.md#Story 4.8: About Page]
- [Source: epics.md#Epic 4: Public Portal Experience]
- [Source: prd.md#FR43 - Posetilac moze videti stranicu "O portalu"]
- [Source: prd.md#Javni portal moduli - Pocetna, Publikacije, Izdavaci, O portalu, Kontakt]
- [Source: project-context.md#Naming Konvencije - PascalCase za CBV, kebab-case za URL]
- [Source: project-context.md#Lokalizacija - Srpski Karakteri, sr-Latn]
- [Source: project-context.md#Template Struktura - portal/ direktorijum]
- [Source: config/urls.py - path("about/", TemplateView.as_view(...), name="about")]
- [Source: portal/base.html - navbar sa "O portalu" linkom, breadcrumbs blok]
- [Source: portal/home.html - quick links sekcija sa "O portalu" linkom]
- [Source: pages/about.html - prazan stub koji extends base.html (POGRESNO)]
- [Source: 4-7-citation-modal.md - Previous story: portal template patterns, test patterns]

## Dev Agent Record

### Agent Model Used

Claude Opus 4.5 (claude-opus-4-5-20251101)

### Debug Log References

None - implementation proceeded without issues.

### Completion Notes List

1. **Task 1 Complete**: Created `AboutView` CBV in `portal/views.py` extending `TemplateView` with `template_name="portal/about.html"` and `get_context_data()` providing breadcrumbs context.

2. **Task 2 Complete**: Updated `config/urls.py` to use `AboutView.as_view()` instead of generic `TemplateView`. Added import for `AboutView`. URL pattern `name="about"` preserved. Legacy `pages/about.html` left unchanged.

3. **Task 3 Complete**: Created full `portal/about.html` template with:
   - Extends `portal/base.html` (correct portal template)
   - Proper `{% block title %}` and `{% block meta_description %}`
   - Four main sections: Misija portala, O nama, Naše usluge
   - Sidebar with Kontakt card, Korisni linkovi card, and DOI info card
   - Semantic HTML5 with `<section aria-labelledby="...">` elements
   - Proper heading hierarchy (h1 > h2 > h3)
   - Bootstrap 5 grid (col-lg-8 / col-lg-4) for responsive two-column layout
   - Bootstrap Icons throughout
   - Serbian text with proper diacritics (č, š, ž, ć, đ)

4. **Task 4 Complete**: No custom CSS needed - used existing Bootstrap 5 classes and portal.css variables. The existing `.card`, `.shadow-sm`, `.mb-4` classes handle all styling. Contrast 4.5:1 ensured via portal CSS variables.

5. **Task 5 Complete**: Created 17 comprehensive tests in `test_about.py` covering:
   - 200 status response
   - Correct template usage (portal/about.html)
   - Portal base template inheritance
   - Breadcrumbs presence and context
   - Mission, organization, contact, useful links sections
   - Serbian content
   - No authentication required (public)
   - Portal navigation links
   - Navbar active state for "O portalu"
   - Semantic HTML elements (section, h1, aria-labelledby)
   - Page title

6. **Navbar Fix**: Added active state logic to "O portalu" nav link in `portal/base.html` using `{% if request.resolver_match.url_name == 'about' %} active{% endif %}`.

7. **Test Results**: All 17 new tests pass. Full test suite: 1318 passed, 3 skipped, 0 failures.

### Code Review Fixes (Adversarial Review by Claude Opus 4.5)

8. **Code Review Complete**: Adversarial review found and fixed 9 issues:
   - **[HIGH] Fixed**: Removed unused `TemplateView` import from `config/urls.py`
   - **[HIGH] Fixed**: Added test for "Naše usluge" section (`test_about_page_has_services_section`)
   - **[MEDIUM] Fixed**: Added `aria-labelledby` to sidebar sections (contact, links, DOI info)
   - **[MEDIUM] Fixed**: Changed "Pošaljite nam poruku" link to static text (Contact form not implemented yet)
   - **[MEDIUM] Fixed**: Added test for responsive Bootstrap classes (`test_about_page_responsive_classes`)
   - **[MEDIUM] Fixed**: Added test for heading hierarchy h1>h2>h3 (`test_about_page_heading_hierarchy`)
   - **[MEDIUM] Fixed**: Updated title test to check exact format "O portalu - DOI Portal"
   - **[MEDIUM] Fixed**: Added test for sidebar aria-labelledby attributes (`test_about_page_sidebar_aria_labelledby`)
   - **[LOW] Fixed**: Updated docstrings to use proper diacritics ("Početna" instead of "Pocetna")

9. **Final Test Results**: All 21 tests pass (4 new tests added). Full test suite: 1322 passed, 3 skipped, 0 failures.

### File List

**Modified files:**
- `doi_portal/config/urls.py` - Replaced TemplateView with AboutView for /about/ route
- `doi_portal/doi_portal/portal/views.py` - Added AboutView CBV with breadcrumbs
- `doi_portal/doi_portal/templates/portal/base.html` - Added active state for "O portalu" nav link

**Created files:**
- `doi_portal/doi_portal/templates/portal/about.html` - Full About page template
- `doi_portal/doi_portal/portal/tests/test_about.py` - 21 comprehensive tests (17 original + 4 added in code review)

**Unchanged files (per story requirements):**
- `doi_portal/doi_portal/templates/pages/about.html` - Legacy stub, not modified
- `doi_portal/doi_portal/static/css/portal.css` - No custom CSS needed

### Definition of Done (DoD) Checklist

| Criterion | Status | Notes |
|-----------|--------|-------|
| All Acceptance Criteria implemented | ✅ PASS | AC#1-6 fully covered |
| All tasks/subtasks marked [x] | ✅ PASS | Tasks 1-5 complete |
| Tests written and passing | ✅ PASS | 21 tests, 100% pass |
| No regressions in test suite | ✅ PASS | 1322 passed, 3 skipped |
| Code follows project-context.md standards | ✅ PASS | CBV pattern, Serbian diacritics, Bootstrap 5 |
| Security review passed | ✅ PASS | Static page, no user input, no auth required |
| Accessibility requirements met | ✅ PASS | aria-labelledby, heading hierarchy, semantic HTML |
| Code review completed | ✅ PASS | 9 issues found and fixed |

**DoD Score: 100%**
