---
title: 'Poboljšanje Article forme i Crossref višejezične podrške'
slug: 'article-form-multilingual-crossref'
created: '2026-03-11'
status: 'completed'
stepsCompleted: [1, 2, 3, 4, 5]
tech_stack: ['Django 5.2+', 'Python 3.13', 'Jinja2', 'Alpine.js 3.15.3', 'HTMX 2.0.8', 'Bootstrap 5.3', 'PostgreSQL 16+']
files_to_modify:
  - 'doi_portal/doi_portal/articles/models.py'
  - 'doi_portal/doi_portal/articles/forms.py'
  - 'doi_portal/doi_portal/templates/articles/article_form.html'
  - 'doi_portal/doi_portal/crossref/templates/crossref/journal_article.xml.j2'
  - 'doi_portal/doi_portal/crossref/templates/crossref/book_chapter.xml.j2'
  - 'doi_portal/doi_portal/crossref/templates/crossref/conference_paper.xml.j2'
  - 'doi_portal/doi_portal/crossref/services.py'
  - 'doi_portal/doi_portal/core/constants.py'
  - 'doi_portal/doi_portal/articles/tests/test_models.py'
  - 'doi_portal/doi_portal/articles/tests/factories.py'
  - 'doi_portal/doi_portal/crossref/tests/test_generation.py'
code_patterns:
  - 'Django models: CharField/TextField sa verbose_name=_(), blank=True, help_text=_()'
  - 'Forms: Meta.fields lista, Meta.widgets dict, Meta.labels dict, Meta.help_texts dict'
  - 'Jinja2 XML: {% if field %}...{% endif %} conditional blocks'
  - 'Alpine.js: x-data komponente za interaktivnost, x-model za binding'
  - 'HTMX: hx-post autosave sa change delay:2s, hx-target="#save-indicator"'
  - 'Services: _build_context() gradi dict sa article fieldovima za template rendering'
  - 'Validation: PreValidationService sa add_error/add_warning pattern-om'
  - 'Lokalizacija: gettext_lazy as _, srpski (sr-Latn) sa dijakriticima'
test_patterns:
  - 'pytest-django sa @pytest.mark.django_db dekoratorom'
  - 'Factory pattern za kreiranje test instanci (articles/tests/factories.py)'
  - 'Crossref testovi u crossref/tests/test_generation.py'
  - 'Article testovi u articles/tests/test_models.py'
---

# Tech-Spec: Poboljšanje Article forme i Crossref višejezične podrške

**Created:** 2026-03-11

## Overview

### Problem Statement

1. Polje `article_number` ima nejasan help text ("Za online-only članke") i korisnici ne razumeju da je alternativa za polja prva/poslednja stranica. U Crossref XML-u ova dva podatka su međusobno isključiva — šalje se ili `<pages>` ili `<publisher_item>` sa article_number.

2. Aplikacija ne podržava naslove na originalnom jeziku. Crossref šema 5.4.0 omogućava `<original_language_title>` element unutar `<titles>` bloka sa opcionim `language` atributom, kao i drugi `<subtitle>` element za subtitle originalnog naslova. Ovo je važno za srpske časopise gde engleski naslov ide u međunarodne citatne baze, a srpski original treba da bude sačuvan.

### Solution

1. UX poboljšanje article_number polja — jasniji help text, placeholder, i JavaScript logika (Alpine.js) za vizuelnu međusobnu isključivost sa pages poljima (readonly + CSS vizuelni feedback + clear vrednosti). Polja nikad ne koriste `disabled` atribut jer disabled polja se ne šalju u HTMX POST.

2. Nova model polja (`original_language_title`, `original_language_subtitle`, `original_language_title_language`) sa odgovarajućim form poljima, jasnim labelama/help tekstovima, i ažuriranim Crossref XML template-ima za sva tri tipa publikacija.

### Scope

**In Scope:**
- Help text i placeholder za `article_number`
- Frontend JS (Alpine.js) za mutual exclusivity article_number ↔ pages (readonly + CSS + clear)
- Nova polja u Article modelu: `original_language_title`, `original_language_subtitle`, `original_language_title_language`
- ArticleForm ažuriranje sa jasnim labelama i help tekstovima
- Sva tri Crossref XML template-a (journal_article, book_chapter, conference_paper)
- CrossrefService `_build_context()` — prosleđivanje novih polja
- PreValidationService — validacija novih polja
- Testovi za nove funkcionalnosti
- ArticleFactory — ažuriranje za nova polja

**Out of Scope:**
- Backend validacija mutual exclusivity (article_number ↔ pages)
- Promene na existing `title`/`subtitle` poljima (osim labela/help text)
- Migracija postojećih podataka
- UI za `<title>` language atribut (Crossref ga ne podržava na `<title>`)
- Automatizovani E2E/browser testovi za Alpine.js logiku (za sada manualni)

## Context for Development

### Codebase Patterns

- **Django MPA** sa HTMX + Alpine.js frontend-om, Bootstrap 5.3 styling
- **Model pattern:** `CharField` sa `verbose_name=_()`, `blank=True`, `help_text=_()`
- **Form pattern:** `ArticleForm(ModelForm)` sa `Meta.fields`, `Meta.widgets`, `Meta.labels`, `Meta.help_texts`
- **Form init:** `__init__(self, *args, user=None, **kwargs)` — prima user za issue queryset scoping
- **Crossref XML:** Jinja2 template-i (`.xml.j2`) sa conditional blocks `{% if field %}...{% endif %}`
- **Services pattern:** `CrossrefService._build_context()` gradi Python dict iz Django modela → prosleđuje template-u
- **Validation pattern:** `PreValidationService._validate_article()` sa `result.add_error(message, field_name, article_id, fix_url)`
- **Auto-save:** HTMX POST sa `change delay:2s` na `input/select/textarea`, target `#save-indicator`
- **Lokalizacija:** `gettext_lazy as _`, srpski (sr-Latn) sa dijakriticima (č, ć, š, đ, ž)
- **Constants:** `LANGUAGE_CHOICES` u `core/constants.py` — lista tuple-ova `(code, label)`, ISO 639-1

### Files to Reference

| File | Purpose | Anchor Points |
| ---- | ------- | ------------- |
| `articles/models.py:142-147` | Article model | `article_number` polje (linija 142) — menjati help_text na liniji 146. Nova polja dodati posle `language` polja (linija 148-152), a pre `publication_type` (linija 153) |
| `articles/forms.py:30-51` | ArticleForm Meta.fields | Dodati nova polja u listu. Postoji `LANGUAGE_CHOICES` import (linija 14) |
| `articles/forms.py:96-101` | article_number widget | Menjati placeholder na liniji 99 |
| `articles/forms.py:154-156` | help_texts dict | Dodati help tekstove za nova polja |
| `articles/forms.py:157-176` | labels dict | Dodati labele za nova polja |
| `articles/tests/factories.py` | ArticleFactory | Dodati nova polja u factory |
| `templates/articles/article_form.html:69-75` | Title sekcija u HTML-u | Dodati help text za title, dodati original_language_title polja posle subtitle |
| `templates/articles/article_form.html:122-155` | Pages/article_number sekcija | Dodati Alpine.js mutual exclusivity logiku, menjati help text |
| `templates/articles/article_form.html:210-251` | `<script>` blok (NON-edit) | `keywordsInput()` je ovde — dodati `paginationToggle()` u ISTI blok (pre `</script>` na liniji 251) |
| `crossref/.../journal_article.xml.j2:54-59` | `<titles>` blok | Dodati `original_language_title` + drugi `subtitle` |
| `crossref/.../book_chapter.xml.j2:50-55` | `<titles>` blok | Isto kao journal |
| `crossref/.../conference_paper.xml.j2:62-67` | `<titles>` blok | Isto kao journal |
| `crossref/services.py:294-313` | `_build_context()` articles_data | Dodati nova polja u dict odmah posle `"subtitle": article.subtitle` (linija 297), pre `"abstract"` (linija 298) |
| `crossref/services.py:634-689` | `_validate_article()` | Dodati validaciju posle external resource provere (linija 687) |
| `core/constants.py:7-20` | LANGUAGE_CHOICES | Referenca za novo language polje |

### Technical Decisions

- **Mutual exclusivity article_number ↔ pages — READONLY + CSS, NE DISABLED:**
  - **NIKAD ne koristiti `disabled` atribut** jer disabled polja se ne šalju u HTML form POST, što znači da HTMX auto-save ne bi primio očišćenu vrednost
  - Umesto toga koristiti `readonly` atribut + CSS klasu `pagination-inactive` (opacity: 0.5, background: #e9ecef) za vizuelni feedback
  - `readonly` polja SE šalju u form POST → auto-save ispravno čuva očišćene vrednosti
  - Na `@change` event (ne `@input`) — čistiti suprotna polja i triggerovati `change` event za auto-save
  - Korisnik može promeniti izbor klikom na readonly polje (readonly text input prima fokus ali ne dozvoljava direktno tipkanje — korisnik mora prvo obrisati aktivno polje da bi se readonly skinuo sa suprotnih)

- **Language za original_language_title:** Zasebno polje `original_language_title_language` sa istom `LANGUAGE_CHOICES` listom iz `core/constants.py`. Widget se inicijalizuje u `__init__` za pravilno rukovanje praznom opcijom.

- **Crossref XML redosled striktan** (XSD sequence): `title` → `subtitle` → `original_language_title` → `subtitle`

- **Title labele:** `title` → "Naslov" (help: "Naslov koji će se prikazivati u međunarodnim citatnim bazama"), `original_language_title` → "Naslov na originalnom jeziku" (help: "Naslov na jeziku članka (opciono)")

- **CharField sa blank=True** — Django CharField sa `blank=True` bez `null=True` koristi prazan string `""` kao default u bazi (NOT NULL constraint, default ""). NE dodavati `null=True` na CharField — to bi stvorilo anti-pattern sa dva moguća "prazna" stanja (NULL i "").

- **Alpine.js paginationToggle()** — definiše se u NON-edit `<script>` bloku (posle `keywordsInput()`, pre `</script>` na liniji 251) tako da radi i u create i u edit modu.

## Implementation Plan

### Tasks

#### Izmena 1: Poboljšanje article_number polja

- [x] **Task 1: Ažurirati Article model — article_number help_text**
  - File: `doi_portal/doi_portal/articles/models.py`
  - Action: Na liniji 146, promeniti `help_text=_("Za online-only članke")` u `help_text=_("Alternativa za stranice kod članaka bez paginacije (npr. e12345)")`

- [x] **Task 2: Ažurirati ArticleForm — article_number widget i help_text**
  - File: `doi_portal/doi_portal/articles/forms.py`
  - Action: Na liniji 99, promeniti placeholder sa `"Za online-only članke"` u `"e12345"`
  - Action: U `Meta.help_texts` dict (linija 154), dodati `"article_number": _("Alternativa za stranice kod članaka bez paginacije (npr. e12345)")`

- [x] **Task 3: Dodati Alpine.js mutual exclusivity — JS komponenta i HTML markup**
  - File: `doi_portal/doi_portal/templates/articles/article_form.html`
  - **3a) Definisati `paginationToggle()` funkciju** u NON-edit `<script>` bloku (linija 210-251), pre zatvarajućeg `</script>` taga na liniji 251. Dodati i CSS stil za `.pagination-inactive`:
  ```javascript
  function paginationToggle() {
      return {
          hasPages: false,
          hasArticleNumber: false,
          init() {
              const fp = document.getElementById('id_first_page');
              const lp = document.getElementById('id_last_page');
              const an = document.getElementById('id_article_number');
              this.hasPages = !!(fp?.value || lp?.value);
              this.hasArticleNumber = !!an?.value;
          },
          onPageChange() {
              const fp = document.getElementById('id_first_page');
              const lp = document.getElementById('id_last_page');
              this.hasPages = !!(fp?.value || lp?.value);
              if (this.hasPages) {
                  const an = document.getElementById('id_article_number');
                  if (an && an.value) {
                      an.value = '';
                      an.dispatchEvent(new Event('change', { bubbles: true }));
                  }
                  this.hasArticleNumber = false;
              }
          },
          onArticleNumberChange() {
              const an = document.getElementById('id_article_number');
              this.hasArticleNumber = !!an?.value;
              if (this.hasArticleNumber) {
                  const fp = document.getElementById('id_first_page');
                  const lp = document.getElementById('id_last_page');
                  [fp, lp].forEach(el => {
                      if (el && el.value) {
                          el.value = '';
                          el.dispatchEvent(new Event('change', { bubbles: true }));
                      }
                  });
                  this.hasPages = false;
              }
          }
      }
  }
  ```
  - **3b) Dodati CSS stil** u `{% block css %}` ili inline `<style>` tag:
  ```css
  .pagination-inactive {
      opacity: 0.5;
      background-color: #e9ecef !important;
  }
  ```
  - **3c) Ažurirati HTML markup** za sekciju "Stranice i identifikacija" (linije 122-155):
    - Dodati `x-data="paginationToggle()"` na wrapper `<div>` oko page/article_number polja
    - Na `first_page` i `last_page` inpute dodati: `@change="onPageChange()"` i `:class="{ 'pagination-inactive': hasArticleNumber }"` i `:readonly="hasArticleNumber"`
    - Na `article_number` input dodati: `@change="onArticleNumberChange()"` i `:class="{ 'pagination-inactive': hasPages }"` i `:readonly="hasPages"`
    - Promeniti help text sa `<div class="form-text">Za online-only članke</div>` u `<div class="form-text">Alternativa za stranice kod članaka bez paginacije</div>`
  - Notes:
    - `readonly` umesto `disabled` — readonly polja SE šalju u HTMX POST, čime se rešava problem persistencije (F3/F4)
    - `@change` umesto `@input` — `change` se okida kad polje izgubi fokus, što sprečava prerano čišćenje dok korisnik još tipka
    - Funkcija je u NON-edit `<script>` bloku pa radi i u create i u edit modu (F6)

#### Izmena 2: Dodavanje naslova na originalnom jeziku

- [x] **Task 4: Dodati nova polja u Article model**
  - File: `doi_portal/doi_portal/articles/models.py`
  - Action: Posle `language` polja (linije 148-152), a pre `publication_type` (linija 153), dodati tri nova polja:
  ```python
  original_language_title = models.CharField(
      _("Naslov na originalnom jeziku"),
      max_length=500,
      blank=True,
      help_text=_("Naslov na jeziku članka (opciono)"),
  )
  original_language_subtitle = models.CharField(
      _("Podnaslov na originalnom jeziku"),
      max_length=500,
      blank=True,
      help_text=_("Podnaslov na jeziku članka (opciono)"),
  )
  original_language_title_language = models.CharField(
      _("Jezik originalnog naslova"),
      max_length=10,
      blank=True,
      help_text=_("ISO 639 jezički kod za originalni naslov (npr. sr, en)"),
  )
  ```
  - Notes: Sva tri polja su CharField sa `blank=True` bez `null=True`. Django CharField koristi prazan string `""` kao default — NE dodavati `null=True` jer bi to stvorilo anti-pattern sa dva moguća "prazna" stanja.

- [x] **Task 5: Kreirati Django migraciju**
  - Action: Pokrenuti `python manage.py makemigrations articles`
  - Notes: Tri nova CharField polja sa `blank=True` — migracija je bezopasna. Django automatski postavlja `default=""` za CharField bez null=True. Nema potrebe za data migration.

- [x] **Task 6: Ažurirati ArticleForm — dodati nova polja**
  - File: `doi_portal/doi_portal/articles/forms.py`
  - Action: U `Meta.fields` listu (linija 32-51) dodati posle `"subtitle"`:
    - `"original_language_title"`
    - `"original_language_subtitle"`
    - `"original_language_title_language"`
  - Action: U `Meta.widgets` dict dodati:
    ```python
    "original_language_title": forms.TextInput(
        attrs={
            "class": "form-control",
            "placeholder": "Naslov na originalnom jeziku",
        }
    ),
    "original_language_subtitle": forms.TextInput(
        attrs={
            "class": "form-control",
            "placeholder": "Podnaslov na originalnom jeziku",
        }
    ),
    "original_language_title_language": forms.Select(
        attrs={
            "class": "form-select",
        }
    ),
    ```
  - Action: U `Meta.labels` dict dodati:
    ```python
    "original_language_title": _("Naslov na originalnom jeziku"),
    "original_language_subtitle": _("Podnaslov na originalnom jeziku"),
    "original_language_title_language": _("Jezik originalnog naslova"),
    ```
  - Action: U `Meta.help_texts` dict dodati:
    ```python
    "original_language_title": _("Naslov na jeziku članka (opciono)"),
    "original_language_subtitle": _("Podnaslov na jeziku članka (opciono)"),
    "original_language_title_language": _("Jezik originalnog naslova za Crossref registraciju"),
    ```
  - Action: U `__init__` metodu (posle language injection logike, oko linije 194), dodati inicijalizaciju choices za `original_language_title_language`:
    ```python
    # Set choices for original_language_title_language field
    self.fields["original_language_title_language"].widget.choices = [
        ("", "---------")
    ] + list(LANGUAGE_CHOICES)
    ```
  - Notes: Choices se postavlja u `__init__` umesto u `Meta.widgets` da bi se osiguralo da prazna opcija bude default kad je polje prazno (F5). Isti pattern kao postojeći `language` field handling.

- [x] **Task 7: Ažurirati HTML template — dodati polja za originalni naslov**
  - File: `doi_portal/doi_portal/templates/articles/article_form.html`
  - Action: Posle subtitle bloka (linija 83), dodati help text za `title` polje i nova polja:
    - Ispod `{{ form.title }}` (linija 71): dodati `<div class="form-text">Naslov koji će se prikazivati u međunarodnim citatnim bazama</div>`
    - Posle subtitle `</div>` (linija 83): dodati novu sekciju sa:
      - `original_language_title` — full width (`mb-3`)
      - `original_language_subtitle` i `original_language_title_language` — u istom redu (`col-md-8` i `col-md-4`)
    - Koristiti isti Bootstrap pattern kao ostala polja (label, field, help_text, error feedback)

- [x] **Task 8: Ažurirati Crossref XML template-e — titles blok**
  - Files:
    - `doi_portal/doi_portal/crossref/templates/crossref/journal_article.xml.j2` (linije 54-59)
    - `doi_portal/doi_portal/crossref/templates/crossref/book_chapter.xml.j2` (linije 50-55)
    - `doi_portal/doi_portal/crossref/templates/crossref/conference_paper.xml.j2` (linije 62-67)
  - Action: U sva tri fajla, zameniti `<titles>` blok sa:
  ```xml
  <titles>
    <title>{{ article.title }}</title>
    {% if article.subtitle %}
    <subtitle>{{ article.subtitle }}</subtitle>
    {% endif %}
    {% if article.original_language_title %}
    <original_language_title{% if article.original_language_title_language %} language="{{ article.original_language_title_language|xml_escape }}"{% endif %}>{{ article.original_language_title }}</original_language_title>
    {% if article.original_language_subtitle %}
    <subtitle>{{ article.original_language_subtitle }}</subtitle>
    {% endif %}
    {% endif %}
  </titles>
  ```
  - Notes:
    - Redosled je striktan po XSD: title → subtitle → original_language_title → subtitle
    - Drugi `<subtitle>` se renderuje SAMO ako postoji `original_language_title` (jer pripada toj sekvenci u XSD-u)
    - `xml_escape` filter primenjen na `language` atribut za sigurnost (F7), iako vrednost dolazi iz kontrolisane LANGUAGE_CHOICES liste

- [x] **Task 9: Ažurirati CrossrefService._build_context()**
  - File: `doi_portal/doi_portal/crossref/services.py`
  - Action: U `articles_data` dict, odmah posle `"subtitle": article.subtitle` (linija 297), pre `"abstract": article.abstract` (linija 298), dodati:
  ```python
  "original_language_title": article.original_language_title,
  "original_language_subtitle": article.original_language_subtitle,
  "original_language_title_language": article.original_language_title_language,
  ```

- [x] **Task 10: Ažurirati PreValidationService._validate_article()**
  - File: `doi_portal/doi_portal/crossref/services.py`
  - Action: U `_validate_article()` metodu, posle external resource provere (linija 687, pre `return result`), dodati:
  ```python
  # Validate original language title consistency
  if article.original_language_title and not article.original_language_title_language:
      result.add_warning(
          message=f"Naslov na originalnom jeziku je popunjen ali jezik nije izabran (članak: {article.title or article.pk})",
          field_name="original_language_title_language",
          article_id=article.pk,
          fix_url=f"/admin/articles/article/{article.pk}/change/",
      )
  if article.original_language_subtitle and not article.original_language_title:
      result.add_warning(
          message=f"Podnaslov na originalnom jeziku je popunjen ali naslov nije (članak: {article.title or article.pk})",
          field_name="original_language_title",
          article_id=article.pk,
          fix_url=f"/admin/articles/article/{article.pk}/change/",
      )
  ```

#### Testovi

- [x] **Task 11: Ažurirati ArticleFactory — dodati nova polja**
  - File: `doi_portal/doi_portal/articles/tests/factories.py`
  - Action: Dodati nova polja u ArticleFactory sa default praznim vrednostima:
  ```python
  original_language_title = ""
  original_language_subtitle = ""
  original_language_title_language = ""
  ```

- [x] **Task 12: Napisati testove za Article model — nova polja**
  - File: `doi_portal/doi_portal/articles/tests/test_models.py`
  - Action: Dodati test klasu/metode za:
    1. Kreiranje Article sa `original_language_title`, `original_language_subtitle`, `original_language_title_language`
    2. Default vrednosti (sva tri polja su prazni stringovi — NE NULL)
    3. Max length validacija (500, 500, 10)

- [x] **Task 13: Napisati testove za Crossref XML generisanje sa original_language_title**
  - File: `doi_portal/doi_portal/crossref/tests/test_generation.py`
  - Action: Dodati testove za:
    1. XML bez original_language_title — `<titles>` sadrži samo `<title>` i opcioni `<subtitle>`
    2. XML sa original_language_title i language — `<titles>` sadrži `<original_language_title language="sr">`
    3. XML sa original_language_title bez language — `<original_language_title>` bez language atributa
    4. XML sa original_language_title i original_language_subtitle — dva `<subtitle>` elementa u ispravnom redosledu
    5. XSD validacija prolazi za sve varijante
  - Notes: Koristiti ažuriran ArticleFactory iz Task 11

- [x] **Task 14: Napisati testove za PreValidationService — nova validaciona pravila**
  - File: `doi_portal/doi_portal/crossref/tests/test_generation.py`
  - Action: Dodati testove za:
    1. Warning kad je original_language_title popunjen bez language-a
    2. Warning kad je original_language_subtitle popunjen bez original_language_title
    3. Nema warning-a kad su sva polja konzistentna

### Acceptance Criteria

#### Izmena 1: article_number UX poboljšanje

- [x] **AC 1:** Given article forma je otvorena, when korisnik vidi polje "Broj članka", then help text prikazuje "Alternativa za stranice kod članaka bez paginacije (npr. e12345)" i placeholder je "e12345"
- [x] **AC 2:** Given polja "Prva stranica" i "Poslednja stranica" su prazna, when korisnik unese vrednost u "Broj članka" i polje izgubi fokus, then polja za stranice postaju readonly sa vizuelnim feedbackom (smanjena vidljivost)
- [x] **AC 3:** Given polje "Broj članka" je prazno, when korisnik unese vrednost u "Prva stranica" ili "Poslednja stranica" i polje izgubi fokus, then polje "Broj članka" postaje readonly sa vizuelnim feedbackom
- [x] **AC 4:** Given polje "Broj članka" ima vrednost i stranice su readonly, when korisnik obriše vrednost iz "Broj članka" i polje izgubi fokus, then polja za stranice ponovo postaju aktivna (readonly se uklanja)
- [x] **AC 5:** Given polja za stranice imaju vrednosti, when "Broj članka" postane readonly, then njegova vrednost se čisti i auto-save sačuva praznu vrednost u bazu (polje NIJE disabled — šalje se u POST)
- [x] **AC 6:** Given članak ima sačuvane stranice u bazi, when korisnik otvori formu za uređivanje, then "Broj članka" je readonly sa vizuelnim feedbackom (i obrnuto — ako ima article_number, stranice su readonly)
- [x] **AC 6a:** Given article forma je u CREATE modu (novi članak), when korisnik popuni pages pa onda article_number, then mutual exclusivity logika radi isto kao u edit modu

#### Izmena 2: Naslov na originalnom jeziku

- [x] **AC 7:** Given article forma je otvorena, when korisnik vidi polja za naslov, then postoje polja "Naslov na originalnom jeziku", "Podnaslov na originalnom jeziku" i "Jezik originalnog naslova" sa odgovarajućim help tekstovima
- [x] **AC 8:** Given članak ima popunjen `original_language_title` sa `language="sr"`, when se generiše Crossref XML, then `<titles>` blok sadrži `<original_language_title language="sr">...</original_language_title>` posle `<subtitle>`
- [x] **AC 9:** Given članak ima popunjen `original_language_title` i `original_language_subtitle`, when se generiše Crossref XML, then `<titles>` blok sadrži drugi `<subtitle>` element posle `<original_language_title>`
- [x] **AC 10:** Given članak nema popunjen `original_language_title`, when se generiše Crossref XML, then `<titles>` blok sadrži samo `<title>` i opcioni `<subtitle>` (bez `<original_language_title>`)
- [x] **AC 11:** Given članak ima popunjen `original_language_title` bez izabranog jezika, when se pokrene PreValidation, then se generiše warning "Naslov na originalnom jeziku je popunjen ali jezik nije izabran"
- [x] **AC 12:** Given generisan Crossref XML sa `original_language_title`, when se validira protiv XSD 5.4.0 šeme, then validacija prolazi bez grešaka

## Additional Context

### Dependencies

- Nema novih eksternih zavisnosti
- Zavisi od postojećeg `LANGUAGE_CHOICES` iz `core/constants.py`
- Zavisi od Crossref XSD 5.4.0 šeme za validaciju

### Testing Strategy

**Unit testovi:**
- Article model: kreiranje sa novim poljima, default vrednosti (prazan string, NE null), max_length
- ArticleForm: validacija novih polja, widget rendering, language choices inicijalizacija
- PreValidationService: warning za inconsistent original_language_title/language

**Integration testovi:**
- CrossrefService.generate_xml: XML output sa/bez original_language_title za sva tri publication tipa
- XSD validacija: generisani XML prolazi Crossref 5.4.0 šemu

**Manual testing:**
- Otvoriti article formu u CREATE modu → proveriti article_number readonly logiku
- Otvoriti article formu u EDIT modu → proveriti article_number readonly logiku
- Proveriti da readonly polja šalju vrednost u auto-save POST (DevTools Network tab)
- Popuniti original_language_title → generisati XML → proveriti output
- Proveriti auto-save radi ispravno sa novim poljima

**Napomena o E2E testovima:** Automatizovani browser testovi (Playwright/Selenium) za Alpine.js mutual exclusivity logiku nisu u scope-u ovog task-a. Frontend ponašanje se verifikuje manualnim testiranjem. E2E testovi se mogu dodati naknadno.

### Notes

- Crossref XSD 5.4.0 potvrđen iz zvaničnog izvora (https://data.crossref.org/schemas/crossref5.4.0.xsd) i upoređen sa lokalnom kopijom — potpuno poklapanje
- `<subtitle>` nema language atribut — to je po Crossref specifikaciji
- `<original_language_title>` language atribut je opcioni (use="optional"), ali preporučljiv
- Alpine.js `paginationToggle()` komponenta je u NON-edit `<script>` bloku — radi i u create i edit modu
- **KRITIČNO:** Koristiti `readonly` + CSS umesto `disabled` — disabled polja se NE šalju u HTMX POST, što bi sprečilo auto-save da sačuva očišćene vrednosti
- **KRITIČNO:** Koristiti `@change` event (okida se na blur) umesto `@input` (okida se na svaki keystroke) — sprečava prerano čišćenje dok korisnik tipka
- Migracija je bezopasna — sva tri nova polja su CharField sa blank=True, default je prazan string ""
- `fix_url` u PreValidationService pokazuje na Django admin (konzistentno sa postojećim pattern-om)

### Adversarial Review Log

Izvršen adversarial review koji je identifikovao 12 nalaza. Svi su adresirani:

| ID | Severity | Status | Opis |
|----|----------|--------|------|
| F1 | Medium | Ispravljeno | Preciznije insertion tačke u `_build_context()` |
| F2 | Medium | Ispravljeno | Ispravljena terminologija — "blank=True sa praznim stringom" umesto "nullable" |
| F3 | High | Ispravljeno | `@change` umesto `@input` — sprečava prerano čišćenje |
| F4 | High | Ispravljeno | `readonly` umesto `disabled` — polja se šalju u HTMX POST |
| F5 | Medium | Ispravljeno | Choices se postavlja u `__init__` za pravilnu blank opciju |
| F6 | Medium | Ispravljeno | `paginationToggle()` u NON-edit script bloku |
| F7 | Low | Ispravljeno | `xml_escape` filter na language atributu |
| F8 | Medium | Ispravljeno | `ArticleFactory` dodat u listu fajlova i Task 11 |
| F9 | Medium | Dokumentovano | E2E testovi eksplicitno navedeni kao out of scope |
| F10 | Low | Ispravljeno | Task 3 i 4 spojeni u jedan task |
| F11 | Low | Dokumentovano | `fix_url` → admin je konzistentno sa postojećim pattern-om |
| F12 | Low | Ispravljeno | Precizna pozicija: posle linije 297, pre linije 298 |
