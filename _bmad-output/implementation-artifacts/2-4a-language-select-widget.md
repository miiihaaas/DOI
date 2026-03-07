# Story 2.4a: Language Select Widget za Publication i Article forme

Status: done

## Story

As an **Urednik/Administrator**,
I want **language polje na formama za publikaciju i članak da bude Select dropdown sa predefinisanim jezicima**,
So that **mogu brzo izabrati ispravan ISO 639-1 kod bez mogućnosti greške pri slobodnom unosu**.

## Background

Trenutno language polje na obe forme koristi TextInput widget sa placeholder tekstom. Ovo dozvoljava slobodan unos koji može rezultirati nevalidnim ISO 639-1 kodovima. Crossref XML zahteva validan ISO 639-1 kod u `language` atributu na metadata elementima.

Crossref `language` atribut na metadata elementu (journal_metadata, proceedings_metadata, book_metadata) prima samo jedan ISO 639-1 kod. Publication.language treba da ostane jedno polje — to je primarni jezik publikacije. Članci mogu imati različit jezik od publikacije.

**Ref:** docs/potrebne-ispravke.md, Sekcija 1

## Acceptance Criteria

1. **Given** otvorim formu za kreiranje/edit publikacije,
   **When** vidim language polje,
   **Then** je Select dropdown sa predefinisanim ISO 639-1 jezicima
   **And** default selekcija je "Srpski (sr)"

2. **Given** otvorim formu za kreiranje/edit članka,
   **When** vidim language polje,
   **Then** je Select dropdown sa istom listom jezika kao na publikaciji

3. **Given** postojeća publikacija ima language="sr",
   **When** otvorim edit formu,
   **Then** "Srpski (sr)" je selektovan u dropdown-u

4. **Given** postojeći članak ima language="en",
   **When** otvorim edit formu,
   **Then** "Engleski (en)" je selektovan u dropdown-u

5. **Given** Publication forma,
   **When** vidim help text za language polje,
   **Then** piše "Primarni jezik publikacije. Članci/radovi mogu biti na različitim jezicima."

## Tasks

### Task 1: Kreiraj LANGUAGE_CHOICES konstantu

- [x] 1.1: Dodati LANGUAGE_CHOICES listu u core/constants.py

### Task 2: Ažuriraj PublicationForm

- [x] 2.1: Zameni TextInput sa Select widget-om koristeći LANGUAGE_CHOICES
- [x] 2.2: Widget attrs: `{"class": "form-select"}`
- [x] 2.3: Dodaj help_text na language polje

### Task 3: Ažuriraj ArticleForm

- [x] 3.1: Zameni TextInput sa Select widget-om koristeći LANGUAGE_CHOICES
- [x] 3.2: Widget attrs: `{"class": "form-select"}`

### Task 4: Testovi

- [x] 4.1: Verifikuj da forme renderuju Select widget umesto TextInput
- [x] 4.2: Verifikuj da postojeći podaci sa validnim jezičkim kodovima ispravno selektuju opciju

## Dev Notes

- Ne treba migracija — model polje ostaje CharField, samo se menja widget na formi
- Ako neki postojeći podatak ima jezik koji nije u LANGUAGE_CHOICES listi, Select neće prikazati tu opciju — razmotriti dodavanje catch-all opcije ili proveriti postojeće podatke
- Publication.language i Article.language su nezavisna polja — članak može biti na drugom jeziku od publikacije

## Dev Agent Record

### Implementation Plan

- Kreiran `core/constants.py` sa LANGUAGE_CHOICES (12 ISO 639-1 jezika, labele na srpskom)
- Obe forme ažurirane da koriste Select widget sa `form-select` klasom
- Help text dodat na obe forme (Publication i Article)
- Testovi kreirani za obe forme (widget type, CSS class, choices, initial values, rendered HTML)

### Completion Notes

- 1594 testova prolazi, 0 failures
- Obe forme koriste isti LANGUAGE_CHOICES iz centralizovanog modula
- Dinamičko injektovanje nepoznatih jezičkih kodova u __init__ za backward compatibility

### Code Review Follow-ups (resolved)

- [x] #1 HIGH: Dodat __init__ override za dinamičko injektovanje nepoznatih jezičkih kodova
- [x] #3 MED: Dodati testovi za form submission sa invalidnim jezičkim kodom
- [x] #4 MED: Dodat help_text za language polje na ArticleForm
- [x] #5 MED: Testovi ažurirani da verifikuju rendered HTML sa selected atributom
- Skipped #2 (model choices — design decision za later), #6 (additional languages), #7 (label verification)

## File List

- `doi_portal/doi_portal/core/constants.py` (new) — LANGUAGE_CHOICES konstanta
- `doi_portal/doi_portal/publications/forms.py` (modified) — Select widget, help_text, __init__ override
- `doi_portal/doi_portal/articles/forms.py` (modified) — Select widget, help_text, __init__ override
- `doi_portal/doi_portal/publications/tests/test_forms.py` (new) — 8 testova za language widget
- `doi_portal/doi_portal/articles/tests/test_forms.py` (modified) — 8 testova za language widget

## Change Log

- 2026-03-07: Story 2-4a implementirana — Language Select Widget za obe forme. 1594 testova prolazi.
- 2026-03-07: Code review — 4 nalaza rešena (1 HIGH, 3 MED). Dodat backward compatibility za nepoznate kodove, form submission testovi, help_text, HTML rendering testovi.
