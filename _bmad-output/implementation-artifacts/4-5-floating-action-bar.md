# Story 4.5: Floating Action Bar

Status: done

## Story

As a **visitor**,
I want **quick access to PDF, citation, and sharing options via a floating action bar**,
So that **I can take action without scrolling on the article landing page**.

## Background

Ovo je peta priča u Epiku 4 (Public Portal Experience). Story 4.4 je implementirala Article Landing Page sa two-column layoutom, autorom/metapodacima i withdrawn banerom. Ovaj story dodaje **Floating Action Bar** - komponentu koja je uvek vidljiva na ekranu i pruža brz pristup ključnim akcijama: PDF download, citiranje, deljenje i kopiranje DOI linka.

Floating Action Bar je jedan od 10 custom UI komponenti definisanih u UX Design specifikaciji. Inspirisan je Frontiers pattern-om: PDF/Share/DOI uvek vidljivi dok se posetilac kreće po article landing stranici.

**FR Pokrivenost:**
- FR42: Posetilac može preuzeti PDF članka (pripremamo dugme, sama download logika je Story 4.6)
- FR41: Posetilac može videti landing stranicu članka (upotpunjujemo iskustvo sa floating akcijama)

**NFR Pokrivenost:**
- NFR1: Landing stranica članka - First Contentful Paint < 3 sekunde (floating bar ne sme dodati blocking JS)
- NFR14-NFR18: Accessibility (keyboard navigacija, ARIA labels, focus states, touch targets)

**Zavisnosti (sve DONE):**
- Story 4.4: Article Landing Page - `article_detail.html`, `ArticleLandingView`, `portal.css`, context varijable (`full_doi`, `doi_url`, `is_withdrawn`, `article`)
- Story 4.1: Portal Home Page - `portal/base.html`, portal nav, `portal.css`
- Story 3.3: PDF Upload - `Article.pdf_file` FileField, `Article.pdf_status` field

**Blokira:**
- Story 4.6: PDF Download - koristiće PDF dugme iz floating action bar-a (dodaje URL i download logiku)
- Story 4.7: Citation Modal - koristiće Cite dugme iz floating action bar-a (dodaje modal sa formatima). **Napomena:** Cite dugme je namerno placeholder u ovom story-ju; Epic AC "Cite button opens citation modal" se ispunjava tek kad Story 4.7 bude implementirana.

**NAPOMENA:** Ova priča kreira VIZUELNU KOMPONENTU sa placeholder akcijama. PDF download dugme NEĆE implementirati pravi download (to je Story 4.6). Cite dugme NEĆE otvarati pravi citation modal (to je Story 4.7). Share i Copy DOI dugmad su KOMPLETNA u ovom story-ju.

## Acceptance Criteria

1. **Given** posetilac je na article landing stranici
   **When** pregleda stranicu
   **Then** floating action bar je prikazan
   **And** na desktopu: fixed pozicija na desnoj strani (`position: fixed`)
   **And** na mobilnom: fixed pozicija na dnu (`position: fixed; bottom: 0`)

2. **Given** floating action bar sadrzi akcije
   **When** posetilac pregleda dostupne akcije
   **Then** PDF download dugme je prominentno (primary stil)
   **And** Cite dugme je vidljivo (placeholder do Story 4.7)
   **And** Share dugme prikazuje opcije deljenja
   **And** Copy DOI dugme kopira DOI u clipboard

3. **Given** članak nema PDF (withdrawn ili nije uploadovan)
   **When** posetilac pregleda PDF dugme
   **Then** dugme je onemogućeno (disabled) sa tooltip objašnjenjem

4. **Given** posetilac klikne Share
   **When** opcije deljenja se pojave
   **Then** opcije uključuju: Kopiraj link, Email, Twitter/X, LinkedIn
   **And** na mobilnom se koristi native share sheet (ako je dostupan via navigator.share API)

5. **Given** posetilac skroluje stranicu
   **When** floating bar pozicija se menja
   **Then** bar ostaje vidljiv i pristupačan
   **And** ne prekriva sadržaj

6. **Given** posetilac koristi tastaturu
   **When** navigira kroz floating bar
   **Then** sve dugmad su dostupna putem Tab navigacije
   **And** focus states su jasno vidljivi
   **And** tooltips su prisutni za sve ikonice

7. **Given** posetilac klikne Copy DOI
   **When** DOI je kopiran u clipboard
   **Then** dugme privremeno prikazuje potvrdu "Kopirano!"
   **And** nakon 2 sekunde vraća se na originalni tekst

8. **Given** posetilac klikne Cite dugme
   **When** trenutno nema citation modal (Story 4.7)
   **Then** dugme prikazuje tooltip "Citiranje uskoro dostupno"
   **And** dugme je vizuelno dostupno ali funkcionalnost je placeholder
   > **Napomena:** Epic AC navodi "Cite button opens citation modal", ali je ovde namerno implementiran kao placeholder. Puni citation modal sa formatima (APA, BibTeX, itd.) je odgovornost Story 4.7 koja zavisi od ovog story-ja. Ovo je planirano razdvajanje odgovornosti, ne odstupanje od Epic AC.

9. **Given** posetilac klikne PDF dugme na članku sa PDF-om
   **When** trenutno nema download logika (Story 4.6)
   **Then** dugme prikazuje tooltip "Preuzimanje uskoro dostupno"
   **And** dugme je vizuelno dostupno (primary stil) ali funkcionalnost je placeholder

10. **Given** stranica je učitana na mobilnom uređaju
    **When** floating bar je prikazan na dnu
    **Then** touch targets su minimum 44x44px
    **And** bar ne prekriva footer ili kritične metapodatke

## Tasks / Subtasks

- [x] Task 1: Ažurirati `ArticleLandingView` context sa PDF dostupnošću (AC: #3, #9)
  - [x] 1.1 U `portal/views.py`, `ArticleLandingView.get_context_data()`, dodati `has_pdf` boolean u context
  - [x] 1.2 `has_pdf` = `bool(article.pdf_file)` i `not is_withdrawn` (withdrawn članci nemaju dostupan PDF)
  - [x] 1.3 Dodati `share_url` u context: pun kanonski URL article landing stranice za share funkcije (koristi se u Alpine.js `floatingActionBar({ shareUrl })` umesto `window.location.href` - daje server-side kontrolu nad kanoničkim URL-om)

- [x] Task 2: Kreirati `_floating_action_bar.html` partial (AC: #1, #2, #3, #5, #6, #8, #9)
  - [x] 2.1 Kreirati `portal/partials/_floating_action_bar.html` partial template
  - [x] 2.2 Wrapper: `<nav class="floating-action-bar" aria-label="Akcije za članak" role="navigation">`
  - [x] 2.3 PDF dugme: `<button>` sa `btn-primary`, ikonica `bi-file-earmark-pdf`, disabled ako `not has_pdf`, tooltip objašnjenje
  - [x] 2.4 Cite dugme: `<button>` sa `btn-outline-secondary`, ikonica `bi-quote`, tooltip "Citiranje uskoro dostupno"
  - [x] 2.5 Share dugme: `<button>` sa `btn-outline-secondary`, ikonica `bi-share`, Alpine.js `@click` za share dropdown
  - [x] 2.6 Copy DOI dugme: `<button>` sa `btn-outline-secondary`, ikonica `bi-clipboard`, Alpine.js `@click` za clipboard copy
  - [x] 2.7 Share dropdown: lista sa opcijama (Kopiraj link, Email, Twitter/X, LinkedIn)
  - [x] 2.8 Svi dugmadi imaju `aria-label` atribute i `title` tooltips
  - [x] 2.9 Srpski tekst za sve labele i tooltips

- [x] Task 3: Uključiti partial u `article_detail.html` (AC: #1, #5)
  - [x] 3.1 Dodati `{% include "portal/partials/_floating_action_bar.html" %}` pre zatvaranja `{% endblock portal_content %}`
  - [x] 3.2 Proslediti context varijable: `full_doi`, `doi_url`, `has_pdf`, `is_withdrawn`, `article`

- [x] Task 4: Implementirati Alpine.js interaktivnost (AC: #4, #7, #8, #9)
  - [x] 4.1 Share dropdown: `x-data="{ open: false }"` sa `@click` toggle i `@click.outside` zatvaranje
  - [x] 4.2 Copy DOI: koristi `this.doi` iz x-data inicijalizacije, `navigator.clipboard.writeText()` sa fallback za starije browsere
  - [x] 4.3 Copy DOI feedback: `x-data` sa `copied` state, privremeni "Kopirano!" tekst za 2s
  - [x] 4.4 Copy link: kopira `this.shareUrl` (kanonski URL iz server konteksta) u clipboard
  - [x] 4.5 Email share: `mailto:?subject=...&body=...` sa URL-encoded naslovom i `this.shareUrl`
  - [x] 4.6 Twitter/X share: `https://twitter.com/intent/tweet?url=...&text=...` koristi `this.shareUrl`
  - [x] 4.7 LinkedIn share: `https://www.linkedin.com/sharing/share-offsite/?url=...` koristi `this.shareUrl`
  - [x] 4.8 Native share API: `if (navigator.share)` za mobile, `navigator.share({ title, url: this.shareUrl })`
  - [x] 4.9 PDF i Cite dugmad: placeholder `@click` sa tooltip feedback (do Stories 4.6 i 4.7)

- [x] Task 5: Dodati CSS stilove za floating action bar (AC: #1, #5, #10)
  - [x] 5.1 Desktop: `position: fixed; right: 2rem; top: 50%; transform: translateY(-50%)` vertikalni bar
  - [x] 5.2 Desktop: `flex-direction: column; gap: 0.5rem; z-index: 1030` (ispod Bootstrap modala)
  - [x] 5.3 Mobile (< 992px): `position: fixed; bottom: 0; left: 0; right: 0` horizontalni bar
  - [x] 5.4 Mobile: `flex-direction: row; justify-content: space-around; padding: 0.75rem`
  - [x] 5.5 Mobile: `background: white; border-top: 1px solid var(--portal-border); box-shadow: 0 -2px 8px rgba(0,0,0,0.1)`
  - [x] 5.6 Dugmad: `min-width: 44px; min-height: 44px` (touch targets NFR17)
  - [x] 5.7 Desktop dugmad: okrugla (`border-radius: 50%`), 48x48px, sa tooltip-om
  - [x] 5.8 Hover/focus states: `box-shadow` efekat, `outline: 2px solid var(--portal-secondary)`
  - [x] 5.9 Share dropdown: apsolutno pozicioniran iznad/pored share dugmeta
  - [x] 5.10 `body` padding-bottom na mobilnom da floating bar ne prekriva footer content
  - [x] 5.11 Z-index strategija: bar na `1030`, dropdown na `1031` (ispod Bootstrap modal `1050`)

- [x] Task 6: Dodati `article_detail.html` body padding za mobile (AC: #5, #10)
  - [x] 6.1 Dodati `pb-5` ili custom padding na mobilnom za `portal_content` blok da bar ne prekriva zadnji sadržaj
  - [x] 6.2 CSS media query: `@media (max-width: 991.98px)` dodaje `padding-bottom` na main content

- [x] Task 7: Kreirati testove (AC: #1-#10)
  - [x] 7.1 View test: context sadrži `has_pdf` = True za članak sa PDF-om
  - [x] 7.2 View test: context sadrži `has_pdf` = False za članak bez PDF-a
  - [x] 7.3 View test: context sadrži `has_pdf` = False za WITHDRAWN članak (čak i sa PDF-om)
  - [x] 7.4 View test: response sadrži `floating-action-bar` klasu u HTML-u
  - [x] 7.5 View test: response sadrži PDF dugme sa `disabled` atributom za članak bez PDF-a
  - [x] 7.6 View test: response sadrži PDF dugme BEZ `disabled` atributa za članak sa PDF-om (non-withdrawn)
  - [x] 7.7 View test: response sadrži Copy DOI dugme; DOI vrednost se prosleđuje kroz `floatingActionBar({ doi: '...' })` x-data inicijalizaciju
  - [x] 7.8 View test: response sadrži share dugme
  - [x] 7.9 View test: response sadrži cite dugme
  - [x] 7.10 View test: response sadrži `aria-label` na floating bar nav elementu
  - [x] 7.11 View test: WITHDRAWN članak ima disabled PDF dugme

## Dev Notes

### KRITIČNO: Ovo je Custom UI Komponenta #4 iz UX Specifikacije

Floating Action Bar je definisan u UX Design specifikaciji kao jedna od 10 custom komponenti za MVP. Inspirisan Frontiers pattern-om: PDF/Share/DOI uvek vidljivi dok korisnik skroluje.

**Key Design Decisions:**
- Desktop: Vertikalni bar, fixed desno, okrugla dugmad (FAB stil)
- Mobile: Horizontalni bar, fixed na dnu, full-width
- Z-index: 1030 (ispod Bootstrap modala koji je 1050)
- Interaktivnost: Alpine.js za share dropdown i clipboard copy (Alpine.js je VEĆ uključen u `base.html`)
- Placeholder dugmad za PDF i Cite: vizuelno prisutna, funkcionalno čekaju Stories 4.6 i 4.7

### Postojeći Patterns koje MORAMO slediti

**Portal base.html pattern** (VEĆ implementirano):
- `{% extends "portal/base.html" %}` -> extends `base.html`
- Alpine.js 3.15.3 VEĆ uključen u `base.html` (linija 46-49)
- HTMX 2.0.8 VEĆ uključen u `base.html` (linija 52-55)
- Bootstrap Icons CDN VEĆ uključen u `portal/base.html`
- `portal.css` VEĆ učitan u `portal/base.html`

**HTMX Partial naming**: `_` prefix za sve partials - koristiti `_floating_action_bar.html`

**Article detail context** (VEĆ dostupno iz Story 4.4):
- `article` - Article objekat sa svim related data
- `full_doi` - string, npr. "10.9999/test-001"
- `doi_url` - string, npr. "https://doi.org/10.9999/test-001"
- `is_withdrawn` - boolean
- Dodajemo: `has_pdf` - boolean (nova context varijabla)
- Dodajemo: `share_url` - string, kanonski URL članka (koristi se u Alpine.js umesto `window.location.href` za server-side kontrolu URL-a)

### View Ažuriranje

```python
# portal/views.py - ArticleLandingView.get_context_data()
# DODATI nakon postojećih context varijabli:

context["has_pdf"] = bool(article.pdf_file) and article.status != ArticleStatus.WITHDRAWN
```

**NAPOMENA o has_pdf logici:**
- `bool(article.pdf_file)` proverava da li je FileField prazan ili ne
- WITHDRAWN članci NE smeju imati dostupan PDF download (per Story 3.7 AC: "PDF may be removed or retained (configurable)")
- Za sada koristimo konzervativni pristup: withdrawn = no PDF
- Story 4.6 će implementirati finu logiku za download

### Floating Action Bar Partial: `_floating_action_bar.html`

```html
{% comment %}
Floating Action Bar - Custom UI Component #4
Story 4.5: Quick access to PDF, citation, sharing, and DOI copy.
Included in article_detail.html. Requires Alpine.js (available in base.html).
Context: article, full_doi, doi_url, has_pdf, is_withdrawn
{% endcomment %}
<nav class="floating-action-bar"
     aria-label="Akcije za članak"
     role="navigation"
     x-data="floatingActionBar({ doi: '{{ full_doi }}', shareUrl: '{{ share_url }}' })">

  <!-- PDF Download Button (placeholder - Story 4.6) -->
  <button type="button"
          class="btn btn-primary fab-btn"
          {% if not has_pdf %}disabled{% endif %}
          title="{% if has_pdf %}Preuzmi PDF{% else %}PDF nije dostupan{% endif %}"
          aria-label="{% if has_pdf %}Preuzmi PDF{% else %}PDF nije dostupan{% endif %}"
          @click="handlePdfClick()">
    <i class="bi bi-file-earmark-pdf-fill" aria-hidden="true"></i>
    <span class="fab-label d-lg-none">PDF</span>
  </button>

  <!-- Cite Button (placeholder - Story 4.7) -->
  <button type="button"
          class="btn btn-outline-secondary fab-btn"
          title="Citiranje uskoro dostupno"
          aria-label="Citiraj članak"
          @click="handleCiteClick()">
    <i class="bi bi-quote" aria-hidden="true"></i>
    <span class="fab-label d-lg-none">Citiraj</span>
  </button>

  <!-- Share Button -->
  <div class="fab-share-wrapper" style="position: relative;">
    <button type="button"
            class="btn btn-outline-secondary fab-btn"
            title="Podeli članak"
            aria-label="Podeli članak"
            aria-expanded="false"
            :aria-expanded="shareOpen.toString()"
            @click="handleShare()">
      <i class="bi bi-share" aria-hidden="true"></i>
      <span class="fab-label d-lg-none">Podeli</span>
    </button>

    <!-- Share Dropdown -->
    <div class="fab-share-dropdown"
         x-show="shareOpen"
         x-transition
         @click.outside="shareOpen = false"
         role="menu"
         aria-label="Opcije deljenja">
      <button type="button" class="fab-share-option" role="menuitem"
              @click="copyLink()" aria-label="Kopiraj link">
        <i class="bi bi-link-45deg" aria-hidden="true"></i> Kopiraj link
      </button>
      <a href="#" class="fab-share-option" role="menuitem"
         :href="emailShareUrl" aria-label="Podeli putem e-pošte">
        <i class="bi bi-envelope" aria-hidden="true"></i> E-pošta
      </a>
      <a :href="twitterShareUrl" class="fab-share-option" role="menuitem"
         target="_blank" rel="noopener noreferrer" aria-label="Podeli na Twitter/X">
        <i class="bi bi-twitter-x" aria-hidden="true"></i> Twitter/X
      </a>
      <a :href="linkedinShareUrl" class="fab-share-option" role="menuitem"
         target="_blank" rel="noopener noreferrer" aria-label="Podeli na LinkedIn">
        <i class="bi bi-linkedin" aria-hidden="true"></i> LinkedIn
      </a>
    </div>
  </div>

  <!-- Copy DOI Button -->
  <button type="button"
          class="btn btn-outline-secondary fab-btn"
          :title="doiCopied ? 'Kopirano!' : 'Kopiraj DOI'"
          :aria-label="doiCopied ? 'DOI kopiran' : 'Kopiraj DOI: {{ full_doi }}'"
          @click="copyDoi()">
    <i :class="doiCopied ? 'bi bi-check-lg text-success' : 'bi bi-clipboard'" aria-hidden="true"></i>
    <span class="fab-label d-lg-none" x-text="doiCopied ? 'Kopirano!' : 'DOI'"></span>
  </button>
</nav>
```

### Alpine.js Komponenta

```javascript
// Inline u _floating_action_bar.html ili u <script> bloku
function floatingActionBar({ doi = '', shareUrl = '' } = {}) {
  return {
    doi: doi,
    shareUrl: shareUrl,
    shareOpen: false,
    doiCopied: false,

    get emailShareUrl() {
      const subject = encodeURIComponent(document.title);
      const body = encodeURIComponent(this.shareUrl);
      return `mailto:?subject=${subject}&body=${body}`;
    },

    get twitterShareUrl() {
      const text = encodeURIComponent(document.title);
      const url = encodeURIComponent(this.shareUrl);
      return `https://twitter.com/intent/tweet?text=${text}&url=${url}`;
    },

    get linkedinShareUrl() {
      const url = encodeURIComponent(this.shareUrl);
      return `https://www.linkedin.com/sharing/share-offsite/?url=${url}`;
    },

    async handleShare() {
      // Use native share API on mobile if available
      if (navigator.share) {
        try {
          await navigator.share({
            title: document.title,
            url: this.shareUrl,
          });
          return;
        } catch (e) {
          // User cancelled or error - fall through to dropdown
        }
      }
      this.shareOpen = !this.shareOpen;
    },

    async copyLink() {
      await this.copyToClipboard(this.shareUrl);
      this.shareOpen = false;
    },

    async copyDoi() {
      await this.copyToClipboard(this.doi);
      this.doiCopied = true;
      setTimeout(() => { this.doiCopied = false; }, 2000);
    },

    async copyToClipboard(text) {
      try {
        await navigator.clipboard.writeText(text);
      } catch {
        // Fallback for older browsers
        const ta = document.createElement('textarea');
        ta.value = text;
        ta.style.position = 'fixed';
        ta.style.opacity = '0';
        document.body.appendChild(ta);
        ta.select();
        document.execCommand('copy');
        document.body.removeChild(ta);
      }
    },

    handlePdfClick() {
      // Placeholder - Story 4.6 će dodati pravi download
      // Trenutno ne radi ništa za enabled dugme
    },

    handleCiteClick() {
      // Placeholder - Story 4.7 će dodati citation modal
      // Trenutno ne radi ništa
    },
  };
}
```

### CSS Stilovi za Floating Action Bar

```css
/* ===========================
   Floating Action Bar (Story 4.5)
   =========================== */

/* Desktop: Vertikalni bar na desnoj strani */
.floating-action-bar {
    position: fixed;
    right: 2rem;
    top: 50%;
    transform: translateY(-50%);
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
    z-index: 1030;
    padding: 0.75rem;
    background: white;
    border-radius: 2rem;
    box-shadow: 0 2px 12px rgba(0, 0, 0, 0.15);
    border: 1px solid var(--portal-border);
}

/* FAB dugmad - okrugla na desktopu.
   Na desktopu, flex-direction je default (row) - ovo je namerno jer je .fab-label
   skriven (d-lg-none), pa samo ikonica ostaje centrirana. Na mobilnom se
   eksplicitno postavlja flex-direction: column (videti media query ispod). */
.fab-btn {
    width: 48px;
    height: 48px;
    min-width: 44px;
    min-height: 44px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 1.25rem;
    padding: 0;
    position: relative;
}

.fab-btn:focus-visible {
    outline: 2px solid var(--portal-secondary);
    outline-offset: 2px;
}

.fab-btn:disabled {
    opacity: 0.5;
    cursor: not-allowed;
}

/* Label vidljiv samo na mobilnom */
.fab-label {
    font-size: 0.7rem;
    margin-left: 0.25rem;
}

/* Share dropdown */
.fab-share-dropdown {
    position: absolute;
    left: -200px;
    top: 50%;
    transform: translateY(-50%);
    background: white;
    border: 1px solid var(--portal-border);
    border-radius: 0.5rem;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
    min-width: 180px;
    z-index: 1031;
    padding: 0.5rem 0;
}

.fab-share-option {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0.5rem 1rem;
    width: 100%;
    border: none;
    background: none;
    color: var(--portal-text);
    text-decoration: none;
    font-size: 0.875rem;
    cursor: pointer;
    text-align: left;
}

.fab-share-option:hover {
    background-color: var(--portal-bg-secondary);
    color: var(--portal-primary);
}

/* Mobile: Horizontalni bar na dnu */
@media (max-width: 991.98px) {
    .floating-action-bar {
        position: fixed;
        bottom: 0;
        left: 0;
        right: 0;
        top: auto;
        transform: none;
        flex-direction: row;
        justify-content: space-around;
        border-radius: 0;
        padding: 0.75rem 1rem;
        border-top: 1px solid var(--portal-border);
        box-shadow: 0 -2px 8px rgba(0, 0, 0, 0.1);
        gap: 0;
    }

    .fab-btn {
        width: auto;
        height: auto;
        min-width: 44px;
        min-height: 44px;
        border-radius: 0.5rem;
        font-size: 1rem;
        padding: 0.5rem 0.75rem;
        flex-direction: column;
        gap: 0.125rem;
    }

    .fab-label {
        display: block !important;
        margin-left: 0;
    }

    /* Share dropdown na mobilnom - iznad dugmeta */
    .fab-share-dropdown {
        left: 50%;
        transform: translateX(-50%);
        top: auto;
        bottom: 100%;
        margin-bottom: 0.5rem;
    }

    /* Padding na main content da bar ne prekriva sadržaj */
    .portal-content {
        padding-bottom: 5rem;
    }
}
```

### Ažuriranje article_detail.html

Dodati include PRED zatvaranje `{% endblock portal_content %}`:

```html
<!-- Pre </aside> closing div i endblock -->
</div>

<!-- Floating Action Bar (Story 4.5) -->
{% include "portal/partials/_floating_action_bar.html" %}
{% endblock portal_content %}
```

### Srpski Karakteri (OBAVEZNO - videti project-context.md)

| Kontekst | ISPRAVNO |
|----------|----------|
| Nav aria-label | "Akcije za članak" |
| PDF tooltip (enabled) | "Preuzmi PDF" |
| PDF tooltip (disabled) | "PDF nije dostupan" |
| Cite tooltip | "Citiranje uskoro dostupno" |
| Cite label | "Citiraj" |
| Share tooltip | "Podeli članak" |
| Share label | "Podeli" |
| Copy DOI tooltip | "Kopiraj DOI" |
| DOI copied feedback | "Kopirano!" |
| DOI copied aria | "DOI kopiran" |
| Copy link | "Kopiraj link" |
| Email | "E-pošta" |
| Share options aria | "Opcije deljenja" |

### Previous Story Learnings (Story 4.4 + Story 4.3 + Story 4.2)

1. **Portal base.html pattern**: Extends `portal/base.html`, koristi `{% block portal_content %}`, breadcrumbs se automatski renderuju iz context varijable.
2. **Alpine.js VEĆ dostupan**: `base.html` uključuje Alpine.js 3.15.3 CDN sa `defer` - NE dodavati ponovo.
3. **HTMX VEĆ dostupan**: `base.html` uključuje HTMX 2.0.8 CDN - NE dodavati ponovo.
4. **Bootstrap Icons**: VEĆ uključeni u `portal/base.html` kao CDN. Koristiti `bi-*` klase.
5. **Portal CSS**: `static/css/portal.css` - VEĆ učitan u `portal/base.html`. Dodati floating-action-bar stilove u OVAJ fajl.
6. **DetailView context**: `ArticleLandingView.get_context_data()` VEĆ ima `article`, `full_doi`, `doi_url`, `is_withdrawn`.
7. **Test pattern**: pytest-django, `@pytest.mark.django_db`, Factory Boy. `ArticleFactory`, `IssueFactory`, `PublicationFactory`, `PublisherFactory` su VEĆ dostupni.
8. **SoftDeleteManager**: Automatski filtrira soft-deleted zapise.
9. **Article.pdf_file**: FileField sa `upload_to="articles/pdfs/"`, `blank=True`. `bool(article.pdf_file)` = True ako fajl postoji.
10. **Article.pdf_status**: CharField sa PdfStatus choices - ali za has_pdf provjeru dovoljno je `bool(pdf_file)`.
11. **ArticleStatus**: DRAFT, REVIEW, READY, PUBLISHED, WITHDRAWN - VEĆ importovan u `portal/views.py`.
12. **Partial prefix**: Svi HTMX/include partials imaju `_` prefix. Floating bar: `_floating_action_bar.html`.
13. **Test suite**: Story 4.4 ima 1177 passed, 3 skipped. Ne smemo imati regresije.
14. **Z-index Bootstrap**: Modal = 1050, Dropdown = 1000, Sticky = 1020, Fixed = 1030. Floating bar = 1030 je OK.

### Git Commit Pattern

```
story-4-5: feat(portal): implementiraj Floating Action Bar sa PDF/Share/Cite/DOI akcijama na article landing page (Story 4.5)
```

### Fajlovi za kreiranje (NOVI)

```
doi_portal/doi_portal/templates/portal/partials/_floating_action_bar.html  # Floating Action Bar partial template
doi_portal/doi_portal/portal/tests/test_floating_action_bar.py             # Floating Action Bar testovi
```

### Fajlovi za modifikaciju (POSTOJEĆI)

```
doi_portal/doi_portal/portal/views.py                                      # Dodati has_pdf u ArticleLandingView context
doi_portal/doi_portal/templates/portal/article_detail.html                 # Dodati include za floating action bar
doi_portal/doi_portal/static/css/portal.css                                # Dodati floating action bar stilove
```

### Fajlovi koji se NE MENJAJU

```
doi_portal/doi_portal/templates/portal/base.html                           # VEĆ postoji - NE MENJATI
doi_portal/doi_portal/templates/base.html                                  # VEĆ postoji - NE MENJATI (Alpine.js VEĆ uključen)
doi_portal/doi_portal/portal/services.py                                   # NE MENJATI - nema novih servisnih funkcija
doi_portal/doi_portal/portal/urls_articles.py                              # VEĆ postoji - NE MENJATI
doi_portal/doi_portal/articles/models.py                                   # VEĆ postoji - NE MENJATI
doi_portal/config/urls.py                                                  # VEĆ postoji - NE MENJATI
```

### Anti-Patterns (ZABRANJENO)

```python
# POGREŠNO - Dodavati Alpine.js CDN ponovo u template
<script src="alpinejs..."></script>  # NE! VEĆ je u base.html

# POGREŠNO - Koristiti jQuery umesto Alpine.js
$('.fab-btn').click(...)  # NE! Koristiti Alpine.js x-data

# POGREŠNO - Koristiti position: absolute umesto fixed za floating bar
position: absolute;  # NE! Fixed je potreban da bar prati scroll

# POGREŠNO - Staviti inline script u partial bez Alpine.js function pattern
<script>document.querySelector(...)...</script>  # NE! Koristiti Alpine.js component

# POGREŠNO - Implementirati pravi PDF download u ovom story-ju
def pdf_download(request, pk):  # NE! To je Story 4.6

# POGREŠNO - Implementirati pravi citation modal u ovom story-ju
class CitationModal:  # NE! To je Story 4.7

# POGREŠNO - Koristiti position: fixed bez z-index strategije
z-index: 9999;  # NE! Koristiti Bootstrap z-index scale (1030)

# POGREŠNO - Zaboraviti touch targets na mobilnom
width: 32px; height: 32px;  # NE! Minimum 44x44px (NFR17)

# POGREŠNO - Blocking JS koji usporava FCP
<script src="heavy-library.js"></script>  # NE! Koristiti defer ili Alpine.js inline

# POGREŠNO - Zaboraviti srpske karaktere sa dijakriticima
"Podeli clanak"  # POGREŠNO!
"Podeli članak"  # ISPRAVNO!

# POGREŠNO - Hardcoded DOI u JavaScript
const doi = "10.9999/test-001";  # NE! Koristiti x-data inicijalizaciju: floatingActionBar({ doi: '{{ full_doi }}' })

# POGREŠNO - Ne koristiti ARIA atribute na interactive elementima
<button @click="...">  # NE! Dodati aria-label, title, role
```

### Performance (NFR1 - FCP < 3s)

```
# Floating action bar NE SME usporiti FCP:
# 1. Alpine.js je VEĆ učitan sa defer - nema dodatnog JS load-a
# 2. CSS je u portal.css - VEĆ učitan
# 3. Nema dodatnih HTTP zahteva za floating bar
# 4. Nema blocking JavaScript
# 5. Inline Alpine.js function je minimalna
```

### Accessibility (NFR14-NFR18)

```html
<!-- Nav landmark sa aria-label -->
<nav aria-label="Akcije za članak" role="navigation">

<!-- Dugmad sa aria-label i title -->
<button aria-label="Preuzmi PDF" title="Preuzmi PDF">

<!-- Disabled state sa aria-disabled -->
<button disabled aria-label="PDF nije dostupan">

<!-- Focus visible -->
.fab-btn:focus-visible { outline: 2px solid ...; }

<!-- Touch targets -->
min-width: 44px; min-height: 44px;

<!-- Share dropdown role -->
<div role="menu" aria-label="Opcije deljenja">
  <button role="menuitem">
```

### Test Pattern

```python
# portal/tests/test_floating_action_bar.py

import pytest
from django.urls import reverse

from doi_portal.articles.models import ArticleStatus
from doi_portal.articles.tests.factories import ArticleFactory
from doi_portal.issues.models import IssueStatus
from doi_portal.issues.tests.factories import IssueFactory
from doi_portal.publications.tests.factories import PublicationFactory
from doi_portal.publishers.tests.factories import PublisherFactory


@pytest.mark.django_db
class TestFloatingActionBarContext:
    """Tests for floating action bar context variables."""

    def _create_article(self, status=ArticleStatus.PUBLISHED, has_pdf=False):
        publisher = PublisherFactory(doi_prefix="10.9999")
        pub = PublicationFactory(publisher=publisher)
        issue = IssueFactory(publication=pub, status=IssueStatus.PUBLISHED)
        article = ArticleFactory(
            issue=issue,
            doi_suffix="fab-test-001",
            status=status,
        )
        if has_pdf:
            article.pdf_file = "articles/pdfs/test.pdf"
            article.save()
        return article

    def test_has_pdf_true_for_published_with_pdf(self, client):
        article = self._create_article(status=ArticleStatus.PUBLISHED, has_pdf=True)
        response = client.get(reverse("portal-articles:article-detail", kwargs={"pk": article.pk}))
        assert response.context["has_pdf"] is True

    def test_has_pdf_false_for_published_without_pdf(self, client):
        article = self._create_article(status=ArticleStatus.PUBLISHED, has_pdf=False)
        response = client.get(reverse("portal-articles:article-detail", kwargs={"pk": article.pk}))
        assert response.context["has_pdf"] is False

    def test_has_pdf_false_for_withdrawn_with_pdf(self, client):
        article = self._create_article(status=ArticleStatus.WITHDRAWN, has_pdf=True)
        response = client.get(reverse("portal-articles:article-detail", kwargs={"pk": article.pk}))
        assert response.context["has_pdf"] is False


@pytest.mark.django_db
class TestFloatingActionBarRendering:
    """Tests for floating action bar HTML rendering."""

    def _create_published_article(self, has_pdf=False):
        publisher = PublisherFactory(doi_prefix="10.9999")
        pub = PublicationFactory(publisher=publisher)
        issue = IssueFactory(publication=pub, status=IssueStatus.PUBLISHED)
        article = ArticleFactory(
            issue=issue,
            doi_suffix="fab-render-001",
            status=ArticleStatus.PUBLISHED,
        )
        if has_pdf:
            article.pdf_file = "articles/pdfs/test.pdf"
            article.save()
        return article

    def test_floating_bar_present_in_response(self, client):
        article = self._create_published_article()
        response = client.get(reverse("portal-articles:article-detail", kwargs={"pk": article.pk}))
        assert "floating-action-bar" in response.content.decode()

    def test_pdf_button_disabled_without_pdf(self, client):
        article = self._create_published_article(has_pdf=False)
        response = client.get(reverse("portal-articles:article-detail", kwargs={"pk": article.pk}))
        content = response.content.decode()
        assert "disabled" in content
        assert "PDF nije dostupan" in content

    def test_pdf_button_enabled_with_pdf(self, client):
        article = self._create_published_article(has_pdf=True)
        response = client.get(reverse("portal-articles:article-detail", kwargs={"pk": article.pk}))
        content = response.content.decode()
        assert "Preuzmi PDF" in content

    def test_copy_doi_button_present(self, client):
        article = self._create_published_article()
        response = client.get(reverse("portal-articles:article-detail", kwargs={"pk": article.pk}))
        content = response.content.decode()
        # DOI is passed via x-data initialization, not data-doi attribute
        assert "floatingActionBar(" in content
        assert "10.9999/fab-render-001" in content

    def test_share_url_in_context(self, client):
        article = self._create_published_article()
        response = client.get(reverse("portal-articles:article-detail", kwargs={"pk": article.pk}))
        assert "share_url" in response.context

    def test_share_button_present(self, client):
        article = self._create_published_article()
        response = client.get(reverse("portal-articles:article-detail", kwargs={"pk": article.pk}))
        assert "bi-share" in response.content.decode()

    def test_cite_button_present(self, client):
        article = self._create_published_article()
        response = client.get(reverse("portal-articles:article-detail", kwargs={"pk": article.pk}))
        assert "bi-quote" in response.content.decode()

    def test_floating_bar_has_aria_label(self, client):
        article = self._create_published_article()
        response = client.get(reverse("portal-articles:article-detail", kwargs={"pk": article.pk}))
        content = response.content.decode()
        assert 'aria-label="Akcije za' in content

    def test_withdrawn_article_has_disabled_pdf(self, client):
        publisher = PublisherFactory(doi_prefix="10.9999")
        pub = PublicationFactory(publisher=publisher)
        issue = IssueFactory(publication=pub, status=IssueStatus.PUBLISHED)
        article = ArticleFactory(
            issue=issue,
            doi_suffix="fab-withdrawn-001",
            status=ArticleStatus.WITHDRAWN,
        )
        article.pdf_file = "articles/pdfs/test.pdf"
        article.save()
        response = client.get(reverse("portal-articles:article-detail", kwargs={"pk": article.pk}))
        content = response.content.decode()
        assert "disabled" in content
        assert "PDF nije dostupan" in content
```

### Dependencies (Python/Django)

Nema novih Python zavisnosti! Sve je već instalirano:
- Django 5.2+ (DetailView context, templates, include)
- Bootstrap 5 (CSS framework - fixed positioning, buttons, tooltips)
- Bootstrap Icons (već uključeni u portal/base.html CDN)
- Alpine.js 3.15.3 (već uključen u base.html CDN - x-data, @click, x-show)
- pytest-django + Factory Boy (već u test setup-u)

### NFR Requirements

- **FR41:** Upotpunjujemo Article Landing Page sa interactive floating akcijama
- **FR42:** Pripremamo PDF download dugme (placeholder do Story 4.6)
- **NFR1:** FCP < 3 sekunde - nema blocking JS, Alpine.js već učitan sa defer
- **NFR14:** Semantički HTML5 - `<nav>`, `role="navigation"`, `role="menu"`, `role="menuitem"`
- **NFR15:** Aria labels za sve interaktivne elemente
- **NFR16:** Kontrast 4.5:1 - Bootstrap 5 default paleta
- **NFR17:** Touch targets minimum 44x44px - na svim dugmadima
- **NFR18:** Keyboard navigacija - Tab through all buttons, focus-visible states

### References

- [Source: epics.md#Story 4.5: Floating Action Bar]
- [Source: epics.md#Epic 4: Public Portal Experience]
- [Source: ux-design-specification.md#Custom Components - 4. Floating Action Bar]
- [Source: ux-design-specification.md#Layout Adaptations - Floating action bar: Fixed right na desktop, Fixed bottom na mobile]
- [Source: ux-design-specification.md#Journey 3: Posetilac pristupa članku - PDF dugme uvek vidljivo (floating bar)]
- [Source: ux-design-specification.md#Inspiring Products - Frontiers: Floating actions, PDF download, share, DOI link uvek vidljivi]
- [Source: ux-design-specification.md#Design Inspiration Strategy - Adopt: Floating action bar za PDF/Share/DOI (Frontiers)]
- [Source: ux-design-specification.md#Accessibility Strategy - Touch targets min 44x44px, Focus visible]
- [Source: architecture.md#Frontend Architecture - Alpine.js 3.15.3, HTMX 2.0.8, Bootstrap 5]
- [Source: architecture.md#Alpine.js Patterns - x-data function pattern]
- [Source: project-context.md#HTMX Pravila - partials sa _ prefix]
- [Source: project-context.md#Naming Konvencije - snake_case, kebab-case]
- [Source: project-context.md#Lokalizacija - Srpski Karakteri, sr-Latn]
- [Source: project-context.md#Testing (pytest-django) - Factory Boy]
- [Source: 4-4-article-landing-page.md - Previous story: article_detail.html, ArticleLandingView, portal.css patterns]
- [Source: portal/views.py - ArticleLandingView.get_context_data() existing context]
- [Source: portal/base.html - Alpine.js and Bootstrap Icons CDN already included]
- [Source: base.html - Alpine.js 3.15.3 and HTMX 2.0.8 CDN with defer]
- [Source: articles/models.py - Article.pdf_file FileField, Article.pdf_status]
- [Source: static/css/portal.css - Existing portal styles, CSS variables]

## Dev Agent Record

### Agent Model Used

Claude Opus 4.5 (claude-opus-4-5-20251101)

### Debug Log References

- TDD Red phase: 12/12 tests failed (KeyError: 'has_pdf', missing template content)
- TDD Green phase: 12/12 tests passed after implementation
- Full suite: 1231 passed, 3 skipped, 11 pre-existing failures (test_pdf_upload.py - articles.tasks module missing)
- Portal tests: 228 passed, 0 failures
- Zero regressions introduced

### Completion Notes List

1. Added `has_pdf` and `share_url` to ArticleLandingView context. `has_pdf` uses `bool(article.pdf_file) and status != WITHDRAWN`.
2. `share_url` uses `request.build_absolute_uri()` for canonical URL generation (server-side control).
3. Created floating action bar partial with Alpine.js `floatingActionBar()` component function inline in `<script>` tag.
4. All 4 buttons implemented: PDF (primary, disabled when no PDF), Cite (placeholder), Share (dropdown with 4 options + native API), Copy DOI (clipboard + 2s feedback).
5. Share dropdown includes: Copy link, Email (mailto:), Twitter/X (intent/tweet), LinkedIn (share-offsite).
6. Native share API (`navigator.share`) used as primary on mobile, falls back to dropdown.
7. CSS implements desktop vertical bar (fixed right, round buttons) and mobile horizontal bar (fixed bottom, full-width).
8. All touch targets >= 44x44px (NFR17). Z-index: bar=1030, dropdown=1031 (below Bootstrap modal 1050).
9. Mobile padding-bottom: 5rem on .portal-content to prevent floating bar from covering footer.
10. All ARIA labels in Serbian with proper diacritics. `role="navigation"`, `role="menu"`, `role="menuitem"` applied.
11. PDF and Cite buttons are visual placeholders - no download/modal logic (deferred to Stories 4.6 and 4.7).

### File List

**Created (NEW):**
- `doi_portal/doi_portal/templates/portal/partials/_floating_action_bar.html` - Floating Action Bar partial template with Alpine.js component
- `doi_portal/doi_portal/portal/tests/test_floating_action_bar.py` - 12 tests (4 context + 8 rendering)

**Modified (EXISTING):**
- `doi_portal/doi_portal/portal/views.py` - Added has_pdf, share_url to ArticleLandingView.get_context_data()
- `doi_portal/doi_portal/templates/portal/article_detail.html` - Added {% include %} for floating action bar partial
- `doi_portal/doi_portal/static/css/portal.css` - Added floating action bar CSS (desktop + mobile + share dropdown)
- `_bmad-output/implementation-artifacts/sprint-status.yaml` - Status: ready-for-dev -> review
- `_bmad-output/implementation-artifacts/4-5-floating-action-bar.md` - Task checkboxes marked, Dev Agent Record filled
