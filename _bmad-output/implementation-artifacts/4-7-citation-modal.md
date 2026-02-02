# Story 4.7: Citation Modal

Status: done

## Story

As a **visitor (posetilac)**,
I want **to get properly formatted citations in multiple styles from the article landing page**,
So that **I can cite the article in my research using the correct academic citation format**.

## Background

Ovo je sedma priča u Epiku 4 (Public Portal Experience). Story 4.5 je implementirala Floating Action Bar sa placeholder Cite dugmetom (`handleCiteClick()` je prazan metod). Story 4.6 je implementirala PDF Download. Ovaj story zamenjuje placeholder sa **funkcionalnim Citation Modalom** - Bootstrap 5 modal koji prikazuje formatiranu citaciju u 5 formata (APA, MLA, Chicago, BibTeX, RIS) sa copy-to-clipboard i download funkcijama.

Citation Modal je jedan od 10 custom UI komponenti definisanih u UX Design specifikaciji (#8 - "APA, MLA, Chicago, BibTeX, RIS formati, Copy to clipboard funkcionalnost").

**FR Pokrivenost:**
- Nema direktnog FR za citiranje, ali je implicitno u FR41 (landing stranica sa svim metapodacima) i UX specifikaciji (Journey 3: "Citiraj" akcija)

**NFR Pokrivenost:**
- NFR1: Landing stranica članka - FCP < 3 sekunde (modal ne sme dodavati blocking resurse)
- NFR14: Semantički HTML5 elementi (modal ARIA atributi, role="dialog")
- NFR16: Kontrast minimum 4.5:1 za tekst (citacija čitljivost)
- NFR17: Keyboard navigacija za ključne akcije (Tab navigacija, Escape zatvara modal, focus trap)
- NFR25: Graceful degradation (nedostajući metapodaci graciozno izostavljena)

**Zavisnosti (sve DONE):**
- Story 4.5: Floating Action Bar - `_floating_action_bar.html`, `handleCiteClick()` placeholder, `floatingActionBar()` Alpine.js komponenta
- Story 4.4: Article Landing Page - `article_detail.html`, `ArticleLandingView`, context varijable (`full_doi`, `doi_url`, `is_withdrawn`, `article`)
- Story 4.1: Portal Home Page - `portal/base.html`, portal nav, `portal.css`

**Blokira:**
- Nijednu priču direktno.

## Acceptance Criteria

1. **Given** posetilac klikne "Citiraj" dugme u floating action bar-u
   **When** citation modal se otvori
   **Then** Bootstrap 5 modal je prikazan
   **And** naslov članka je prikazan kao modal header

2. **Given** citation modal je otvoren
   **When** posetilac pregleda dostupne formate
   **Then** tabovi ili dugmad prikazuju: APA, MLA, Chicago, BibTeX, RIS
   **And** podrazumevani format je APA

3. **Given** posetilac odabere format citiranja
   **When** format je primenjen
   **Then** pravilno formatirana citacija je prikazana
   **And** citacija uključuje: autore, naslov, publikaciju, godinu, volumen, izdanje, stranice, DOI

4. **Given** citacija je prikazana
   **When** posetilac klikne "Kopiraj u clipboard"
   **Then** tekst citacije je kopiran
   **And** toast notifikacija potvrđuje: "Citacija kopirana!"

5. **Given** BibTeX ili RIS format je odabran
   **When** posetilac pregleda citaciju
   **Then** tekst je prikazan u code-formatu (monospace)
   **And** "Preuzmi" opcija je dostupna za .bib ili .ris fajl

6. **Given** posetilac zatvara modal
   **When** klikne X ili klikne van modala ili pritisne Escape
   **Then** modal se zatvara glatko
   **And** stanje stranice je očuvano

7. **Given** posetilac koristi tastaturu
   **When** navigira kroz citation modal
   **Then** focus trap je aktivan unutar modala
   **And** Tab navigacija radi između tabova i dugmadi
   **And** Escape zatvara modal

8. **Given** članak ima nepotpune metapodatke (npr. bez stranica)
   **When** citacija je generisana
   **Then** nedostajuća polja su graciozno izostavljena
   **And** citacija je i dalje validna prema formatu

## Tasks / Subtasks

- [x] Task 1: Kreirati citation service funkcije u `portal/services.py` (AC: #2, #3, #5, #8)
  - [x] 1.1 Dodati `generate_citation(article, format)` glavnu funkciju koja delegira na specifične formate
  - [x] 1.2 Dodati `format_citation_apa(article)` - APA 7th edition format
  - [x] 1.3 Dodati `format_citation_mla(article)` - MLA 9th edition format
  - [x] 1.4 Dodati `format_citation_chicago(article)` - Chicago 17th edition (author-date)
  - [x] 1.5 Dodati `format_citation_bibtex(article)` - BibTeX @article format
  - [x] 1.6 Dodati `format_citation_ris(article)` - RIS format
  - [x] 1.7 Svaka funkcija prima Article instancu sa prefetch-ovanim autorima i issue/publication/publisher
  - [x] 1.8 Graciozno rukovanje nedostajućim metapodacima (bez stranica, bez apstrakta, itd.)

- [x] Task 2: Kreirati HTMX endpoint za generisanje citacije (AC: #2, #3)
  - [x] 2.1 U `portal/views.py` dodati `article_citation` FBV - prima `pk` i `format` GET parametar
  - [x] 2.2 View vraća HTML fragment sa formatiranom citacijom (HTMX pattern - nikad JSON!)
  - [x] 2.3 Filtrira samo PUBLISHED i WITHDRAWN članke (isti queryset kao ArticleLandingView)
  - [x] 2.4 Podržani formati: "apa", "mla", "chicago", "bibtex", "ris" - default "apa"
  - [x] 2.5 Vraća 404 za nepostojeće ili nepublikovane članke

- [x] Task 3: Dodati URL pattern za citation endpoint (AC: #2)
  - [x] 3.1 U `portal/urls_articles.py` dodati path: `<int:pk>/cite/` sa name `article-citation`
  - [x] 3.2 URL je public (bez autentifikacije)

- [x] Task 4: Kreirati `_citation_content.html` HTMX partial template (AC: #3, #5)
  - [x] 4.1 Kreirati `portal/partials/_citation_content.html` - HTMX fragment za citaciju
  - [x] 4.2 Za plain text formate (APA, MLA, Chicago): prikazati u `<div>` sa klasom za selekciju teksta
  - [x] 4.3 Za code formate (BibTeX, RIS): prikazati u `<pre><code>` bloku sa monospace fontom
  - [x] 4.4 Uključiti data atribute za format tip (`data-citation-format`) koji Alpine.js koristi za download

- [x] Task 5: Kreirati `_citation_modal.html` partial template (AC: #1, #2, #4, #5, #6, #7)
  - [x] 5.1 Kreirati `portal/partials/_citation_modal.html` sa Bootstrap 5 modal strukturom
  - [x] 5.2 Modal header: naslov članka (skraćen na 80 karaktera ako je predugačak)
  - [x] 5.3 Modal body: tabovi za formate (APA | MLA | Chicago | BibTeX | RIS) kao Bootstrap nav-tabs
  - [x] 5.4 Ispod tabova: `#citation-content` div koji se ažurira putem HTMX
  - [x] 5.5 Inicijalni load: APA format učitan pri otvaranju modala (hx-trigger="shown.bs.modal from:closest .modal")
  - [x] 5.6 Tab klik: HTMX poziv ka `/articles/{pk}/cite/?format={tab}` sa hx-target="#citation-content"
  - [x] 5.7 Modal footer: "Kopiraj u clipboard" dugme i "Preuzmi" dugme (za BibTeX/RIS)
  - [x] 5.8 Alpine.js funkcija `citationModal()` za copy i download logiku
  - [x] 5.9 Accessibility: `aria-labelledby`, `role="dialog"`, focus trap (Bootstrap 5 built-in)

- [x] Task 6: Ažurirati `_floating_action_bar.html` - zamena placeholder-a (AC: #1)
  - [x] 6.1 Zameniti `@click="handleCiteClick()"` sa `data-bs-toggle="modal"` i `data-bs-target="#citationModal"` na Cite dugmetu
  - [x] 6.2 Ukloniti placeholder tooltip "Citiranje uskoro dostupno"
  - [x] 6.3 Ažurirati title na "Citiraj članak"
  - [x] 6.4 Ukloniti `handleCiteClick()` metod iz `floatingActionBar()` Alpine.js komponente u `<script>` tagu (više nije potreban jer se koristi `data-bs-toggle`)
  - [x] 6.5 Zadržati sve ARIA atribute i srpske labele

- [x] Task 7: Uključiti citation modal u `article_detail.html` i ažurirati ArticleLandingView context (AC: #1)
  - [x] 7.1 Dodati `{% include "portal/partials/_citation_modal.html" %}` pre zatvaranja `{% endblock %}`
  - [x] 7.2 Modal se renderuje u DOM ali je skriven (Bootstrap modal default)
  - [x] 7.3 U `ArticleLandingView.get_context_data()` dodati `citation_url` (reverse za `article-citation` endpoint)
  - [x] 7.4 U `ArticleLandingView.get_context_data()` dodati `citation_download_url` (reverse za `article-citation-download` endpoint)

- [x] Task 8: Kreirati download endpoint za BibTeX/RIS fajlove (AC: #5)
  - [x] 8.1 U `portal/views.py` dodati `article_citation_download` FBV
  - [x] 8.2 Prima `pk` i `format` parametar (samo "bibtex" i "ris")
  - [x] 8.3 Vraća `HttpResponse` sa `Content-Disposition: attachment` i odgovarajućim MIME type-om
  - [x] 8.4 BibTeX: `application/x-bibtex`, filename `{doi_suffix}.bib`
  - [x] 8.5 RIS: `application/x-research-info-systems`, filename `{doi_suffix}.ris`

- [x] Task 9: Dodati URL pattern za citation download (AC: #5)
  - [x] 9.1 U `portal/urls_articles.py` dodati path: `<int:pk>/cite/download/` sa name `article-citation-download`

- [x] Task 10: Dodati CSS za citation modal (AC: #1, #5)
  - [x] 10.1 U `portal.css` dodati minimalne stilove za citation modal
  - [x] 10.2 `.citation-text` klasa za selectable text sa padding
  - [x] 10.3 `.citation-code` klasa za BibTeX/RIS code blokove
  - [x] 10.4 Tab active state usklađen sa portal temom
  - [x] 10.5 Koristiti postojeće Bootstrap 5 klase koliko je moguće - NE preterivati sa custom CSS

- [x] Task 11: Kreirati testove (AC: #1-#8)
  - [x] 11.1 Test: Citation endpoint vraća HTML fragment za PUBLISHED članak sa APA formatom (default)
  - [x] 11.2 Test: Citation endpoint vraća HTML fragment za svaki format (apa, mla, chicago, bibtex, ris)
  - [x] 11.3 Test: Citation endpoint vraća 404 za DRAFT članak
  - [x] 11.4 Test: Citation endpoint vraća 404 za nepostojeći članak
  - [x] 11.5 Test: Citation endpoint radi za WITHDRAWN članak (citacija se i dalje prikazuje)
  - [x] 11.6 Test: `format_citation_apa()` generiše ispravan APA format sa svim poljima
  - [x] 11.7 Test: `format_citation_apa()` graciozno rukuje nedostajućim stranicama
  - [x] 11.8 Test: `format_citation_bibtex()` generiše validan BibTeX entry
  - [x] 11.9 Test: `format_citation_ris()` generiše validan RIS entry
  - [x] 11.10 Test: Citation download vraća fajl sa ispravnim Content-Disposition headerom
  - [x] 11.11 Test: Citation download vraća 400 za nepoznat format
  - [x] 11.12 Test: Citation modal template sadrži Bootstrap 5 modal strukturu
  - [x] 11.13 Test: Floating action bar Cite dugme sadrži `data-bs-toggle="modal"`
  - [x] 11.14 Test: Citation endpoint ne zahteva autentifikaciju (public)
  - [x] 11.15 Test: `format_citation_mla()` generiše ispravan MLA format
  - [x] 11.16 Test: `format_citation_chicago()` generiše ispravan Chicago format

## Dev Notes

### KRITIČNO: Citation Format Strategija

**Pristupi za citation generisanje:**

1. **Server-side generisanje (IZABRANO):** Citacije se generišu u Python-u na serveru, vraćaju kao HTML fragment putem HTMX. Razlozi:
   - HTMX pattern projekta: "UVEK vračaj HTML, NIKAD JSON"
   - Lakše testiranje (unit testovi za formate)
   - Business logika u `services.py` (project-context.md pravilo)
   - Nema potrebe za JavaScript library za formatiranje citacija

2. **Client-side generisanje (ODBAČENO):** Citacije se generišu u JavaScript-u. Odbačeno jer:
   - Narušava HTMX-first pristup projekta
   - Teže za testiranje
   - Potrebna JS biblioteka (citation.js ili slično)

**HTMX Flow:**
1. Posetilac klikne "Citiraj" dugme -> Bootstrap modal se otvori
2. Modal `shown.bs.modal` event -> HTMX GET ka `/articles/{pk}/cite/?format=apa`
3. Server generiše citaciju, vraća HTML fragment
4. Fragment se prikazuje u `#citation-content` div-u
5. Klik na tab -> HTMX GET ka `/articles/{pk}/cite/?format={selected}` -> zamena sadržaja

### Citation Format Detalji

**APA 7th Edition:**
```
Prezime, Inicijali., Prezime2, Inicijali2., & Prezime3, Inicijali3. (Godina). Naslov članka. Naziv publikacije, Volume(Broj), Stranice. https://doi.org/DOI
```
Primer:
```
Petrović, M., Jovanović, D., & Nikolić, S. (2025). Uticaj digitalizacije na naučno izdavaštvo. Srpski časopis za informatiku, 12(3), 45-67. https://doi.org/10.1234/test-001
```

**MLA 9th Edition:**
```
Prezime, Ime, et al. "Naslov članka." Naziv publikacije, vol. Volume, no. Broj, Godina, pp. Stranice. DOI: doi.
```

**Chicago 17th (Author-Date):**
```
Prezime, Ime, Ime2 Prezime2, and Ime3 Prezime3. Godina. "Naslov članka." Naziv publikacije Volume (Broj): Stranice. https://doi.org/DOI.
```

**BibTeX:**
```bibtex
@article{doi_suffix,
  author = {Prezime, Ime and Prezime2, Ime2 and Prezime3, Ime3},
  title = {Naslov članka},
  journal = {Naziv publikacije},
  year = {2025},
  volume = {12},
  number = {3},
  pages = {45--67},
  doi = {10.1234/test-001}
}
```

**RIS:**
```
TY  - JOUR
AU  - Prezime, Ime
AU  - Prezime2, Ime2
TI  - Naslov članka
JO  - Naziv publikacije
VL  - 12
IS  - 3
SP  - 45
EP  - 67
PY  - 2025
DO  - 10.1234/test-001
ER  -
```

### Alpine.js Modal Integracija

```javascript
// U _citation_modal.html
function citationModal() {
  return {
    copied: false,

    async copyCitation() {
      const el = document.getElementById('citation-content');
      if (!el) return;
      const text = el.innerText;
      try {
        await navigator.clipboard.writeText(text);
      } catch {
        // Fallback za starije browsere
        const ta = document.createElement('textarea');
        ta.value = text;
        ta.style.position = 'fixed';
        ta.style.opacity = '0';
        document.body.appendChild(ta);
        ta.select();
        document.execCommand('copy');
        document.body.removeChild(ta);
      }
      this.copied = true;
      setTimeout(() => { this.copied = false; }, 2000);
    },

    downloadCitation() {
      // Redirect to download endpoint - format is tracked via Alpine data
      const activeTab = document.querySelector('#citationTabs .nav-link.active');
      const format = activeTab?.dataset?.format || 'apa';
      if (format === 'bibtex' || format === 'ris') {
        window.location.href = this.downloadUrl + '?format=' + format;
      }
    },

    get isDownloadable() {
      const activeTab = document.querySelector('#citationTabs .nav-link.active');
      const format = activeTab?.dataset?.format || 'apa';
      return format === 'bibtex' || format === 'ris';
    }
  };
}
```

### Ažuriranje Floating Action Bar Cite Dugmeta

```html
<!-- BEFORE (Story 4.5 - placeholder): -->
<button type="button"
        class="btn btn-outline-secondary fab-btn"
        title="Citiranje uskoro dostupno"
        aria-label="Citiraj članak"
        @click="handleCiteClick()">
  <i class="bi bi-quote" aria-hidden="true"></i>
  <span class="fab-label d-lg-none">Citiraj</span>
</button>

<!-- AFTER (Story 4.7 - functional): -->
<button type="button"
        class="btn btn-outline-secondary fab-btn"
        title="Citiraj članak"
        aria-label="Citiraj članak"
        data-bs-toggle="modal"
        data-bs-target="#citationModal">
  <i class="bi bi-quote" aria-hidden="true"></i>
  <span class="fab-label d-lg-none">Citiraj</span>
</button>
```

### Bootstrap 5 Modal Korišćenje

**KRITIČNO:** Koristiti Bootstrap 5 modal API koji je VEĆ dostupan u projektu:
- Bootstrap 5.3+ je CDN uključen u `base.html` (Cookiecutter Django default)
- `data-bs-toggle="modal"` i `data-bs-target` za otvaranje
- Bootstrap modal ugrađeni focus trap - NE implementirati custom focus trap
- `data-bs-dismiss="modal"` za zatvaranje
- Escape i klik van modala podržani out-of-box

### Context Ažuriranje - ArticleLandingView

```python
# portal/views.py - ArticleLandingView.get_context_data()
# DODATI:
context["citation_url"] = reverse(
    "portal-articles:article-citation",
    kwargs={"pk": article.pk},
)
context["citation_download_url"] = reverse(
    "portal-articles:article-citation-download",
    kwargs={"pk": article.pk},
)
```

### URL Konfiguracija

```python
# portal/urls_articles.py - DODATI:
path(
    "<int:pk>/cite/",
    views.article_citation,
    name="article-citation",
),
path(
    "<int:pk>/cite/download/",
    views.article_citation_download,
    name="article-citation-download",
),
```

### Postojeći Patterns koje MORAMO slediti

**Portal views pattern** (VEĆ implementirano):
- FBV za HTMX endpointe: `snake_case` ime (`article_citation`, `article_citation_download`)
- CBV za stranice sa template-om: `PascalCase + View`
- HTMX response: UVEK HTML fragment, NIKAD JSON

**URL pattern** (VEĆ implementirano):
- `portal/urls_articles.py` - `app_name = "portal-articles"`, public routes
- Kebab-case URL paths
- `<int:pk>/cite/` - nested pod article PK

**Template partial pattern** (VEĆ implementirano):
- `_` prefix za HTMX partials
- Alpine.js `x-data` sa function pattern
- Bootstrap Icons (`bi-*` klase)
- Srpski tekst za sve UI labele

**HTMX pattern** (VEĆ implementirano):
- `hx-get` za dinamički sadržaj
- `hx-target` za zamenu sadržaja
- `hx-swap="innerHTML"` default
- Proveriti `request.headers.get('HX-Request')` u view-u

**Article model** (VEĆ implementirano):
- `Article.title`, `Article.subtitle`, `Article.doi_suffix`
- `Article.first_page`, `Article.last_page`
- `Article.language`
- `article.issue.publication.title` - naziv publikacije
- `article.issue.volume`, `article.issue.issue_number`, `article.issue.year`
- `article.issue.publication.publisher.doi_prefix` - DOI prefix
- `article.authors.all()` - queryset autora sa `given_name`, `surname`, `order`

**Copy to clipboard** (VEĆ implementirano u Story 4.5):
- `navigator.clipboard.writeText()` sa fallback za starije browsere
- Pattern je u `floatingActionBar.copyToClipboard()` - REUSE isti pristup u `citationModal`

### Previous Story Learnings (Story 4.5 + 4.6)

1. **Alpine.js VEĆ dostupan**: `base.html` uključuje Alpine.js 3.15.3 CDN sa `defer` - NE dodavati ponovo.
2. **Bootstrap 5 VEĆ dostupan**: `base.html` uključuje Bootstrap 5.3+ CDN - NE dodavati ponovo.
3. **Bootstrap Icons**: VEĆ uključeni u `portal/base.html` kao CDN. Koristiti `bi-*` klase.
4. **Portal CSS**: `static/css/portal.css` - VEĆ učitan. Dodati minimalne CSS stilove samo za citation-specifične elemente.
5. **Test pattern**: pytest-django, `@pytest.mark.django_db`, Factory Boy. `ArticleFactory`, `IssueFactory`, `PublicationFactory`, `PublisherFactory`, `AuthorFactory` su VEĆ dostupni.
6. **Test suite**: Story 4.6 ima 1259 passed, 3 skipped. Ne smemo imati regresije.
7. **`handleCiteClick()`** je placeholder metod u Alpine.js komponenti - treba ga ukloniti i zameniti Bootstrap modal trigger-om.
8. **`has_pdf`, `share_url`, `pdf_download_url`** su VEĆ u ArticleLandingView context-u. Dodajemo `citation_url` i `citation_download_url`.
9. **Z-index** i CSS stilovi za floating bar su VEĆ podešeni - NE menjamo FAB CSS.
10. **Portal articles URL**: `path("articles/", include("doi_portal.portal.urls_articles", namespace="portal-articles"))` u `config/urls.py`
11. **`article_detail.html`** VEĆ uključuje `_floating_action_bar.html` partial - dodajemo `_citation_modal.html` include u isti template.
12. **Withdrawn članci**: VIDLJIVI su na portalu (ArticleLandingView ih prikazuje) - citacija TREBA biti dostupna i za withdrawn članke jer je to standardna akademska praksa.

### Srpski Karakteri (OBAVEZNO - videti project-context.md)

| Kontekst | ISPRAVNO |
|----------|----------|
| Cite dugme title | "Citiraj članak" |
| Cite dugme label | "Citiraj" |
| Modal header | "Citiranje" |
| Tab labele | "APA", "MLA", "Čikago", "BibTeX", "RIS" |
| Copy dugme | "Kopiraj u clipboard" |
| Copy potvrda | "Citacija kopirana!" |
| Download dugme | "Preuzmi" |
| Download tooltip (disabled) | "Preuzimanje dostupno za BibTeX i RIS formate" |

### Git Commit Pattern

```
story-4-7: feat(portal): implementiraj Citation Modal sa APA/MLA/Chicago/BibTeX/RIS formatima i HTMX tabovima (Story 4.7)
```

### Fajlovi za modifikaciju (POSTOJEĆI)

```
doi_portal/doi_portal/portal/views.py                                      # Dodati article_citation + article_citation_download FBV, citation URLs u context
doi_portal/doi_portal/portal/urls_articles.py                              # Dodati <int:pk>/cite/ i <int:pk>/cite/download/ URL patterns
doi_portal/doi_portal/portal/services.py                                   # Dodati generate_citation() i format_citation_*() funkcije
doi_portal/doi_portal/templates/portal/partials/_floating_action_bar.html  # Zameniti placeholder Cite dugme sa data-bs-toggle="modal"
doi_portal/doi_portal/templates/portal/article_detail.html                 # Dodati {% include "_citation_modal.html" %}
doi_portal/doi_portal/static/css/portal.css                                # Dodati minimalne citation modal stilove
```

### Fajlovi za kreiranje (NOVI)

```
doi_portal/doi_portal/templates/portal/partials/_citation_modal.html       # Citation modal sa tabovima i Alpine.js
doi_portal/doi_portal/templates/portal/partials/_citation_content.html     # HTMX fragment za sadržaj citacije
doi_portal/doi_portal/portal/tests/test_citation.py                        # Citation testovi (view, service, template)
```

### Fajlovi koji se NE MENJAJU

```
doi_portal/doi_portal/templates/portal/base.html                           # VEĆ postoji - NE MENJATI (Bootstrap 5, Alpine.js VEĆ uključeni)
doi_portal/doi_portal/templates/base.html                                  # VEĆ postoji - NE MENJATI
doi_portal/doi_portal/articles/models.py                                   # VEĆ postoji - NE MENJATI
doi_portal/config/urls.py                                                  # VEĆ postoji - NE MENJATI
doi_portal/doi_portal/portal/tests/test_floating_action_bar.py             # NE MENJATI (osim ako postoje testovi za placeholder cite koji se moraju ažurirati)
doi_portal/doi_portal/portal/tests/test_pdf_download.py                    # NE MENJATI
```

### Anti-Patterns (ZABRANJENO)

```python
# POGREŠNO - Vraćati JSON iz HTMX endpointa
return JsonResponse({"citation": citation_text})
# Razlog: HTMX pattern projekta - UVEK HTML, NIKAD JSON

# POGREŠNO - Koristiti JavaScript library za citation formatting
# import citation-js, citeproc-js
# Razlog: Server-side generisanje, Python u services.py

# POGREŠNO - Kreirati novi Alpine.js CDN include
<script src="https://cdn.jsdelivr.net/npm/alpinejs@3.15.3/dist/cdn.min.js"></script>
# Razlog: VEĆ uključen u base.html

# POGREŠNO - Kreirati custom focus trap za modal
# Razlog: Bootstrap 5 modal ima ugrađen focus trap

# POGREŠNO - Dodavati autentifikaciju za citation endpoint
@login_required
def article_citation(request, pk):
# Razlog: Javni portal, bez login-a

# POGREŠNO - Generisati citaciju client-side u JavaScript-u
function generateAPA(articleData) { ... }
# Razlog: HTMX-first pristup, business logika u services.py

# POGREŠNO - Koristiti camelCase za Python funkcije
def formatCitationApa(article):
# Razlog: snake_case za sve Python funkcije

# POGREŠNO - Zaboraviti srpske karaktere sa dijakriticima
"Clanak" -> POGREŠNO!
"Članak" -> ISPRAVNO!

# POGREŠNO - Dodati blocking JavaScript resurse
<script src="citation-formatter.js"></script>  <!-- u <head> -->
# Razlog: NFR1 - FCP < 3 sekunde

# POGREŠNO - Kreirati CBV za HTMX endpointe
class ArticleCitationView(View):
# Razlog: FBV je prikladniji za HTMX endpointe (project-context.md)
```

### Performance (NFR1 - FCP < 3 sekunde)

```
# Citation modal NE SME usporavati initial page load:
# 1. Modal HTML je u DOM-u ali skriven (Bootstrap default) - minimalan overhead
# 2. Sadržaj citacije se učitava putem HTMX TEK kada se modal otvori (lazy loading)
# 3. Nema dodatnih JS biblioteka za citation formatting
# 4. Alpine.js logika za copy/download je minimalna
# 5. CSS stilovi za modal su minimalni (koristimo Bootstrap klase)
```

### Accessibility (NFR14, NFR16, NFR17)

```html
<!-- Modal sa punim accessibility atributima -->
<div class="modal fade" id="citationModal"
     tabindex="-1"
     aria-labelledby="citationModalLabel"
     aria-hidden="true"
     role="dialog">
  <div class="modal-dialog">
    <div class="modal-content">
      <div class="modal-header">
        <h5 class="modal-title" id="citationModalLabel">Citiranje</h5>
        <button type="button" class="btn-close"
                data-bs-dismiss="modal"
                aria-label="Zatvori"></button>
      </div>
      <!-- Tabovi sa aria-role="tablist" -->
      <!-- Sadržaj sa aria-live="polite" za HTMX updates -->
    </div>
  </div>
</div>
```

### Test Pattern

```python
# portal/tests/test_citation.py

import pytest
from django.urls import reverse

from doi_portal.articles.models import ArticleStatus
from doi_portal.articles.tests.factories import ArticleFactory, AuthorFactory
from doi_portal.issues.models import IssueStatus
from doi_portal.issues.tests.factories import IssueFactory
from doi_portal.portal.services import (
    format_citation_apa,
    format_citation_bibtex,
    format_citation_ris,
    generate_citation,
)
from doi_portal.publications.tests.factories import PublicationFactory
from doi_portal.publishers.tests.factories import PublisherFactory


@pytest.mark.django_db
class TestArticleCitationView:
    """Tests for article citation HTMX endpoint."""

    def _create_article(self, status=ArticleStatus.PUBLISHED, num_authors=2):
        publisher = PublisherFactory(doi_prefix="10.9999")
        pub = PublicationFactory(publisher=publisher, title="Test Journal")
        issue = IssueFactory(
            publication=pub, status=IssueStatus.PUBLISHED,
            volume=12, issue_number=3, year=2025,
        )
        article = ArticleFactory(
            issue=issue, doi_suffix="test-001", status=status,
            title="Test Article Title",
            first_page="45", last_page="67",
        )
        for i in range(num_authors):
            AuthorFactory(
                article=article,
                given_name=f"Name{i}",
                surname=f"Surname{i}",
                order=i,
            )
        return article

    def test_citation_returns_html_fragment(self, client):
        article = self._create_article()
        url = reverse("portal-articles:article-citation", kwargs={"pk": article.pk})
        response = client.get(url)
        assert response.status_code == 200
        assert "text/html" in response["Content-Type"]

    def test_citation_default_apa(self, client):
        article = self._create_article()
        url = reverse("portal-articles:article-citation", kwargs={"pk": article.pk})
        response = client.get(url)
        assert response.status_code == 200
        content = response.content.decode()
        assert "Test Article Title" in content

    def test_citation_404_for_draft(self, client):
        article = self._create_article(status=ArticleStatus.DRAFT)
        url = reverse("portal-articles:article-citation", kwargs={"pk": article.pk})
        response = client.get(url)
        assert response.status_code == 404

    def test_citation_works_for_withdrawn(self, client):
        article = self._create_article(status=ArticleStatus.WITHDRAWN)
        url = reverse("portal-articles:article-citation", kwargs={"pk": article.pk})
        response = client.get(url)
        assert response.status_code == 200


@pytest.mark.django_db
class TestCitationFormatting:
    """Tests for citation format service functions."""

    # ... format-specific tests
```

### Dependencies (Python/Django)

Nema novih Python zavisnosti! Sve je već instalirano:
- Django 5.2+ (render, get_object_or_404, reverse, HttpResponse)
- Bootstrap 5.3+ (modal, tabs, nav - CDN u base.html)
- Alpine.js 3.15.3 (x-data, @click, x-show - CDN u base.html)
- pytest-django + Factory Boy (već u test setup-u)

### NFR Requirements

- **FR41 (implicitno):** Landing stranica sa svim metapodacima - citiranje je deo kompletnog iskustva
- **NFR1:** FCP < 3 sekunde - lazy load citacije putem HTMX, nema blocking JS
- **NFR14:** Semantički HTML5 - Bootstrap modal sa aria atributima, role="dialog"
- **NFR16:** Kontrast minimum 4.5:1 - citacija tekst čitljivost
- **NFR17:** Keyboard navigacija - Bootstrap modal focus trap, Tab navigacija, Escape zatvara modal
- **NFR25:** Graceful degradation - nedostajući metapodaci graciozno izostavljena u citaciji

### Project Structure Notes

- Citation view ide u `portal/views.py` jer je to PUBLIC portal view (ne admin)
- URL ide u `portal/urls_articles.py` jer je vezan za article resources
- Citation formatting funkcije idu u `portal/services.py` jer je business logic layer
- Modal template ide u `portal/partials/_citation_modal.html` jer je UI komponenta
- HTMX fragment ide u `portal/partials/_citation_content.html` jer je HTMX partial sa `_` prefix
- Testovi u `portal/tests/test_citation.py` - novi test fajl za citation-specifične testove

### References

- [Source: epics.md#Story 4.7: Citation Modal]
- [Source: epics.md#Epic 4: Public Portal Experience]
- [Source: ux-design-specification.md#Component Strategy - Custom Component #8: Citation Modal]
- [Source: ux-design-specification.md#Journey 3: Posetilac pristupa članku - "Citiraj" akcija]
- [Source: ux-design-specification.md#Modal Patterns - Close: X + Escape + overlay click, Focus trap, Max width 600px]
- [Source: architecture.md#Frontend Architecture - HTMX 2.0.8, Alpine.js 3.15.3, Bootstrap 5]
- [Source: architecture.md#API & Communication Patterns - HTMX endpoints sa HTML fragment responses]
- [Source: project-context.md#HTMX Pravila - partials sa _ prefix, UVEK HTML ne JSON]
- [Source: project-context.md#Naming Konvencije - snake_case za FBV, kebab-case za URL]
- [Source: project-context.md#Lokalizacija - Srpski Karakteri, sr-Latn]
- [Source: project-context.md#Services Layer - kompleksna business logika u services.py]
- [Source: project-context.md#Testing (pytest-django) - Factory Boy]
- [Source: 4-5-floating-action-bar.md - Previous story: _floating_action_bar.html, handleCiteClick placeholder]
- [Source: 4-6-pdf-download.md - Previous story: article_pdf_download FBV pattern, get_pdf_download_filename]
- [Source: portal/views.py - ArticleLandingView.get_context_data() existing context with has_pdf, share_url, pdf_download_url]
- [Source: portal/urls_articles.py - app_name="portal-articles", article-detail pattern, article-pdf-download pattern]
- [Source: portal/partials/_floating_action_bar.html - floatingActionBar() Alpine.js component, handleCiteClick() placeholder]
- [Source: portal/article_detail.html - {% include "_floating_action_bar.html" %} at bottom]
- [Source: articles/models.py - Article fields, Author model with given_name/surname/order, Affiliation model]

## Dev Agent Record

### Agent Model Used

Claude Opus 4.5 (claude-opus-4-5-20251101)

### Debug Log References

- All 31 citation tests pass (0 failures)
- Full portal test suite: 281 passed, 0 failed
- Full project test suite: 1284 passed, 3 skipped, 11 pre-existing failures (test_pdf_upload.py - articles.tasks module missing, unrelated to Story 4.7)

### Completion Notes List

- TDD approach: wrote tests first (RED), then implemented (GREEN)
- Citation formatting follows APA 7th, MLA 9th, Chicago 17th, BibTeX, RIS standards
- All service functions gracefully handle missing metadata (pages, volume, etc.)
- HTMX-first approach: server-side citation generation, HTML fragment responses
- Bootstrap 5 modal with built-in focus trap and accessibility attributes
- Alpine.js `citationModal()` function for copy-to-clipboard and download logic
- Srpski UI labels used throughout (Citiranje, Kopiraj u clipboard, Preuzmi, etc.)
- handleCiteClick() placeholder removed from floatingActionBar() Alpine component
- Cite button now uses data-bs-toggle="modal" + data-bs-target="#citationModal"
- Lazy loading: citation content loaded via HTMX only when modal opens (NFR1 compliance)
- No new Python dependencies added

### File List

**Modified files:**
- `doi_portal/doi_portal/portal/services.py` - Added generate_citation(), format_citation_apa/mla/chicago/bibtex/ris()
- `doi_portal/doi_portal/portal/views.py` - Added article_citation, article_citation_download FBVs; citation URLs in ArticleLandingView context
- `doi_portal/doi_portal/portal/urls_articles.py` - Added <int:pk>/cite/ and <int:pk>/cite/download/ URL patterns
- `doi_portal/doi_portal/templates/portal/partials/_floating_action_bar.html` - Replaced placeholder cite button with data-bs-toggle="modal", removed handleCiteClick()
- `doi_portal/doi_portal/templates/portal/article_detail.html` - Added {% include "_citation_modal.html" %}
- `doi_portal/doi_portal/static/css/portal.css` - Added .citation-text, .citation-code, #citationTabs styles

**New files:**
- `doi_portal/doi_portal/templates/portal/partials/_citation_modal.html` - Bootstrap 5 modal with tabs and Alpine.js
- `doi_portal/doi_portal/templates/portal/partials/_citation_content.html` - HTMX partial fragment for citation content
- `doi_portal/doi_portal/portal/tests/test_citation.py` - 31 tests covering all ACs
