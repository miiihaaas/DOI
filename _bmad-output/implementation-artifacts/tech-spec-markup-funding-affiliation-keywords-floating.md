---
title: 'Markup podrška, Funding info, Afilijacija proširenje, Keyword reordering, Floating action bubble'
slug: 'markup-funding-affiliation-keywords-floating'
created: '2026-03-11'
status: 'ready-for-dev'
stepsCompleted: [1, 2, 3, 4]
tech_stack: ['Python 3.13', 'Django 5.2+', 'PostgreSQL 16+', 'HTMX 2.0.8', 'Alpine.js 3.15.3', 'Bootstrap 5.3+', 'SortableJS 1.15.6', 'Jinja2']
files_to_modify: ['articles/models.py', 'articles/forms.py', 'articles/views.py', 'articles/urls.py', 'articles/admin.py', 'core/markup.py', 'core/templatetags/markup_tags.py', 'templates/articles/article_form.html', 'templates/portal/article_detail.html', 'templates/portal/partials/_article_search_card.html', 'crossref/services.py', 'crossref/templates/crossref/journal_article.xml.j2', 'crossref/templates/crossref/conference_paper.xml.j2', 'crossref/templates/crossref/book_chapter.xml.j2']
code_patterns: ['Alpine.js components', 'HTMX auto-save', 'SortableJS drag-and-drop', 'Django ModelForm + inline formsets', 'Jinja2 XML templates', 'Services layer pattern', 'Server-proxied API calls']
test_patterns: ['pytest-django', 'Factory Boy', 'parametrize for edge cases']
---

# Tech-Spec: Markup podrška, Funding info, Afilijacija proširenje, Keyword reordering, Floating action bubble

**Created:** 2026-03-11

## Overview

### Problem Statement

Tekstualna polja (naslov, podnaslov, apstrakt) ne podržavaju inline formatiranje (italic, bold, subscript, superscript) iako Crossref standard to zahteva za naučne naslove (npr. nazivi vrsta, hemijske formule). Nedostaju podaci o finansiranju projekata koji su bitni i za landing stranicu i za Crossref XML (FundRef standard). Afilijacije autora nemaju polja za mesto i državu, niti autocomplete pretragu institucija. Ključne reči nemaju mogućnost promene redosleda koji je bitan za ispis. Submit i Nazad dugmad na formi za uređivanje članaka nisu uočljiva jer se nalaze na dnu dugačke forme.

### Solution

Pet međusobno nezavisnih poboljšanja: (1) Lightweight markup parser sa dual renderingom — HTML za landing stranicu i Crossref face markup za XML, plus help sekcija sa copy-to-clipboard i preview-om. (2) Novi ArticleFunding model sa Open Funder Registry autocomplete i fr:program blokom u Crossref XML. (3) Nova polja city/country u Affiliation modelu sa ROR API autocomplete za institucije. (4) SortableJS drag-and-drop za promenu redosleda ključnih reči. (5) Floating action bubble (pill) sa spojenim Nazad + Sačuvaj dugmadima u donjem desnom uglu edit stranice.

### Scope

**In Scope:**
- Markup parser utility (markup_to_html, markup_to_crossref_xml, strip_markup) za polja: title, subtitle, original_language_title, original_language_subtitle, abstract
- Help sekcija na article edit stranici sa tabelom sintakse, specijalnim karakterima za kopiranje (copy-to-clipboard), i interaktivnim preview-om
- Affiliation model proširenje: nova polja city i country, samo za landing stranicu (ne za Crossref XML)
- ROR API autocomplete za institution_name u afilijacijama (server-proxied, cached)
- Generička Alpine.js autocomplete komponenta (reusable za ROR i Open Funder Registry)
- ArticleFunding model (funder_name, funder_doi, funder_ror_id, award_number, order) sa FK ka Article
- Open Funder Registry autocomplete za funder_name (server-proxied, cached)
- Funding sekcija na article edit formi (add/remove/reorder)
- Funding prikaz na landing stranici
- Crossref XML: face markup u title/subtitle/abstract, fr:program fundref blok, xmlns:fr namespace
- Keyword drag-and-drop reordering sa SortableJS
- Floating action bubble (btn-group pill) sa Nazad + Sačuvaj, position: fixed, donji desni ugao

**Out of Scope:**
- WYSIWYG editor za tekstualna polja
- Markup u ključnim rečima (keywords ostaju plain text)
- Location polja za afilijacije u Crossref XML (Crossref šema ne podržava)
- Funder Registry bulk import ili batch operacije
- Portal floating action bar (već implementiran, odvojen element na article_detail stranici)
- Markup u imenima autora (Crossref eksplicitno zabranjuje face markup u person_name)

## Context for Development

### Codebase Patterns

- **Alpine.js komponente:** Reaktivne forme sa `x-data`, `x-model`, `@click` event handling. Postojeće komponente u article_form.html: `keywordsInput()` (line 309), `authorList()` (line 602), `paginationToggle()` (line 267), `autosaveManager()` (line 477), `pdfUpload()` (line 579), `relativeTime()` (line 545)
- **HTMX auto-save:** `hx-trigger="change delay:2s"` na formi (line 22), `hx-target="#save-indicator"`, vraća HTML partial. Auto-save handler u `views.py:895-997` radi parcijalni update samo za polja prisutna u POST request-u
- **SortableJS:** Već uključen na stranici (CDN 1.15.6, line 460), koristi se za autor reordering. Pattern: `Sortable.create(container, {handle: '.drag-handle', onEnd: callback})` sa POST ka reorder endpoint-u koji prima JSON `{order: [pk1, pk2, ...]}`
- **HTMX inline editing:** Autori i afilijacije koriste HTMX partial views — `author_add`, `author_update`, `author_delete` vraćaju `_author_list.html` partial. Afilijacije slično — `affiliation_add`, `affiliation_delete` vraćaju isti `_author_list.html` partial
- **Django forme:** ModelForm sa Bootstrap 5 widget klasama (`form-control`, `form-select`), custom `clean()` metode, `add_error_classes()` za `is-invalid` klasu
- **Jinja2 XML template-i:** 3 template-a (journal, conference, book), custom filteri (`xml_escape`, `format_date`, `format_orcid_url`). Template-i koriste `{% if %}` za opciona polja. Autoescape uključen u Jinja2 environment
- **Services layer:** `crossref/services.py` — `CrossrefService._build_context(issue)` (line 258) gradi nested dict sa publication, issue, articles, authors, affiliations za template rendering
- **Permission checks:** FBV views koriste `_check_article_permission(user, article)` helper (line 77) koji proverava publisher scoping. CBV koriste `PublisherScopedMixin` i `PublisherScopedEditMixin`
- **CSRF:** Token injection via `htmx:configRequest` event listener (article_form.html line 468)
- **Submit sa hx-disinherit:** Submit dugme koristi `hx-disinherit="*"` (line 254) da disabluje auto-save HTMX binding pri finalnom submit-u

### Files to Reference

| File | Purpose | Key Lines |
| ---- | ------- | --------- |
| `articles/models.py` | Article (line 94), Author (line 398), Affiliation (line 480) | Dodati ArticleFunding posle line 521, proširiti Affiliation |
| `articles/forms.py` | ArticleForm (line 20), AuthorForm (line 304), AffiliationForm (line 375) | Proširiti AffiliationForm, dodati ArticleFundingForm |
| `articles/views.py` | 24 HTMX endpoint-a, autosave (line 895), affiliation views (line 700) | Dodati ROR/Funder proxy, funding CRUD, ažurirati autosave |
| `articles/urls.py` | 38 URL pattern-a, app_name="articles" | Dodati ror-search, funder-search, funding-* rute |
| `articles/admin.py` | ArticleAdmin sa soft-delete support-om | Registrovati ArticleFunding |
| `templates/articles/article_form.html` | ~647 linija, 6 Alpine komponenti, SortableJS | Markup help, funding sekcija, keyword DnD, floating bubble |
| `templates/portal/article_detail.html` | Landing stranica, 212 linija | Markup rendering, afilijacija city/country, funding sekcija |
| `templates/portal/partials/_article_search_card.html` | Search card partial | Strip markup za čist tekst |
| `crossref/services.py` | CrossrefService._build_context() (line 258) | Markup konverzija, funding context |
| `crossref/templates/crossref/journal_article.xml.j2` | 142 linije, Jinja2 | Face markup, fr:program, xmlns:fr |
| `crossref/templates/crossref/conference_paper.xml.j2` | Conference variant | Iste izmene kao journal |
| `crossref/templates/crossref/book_chapter.xml.j2` | Book variant | Iste izmene kao journal |
| `core/templatetags/menu_tags.py` | Postojeći templatetags pattern | Referenca za kreiranje markup_tags.py |

### Technical Decisions

1. **Markup sintaksa:** Lightweight markup (`_italic_`, `**bold**`, `~sub~`, `^sup^`, `„navodnici"`) — ne Markdown jer su pravila jednostavnija i specifična za naučno izdavaštvo. Navodnici su Unicode karakteri, prolaze bez konverzije
2. **Autocomplete pattern:** Generička Alpine.js komponenta `autocompleteSearch()` sa server-proxied API pozivima (izbegava CORS, omogućava caching). Ista komponenta za ROR i Funder, razlika samo u endpoint-u i field mapping-u
3. **Funding na nivou artikla:** ArticleFunding → FK ka Article (ne Issue), jer različiti članci mogu imati različite projekte
4. **City/country samo za landing:** Crossref `<institution>` nema location polja — čuvamo lokalno za prikaz
5. **ROR API v2:** `https://api.ror.org/v2/organizations?query={term}` — besplatan, bez API ključa, lokacija u `locations[0].geonames_details`
6. **Open Funder Registry:** `https://api.crossref.org/funders?query={term}` — besplatan, DOI u `uri` polju
7. **Markup u Jinja2:** Konverzija u `_build_context()` pre template renderinga, Jinja2 `| safe` filter za pre-konvertovana polja. Jinja2 autoescape se mora zaobići za markup polja
8. **Floating bubble:** Position fixed, z-index 1040 (ispod Bootstrap modala koji je 1050+), btn-group pill sa dva spojena dugmeta

## Implementation Plan

### Tasks

#### Stavka 0: Prerequisiti

- [ ] Task 0.1: Instalirati `requests` dependency
  - Action: Pokrenuti `uv add requests` u root direktorijumu projekta
  - Action: Potvrditi da je `requests` dodat u `pyproject.toml` i `uv.lock`
  - Notes: `requests` je potreban za ROR API proxy (Task 2.3) i Funder Registry proxy (Task 3.3). Trenutno NIJE u `pyproject.toml` — mora se eksplicitno dodati pre implementacije API proxy endpoint-a

- [ ] Task 0.2: Popraviti auto-save da podržava sva polja na formi (BUG FIX)
  - File: `doi_portal/doi_portal/articles/views.py`
  - Action: U `article_autosave()` view-u (~line 926), proširiti `text_fields` listu da uključi polja koja nedostaju:
    - Dodati: `"original_language_title"`, `"original_language_subtitle"`, `"original_language_title_language"` — ova polja su na formi i fire change event ali autosave ih ignoriše, što uzrokuje gubitak podataka pri page refresh-u
    - Dodati: `"external_landing_url"`, `"external_pdf_url"` — URL polja koja nedostaju u autosave handler-u
  - Action: U boolean fields sekciji autosave-a, dodati `"use_external_resource"` — boolean checkbox koji nedostaje
  - Notes: Ovo je pre-existing bug koji se mora popraviti PRE markup implementacije, jer markup konverzija se oslanja na podatke sačuvane u ovim poljima. Bez ove ispravke, korisnik unese `original_language_title`, vidi "Sačuvano", ali na refresh podatak je izgubljen

#### Stavka 1: Markup parser utility

- [ ] Task 1.1: Kreirati markup parser modul
  - File: `doi_portal/doi_portal/core/markup.py` (NOV)
  - Action: Kreirati modul sa četiri funkcije:
    - `markup_to_html(text: str) -> str` — konvertuje markup u HTML (`<em>`, `<strong>`, `<sub>`, `<sup>`). Redosled: (1) `html.escape()` za XSS prevenciju, (2) `**...**` → `<strong>...</strong>`, (3) `_..._` → `<em>...</em>`, (4) `^...^` → `<sup>...</sup>`, (5) `~...~` → `<sub>...</sub>`. Navodnici `„..."` ostaju kao Unicode
    - `markup_to_crossref_xml(text: str) -> str` — konvertuje markup u Crossref face markup (`<i>`, `<b>`, `<sub>`, `<sup>`). Redosled: (1) XML escape (`&`, `<`, `>`, `"`, `'`), (2) isti regex-i ali sa XML tagovima. Koristi se za title, subtitle, original_language_title, original_language_subtitle
    - `markup_to_jats_xml(text: str) -> str` — konvertuje markup u JATS inline markup (`<jats:italic>`, `<jats:bold>`, `<jats:sub>`, `<jats:sup>`). Koristi se ISKLJUČIVO za abstract jer se abstract renderuje unutar `<jats:abstract><jats:p>` gde Crossref face markup tagovi (`<i>`, `<b>`) NISU validni. JATS standard zahteva JATS-specifične tagove
    - `strip_markup(text: str) -> str` — uklanja delimitere, vraća čist tekst za search/meta
  - Notes:
    - Regex pattern-i: bold `\*\*([^*]+)\*\*`, italic `(?<!\w)_([^_]+)_(?!\w)` (word boundary za italic da ne hvata snake_case), sup `\^([^^]+)\^`, sub `~([^~]+)~`
    - Bold MORA ići pre italic-a u parsiranju (jer `**` sadrži `*`)
    - Neupareni delimiteri ostaju kao literal tekst (regex ne matchuje → ne menja)
    - Prazni stringovi i None ulaz — vrati prazan string
    - Nested markup (npr. `**_bold italic_**`) treba da radi korektno jer se parsira sekvencijalno

- [ ] Task 1.2: Kreirati template tagove za markup
  - File: `doi_portal/doi_portal/core/templatetags/markup_tags.py` (NOV)
  - Action: Kreirati templatetags modul:
    - `doi_portal/doi_portal/core/templatetags/__init__.py` već postoji (verifikovano) — NE treba kreirati
    - `@register.filter(name="render_markup")` — poziva `markup_to_html()`, markira rezultat kao `mark_safe()`
    - `@register.filter(name="strip_markup")` — poziva `strip_markup()`
  - Notes: Koristiti `from django.utils.safestring import mark_safe`. Filter se koristi u template-ima kao `{{ article.title|render_markup }}`

- [ ] Task 1.3: Ažurirati landing stranicu za markup rendering
  - File: `doi_portal/doi_portal/templates/portal/article_detail.html`
  - Action:
    - Dodati `{% load markup_tags %}` na vrh fajla (posle `{% extends %}`)
    - Line 26: `{{ article.title }}` → `{{ article.title|render_markup }}`
    - Line 28: `{{ article.subtitle }}` → `{{ article.subtitle|render_markup }}`
    - Line 81: `{{ article.abstract }}` → `{{ article.abstract|render_markup }}`
  - Notes: `render_markup` filter već radi `mark_safe()` interno, pa Django neće escapovati HTML

- [ ] Task 1.4: Ažurirati search card za strip markup
  - File: `doi_portal/doi_portal/templates/portal/partials/_article_search_card.html`
  - Action:
    - Dodati `{% load markup_tags %}` na vrh
    - Primeniti `|strip_markup` na title i subtitle gde se prikazuju u search rezultatima
  - Notes: Search highlighting (ako postoji) treba da radi na stripped tekstu

- [ ] Task 1.5: Ažurirati Crossref XML generisanje za face markup
  - File: `doi_portal/doi_portal/crossref/services.py`
  - Action: U metodi `_build_context()` (linija ~258), pri građenju article dict-a, konvertovati:
    - `"title": Markup(markup_to_crossref_xml(article.title))`
    - `"subtitle": Markup(markup_to_crossref_xml(article.subtitle))`
    - `"original_language_title": Markup(markup_to_crossref_xml(article.original_language_title))`
    - `"original_language_subtitle": Markup(markup_to_crossref_xml(article.original_language_subtitle))`
    - `"abstract": Markup(markup_to_jats_xml(article.abstract))` — **PAŽNJA: koristi markup_to_jats_xml, NE markup_to_crossref_xml** jer abstract ide u `<jats:abstract><jats:p>` gde su validni samo JATS tagovi (`<jats:italic>`, `<jats:bold>`, `<jats:sub>`, `<jats:sup>`)
  - Import: `from doi_portal.core.markup import markup_to_crossref_xml, markup_to_jats_xml` i `from jinja2 import Markup`
  - Notes: Wrappovanje u `jinja2.Markup()` je OBAVEZNO — signalizira Jinja2 da string je safe i da ga NE treba ponovo escapovati. Bez Markup wrapper-a, Jinja2 autoescape (koji je UKLJUČEN u CrossrefService.__init__()) će escapovati `<i>` u `&lt;i&gt;` i markup neće raditi. Dodati komentar u kodu: `# Markup() prevents Jinja2 autoescape from double-escaping face markup tags`
  - Action: U queryset-u za articles (~line 273), **dodati** `prefetch_related("authors__affiliations")` jer TRENUTNO NE POSTOJI (koristi se samo `filter(is_deleted=False)` bez prefetch-a, što uzrokuje N+1 query problem)

- [ ] Task 1.6: Ažurirati Jinja2 XML template-e i dodati defanzivne komentare
  - Files: `crossref/templates/crossref/journal_article.xml.j2`, `conference_paper.xml.j2`, `book_chapter.xml.j2`
  - Action: Nema promena u template rendering-u jer `jinja2.Markup()` wrapper u context-u (Task 1.5) sprečava autoescape. ALI:
    - Dodati Jinja2 komentare u template-e pored title/subtitle/abstract polja: `{# PAŽNJA: ova polja sadrže face markup (i/b/sub/sup) — NE dodavati xml_escape filter, Markup() wrapper u context-u upravlja escape-om #}`
    - Proveriti da `xml_escape` custom filter u services.py NE interferira — markup_to_crossref_xml() već radi XML escape pre konverzije
  - Notes: **Double-escape rizik:** Ako neko u budućnosti ukloni `Markup()` wrapper iz `_build_context()`, face markup tagovi će biti escapovani u `&lt;i&gt;` — XML će i dalje proći XSD validaciju ali tekst će izgledati pogrešno. Zato: (1) komentar u kodu, (2) komentar u template-u, (3) eksplicit test u test suite-u (videti Testing Strategy — test za double-escape)

- [ ] Task 1.7: Dodati help sekciju za markup na article edit formi
  - File: `doi_portal/doi_portal/templates/articles/article_form.html`
  - Action: Dodati collapsible help sekciju (Bootstrap collapse) posle Keywords sekcije (posle line 149), pre Pages sekcije:
    ```html
    <!-- Markup Help Section -->
    <div class="mb-3">
      <a class="text-decoration-none" data-bs-toggle="collapse" href="#markupHelp" role="button" aria-expanded="false">
        <i class="bi bi-question-circle me-1"></i>Pomoć za formatiranje teksta
      </a>
      <div class="collapse" id="markupHelp">
        <div class="card card-body mt-2" x-data="markupHelp()">
          <!-- Tabela sintakse -->
          <h6 class="mb-2">Sintaksa formatiranja</h6>
          <table class="table table-sm table-bordered mb-3">
            <thead><tr><th>Unos</th><th>Rezultat</th><th>Opis</th></tr></thead>
            <tbody>
              <tr><td><code>_tekst_</code></td><td><em>tekst</em></td><td>Italic (kurziv)</td></tr>
              <tr><td><code>**tekst**</code></td><td><strong>tekst</strong></td><td>Bold (podebljano)</td></tr>
              <tr><td><code>~tekst~</code></td><td>tekst<sub>tekst</sub></td><td>Subscript (indeks dole, npr. H₂O)</td></tr>
              <tr><td><code>^tekst^</code></td><td>tekst<sup>tekst</sup></td><td>Superscript (indeks gore, npr. x²)</td></tr>
              <tr><td><code>„tekst"</code></td><td>„tekst"</td><td>Ćirilični navodnici</td></tr>
            </tbody>
          </table>
          <!-- Specijalni karakteri za kopiranje -->
          <h6 class="mb-2">Kopiraj specijalne karaktere</h6>
          <div class="d-flex flex-wrap gap-2 mb-3">
            <!-- Za svaki karakter: dugme sa click-to-copy -->
            <template x-for="char in copyChars" :key="char.label">
              <button type="button" class="btn btn-outline-secondary btn-sm position-relative"
                      @click="copyToClipboard(char.value, char.label)"
                      :title="'Kopiraj: ' + char.label">
                <template x-if="!copyStatus[char.label]">
                  <span><code x-text="char.display"></code> <span class="small text-muted" x-text="char.label"></span></span>
                </template>
                <template x-if="copyStatus[char.label]">
                  <span class="text-success"><i class="bi bi-check"></i> Kopirano</span>
                </template>
              </button>
            </template>
          </div>
          <!-- Interaktivni preview -->
          <h6 class="mb-2">Probaj formatiranje</h6>
          <div class="row">
            <div class="col-md-6">
              <textarea class="form-control form-control-sm" rows="2" x-model="previewInput"
                        placeholder="Unesite tekst sa formatiranjem..."></textarea>
            </div>
            <div class="col-md-6">
              <div class="border rounded p-2 bg-light min-height-equal" x-html="previewOutput"></div>
            </div>
          </div>
        </div>
      </div>
    </div>
    ```
  - Action: Dodati Alpine.js komponentu `markupHelp()` u script blok:
    ```javascript
    function markupHelp() {
      return {
        copyChars: [
          { value: '„', display: '„', label: 'Otvoreni navodnik' },
          { value: '\u201c', display: '\u201c', label: 'Zatvoreni navodnik' },
          { value: '_', display: '_..._', label: 'Italic' },
          { value: '**', display: '**...**', label: 'Bold' },
          { value: '~', display: '~...~', label: 'Subscript' },
          { value: '^', display: '^...^', label: 'Superscript' },
        ],
        previewInput: '',
        get previewOutput() {
          // Client-side preview — isti regex kao backend markup_to_html
          let t = this.previewInput;
          // HTML escape
          t = t.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
          // Bold before italic
          t = t.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>');
          t = t.replace(/(?<!\w)_([^_]+)_(?!\w)/g, '<em>$1</em>');
          t = t.replace(/\^([^^]+)\^/g, '<sup>$1</sup>');
          t = t.replace(/~([^~]+)~/g, '<sub>$1</sub>');
          return t || '<span class="text-muted">Ovde će se prikazati rezultat...</span>';
        },
        copyStatus: {},
        copyToClipboard(text, charLabel) {
          navigator.clipboard.writeText(text).then(() => {
            this.copyStatus[charLabel] = true;
            setTimeout(() => { this.copyStatus[charLabel] = false; }, 1500);
          });
        }
      }
    }
    ```

#### Stavka 2: Afilijacija proširenje — city, country, ROR autocomplete

- [ ] Task 2.1: Dodati city i country polja u Affiliation model
  - File: `doi_portal/doi_portal/articles/models.py`
  - Action: U Affiliation klasi (posle `department` polja, ~line 500), dodati:
    ```python
    city = models.CharField(
        _("Grad"),
        max_length=255,
        blank=True,
    )
    country = models.CharField(
        _("Država"),
        max_length=255,
        blank=True,
    )
    ```
  - Action: NE pokretati migraciju odmah — sačekati Task 3.1 da se oba modela menjaju u jednoj migraciji (videti napomenu F9 u Notes sekciji)

- [ ] Task 2.2: Ažurirati AffiliationForm
  - File: `doi_portal/doi_portal/articles/forms.py`
  - Action: U AffiliationForm.Meta:
    - `fields` — dodati `"city"` i `"country"` posle `"department"`
    - `widgets` — dodati `"city": forms.TextInput(attrs={"class": "form-control", "placeholder": "npr. Beograd"})` i `"country": forms.TextInput(attrs={"class": "form-control", "placeholder": "npr. Srbija"})`
    - `labels` — dodati `"city": _("Grad")`, `"country": _("Država")`

- [ ] Task 2.3: Kreirati ROR API proxy endpoint
  - File: `doi_portal/doi_portal/articles/views.py`
  - Action: Dodati FBV (posle affiliation views, ~line 785):
    ```python
    @login_required
    @require_GET
    def ror_search(request):
        """Proxy search to ROR API for institution autocomplete."""
        query = request.GET.get("q", "").strip()
        if len(query) < 2:
            return JsonResponse({"items": []})

        cache_key = f"ror_search:{query.lower()}"
        cached = cache.get(cache_key)
        if cached:
            return JsonResponse(cached)

        try:
            response = requests.get(
                "https://api.ror.org/v2/organizations",
                params={"query": query},
                timeout=5,
            )
            response.raise_for_status()
            data = response.json()

            results = []
            for item in data.get("items", [])[:10]:
                # Get display name (prefer ror_display type)
                name = ""
                for n in item.get("names", []):
                    if "ror_display" in n.get("types", []):
                        name = n["value"]
                        break
                if not name:
                    name = item.get("names", [{}])[0].get("value", "")

                location = item.get("locations", [{}])[0].get("geonames_details", {})
                results.append({
                    "id": item.get("id", ""),
                    "name": name,
                    "city": location.get("name", ""),
                    "country": location.get("country_name", ""),
                })

            result = {"items": results}
            cache.set(cache_key, result, 3600)  # Cache 1 hour
            return JsonResponse(result)
        except (requests.RequestException, ValueError, KeyError):
            return JsonResponse({"items": []})
    ```
  - Import: `import requests`, `from django.core.cache import cache`, `from django.http import JsonResponse`
  - Notes:
    - Vraća JSON (ne HTML) jer Alpine.js komponenta čita response direktno. Ovo je izuzetak od HTMX-always-HTML pravila jer je ovo API proxy, ne UI endpoint
    - **Rate limiting:** Endpoint je zaštićen `@login_required` ali nema per-user throttling. Za produkciju razmotriti django-ratelimit ili Django REST framework throttling. Za sada, server-side cache (1h TTL) smanjuje broj zahteva ka eksternim API-jima za iste upite

- [ ] Task 2.4: Dodati URL za ROR search
  - File: `doi_portal/doi_portal/articles/urls.py`
  - Action: Dodati u urlpatterns (posle affiliation ruta):
    ```python
    path("api/ror-search/", views.ror_search, name="ror-search"),
    ```

- [ ] Task 2.5: Kreirati generičku Alpine.js autocomplete komponentu
  - File: `doi_portal/doi_portal/templates/articles/article_form.html`
  - Action: U script bloku, dodati reusable autocomplete komponentu:
    ```javascript
    function autocompleteSearch(endpoint, options = {}) {
      return {
        query: '',
        results: [],
        isOpen: false,
        loading: false,
        debounceTimer: null,
        minChars: options.minChars || 2,

        search() {
          clearTimeout(this.debounceTimer);
          if (this.query.length < this.minChars) {
            this.results = [];
            this.isOpen = false;
            return;
          }
          this.debounceTimer = setTimeout(async () => {
            this.loading = true;
            try {
              const resp = await fetch(`${endpoint}?q=${encodeURIComponent(this.query)}`);
              const data = await resp.json();
              this.results = data.items || [];
              this.isOpen = this.results.length > 0;
            } catch (e) {
              this.results = [];
            }
            this.loading = false;
          }, 300);
        },

        select(item) {
          this.isOpen = false;
          this.query = '';
          // Dispatch custom event with selected item
          this.$dispatch('autocomplete-selected', item);
        },

        close() {
          setTimeout(() => { this.isOpen = false; }, 200);
        }
      }
    }
    ```
  - Notes: Ova komponenta se koristi i za ROR (Task 2) i za Funder (Task 3). Event `autocomplete-selected` se hvata na parent elementu koji zna koji form fields da popuni

- [ ] Task 2.6: Ažurirati affiliation formu sa ROR autocomplete
  - File: `doi_portal/doi_portal/templates/articles/partials/_affiliation_form.html` (ili gde god se affiliation forma renderuje)
  - Action: Na `institution_name` input, dodati Alpine.js autocomplete wrapping:
    - Wrapper div sa `x-data="autocompleteSearch('{% url 'articles:ror-search' %}')"` i `@autocomplete-selected.stop="..."` handler
    - Na select: popuniti `institution_name`, `institution_ror_id`, `city`, `country` iz selektovanog item-a
    - Dropdown lista ispod input-a sa rezultatima (position: absolute, z-index)
    - Svaki rezultat prikazuje: ime institucije, grad, država
  - Notes: Proveri da li se affiliation forma renderuje inline u `_author_list.html` ili kao zaseban partial. Na osnovu deep investigation, affiliation CRUD koristi `affiliation_add` i `affiliation_form_view` endpoint-e koji vraćaju partiale

- [ ] Task 2.7: Ažurirati landing stranicu za prikaz city/country
  - File: `doi_portal/doi_portal/templates/portal/article_detail.html`
  - Action: Linija ~67-69, izmeniti prikaz afilijacija:
    ```html
    <div class="text-muted small ms-3">
      {{ affiliation.institution_name }}{% if affiliation.department %}, {{ affiliation.department }}{% endif %}{% if affiliation.city %}, {{ affiliation.city }}{% endif %}{% if affiliation.country %}, {{ affiliation.country }}{% endif %}
    </div>
    ```

#### Stavka 3: Funding info — model, forma, autocomplete, Crossref XML

- [ ] Task 3.1: Kreirati ArticleFunding model
  - File: `doi_portal/doi_portal/articles/models.py`
  - Action: Posle Affiliation klase (~line 521), dodati:
    ```python
    class ArticleFunding(models.Model):
        """Funding/grant information for an article (Crossref FundRef)."""

        article = models.ForeignKey(
            Article,
            on_delete=models.CASCADE,
            related_name="fundings",
            verbose_name=_("Članak"),
        )
        funder_name = models.CharField(
            _("Naziv finansijera"),
            max_length=500,
        )
        funder_doi = models.URLField(
            _("Funder Registry DOI"),
            blank=True,
            help_text=_("DOI iz Open Funder Registry (npr. https://doi.org/10.13039/501100004564)"),
        )
        funder_ror_id = models.URLField(
            _("Funder ROR ID"),
            blank=True,
        )
        award_number = models.CharField(
            _("Broj projekta"),
            max_length=255,
            blank=True,
        )
        order = models.PositiveIntegerField(
            _("Redosled"),
            default=0,
        )

        class Meta:
            verbose_name = _("Finansiranje")
            verbose_name_plural = _("Finansiranja")
            ordering = ["order"]

        def __str__(self):
            s = self.funder_name
            if self.award_number:
                s += f" — {self.award_number}"
            return s
    ```
  - Action: Sada pokrenuti JEDNU zajedničku migraciju za obe promene (Task 2.1 city/country + Task 3.1 ArticleFunding): `python manage.py makemigrations articles -n add_affiliation_location_and_funding_model` i `python manage.py migrate`
  - Notes: Korištenje jedne migracije za obe izmene sprečava potencijalne konflikte migracija i olakšava rollback
  - Action: Registrovati u auditlog ako se koristi:
    ```python
    from auditlog.registry import auditlog
    auditlog.register(ArticleFunding)
    ```

- [ ] Task 3.2: Kreirati ArticleFundingForm
  - File: `doi_portal/doi_portal/articles/forms.py`
  - Action: Posle AffiliationForm klase, dodati:
    ```python
    class ArticleFundingForm(forms.ModelForm):
        """Form for article funding/grant information."""

        class Meta:
            model = ArticleFunding
            fields = ["funder_name", "funder_doi", "funder_ror_id", "award_number"]
            widgets = {
                "funder_name": forms.TextInput(attrs={
                    "class": "form-control",
                    "placeholder": "Naziv finansijera",
                }),
                "funder_doi": forms.URLInput(attrs={
                    "class": "form-control",
                    "placeholder": "https://doi.org/10.13039/...",
                    "readonly": "readonly",
                }),
                "funder_ror_id": forms.URLInput(attrs={
                    "class": "form-control",
                    "placeholder": "https://ror.org/...",
                    "readonly": "readonly",
                }),
                "award_number": forms.TextInput(attrs={
                    "class": "form-control",
                    "placeholder": "Broj projekta/granta",
                }),
            }
            labels = {
                "funder_name": _("Naziv finansijera"),
                "funder_doi": _("Funder DOI"),
                "funder_ror_id": _("Funder ROR ID"),
                "award_number": _("Broj projekta"),
            }
    ```
  - Import: Dodati `ArticleFunding` u import iz `.models`

- [ ] Task 3.3: Kreirati Funder Registry API proxy endpoint
  - File: `doi_portal/doi_portal/articles/views.py`
  - Action: Dodati FBV (posle ror_search):
    ```python
    @login_required
    @require_GET
    def funder_search(request):
        """Proxy search to Crossref Funder Registry for autocomplete."""
        query = request.GET.get("q", "").strip()
        if len(query) < 2:
            return JsonResponse({"items": []})

        cache_key = f"funder_search:{query.lower()}"
        cached = cache.get(cache_key)
        if cached:
            return JsonResponse(cached)

        try:
            response = requests.get(
                "https://api.crossref.org/funders",
                params={"query": query, "rows": 10},
                headers={"User-Agent": "DOIPortal/1.0 (mailto:admin@publikacije.doi.rs)"},
                timeout=5,
            )
            response.raise_for_status()
            data = response.json()

            results = []
            for item in data.get("message", {}).get("items", []):
                results.append({
                    "name": item.get("name", ""),
                    "doi": item.get("uri", ""),
                    "location": item.get("location", ""),
                    "alt_names": item.get("alt-names", [])[:2],
                })

            result = {"items": results}
            cache.set(cache_key, result, 3600)
            return JsonResponse(result)
        except (requests.RequestException, ValueError, KeyError):
            return JsonResponse({"items": []})
    ```

- [ ] Task 3.4: Dodati URL-ove za funding
  - File: `doi_portal/doi_portal/articles/urls.py`
  - Action: Dodati u urlpatterns:
    ```python
    path("api/funder-search/", views.funder_search, name="funder-search"),
    path("<int:article_pk>/funding/add/", views.funding_add, name="funding-add"),
    path("funding/<int:pk>/delete/", views.funding_delete, name="funding-delete"),
    path("<int:article_pk>/funding/reorder/", views.funding_reorder, name="funding-reorder"),
    path("<int:article_pk>/funding/form/", views.funding_form_view, name="funding-form"),
    ```

- [ ] Task 3.5: Kreirati funding HTMX views
  - File: `doi_portal/doi_portal/articles/views.py`
  - Action: Dodati FBV-ove za funding CRUD (isti pattern kao author/affiliation views):
    - `funding_add(request, article_pk)` — POST, kreira ArticleFunding, auto-set order, vraća `_funding_list.html` partial
    - `funding_delete(request, pk)` — POST, briše funding, vraća `_funding_list.html` partial
    - `funding_reorder(request, article_pk)` — POST sa JSON `{order: [pk1, pk2, ...]}`, ažurira order
    - `funding_form_view(request, article_pk)` — GET, vraća prazan `_funding_form.html` partial
    - Svi proveravaju `_check_article_permission(request.user, article)`

- [ ] Task 3.6: Kreirati funding partials
  - Files: `doi_portal/doi_portal/templates/articles/partials/_funding_list.html` (NOV), `_funding_form.html` (NOV)
  - Action: Kreirati po uzoru na `_author_list.html`:
    - `_funding_list.html`: Lista funding zapisa sa drag handle, funder name, award number, delete dugme. SortableJS kontejner
    - `_funding_form.html`: Forma sa autocomplete za funder_name, readonly funder_doi/funder_ror_id, tekst input za award_number

- [ ] Task 3.7: Dodati funding sekciju na article edit formu
  - File: `doi_portal/doi_portal/templates/articles/article_form.html`
  - Action: Posle Author sekcije (~line 373), dodati novu sekciju "Finansiranje":
    - Naslov "Finansiranje" sa "Dodaj finansijera" dugmetom (hx-get za funding-form)
    - Include `_funding_list.html` partial
    - SortableJS inicijalizacija za funding kontejner (isti pattern kao authorList())
    - Funder autocomplete koristi generičku `autocompleteSearch()` komponentu iz Task 2.5

- [ ] Task 3.8: Ažurirati auto-save za funding
  - File: `doi_portal/doi_portal/articles/views.py`
  - Action: U `article_autosave()` (line 895), ne treba posebna logika za funding jer funding ima sopstvene HTMX endpoint-e (add/delete/reorder). Funding se čuva odmah pri add/delete, ne kroz autosave

- [ ] Task 3.9: Dodati funding sekciju na landing stranicu
  - File: `doi_portal/doi_portal/templates/portal/article_detail.html`
  - Action: Posle Keywords sekcije (~line 95), dodati:
    ```html
    {% if article.fundings.exists %}
    <section class="article-funding mb-4" aria-labelledby="funding-heading">
      <h2 id="funding-heading" class="h5 mb-3">Finansiranje</h2>
      {% for funding in article.fundings.all %}
      <div class="mb-1">
        <span class="fw-semibold">{{ funding.funder_name }}</span>
        {% if funding.award_number %}
        <span class="text-muted">— Projekat br. {{ funding.award_number }}</span>
        {% endif %}
      </div>
      {% endfor %}
    </section>
    {% endif %}
    ```

- [ ] Task 3.10: Ažurirati Crossref XML za funding (FundRef)
  - File: `doi_portal/doi_portal/crossref/services.py`
  - Action: U `_build_context()`, za svaki article dodati funding data:
    ```python
    "fundings": [
        {
            "funder_name": f.funder_name,
            "funder_doi": f.funder_doi,
            "funder_ror_id": f.funder_ror_id,
            "award_number": f.award_number,
        }
        for f in article.fundings.all()
    ],
    ```
  - Action: U queryset-u za articles u `_build_context()` (~line 273), zameniti `issue.articles.filter(is_deleted=False)` sa `issue.articles.filter(is_deleted=False).prefetch_related("authors__affiliations", "fundings")` — PAŽNJA: `prefetch_related` trenutno NE POSTOJI u ovom queryset-u (N+1 query bug), pa se dodaje i za authors/affiliations i za fundings u istom koraku
  - Notes: **Poznati problem (out of scope za ovaj spec):** `_build_context()` filtrira samo `is_deleted=False` ali NE filtrira po statusu — uključuje DRAFT, REVIEW, READY članke pored PUBLISHED. `PreValidationService` pre generisanja XML-a upozorava na ovo, ali sam `_build_context()` ne filtrira. Ovo je van scope-a ovog spec-a ali vredi napomenuti kao buduće poboljšanje

- [ ] Task 3.11: Dodati fr:program u XML template-e
  - Files: `journal_article.xml.j2`, `conference_paper.xml.j2`, `book_chapter.xml.j2`
  - Action 1: Dodati namespace u root `<doi_batch>` element:
    ```xml
    xmlns:fr="http://www.crossref.org/fundref.xsd"
    ```
  - Action 2: Posle `</ai:program>` (ili posle license bloka), pre `<doi_data>`, dodati:
    ```xml
    {% if article.fundings %}
    <fr:program name="fundref">
      {% for funding in article.fundings %}
      <fr:assertion name="fundgroup">
        <fr:assertion name="funder_name">{{ funding.funder_name }}</fr:assertion>
        {% if funding.funder_doi %}
        <fr:assertion name="funder_identifier">{{ funding.funder_doi }}</fr:assertion>
        {% endif %}
        {% if funding.award_number %}
        <fr:assertion name="award_number">{{ funding.award_number }}</fr:assertion>
        {% endif %}
      </fr:assertion>
      {% endfor %}
    </fr:program>
    {% endif %}
    ```
  - Notes:
    - Dodati u sva tri template-a. Pozicija: posle `<ai:program>` bloka, pre `<doi_data>`
    - **VAŽNO:** `funder_identifier` je SIBLING (brat) od `funder_name` unutar `fundgroup`, NE child (dete). Crossref XSD zahteva da svi assertion elementi budu direktna deca `fundgroup` assertion-a. Nesting funder_identifier unutar funder_name je NEVAŽEĆA struktura
    - `funder_ror_id` se NE koristi u FundRef XML-u jer `ror` NIJE standardni Crossref FundRef assertion name. ROR ID finansijera se čuva u modelu za interne potrebe ali se ne šalje u XML

- [ ] Task 3.12: Registrovati ArticleFunding u admin
  - File: `doi_portal/doi_portal/articles/admin.py`
  - Action: Dodati inline admin ili jednostavnu registraciju:
    ```python
    @admin.register(ArticleFunding)
    class ArticleFundingAdmin(admin.ModelAdmin):
        list_display = ("funder_name", "award_number", "article", "order")
        list_filter = ("funder_name",)
        search_fields = ("funder_name", "award_number")
        raw_id_fields = ("article",)
    ```
  - Import: Dodati `ArticleFunding` u import

#### Stavka 4: Keyword reordering

- [ ] Task 4.1: Dodati SortableJS na keywords kontejner
  - File: `doi_portal/doi_portal/templates/articles/article_form.html`
  - Action: Ažurirati `keywordsInput()` Alpine komponentu (line 309):
    - Dodati `x-ref="keywordsList"` na wrapper div sa badge-ovima
    - Dodati `data-index` atribut na svaki badge (`<template x-for>`)
    - Dodati drag handle ikonicu (`<i class="bi bi-grip-vertical"></i>`) pre keyword teksta u svakom badge-u
    - Dodati `initSortable()` metodu u komponentu:
      ```javascript
      initSortable() {
        this.$nextTick(() => {
          if (this.$refs.keywordsList) {
            Sortable.create(this.$refs.keywordsList, {
              animation: 150,
              handle: '.keyword-drag-handle',
              onEnd: (evt) => {
                // Reorder keywords array based on new DOM order
                const item = this.keywords.splice(evt.oldIndex, 1)[0];
                this.keywords.splice(evt.newIndex, 0, item);
                // Trigger auto-save
                this.$nextTick(() => {
                  const hidden = document.querySelector('input[name="keywords"]');
                  if (hidden) hidden.dispatchEvent(new Event('change', { bubbles: true }));
                });
              }
            });
          }
        });
      }
      ```
    - Pozvati `this.initSortable()` na kraju `init()` metode
    - Dodati CSS: `.keyword-drag-handle { cursor: grab; }` i `.sortable-ghost { opacity: 0.4; }`
  - Notes:
    - **SortableJS + Alpine.js reactivity konflikt:** SortableJS fizički pomera DOM čvorove, dok Alpine.js `x-for` očekuje da sam kontroliše DOM. Nakon što SortableJS pomeri čvor, Alpine-ov virtualni DOM i stvarni DOM nisu u sinhronizaciji. Rešenje: u `onEnd` callback-u, (1) splice-ovati `keywords` niz (ovo triggeruje Alpine re-render), (2) Alpine će ponovo renderovati `x-for` listu na osnovu novog niza, efektivno popravljajući DOM. Ovo je isti pattern koji već radi za author reordering u `authorList()` komponenti. Ključno: NE koristiti `evt.item` ili DOM referencu nakon splice-a jer će Alpine ponovo renderovati elemente

#### Stavka 5: Floating action bubble

- [ ] Task 5.1: Zameniti submit/back dugmad floating bubble-om
  - File: `doi_portal/doi_portal/templates/articles/article_form.html`
  - Action: Obrisati postojeći blok (linije 250-257):
    ```html
    <div class="d-flex justify-content-between mt-4">
        <a href="{% url 'articles:list' %}" class="btn btn-outline-secondary">
            <i class="bi bi-arrow-left me-1"></i>Nazad
        </a>
        <button type="submit" class="btn btn-primary" hx-disinherit="*">
            <i class="bi bi-check-lg me-1"></i>{{ submit_text }}
        </button>
    </div>
    ```
  - Action: Dodati floating bubble VAN forme ali unutar content bloka (ili na kraj body-ja), sa `form="article-main-form"` atributom na submit dugmetu:
    ```html
    <!-- Floating Action Bubble -->
    <div class="floating-action-bubble">
      <div class="btn-group btn-group-lg shadow-lg" role="group">
        <a href="{% url 'articles:list' %}" class="btn btn-outline-secondary">
          <i class="bi bi-arrow-left me-1"></i>Nazad
        </a>
        <button type="submit" form="article-main-form" class="btn btn-primary" hx-disinherit="*">
          <i class="bi bi-check-lg me-1"></i>{{ submit_text }}
        </button>
      </div>
    </div>
    ```
  - Action: Dodati CSS (u `<style>` bloku ili zasebnom CSS fajlu):
    ```css
    .floating-action-bubble {
      position: fixed;
      bottom: 1.5rem;
      right: 1.5rem;
      z-index: 1040;
    }
    .floating-action-bubble .btn-group {
      border-radius: 50rem;
      overflow: hidden;
    }
    .floating-action-bubble .btn {
      border-radius: 0;
      padding: 0.6rem 1.2rem;
    }
    .floating-action-bubble .btn:first-child {
      border-top-left-radius: 50rem;
      border-bottom-left-radius: 50rem;
    }
    .floating-action-bubble .btn:last-child {
      border-top-right-radius: 50rem;
      border-bottom-right-radius: 50rem;
    }
    ```
  - Notes:
    - `form="article-main-form"` atribut omogućava submit dugmetu da submituje formu iako je izvan `<form>` elementa
    - **HTMX interakcija:** Klik na submit dugme sa `form=` atributom triggeruje form submit event na `<form>` elementu. HTMX sluša submit event na formi i može interceptovati ga za auto-save. Da bi se ovo sprečilo, submit dugme MORA imati `hx-disinherit="*"` ALI to samo sprečava nasleđivanje — pravi fix je dodati `hx-disable` atribut na submit dugme ili koristiti `event.preventDefault()` pattern. **Preporučeni pristup:** Dodati `@click="$el.closest('form') || document.getElementById('article-main-form').setAttribute('data-submitting', 'true')"` i u autosaveManager() proveriti `data-submitting` flag pre auto-save-a. Alternativno, postaviti submit dugme UNUTAR forme (na dnu) ali sa `position: fixed` CSS-om umesto da ga stavljamo izvan forme — ovo eliminiše problem jer `hx-disinherit="*"` radi korektno za child elemente
    - **Preporučena alternativa:** Umesto da stavljamo bubble izvan forme, staviti ga UNUTAR forme kao poslednji element pre `</form>`, sa `position: fixed` CSS-om. Ovo je jednostavnije i `hx-disinherit="*"` već radi korektno za child elemente forme

### Acceptance Criteria

#### Stavka 0: Prerequisiti

- [ ] AC 0.1: Given projekat, when se pokrene `uv sync`, then `requests` paket je instaliran bez greške
- [ ] AC 0.2: Given korisnik izmeni `original_language_title` na edit stranici, when se auto-save triggeruje i korisnik refreshuje stranicu, then podatak je sačuvan i prikazan
- [ ] AC 0.3: Given korisnik uključi `use_external_resource` i unese `external_landing_url`, when se auto-save triggeruje, then oba polja su sačuvana

#### Stavka 1: Markup

- [ ] AC 1.1: Given korisnik unese `_Escherichia coli_` u title polje, when se članak prikaže na landing stranici, then se tekst renderuje kao `<em>Escherichia coli</em>` (italic)
- [ ] AC 1.2: Given korisnik unese `H~2~O` u title polje, when se generiše Crossref XML, then title element sadrži `H<sub>2</sub>O`
- [ ] AC 1.3: Given korisnik unese `**tekst**` u abstract, when se članak prikaže na landing stranici, then se tekst renderuje kao bold
- [ ] AC 1.4: Given korisnik unese `x^2^ + y^2^` u title, when se generiše Crossref XML, then title sadrži `x<sup>2</sup> + y<sup>2</sup>`
- [ ] AC 1.5: Given korisnik unese tekst sa neuparenim delimiterom (npr. `_nepotpun`), when se tekst renderuje, then delimiter ostaje kao literal tekst bez greške
- [ ] AC 1.6: Given korisnik unese `<script>alert('xss')</script>` u title, when se renderuje na landing stranici, then HTML je escapovan i script se NE izvršava
- [ ] AC 1.7: Given korisnik otvori article edit stranicu, when klikne na "Pomoć za formatiranje teksta", then se prikaže collapsible help sekcija sa tabelom sintakse
- [ ] AC 1.8: Given korisnik klikne na dugme za kopiranje karaktera `„` u help sekciji, when klikne, then se karakter kopira u clipboard i prikaže vizuelni feedback "Kopirano"
- [ ] AC 1.9: Given korisnik unese `_test_` u preview polje help sekcije, when se tekst renderuje, then desna strana prikazuje *test* u italic-u u realnom vremenu
- [ ] AC 1.10: Given generisani XML sa face markup-om, when se validira protiv Crossref XSD šeme 5.4.0, then validacija prolazi bez grešaka
- [ ] AC 1.11: Given korisnik unese `_italic_` u abstract, when se generiše Crossref XML, then `<jats:p>` element sadrži `<jats:italic>italic</jats:italic>` (JATS tagove, NE `<i>` Crossref face markup)
- [ ] AC 1.12: Given generisani XML sa face markup u title-u, when se pregleda XML source, then NE postoji double-escape (`&lt;i&gt;` umesto `<i>`) — face markup tagovi su korektni XML elementi

#### Stavka 2: Afilijacija

- [ ] AC 2.1: Given korisnik počne da kuca "Univerzitet" u institution_name polje, when upiše bar 2 karaktera, then se prikazuje dropdown sa rezultatima iz ROR API-ja
- [ ] AC 2.2: Given korisnik izabere instituciju iz ROR dropdown-a, when klikne na rezultat, then se automatski popune institution_name, institution_ror_id, city i country
- [ ] AC 2.3: Given korisnik ručno unese institution_name bez ROR-a, when sačuva, then se afilijacija čuva sa praznim ror_id, city i country (sva opciona)
- [ ] AC 2.4: Given članak sa afilijacijom koja ima city i country, when se prikaže na landing stranici, then se vidi format "Institucija, Departman, Grad, Država"
- [ ] AC 2.5: Given članak sa afilijacijom sa city/country, when se generiše Crossref XML, then `<institution>` element NE sadrži city/country (samo institution_name i institution_id)
- [ ] AC 2.6: Given ROR API je nedostupan (timeout), when korisnik pretražuje, then dropdown prikazuje prazan rezultat bez greške, korisnik može ručno uneti

#### Stavka 3: Funding

- [ ] AC 3.1: Given korisnik na article edit stranici klikne "Dodaj finansijera", when se prikaže forma, then vidi polja za funder_name, funder_doi, funder_ror_id i award_number
- [ ] AC 3.2: Given korisnik počne da kuca "Ministarstvo" u funder_name, when upiše bar 2 karaktera, then se prikazuje dropdown sa rezultatima iz Open Funder Registry
- [ ] AC 3.3: Given korisnik izabere finansijera iz dropdown-a, when klikne na rezultat, then se automatski popune funder_name i funder_doi
- [ ] AC 3.4: Given članak sa dva funding zapisa, when se prikaže na landing stranici, then se vide oba sa formatom "Naziv finansijera — Projekat br. XXX"
- [ ] AC 3.5: Given članak sa funding informacijom, when se generiše Crossref XML, then XML sadrži `<fr:program name="fundref">` sa korektnom strukturom (fundgroup, funder_name, funder_identifier, award_number)
- [ ] AC 3.6: Given generisani XML sa fr:program blokom, when se validira protiv Crossref XSD šeme 5.4.0, then validacija prolazi bez grešaka
- [ ] AC 3.7: Given korisnik ima više funding zapisa, when koristi drag-and-drop za reorder, then se novi redosled čuva i prikazuje

#### Stavka 4: Keyword reordering

- [ ] AC 4.1: Given korisnik ima 3 ključne reči ["A", "B", "C"], when prevuče "C" na prvu poziciju, then redosled postaje ["C", "A", "B"]
- [ ] AC 4.2: Given korisnik promeni redosled ključnih reči, when se auto-save triggeruje, then se novi redosled sačuva u bazi
- [ ] AC 4.3: Given ključne reči sa promenjenim redosledom, when se članak prikaže na landing stranici, then se ključne reči prikazuju u novom redosledu
- [ ] AC 4.4: Given korisnik vidi ključne reči na edit formi, when pogleda badge-ove, then svaki badge ima vidljivu drag handle ikonicu

#### Stavka 5: Floating action bubble

- [ ] AC 5.1: Given korisnik otvori article edit stranicu, when skroluje bilo gde, then floating bubble sa "Nazad" i "Sačuvaj" je uvek vidljiv u donjem desnom uglu
- [ ] AC 5.2: Given floating bubble, when korisnik klikne "Nazad", then se vraća na listu članaka
- [ ] AC 5.3: Given floating bubble, when korisnik klikne "Sačuvaj izmene", then se forma submituje (standardni POST, ne auto-save) i podaci se čuvaju
- [ ] AC 5.4: Given floating bubble na mobilnom uređaju, when se prikaže, then je vizuelno pristupačan i ne preklapa bitan sadržaj
- [ ] AC 5.5: Given dugme "Sačuvaj" u floating bubble-u, when se klikne, then HTMX auto-save se NE triggeruje (hx-disinherit="*" radi korektno)

## Additional Context

### Dependencies

- **requests** Python paket — za HTTP pozive ka ROR i Funder API-jima. Proveriti da li je već u `pyproject.toml`, ako nije dodati sa `uv add requests`
- **Django cache framework** — za keširanje API odgovora. Već konfigurisano ako Redis postoji u stack-u
- **Bootstrap Icons** — `bi-grip-vertical` za drag handle, `bi-question-circle` za help. Proveriti da li je Bootstrap Icons CDN već uključen
- **Crossref XSD šema 5.4.0** — za validaciju generisanog XML-a sa funding blokom. Već se koristi u XSD validation modulu

### Testing Strategy

**Unit testovi (pytest-django):**
- `tests/test_markup.py` — testovi za `markup_to_html()`, `markup_to_crossref_xml()`, `strip_markup()`:
  - Osnovni slučajevi: svaki markup tip pojedinačno
  - Kombinovani slučajevi: svi markup-i u jednom stringu
  - Edge cases: prazni stringovi, None, neupareni delimiteri, nested markup, samo delimiteri, snake_case tekst (ne sme hvatati `_`)
  - XSS prevencija: HTML tagovi u ulazu moraju biti escapovani
  - Koristiti `@pytest.mark.parametrize` za kompaktne test tabele

- `tests/test_article_funding_model.py` — testovi za ArticleFunding model:
  - CRUD operacije
  - Ordering po `order` polju
  - Cascade delete kad se obriše Article
  - `__str__` metoda

- `tests/test_affiliation_extended.py` — testovi za nova city/country polja:
  - Migracija radi korektno
  - Polja su opciona (blank=True)

**Integration testovi:**
- `tests/test_crossref_xml_markup.py` — testovi za XML generisanje sa face markup-om:
  - XML sadrži `<i>`, `<b>`, `<sub>`, `<sup>` tagove u naslovu
  - Abstract XML sadrži `<jats:italic>`, `<jats:bold>`, `<jats:sub>`, `<jats:sup>` (JATS tagove, NE Crossref face markup)
  - XML prolazi XSD validaciju
  - XML sadrži `<fr:program>` blok kad funding postoji
  - XML NE sadrži `<fr:program>` kad funding ne postoji
  - **Double-escape test:** XML NE sadrži `&lt;i&gt;` ili `&lt;jats:italic&gt;` — potvrda da `jinja2.Markup()` wrapper radi korektno

**Manual testovi:**
- Proveriti markup help sekciju na edit stranici — collapsible, copy-to-clipboard, preview
- Proveriti ROR autocomplete — ukucati "Univerzitet u Beogradu", proveriti dropdown, selektovati, proveriti popunjena polja
- Proveriti Funder autocomplete — ukucati "Ministarstvo", proveriti dropdown, selektovati
- Proveriti keyword drag-and-drop — promeniti redosled, proveriti auto-save, proveriti landing stranicu
- Proveriti floating bubble — vidljivost pri skrolovanju, submit radi, nazad radi
- Proveriti responsive prikaz na mobilnom uređaju

### Notes

- **Crossref face markup dokumentacija:** `<i>`, `<b>`, `<sub>`, `<sup>` dozvoljeni u `<title>`, `<subtitle>`, `<original_language_title>`. U `<jats:abstract><jats:p>` se koristi JATS inline markup
- **Crossref FundRef:** `xmlns:fr="http://www.crossref.org/fundref.xsd"`, `<fr:program name="fundref">`, pozicija: posle `<ai:program>` pre `<doi_data>`
- **ROR API v2:** `https://api.ror.org/v2/organizations?query={term}` — besplatan, bez API ključa, vraća lokaciju u `locations[0].geonames_details`
- **Funder API:** `https://api.crossref.org/funders?query={term}&rows=10` — besplatan, DOI u `uri` polju, lokacija u `location` polju
- **Jinja2 Markup wrapper:** `jinja2.Markup(string)` signalizira Jinja2 da string je safe i da ga NE treba escapovati. Ovo je ključno za face markup u XML template-ima
- **Word boundary za italic regex:** `(?<!\w)_([^_]+)_(?!\w)` sprečava hvatanje `_` u snake_case imenima (npr. `some_variable_name` se ne konvertuje)
- **Detaljan prompt:** `docs/tech-spec-prompt-markup-funding-keywords.md` — sadrži kompletno Crossref istraživanje, XML primere, API response strukture
- **Migracije (F9):** Task 2.1 (city/country) i Task 3.1 (ArticleFunding) se kombinuju u JEDNU migraciju sa eksplicitnim imenom `add_affiliation_location_and_funding_model`. Ne pokretati `makemigrations` posle Task 2.1 — sačekati Task 3.1
- **Auto-save bug (F2/F3):** Pre-existing bug gde `original_language_*` i `external_resource_*` polja nisu u auto-save handler-u. Task 0.2 ovo popravlja kao prerequisit
- **_build_context status filter (F10):** Queryset u `_build_context()` uključuje sve statuse osim soft-deleted. Ovo je poznato ponašanje — `PreValidationService` upozorava pre generisanja. Van scope-a ovog spec-a
- **Rate limiting (F14):** ROR i Funder proxy endpoint-i nemaju per-user throttling. Cache (1h) smanjuje opterećenje za iste upite. Za produkciju razmotriti django-ratelimit
- **Crossref polite pool (F14):** Funder API zahtevi uključuju `User-Agent` header sa `mailto:` za Crossref polite pool pristup
