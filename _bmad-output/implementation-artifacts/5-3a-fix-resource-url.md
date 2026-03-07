# Story 5.3a: Fix `<resource>` URL u Crossref XML šablonima

Status: done

## Story

As an **Administrator**,
I want **`<resource>` element u Crossref XML-u da sadrži ispravan portal URL landing stranice članka**,
So that **DOI linkovi ispravno redirectuju čitaoce na landing stranicu umesto da stvaraju kružnu referencu**.

## Background

Crossref XML `<resource>` element definiše destinaciju — URL na koji Crossref redirectuje korisnika kada klikne na DOI link. Trenutno sva 3 XML šablona generišu `https://doi.org/{prefix}/{suffix}` kao resource URL, što stvara kružnu referencu: DOI link vodi na doi.org koji gleda `<resource>` da vidi gde da redirectuje, ali `<resource>` pokazuje na isti doi.org URL.

**Ispravan tok:**
```
Čitalac klikne DOI: doi.org/10.65845/...
        ↓
Crossref gleda <resource>
        ↓
<resource> = https://publikacije.doi.rs/articles/123/
        ↓
Čitalac vidi landing stranicu sa metapodacima i PDF-om
```

Ovo je KRITIČAN bug koji utiče na svaki registrovani DOI.

**Ref:** docs/potrebne-ispravke.md, Sekcija 2

## Acceptance Criteria

1. **Given** XML se generiše za journal article,
   **When** pregledam `<resource>` element u generisanom XML-u,
   **Then** sadrži portal URL formata `https://{site_domain}/articles/{article.pk}/`
   **And** NE sadrži `https://doi.org/` prefix

2. **Given** XML se generiše za conference paper,
   **When** pregledam `<resource>` element,
   **Then** sadrži isti portal URL format kao za journal article

3. **Given** XML se generiše za book chapter,
   **When** pregledam `<resource>` element,
   **Then** sadrži isti portal URL format kao za journal article

4. **Given** Django settings ima definisan `SITE_URL` ili koristi Sites framework,
   **When** se XML generiše,
   **Then** `site_url` varijabla je dostupna u template context-u
   **And** koristi se kao base URL za `<resource>` element

5. **Given** postojeći testovi za XML generisanje,
   **When** pokrenemo test suite,
   **Then** svi testovi prolaze sa novim URL formatom

## Tasks

### Task 1: Dodaj `site_url` u XML template context

- [x] 1.1: Odrediti izvor za site URL (Django Sites framework, settings.SITE_URL, ili environment variable)
- [x] 1.2: Proslediti `site_url` u Jinja2 template context u crossref service-u koji generiše XML
- [x] 1.3: Verifikovati da `site_url` nema trailing slash

### Task 2: Ažuriraj XML šablone

- [x] 2.1: `journal_article.xml.j2` (linija 126) — zameni `https://doi.org/{{ publisher.doi_prefix }}/{{ article.doi_suffix }}` sa `{{ site_url }}/articles/{{ article.pk }}/`
- [x] 2.2: `conference_paper.xml.j2` (linija 134) — ista izmena
- [x] 2.3: `book_chapter.xml.j2` (linija 111) — ista izmena

### Task 3: Ažuriraj testove

- [x] 3.1: Ažuriraj postojeće XML generation testove da očekuju novi URL format
- [x] 3.2: Dodaj test koji verifikuje da `<resource>` NE sadrži `doi.org`
- [x] 3.3: Dodaj test koji verifikuje da `site_url` je prisutan u template context-u

## Dev Notes

- Pogledaj kako je `site_url` rešen u portal views-u (npr. article landing page) za konzistentnost
- XML šabloni su Jinja2 (.j2), ne Django templates
- Crossref service je u `doi_portal/crossref/` app-u
- Ova story je preduslov za Story 3-1a (eksterni URL podrška)

## Dev Agent Record

### Implementation Plan

- Koristim Django Sites framework (`Site.objects.get_current().domain`) kao izvor za site URL — vec je konfigurisan sa `SITE_ID = 1`
- Dodao `_get_site_url()` metodu na `CrossrefService` koja konstruise `https://{domain}` URL bez trailing slash-a
- Dodao `site_url` u top-level context i `pk` u svaki article dict u `_build_context()`
- Azurirao sva 3 XML sablona da koriste `{{ site_url }}/articles/{{ article.pk }}/`
- Azurirao postojeci test `test_generate_xml_has_doi_data` da verifikuje novi URL format
- Dodao `TestResourceUrlFix` test klasu sa 4 testa (journal, conference, book + portal URL verifikacija)
- Dodao `TestBuildContext` testove za `site_url` i `pk` u context-u

### Completion Notes

- Svi taskovi kompletni, svi testovi prolaze (218/218 u celom crossref app-u)
- Bug fix koristi Django Sites framework umesto hardkodiranog URL-a
- `_get_site_url()` metoda strip-uje trailing slash za konzistentnost
- `pk` polje dodato u article context dict da bi sabloni mogli da ga koriste

### Code Review Follow-ups (resolved)

- [x] #1 HIGH: Dodat error handling za missing Site objekat (ValueError)
- [x] #2 HIGH: Dodat `CROSSREF_SITE_PROTOCOL` setting umesto hardkodiranog `https://`
- [x] #3 MED: `strip("/")` premesten na domain pre URL konstruisanja
- [x] #4 MED: Dodat eksplicitni `site` fixture sa poznatim domenom u testovima
- [x] #5 MED: Dodat `_cached_site_url` caching na service instanci
- [x] #6 LOW: Uklonjen fragilan `xml.split()` pattern iz testa
- [x] #7 LOW: Dodati pozitivni URL assertions za conference i book tipove

## File List

- `doi_portal/doi_portal/crossref/services.py` (modified) — dodao `_get_site_url()` sa error handling i caching, `site_url` u context, `pk` u articles_data
- `doi_portal/doi_portal/crossref/templates/crossref/journal_article.xml.j2` (modified) — fix `<resource>` URL
- `doi_portal/doi_portal/crossref/templates/crossref/conference_paper.xml.j2` (modified) — fix `<resource>` URL
- `doi_portal/doi_portal/crossref/templates/crossref/book_chapter.xml.j2` (modified) — fix `<resource>` URL
- `doi_portal/doi_portal/crossref/tests/test_services.py` (modified) — azurirani i novi testovi, dodat `site` fixture
- `doi_portal/config/settings/base.py` (modified) — dodat `CROSSREF_SITE_PROTOCOL` setting

## Change Log

- 2026-03-07: Story 5.3a implementirana — fix kruzne reference u `<resource>` elementu Crossref XML-a. Svi testovi prolaze (218/218).
- 2026-03-07: Code review — 7 nalaza rešeno (2 HIGH, 3 MED, 2 LOW). Dodat error handling, protocol setting, caching, robusniji testovi.
