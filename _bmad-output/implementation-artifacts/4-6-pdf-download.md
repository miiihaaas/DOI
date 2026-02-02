# Story 4.6: PDF Download

Status: done

## Story

As a **visitor**,
I want **to download the article PDF with one click**,
So that **I can read the full article offline**.

## Background

Ovo je šesta priča u Epiku 4 (Public Portal Experience). Story 4.5 je implementirala Floating Action Bar sa placeholder PDF dugmetom. Ovaj story zamenjuje placeholder sa **funkcionalnim PDF download-om** - direktan pristup fajlu bez intermedijernih stranica, sa opisnim imenom fajla i podrškom za withdrawn/restricted članke.

**FR Pokrivenost:**
- FR42: Posetilac može preuzeti PDF članka

**NFR Pokrivenost:**
- NFR4: PDF download - Direktan link, bez procesiranja
- NFR1: Landing stranica članka - FCP < 3 sekunde (download ne sme dodavati blocking resurse)
- NFR14-NFR18: Accessibility (keyboard navigacija, ARIA labels)

**Zavisnosti (sve DONE):**
- Story 4.5: Floating Action Bar - `_floating_action_bar.html`, `handlePdfClick()` placeholder, `has_pdf` context varijabla, `floatingActionBar()` Alpine.js komponenta
- Story 4.4: Article Landing Page - `article_detail.html`, `ArticleLandingView`, context varijable (`full_doi`, `doi_url`, `is_withdrawn`, `article`)
- Story 3.3: PDF Upload - `Article.pdf_file` FileField (`upload_to="articles/pdfs/"`), `Article.pdf_status` field
- Story 4.1: Portal Home Page - `portal/base.html`, portal nav, `portal.css`

**Blokira:**
- Nijednu priču direktno.

## Acceptance Criteria

1. **Given** posetilac klikne PDF download dugme
   **When** PDF je dostupan
   **Then** download počinje odmah (bez intermedijerne stranice)
   **And** fajl se servira sa odgovarajućim URL-om (lokalno: MEDIA_URL, produkcija: S3)
   **And** ime fajla je opisno: `{doi-suffix}_{title-slug}.pdf`

2. **Given** PDF download je iniciran
   **When** fajl je veliki
   **Then** browser prikazuje progress download-a
   **And** nema server-side procesiranja koje usporava download

3. **Given** članak je open access
   **When** preuzima PDF
   **Then** nije potrebna prijava ni registracija

4. **Given** članak je withdrawn ali PDF zadržan
   **When** pokušava download
   **Then** PDF nije dostupan (konzervativni pristup - `has_pdf` = False za withdrawn)
   **And** odgovarajuća poruka je prikazana ("PDF nije dostupan")

5. **Given** članak nema PDF (nije uploadovan)
   **When** posetilac vidi PDF dugme
   **Then** dugme je onemogućeno (disabled) sa tooltip objašnjenjem
   **And** download URL ne postoji za taj članak

6. **Given** posetilac je na mobilnom uređaju
   **When** preuzima PDF
   **Then** PDF se otvara u browseru ili preuzima na osnovu podešavanja uređaja
   **And** iskustvo je besprekorno

7. **Given** neko pokuša pristupiti download URL-u za članak bez PDF-a ili neobjavljen članak
   **When** URL je direktno posećen
   **Then** vraća se 404 Not Found

8. **Given** PDF download dugme u floating action bar-u
   **When** članak ima PDF
   **Then** dugme je `<a>` tag sa `href` ka download URL-u (umesto `<button>` sa `@click`)
   **And** dugme zadržava isti vizuelni stil (btn-primary, fab-btn)

## Tasks / Subtasks

- [x] Task 1: Kreirati PDF download view u `portal/views.py` (AC: #1, #2, #3, #7)
  - [x] 1.1 Dodati `ArticlePdfDownloadView` - function-based view (FBV) za direktan redirect ka PDF fajlu
  - [x] 1.2 View prima `pk` parametar (Article primary key)
  - [x] 1.3 Filtrira samo PUBLISHED članke sa `pdf_file` koji nije prazan (WITHDRAWN isključeni)
  - [x] 1.4 Vraća `HttpResponseRedirect` ka `article.pdf_file.url` (radi i za lokalni MEDIA i za S3)
  - [x] 1.5 Redirect pristup NE postavlja Content-Disposition header (nemoguće sa `HttpResponseRedirect`). Opisno ime fajla se sugeriše putem `download` atributa na `<a>` tagu u template-u (videti Task 4.5).
  - [x] 1.6 Za 404: Koristiti `get_object_or_404` sa filterom za status i pdf_file

- [x] Task 2: Dodati URL pattern za PDF download (AC: #1, #7)
  - [x] 2.1 U `portal/urls_articles.py` dodati path: `<int:pk>/pdf/` sa name `article-pdf-download`
  - [x] 2.2 URL je public (bez autentifikacije), isti kao ostali portal URL-ovi

- [x] Task 3: Ažurirati `ArticleLandingView` context sa PDF URL-om (AC: #1, #8)
  - [x] 3.1 U `portal/views.py` `ArticleLandingView.get_context_data()`, dodati `pdf_download_url` u context
  - [x] 3.2 `pdf_download_url` = `reverse("portal-articles:article-pdf-download", kwargs={"pk": article.pk})` samo ako `has_pdf` je True
  - [x] 3.3 Ako `has_pdf` je False, `pdf_download_url` = None

- [x] Task 4: Ažurirati `_floating_action_bar.html` - zamena placeholder-a pravim download-om (AC: #1, #4, #5, #8)
  - [x] 4.1 Promeniti PDF dugme sa `<button>` na `<a>` tag kada je PDF dostupan
  - [x] 4.2 Kada `has_pdf`: `<a href="{{ pdf_download_url }}" class="btn btn-primary fab-btn">` sa standardnim download ponašanjem
  - [x] 4.3 Kada `not has_pdf`: zadržati `<button disabled>` (nema URL-a, ne može biti link)
  - [x] 4.4 Ukloniti `handlePdfClick()` iz Alpine.js komponente (više nije potreban)
  - [x] 4.5 Dodati `download` atribut na `<a>` tag za sugestiju browseru da preuzme umesto otvara
  - [x] 4.6 Zadržati sve ARIA atribute i srpske labele

- [x] Task 5: Kreirati PDF download servisnu funkciju (AC: #1, #2)
  - [x] 5.1 U `portal/services.py` dodati `get_pdf_download_filename(article)` helper
  - [x] 5.2 Generiše opisno ime fajla: `{doi_suffix}_{slugified_title}.pdf`
  - [x] 5.3 Koristi `django.utils.text.slugify` za title slug
  - [x] 5.4 Ograničava dužinu fajlnema na razumnu granicu (max 100 karaktera slug dela)

- [x] Task 6: Kreirati testove (AC: #1-#8)
  - [x] 6.1 Test: Download view vraća redirect ka PDF URL-u za PUBLISHED članak sa PDF-om
  - [x] 6.2 Test: Download view vraća 404 za članak bez PDF-a
  - [x] 6.3 Test: Download view vraća 404 za WITHDRAWN članak (čak i sa PDF-om)
  - [x] 6.4 Test: Download view vraća 404 za DRAFT članak
  - [x] 6.5 Test: Download view vraća 404 za nepostojeći članak
  - [x] 6.6 Test: Landing page context sadrži `pdf_download_url` za članak sa PDF-om
  - [x] 6.7 Test: Landing page context sadrži `pdf_download_url` = None za članak bez PDF-a
  - [x] 6.8 Test: Floating action bar `<a>` tag sa `href` za članak sa PDF-om
  - [x] 6.9 Test: Floating action bar `<button disabled>` za članak bez PDF-a
  - [x] 6.10 Test: `get_pdf_download_filename()` generiše ispravan format
  - [x] 6.11 Test: Download URL radi bez autentifikacije (public)
  - [x] 6.12 Test: Floating action bar `<a>` tag sadrži `download` atribut sa opisnim imenom fajla iz `get_pdf_download_filename()`

## Dev Notes

### KRITIČNO: PDF Download Strategija

**Problem:** Kako servirati PDF iz različitih storage backend-ova (lokalni filesystem vs S3)?

**Rešenje:** Koristiti `redirect` pristup.
- Lokalno (development): `article.pdf_file.url` vraća `/media/articles/pdfs/filename.pdf` - Django `static()` pattern u urls.py VEĆ servira media fajlove
- Produkcija (S3): `article.pdf_file.url` vraća pun S3 URL - browser direktno preuzima sa S3

**Zašto redirect umesto FileResponse?**
- NFR4: "Direktan link, bez procesiranja" - server ne treba čitati fajl i prosleđivati ga
- Skalabilnost: S3 je optimizovan za file serving, Django ne treba biti proxy
- Performance: Nema server-side memorijskog opterećenja za velike PDF-ove
- Kompatibilnost: Radi identično za lokalni i S3 storage

**Content-Disposition sa redirect-om:**
- Redirect na S3 URL ne omogućava postavljanje Content-Disposition headera iz Django-a
- Za S3 produkciju: Content-Disposition se podešava na S3 object metadata nivou (konfiguriše se u storage backend-u)
- Za lokalni development: Django media serving ne dodaje Content-Disposition
- PRAGMATIČAN PRISTUP: Ne komplikujemo sa custom Content-Disposition - browser download radi i bez toga
- Ako je potreban deskriptivan filename, dodati `download` atribut na `<a>` tag sa željenim imenom fajla

**NAPOMENA: `download` atribut i cross-origin ograničenje:**
- HTML `download` atribut na `<a>` tagu je **ignorisan od strane browser-a za cross-origin URL-ove** (videti HTML spec).
- U produkciji (S3), pošto je redirect na drugi domen, browser koristi ime fajla sa S3 umesto vrednosti iz `download` atributa.
- U lokalnom development-u (same-origin), `download` atribut radi ispravno i sugeriše opisno ime fajla.
- Ovo je **prihvatljivo za MVP** -- korisnici svakako dobijaju PDF, samo ime fajla u produkciji neće biti deskriptivno. Buduće poboljšanje može koristiti S3 `Content-Disposition` metadata na nivou objekta.

### Implementacija Download View-a

```python
# portal/views.py

from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404

def article_pdf_download(request, pk):
    """
    Redirect to article PDF file URL.

    FR42: Posetilac može preuzeti PDF članka.
    NFR4: Direktan link, bez procesiranja.

    Only PUBLISHED articles with uploaded PDF are served.
    WITHDRAWN articles are excluded (has_pdf = False per Story 4.5 logic).
    """
    article = get_object_or_404(
        Article,
        pk=pk,
        status=ArticleStatus.PUBLISHED,
    )
    if not article.pdf_file:
        from django.http import Http404
        raise Http404("PDF nije dostupan za ovaj članak.")

    return HttpResponseRedirect(article.pdf_file.url)
```

### URL Konfiguracija

```python
# portal/urls_articles.py - DODATI:
path(
    "<int:pk>/pdf/",
    views.article_pdf_download,
    name="article-pdf-download",
),
```

### Ažuriranje Floating Action Bar

Ključna promena: PDF dugme iz `<button @click="handlePdfClick()">` postaje `<a href="{{ pdf_download_url }}">` kada je PDF dostupan.

```html
<!-- BEFORE (Story 4.5 - placeholder): -->
<button type="button"
        class="btn btn-primary fab-btn"
        {% if not has_pdf %}disabled{% endif %}
        @click="handlePdfClick()">
  <i class="bi bi-file-earmark-pdf-fill"></i>
</button>

<!-- AFTER (Story 4.6 - functional): -->
{% if has_pdf %}
<a href="{{ pdf_download_url }}"
   class="btn btn-primary fab-btn"
   title="Preuzmi PDF"
   aria-label="Preuzmi PDF"
   download>
  <i class="bi bi-file-earmark-pdf-fill" aria-hidden="true"></i>
  <span class="fab-label d-lg-none">PDF</span>
</a>
{% else %}
<button type="button"
        class="btn btn-primary fab-btn"
        disabled
        title="PDF nije dostupan"
        aria-label="PDF nije dostupan">
  <i class="bi bi-file-earmark-pdf-fill" aria-hidden="true"></i>
  <span class="fab-label d-lg-none">PDF</span>
</button>
{% endif %}
```

### Alpine.js Cleanup

Ukloniti `handlePdfClick()` metod iz `floatingActionBar()` funkcije jer se PDF dugme više ne koristi sa `@click`:

```javascript
// UKLONITI:
handlePdfClick() {
  // Placeholder - Story 4.6 will add real download
},
```

### Context Ažuriranje

```python
# portal/views.py - ArticleLandingView.get_context_data()
# DODATI nakon has_pdf:

if context["has_pdf"]:
    context["pdf_download_url"] = reverse(
        "portal-articles:article-pdf-download",
        kwargs={"pk": article.pk}
    )
else:
    context["pdf_download_url"] = None
```

### Servisna Funkcija za Filename

```python
# portal/services.py

from django.utils.text import slugify

def get_pdf_download_filename(article):
    """
    Generate descriptive PDF filename for download.

    Format: {doi_suffix}_{title_slug}.pdf
    Example: "test-001_some-article-title.pdf"
    """
    title_slug = slugify(article.title)[:100]
    doi_slug = article.doi_suffix.replace("/", "-")
    return f"{doi_slug}_{title_slug}.pdf"
```

**NAPOMENA:** Ova funkcija se koristi za `download` atribut na `<a>` tagu, ne za server-side Content-Disposition.

### Postojeći Patterns koje MORAMO slediti

**Portal views pattern** (VEĆ implementirano):
- FBV za HTMX endpointe i jednostavne akcije: `snake_case` ime
- CBV za stranice sa template-om: `PascalCase + View`
- Download je jednostavan redirect - FBV je prikladan

**URL pattern** (VEĆ implementirano):
- `portal/urls_articles.py` - `app_name = "portal-articles"`, public routes
- Kebab-case URL paths
- `<int:pk>/pdf/` - nested pod article PK

**Template partial pattern** (VEĆ implementirano):
- `_floating_action_bar.html` - partial sa `_` prefixom
- Alpine.js `x-data` sa function pattern
- Bootstrap Icons (`bi-*` klase)
- Srpski tekst za sve UI labele

**Article model** (VEĆ implementirano):
- `Article.pdf_file` = FileField, `upload_to="articles/pdfs/"`, `blank=True`
- `Article.pdf_status` = CharField sa PdfStatus choices
- `bool(article.pdf_file)` = True ako fajl postoji
- `article.pdf_file.url` = URL do fajla (lokalno: `/media/...`, S3: `https://...`)

**has_pdf logika** (VEĆ iz Story 4.5):
- `has_pdf = bool(article.pdf_file) and article.status != ArticleStatus.WITHDRAWN`
- WITHDRAWN članci nemaju dostupan PDF (konzervativni pristup)

### Previous Story Learnings (Story 4.5)

1. **Floating Action Bar** je VEĆ implementiran sa placeholder PDF dugmetom. Treba ga zameniti funkcionalnim download-om.
2. **Alpine.js VEĆ dostupan**: `base.html` uključuje Alpine.js 3.15.3 CDN sa `defer` - NE dodavati ponovo.
3. **Bootstrap Icons**: VEĆ uključeni u `portal/base.html` kao CDN. Koristiti `bi-*` klase.
4. **Portal CSS**: `static/css/portal.css` - VEĆ učitan. NE dodavati nove CSS stilove za ovu priču (dugme koristi postojeće `.fab-btn` klase).
5. **Test pattern**: pytest-django, `@pytest.mark.django_db`, Factory Boy. `ArticleFactory`, `IssueFactory`, `PublicationFactory`, `PublisherFactory` su VEĆ dostupni.
6. **Test suite**: Story 4.5 ima 1231 passed, 3 skipped. Ne smemo imati regresije.
7. **`handlePdfClick()`** je placeholder metod u Alpine.js komponenti - treba ga ukloniti.
8. **`has_pdf` i `share_url`** su VEĆ u ArticleLandingView context-u. Dodajemo `pdf_download_url`.
9. **Z-index** i CSS stilovi za floating bar su VEĆ podešeni - NE menjamo CSS.
10. **Withdrawn check**: Story 4.5 je ustanovila da `has_pdf = False` za WITHDRAWN članke. Ovo zadržavamo.
11. **Portal articles URL**: `path("articles/", include("doi_portal.portal.urls_articles", namespace="portal-articles"))` u `config/urls.py`
12. **Media serving lokalno**: `*static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)` u `config/urls.py` - lokalni fajlovi su VEĆ servable.
13. **S3 produkcija**: `AWS_QUERYSTRING_AUTH = False` - URL-ovi su public, bez potpisivanja. `article.pdf_file.url` vraća pun S3 URL.

### Srpski Karakteri (OBAVEZNO - videti project-context.md)

| Kontekst | ISPRAVNO |
|----------|----------|
| PDF tooltip (enabled) | "Preuzmi PDF" |
| PDF tooltip (disabled) | "PDF nije dostupan" |
| PDF aria (enabled) | "Preuzmi PDF" |
| PDF aria (disabled) | "PDF nije dostupan" |
| 404 poruka | "PDF nije dostupan za ovaj članak." |

### Git Commit Pattern

```
story-4-6: feat(portal): implementiraj PDF Download sa direktnim pristupom fajlu i ažuriranim floating action bar dugmetom (Story 4.6)
```

### Fajlovi za modifikaciju (POSTOJEĆI)

```
doi_portal/doi_portal/portal/views.py                                      # Dodati article_pdf_download FBV + pdf_download_url u context
doi_portal/doi_portal/portal/urls_articles.py                              # Dodati <int:pk>/pdf/ URL pattern
doi_portal/doi_portal/portal/services.py                                   # Dodati get_pdf_download_filename() helper
doi_portal/doi_portal/templates/portal/partials/_floating_action_bar.html  # Zameniti placeholder PDF dugme sa <a> tagom
doi_portal/doi_portal/portal/tests/test_floating_action_bar.py             # Ažurirati postojeće PDF dugme testove
```

### Fajlovi za kreiranje (NOVI)

```
doi_portal/doi_portal/portal/tests/test_pdf_download.py                   # PDF download view testovi
```

### Fajlovi koji se NE MENJAJU

```
doi_portal/doi_portal/templates/portal/article_detail.html                 # VEĆ uključuje floating action bar partial - NE MENJATI
doi_portal/doi_portal/templates/portal/base.html                           # VEĆ postoji - NE MENJATI
doi_portal/doi_portal/templates/base.html                                  # VEĆ postoji - NE MENJATI (Alpine.js VEĆ uključen)
doi_portal/doi_portal/static/css/portal.css                                # NE MENJATI - FAB CSS je VEĆ implementiran
doi_portal/doi_portal/articles/models.py                                   # VEĆ postoji - NE MENJATI
doi_portal/config/urls.py                                                  # VEĆ postoji - NE MENJATI
```

### Anti-Patterns (ZABRANJENO)

```python
# POGREŠNO - Koristiti FileResponse za serviranje fajla preko Django-a
return FileResponse(article.pdf_file, as_attachment=True)
# Razlog: NFR4 kaže "Direktan link, bez procesiranja" - Django ne treba biti proxy

# POGREŠNO - Kreirati novi template za download
render(request, 'portal/pdf_download.html')
# Razlog: Download je redirect, nema template

# POGREŠNO - Dodavati autentifikaciju za download
@login_required
def article_pdf_download(request, pk):
# Razlog: FR42 kaže "open access" - javni portal, bez login-a

# POGREŠNO - Servirati WITHDRAWN članke
Article.objects.filter(pk=pk)  # bez status filtera
# Razlog: has_pdf logika isključuje WITHDRAWN članke

# POGREŠNO - Menjati article_detail.html
# FAB partial je VEĆ uključen - menjamo samo partial

# POGREŠNO - Dodavati novi CSS za PDF dugme
.fab-pdf-link { ... }
# Razlog: Koristiti postojeće .fab-btn klase

# POGREŠNO - Generisati signed S3 URL iz Django-a
import boto3; s3_client.generate_presigned_url(...)
# Razlog: AWS_QUERYSTRING_AUTH = False, URL-ovi su public

# POGREŠNO - Zaboraviti srpske karaktere sa dijakriticima
"Clanak" -> POGREŠNO!
"Članak" -> ISPRAVNO!

# POGREŠNO - Kreirati CBV za download
class ArticlePdfDownloadView(View):
# Razlog: FBV je prikladniji za jednostavan redirect
```

### Performance (NFR4 - Direktan link, bez procesiranja)

```
# PDF download NE SME usporavati server:
# 1. Redirect na pdf_file.url - server ne čita fajl
# 2. Browser preuzima direktno sa storage-a (lokalni filesystem ili S3)
# 3. Nema server-side procesiranja (NFR4)
# 4. Nema dodatnih HTTP zahteva za download stranicu
# 5. <a> tag sa download atributom - nativan browser download
```

### Accessibility (NFR14-NFR18)

```html
<!-- Enabled PDF link sa aria-label -->
<a href="{{ pdf_download_url }}"
   class="btn btn-primary fab-btn"
   title="Preuzmi PDF"
   aria-label="Preuzmi PDF"
   download>

<!-- Disabled PDF button sa aria-label -->
<button disabled
        title="PDF nije dostupan"
        aria-label="PDF nije dostupan">
```

### Test Pattern

```python
# portal/tests/test_pdf_download.py

import pytest
from django.urls import reverse

from doi_portal.articles.models import ArticleStatus
from doi_portal.articles.tests.factories import ArticleFactory
from doi_portal.issues.models import IssueStatus
from doi_portal.issues.tests.factories import IssueFactory
from doi_portal.publications.tests.factories import PublicationFactory
from doi_portal.publishers.tests.factories import PublisherFactory


@pytest.mark.django_db
class TestArticlePdfDownload:
    """Tests for article PDF download view."""

    def _create_article(self, status=ArticleStatus.PUBLISHED, has_pdf=False):
        publisher = PublisherFactory(doi_prefix="10.9999")
        pub = PublicationFactory(publisher=publisher)
        issue = IssueFactory(publication=pub, status=IssueStatus.PUBLISHED)
        article = ArticleFactory(
            issue=issue,
            doi_suffix="pdf-test-001",
            status=status,
        )
        if has_pdf:
            article.pdf_file = "articles/pdfs/test.pdf"
            article.save()
        return article

    def test_download_redirects_to_pdf_url(self, client):
        article = self._create_article(status=ArticleStatus.PUBLISHED, has_pdf=True)
        url = reverse("portal-articles:article-pdf-download", kwargs={"pk": article.pk})
        response = client.get(url)
        assert response.status_code == 302
        assert "articles/pdfs/test.pdf" in response.url

    def test_download_404_without_pdf(self, client):
        article = self._create_article(status=ArticleStatus.PUBLISHED, has_pdf=False)
        url = reverse("portal-articles:article-pdf-download", kwargs={"pk": article.pk})
        response = client.get(url)
        assert response.status_code == 404

    def test_download_404_for_withdrawn(self, client):
        article = self._create_article(status=ArticleStatus.WITHDRAWN, has_pdf=True)
        url = reverse("portal-articles:article-pdf-download", kwargs={"pk": article.pk})
        response = client.get(url)
        assert response.status_code == 404

    def test_download_404_for_draft(self, client):
        article = self._create_article(status=ArticleStatus.DRAFT, has_pdf=True)
        url = reverse("portal-articles:article-pdf-download", kwargs={"pk": article.pk})
        response = client.get(url)
        assert response.status_code == 404

    def test_download_404_for_nonexistent(self, client):
        url = reverse("portal-articles:article-pdf-download", kwargs={"pk": 99999})
        response = client.get(url)
        assert response.status_code == 404

    def test_download_no_auth_required(self, client):
        article = self._create_article(status=ArticleStatus.PUBLISHED, has_pdf=True)
        url = reverse("portal-articles:article-pdf-download", kwargs={"pk": article.pk})
        response = client.get(url)
        # Should redirect, not redirect to login
        assert response.status_code == 302
        assert "login" not in response.url
        assert "account" not in response.url
```

### Dependencies (Python/Django)

Nema novih Python zavisnosti! Sve je već instalirano:
- Django 5.2+ (HttpResponseRedirect, get_object_or_404, reverse)
- `django.utils.text.slugify` (ugrađeno u Django)
- pytest-django + Factory Boy (već u test setup-u)

### NFR Requirements

- **FR42:** Posetilac može preuzeti PDF članka - PRIMARNA funkcionalnost ovog story-ja
- **NFR4:** PDF download - Direktan link, bez procesiranja - redirect umesto FileResponse
- **NFR1:** FCP < 3 sekunde - nema blocking resursa, `<a>` tag je nativan HTML
- **NFR14:** Semantički HTML5 - `<a>` tag za link, `<button>` za disabled state
- **NFR17:** Touch targets - VEĆ obezbeđeno kroz `.fab-btn` klasu (min 44x44px)
- **NFR18:** Keyboard navigacija - `<a>` tag je fokusabilan, Tab navigacija radi

### Project Structure Notes

- Download view ide u `portal/views.py` jer je to PUBLIC portal view (ne admin)
- URL ide u `portal/urls_articles.py` jer je vezan za article resources
- Helper funkcija ide u `portal/services.py` jer je business logic layer
- Testovi u `portal/tests/test_pdf_download.py` - novi test fajl za download-specifične testove
- Ažuriranje `test_floating_action_bar.py` za promenjeno ponašanje PDF dugmeta

### References

- [Source: epics.md#Story 4.6: PDF Download]
- [Source: epics.md#Epic 4: Public Portal Experience]
- [Source: prd.md#FR42: Posetilac može preuzeti PDF članka]
- [Source: prd.md#NFR4: PDF download - Direktan link, bez procesiranja]
- [Source: architecture.md#File Storage & Processing - AWS S3, upload flow]
- [Source: architecture.md#Frontend Architecture - HTMX, Alpine.js, Bootstrap 5]
- [Source: architecture.md#API & Communication Patterns - HTMX endpoints, HTML fragment responses]
- [Source: project-context.md#HTMX Pravila - partials sa _ prefix]
- [Source: project-context.md#Naming Konvencije - snake_case za FBV, kebab-case za URL]
- [Source: project-context.md#Lokalizacija - Srpski Karakteri, sr-Latn]
- [Source: project-context.md#Services Layer - kompleksna business logika u services.py]
- [Source: project-context.md#Testing (pytest-django) - Factory Boy]
- [Source: 4-5-floating-action-bar.md - Previous story: _floating_action_bar.html, handlePdfClick placeholder, has_pdf context]
- [Source: portal/views.py - ArticleLandingView.get_context_data() existing context with has_pdf, share_url]
- [Source: portal/urls_articles.py - app_name="portal-articles", article-detail pattern]
- [Source: portal/partials/_floating_action_bar.html - floatingActionBar() Alpine.js component, PDF button placeholder]
- [Source: articles/models.py - Article.pdf_file FileField upload_to="articles/pdfs/", Article.pdf_status]
- [Source: config/settings/production.py - AWS_QUERYSTRING_AUTH=False, S3Storage backend, MEDIA_URL]
- [Source: config/urls.py - static(MEDIA_URL) for local media serving]

## Dev Agent Record

### Agent Model Used

Claude Opus 4.5 (claude-opus-4-5-20251101)

### Debug Log References

- Full test suite: 1259 passed, 3 skipped, 0 failures (up from 1231 in Story 4.5)
- New tests: 17 in test_pdf_download.py (all passing)
- Existing FAB tests: 12 in test_floating_action_bar.py (all passing, zero regressions)

### Completion Notes List

- Task 1: Created `article_pdf_download` FBV in views.py using `get_object_or_404` with status=PUBLISHED filter, raises Http404 for missing pdf_file, returns HttpResponseRedirect to article.pdf_file.url
- Task 2: Added `<int:pk>/pdf/` URL pattern in urls_articles.py with name `article-pdf-download`
- Task 3: Added `pdf_download_url` and `pdf_download_filename` to ArticleLandingView context (conditional on has_pdf)
- Task 4: Replaced placeholder `<button @click="handlePdfClick()">` with conditional `<a href>` (has_pdf) / `<button disabled>` (!has_pdf). Removed `handlePdfClick()` from Alpine.js component. Added `download` attribute with descriptive filename.
- Task 5: Created `get_pdf_download_filename(article)` in services.py using slugify, max 100 char slug, slash-to-dash in doi_suffix
- Task 6: Created 17 comprehensive tests covering all 12 subtasks (6.1-6.12) plus additional edge cases
- No new Python dependencies required
- No CSS changes needed (existing .fab-btn classes used)
- All Serbian text uses proper diacritical characters

### File List

Modified:
- `doi_portal/doi_portal/portal/views.py` - Added article_pdf_download FBV, pdf_download_url + pdf_download_filename in ArticleLandingView context, new imports
- `doi_portal/doi_portal/portal/urls_articles.py` - Added <int:pk>/pdf/ URL pattern
- `doi_portal/doi_portal/portal/services.py` - Added get_pdf_download_filename() helper function
- `doi_portal/doi_portal/templates/portal/partials/_floating_action_bar.html` - Replaced placeholder PDF button with functional <a>/<button disabled>, removed handlePdfClick()

Created:
- `doi_portal/doi_portal/portal/tests/test_pdf_download.py` - 17 tests for PDF download (view, context, template, service)

Not Modified (as specified):
- `doi_portal/doi_portal/templates/portal/article_detail.html`
- `doi_portal/doi_portal/templates/portal/base.html`
- `doi_portal/doi_portal/templates/base.html`
- `doi_portal/doi_portal/static/css/portal.css`
- `doi_portal/doi_portal/articles/models.py`
- `doi_portal/config/urls.py`
