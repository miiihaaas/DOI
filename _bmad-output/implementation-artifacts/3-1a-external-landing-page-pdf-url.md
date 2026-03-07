# Story 3.1a: Podrška za eksterni landing page i PDF URL

Status: done

## Story

As an **Urednik/Administrator**,
I want **mogućnost da konfigurisem da DOI članka pokazuje na sajt izdavača umesto na portal**,
So that **izdavači koji imaju sopstveni sajt mogu koristiti portal za DOI registraciju dok čitaoci pristupaju članku na sajtu izdavača**.

## Background

Neki izdavači imaju sopstveni sajt gde objavljuju članke (npr. `casopisnvd.rs`). Trenutno portal podržava samo scenario gde landing stranica i PDF se nalaze na portalu (`publikacije.doi.rs`). Potrebno je omogućiti da DOI `<resource>` element u Crossref XML-u pokazuje na sajt izdavača.

**Ref:** docs/potrebne-ispravke.md, Sekcija 3
**Zavisnost:** Story 5-3a (Fix resource URL) — done

## Acceptance Criteria

1. **Given** otvorim formu za kreiranje/edit članka,
   **When** vidim sekciju za PDF/resource,
   **Then** postoji checkbox/switch "Članak se nalazi i na sajtu izdavača"

2. **Given** switch je isključen,
   **When** pregledam formu,
   **Then** polja za eksterni URL su skrivena

3. **Given** kliknem na switch da ga uključim,
   **When** se switch aktivira,
   **Then** prikazuju se polja za eksterni landing URL i PDF URL

4. **Given** switch je uključen i `external_landing_url` je prazan,
   **When** pokušam da sačuvam formu,
   **Then** dobijem validation error

5. **Given** switch je uključen i `external_landing_url` je popunjen,
   **When** se generiše Crossref XML,
   **Then** `<resource>` element sadrži vrednost iz `external_landing_url`

6. **Given** switch je isključen,
   **When** se generiše Crossref XML,
   **Then** `<resource>` element sadrži portal URL

7. **Given** članak ima `use_external_resource=True` i popunjen `external_landing_url`,
   **When** posetim landing stranicu članka na portalu,
   **Then** vidim link ka originalnom sajtu izdavača

8. **Given** članak ima `use_external_resource=True` i popunjen `external_pdf_url`,
   **When** posetim landing stranicu članka na portalu,
   **Then** vidim i link ka eksternom PDF-u

## Tasks

### Task 1: Model izmene

- [x] 1.1: Dodati nova polja na Article model
- [x] 1.2: Kreirati i primeniti migraciju

### Task 2: Form izmene

- [x] 2.1: Dodati nova 3 polja u ArticleForm
- [x] 2.2: use_external_resource kao CheckboxInput sa Bootstrap switch stilom
- [x] 2.3: external_landing_url i external_pdf_url kao URLInput
- [x] 2.4: Dodati custom clean() metodu sa whitespace strip-ovanjem

### Task 3: Template — Article forma

- [x] 3.1: Dodati switch checkbox (vidljiv u create i edit modu)
- [x] 3.2: Alpine.js x-show za toggle prikaz/skrivanje
- [x] 3.3: Info alert tekst kad su polja vidljiva

### Task 4: XML šabloni — uslovna resource logika

- [x] 4.1: journal_article.xml.j2 — uslovna logika
- [x] 4.2: conference_paper.xml.j2 — uslovna logika
- [x] 4.3: book_chapter.xml.j2 — uslovna logika

### Task 5: Portal landing page

- [x] 5.1: Prikazati link ka originalnom sajtu izdavača
- [x] 5.2: Prikazati link ka eksternom PDF-u

### Task 6: Testovi

- [x] 6.1: Model testovi — default vrednosti
- [x] 6.2: Form testovi — validacija switch + URL
- [x] 6.3: XML generation testovi — oba scenarija
- [x] 6.4: Landing page testovi
- [x] 6.5: XML escape test za URL sa ampersand-om

## Dev Notes

- Zavisnost na Story 5-3a: site_url mora biti u template context-u
- Alpine.js je već u projektu (CDN) — koristi x-show za toggle
- Max URL length 500
- Portal podaci ostaju kao backup

## Dev Agent Record

### Implementation Plan

- 3 nova polja na Article model + migracija
- ArticleForm proširena sa nova 3 polja, clean() validacija, __init__ za widget choices
- article_form.html: Alpine.js toggle sa x-show, vidljiv u create i edit modu
- Sva 3 XML šablona: uslovna logika za resource element
- Portal landing page: "Originalni izvor" sekcija sa eksternim linkovima
- 20 testova u test_external_resource.py

### Completion Notes

- 1614 testova prolazi, 0 failures
- Sva 3 XML šablona imaju istu uslovnu logiku
- Alpine.js toggle radi u create i edit modu
- Eksterni linkovi imaju rel="noopener noreferrer" za bezbednost
- PreValidationService dodato upozorenje za nekonzistentne eksterne resurse

### Code Review Follow-ups (resolved)

- [x] #1 HIGH: Eksterni resursi sekcija premestena van {% if is_edit %} bloka
- [x] #2 HIGH: clean() sada strip-uje whitespace iz external_landing_url
- [x] #3 MED: Dodato rel="noopener noreferrer" na eksterne linkove
- [x] #4 MED: PreValidationService dodato upozorenje za prazan external URL
- [x] #6 MED: Dodat test za XML escape URL-a sa ampersand-om
- [x] #7 LOW: Alpine.js x-data koristi form value umesto object value
- Skipped #5 (template renders fields manually by design), #8 (external_pdf_url forward-compatible)

## File List

- `doi_portal/doi_portal/articles/models.py` (modified) — 3 nova polja
- `doi_portal/doi_portal/articles/migrations/0007_add_external_resource_fields.py` (new) — migracija
- `doi_portal/doi_portal/articles/forms.py` (modified) — nova polja, clean(), widget config
- `doi_portal/doi_portal/templates/articles/article_form.html` (modified) — Alpine.js toggle UX
- `doi_portal/doi_portal/crossref/services.py` (modified) — context + pre-validation warning
- `doi_portal/doi_portal/crossref/templates/crossref/journal_article.xml.j2` (modified) — uslovna resource
- `doi_portal/doi_portal/crossref/templates/crossref/conference_paper.xml.j2` (modified) — uslovna resource
- `doi_portal/doi_portal/crossref/templates/crossref/book_chapter.xml.j2` (modified) — uslovna resource
- `doi_portal/doi_portal/templates/portal/article_detail.html` (modified) — eksterni linkovi
- `doi_portal/doi_portal/articles/tests/test_external_resource.py` (new) — 20 testova

## Change Log

- 2026-03-07: Story 3-1a implementirana — eksterni landing page i PDF URL podrška. 1614 testova prolazi.
- 2026-03-07: Code review — 6 nalaza rešeno (2 HIGH, 3 MED, 1 LOW). Bezbednost, validacija, UX poboljšanja.
