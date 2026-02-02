# Story 4.3: Advanced Filtering for Articles

Status: done

## Story

As a **visitor (posetilac)**,
I want **to filter articles by various criteria (publication type, subject area, language, access type, year range)**,
So that **I can narrow down search results to exactly what I need**.

## Background

Ovo je treca prica u Epiku 4 (Public Portal Experience). Story 4.2 je implementirala Article Search sa pretragom po naslovu, autoru, kljucnim recima i apstraktu. Rezultati se prikazuju na `/search/` stranici kao article kartice sa paginacijom. Ovaj story dodaje **filter sidebar** na search results stranicu koji omogucava posetiocima da suzavaju rezultate pretrage po razlicitim kriterijumima. Filteri rade preko HTMX-a bez ponovnog ucitavanja stranice. URL parametri se azuriraju za deljive linkove.

**FR Pokrivenost:**
- FR40: Posetilac moze filtrirati publikacije po vrsti, oblasti, pristupu, jeziku

**NFR Pokrivenost:**
- NFR5: Pretraga - Rezultati < 2 sekunde
- NFR2: Javne stranice portala - ucitavanje < 3 sekunde
- NFR14-NFR18: Accessibility (semanticki HTML5, alt tekst, kontrast, keyboard, labels)

**Zavisnosti (sve DONE):**
- Story 4.2: Article Search Functionality - search results stranica, `ArticleSearchView`, `search_articles()` service, HTMX partial `_search_results.html`
- Story 4.1: Portal Home Page - hero search bar sa `action="/search/"` i `name="q"`
- Story 2.5: Public Publication List - HTMX filter pattern sa `PublicationPublicListView` (referentna implementacija filtera)
- Story 3.1: Article Model - `Article`, `ArticleStatus`, `Author` modeli
- Story 2.3: Publication Model - `PublicationType`, `AccessType` enum, `subject_area`, `language` polja

**Blokira:**
- Story 4.4: Article Landing Page - article detail stranica

## Acceptance Criteria

1. **Given** posetilac je na search results ili article listing stranici
   **When** pregleda filter sidebar
   **Then** filteri su prikazani u collapsible sekcijama:
   - Tip publikacije (casopis, zbornik, monografija)
   - Naucna oblast
   - Jezik
   - Tip pristupa (otvoreni, ograniceni)
   - Opseg godina (od-do)

2. **Given** posetilac selektuje filter opcije
   **When** primenjuje filtere
   **Then** HTMX azurira rezultate bez ponovnog ucitavanja stranice
   **And** selektovani filteri se prikazuju kao tagovi iznad rezultata
   **And** URL parametri se azuriraju za deljive linkove

3. **Given** vise filtera je selektovano
   **When** pregleda rezultate
   **Then** filteri se kombinuju sa AND logikom
   **And** broj rezultata se azurira da odrazava filtrirani set

4. **Given** posetilac klikne "Obrisi sve filtere"
   **When** akcija se izvrsi
   **Then** svi filteri se resetuju
   **And** prikazuje se pun set rezultata pretrage

5. **Given** posetilac je na mobilnom uredaju
   **When** pregleda filtere
   **Then** filter sidebar je collapsible overlay
   **And** "Primeni filtere" dugme zatvara overlay i prikazuje rezultate

6. **Given** posetilac primeni filter i pretragu istovremeno
   **When** pregleda stranicu
   **Then** i pretraga i filteri su aktivni
   **And** query parametar `q` je sacuvan u URL-u zajedno sa filter parametrima

7. **Given** posetilac pristupi URL-u sa filter parametrima
   **When** stranica se ucitava
   **Then** filteri su unapred selektovani prema URL parametrima
   **And** rezultati su vec filtrirani

8. **Given** stranica se ucitava
   **When** analiziramo pristupacnost
   **Then** filter forma koristi `<fieldset>` i `<legend>` za grupisanje
   **And** checkbox-ovi imaju `<label>` elemente
   **And** filter sekcije imaju `aria-expanded` atribut
   **And** keyboard navigacija funkcionise kroz sve filtere

## Tasks / Subtasks

- [x] Task 1: Prosiriti `search_articles()` service sa filter parametrima (AC: #2, #3, #6)
  - [x] 1.1 Dodati parametar `filters: dict | None = None` u `search_articles()` funkciju
  - [x] 1.2 Filtriranje po `publication_type` - koristiti `issue__publication__publication_type__in` za multi-select
  - [x] 1.3 Filtriranje po `subject_area` - koristiti `issue__publication__subject_area__in` za multi-select
  - [x] 1.4 Filtriranje po `language` - koristiti `issue__publication__language__in` za multi-select
  - [x] 1.5 Filtriranje po `access_type` - koristiti `issue__publication__access_type__in` za multi-select
  - [x] 1.6 Filtriranje po `year_from` i `year_to` - koristiti `issue__year__gte` i `issue__year__lte`
  - [x] 1.7 Filteri se kombinuju sa AND logikom (svi moraju biti zadovoljeni)
  - [x] 1.8 Ako filter nije zadat (prazna lista ili None), ne primenjivati ga
  - [x] 1.9 Zadrzati postojecu logiku pretrage (search query) - filteri se dodaju na search queryset

- [x] Task 2: Prosiriti `ArticleSearchView` sa filter kontekstom (AC: #1, #2, #3, #4, #6, #7)
  - [x] 2.1 Parsirati filter parametre iz `request.GET`: `getlist("type")`, `getlist("subject")`, `getlist("language")`, `getlist("access")`, `get("year_from")`, `get("year_to")`
  - [x] 2.2 Proslediti filter dict u `search_articles()` service
  - [x] 2.3 Dodati filter choices u context: `publication_types` (PublicationType.choices), `access_types` (AccessType.choices)
  - [x] 2.4 Dodati dinamicke filter opcije: `subject_areas` i `languages` iz Publication querysets
  - [x] 2.5 Dodati `year_range` u context: min i max godina iz Issue modela (za year range filter)
  - [x] 2.6 Dodati `current_*` varijable za aktivne filtere (za UI state)
  - [x] 2.7 Dodati `has_active_filters` boolean za "Obrisi sve" dugme
  - [x] 2.8 Dodati `active_filter_tags` listu za prikaz aktivnih filtera kao tagova
  - [x] 2.9 Proslediti `q` parametar u HTMX include da se sacuva pretraga pri filtriranju

- [x] Task 3: Azurirati `search_results.html` template sa filter sidebar (AC: #1, #2, #4, #5, #8)
  - [x] 3.1 Promeniti layout iz single-column u `row` sa `col-lg-3` (filter sidebar) i `col-lg-9` (rezultati)
  - [x] 3.2 Dodati filter sidebar `<aside>` sa card wraperom (isti pattern kao publication_list.html)
  - [x] 3.3 Svaka filter grupa u `<fieldset>` sa `<legend>` elementom
  - [x] 3.4 Multiselect checkbox-ovi za: tip publikacije, naucna oblast, tip pristupa, jezik
  - [x] 3.5 Year range filter: dva `<input type="number">` polja (od-do)
  - [x] 3.6 HTMX atributi na svim filter input-ima: `hx-get`, `hx-trigger="change"`, `hx-target="#search-results"`, `hx-include` za sve filtere + query
  - [x] 3.7 `hx-push-url="true"` za azuriranje URL-a
  - [x] 3.8 Hidden input `<input type="hidden" name="q" value="{{ query }}">` u filter sidebar da se sacuva search query
  - [x] 3.9 "Obrisi sve filtere" dugme (prikazuje se samo kad su filteri aktivni)
  - [x] 3.10 Aktivni filteri kao tagovi iznad rezultata sa "x" dugmetom za uklanjanje
  - [x] 3.11 Mobile: offcanvas Bootstrap 5 overlay za filtere umesto sidebar-a
  - [x] 3.12 Mobile: "Filteri" dugme za otvaranje overlay-a
  - [x] 3.13 Mobile: "Primeni filtere" dugme unutar overlay-a

- [x] Task 4: Azurirati `_search_results.html` HTMX partial (AC: #2, #3)
  - [x] 4.1 Dodati aktivne filter tagove na vrh partial-a
  - [x] 4.2 Azurirati result count poruku da ukljuci filter info
  - [x] 4.3 Sacuvati paginaciju i prazan state

- [x] Task 5: Dodati CSS stilove za filter sidebar (AC: #1, #5)
  - [x] 5.1 Filter sidebar stilovi u `portal.css`
  - [x] 5.2 Active filter tag stilovi (badge sa x dugmetom)
  - [x] 5.3 Collapsible sekcije sa chevron ikonom
  - [x] 5.4 Mobile offcanvas overlay stilovi
  - [x] 5.5 Year range input stilovi (inline dva polja)

- [x] Task 6: Kreirati testove (AC: #1-#8)
  - [x] 6.1 Service test: `search_articles()` sa `type` filterom vraca samo clanke iz tog tipa publikacije
  - [x] 6.2 Service test: `search_articles()` sa `subject` filterom vraca samo clanke iz te oblasti
  - [x] 6.3 Service test: `search_articles()` sa `language` filterom vraca samo clanke na tom jeziku
  - [x] 6.4 Service test: `search_articles()` sa `access` filterom vraca samo clanke sa tim pristupom
  - [x] 6.5 Service test: `search_articles()` sa `year_from` i `year_to` filterom vraca clanke u opsegu
  - [x] 6.6 Service test: kombinacija search query + filter radi ispravno (AND logika)
  - [x] 6.7 Service test: prazan filter ne utice na rezultate
  - [x] 6.8 Service test: nevazeci filter vrednosti se ignorisu
  - [x] 6.9 View test: GET /search/ sa filter parametrima vraca filtrirane rezultate
  - [x] 6.10 View test: context sadrzi `publication_types`, `access_types`, `subject_areas`, `languages`
  - [x] 6.11 View test: context sadrzi `current_types`, `current_subjects` itd.
  - [x] 6.12 View test: `has_active_filters` je True kad su filteri aktivni
  - [x] 6.13 View test: `has_active_filters` je False kad nema filtera
  - [x] 6.14 View test: URL parametri se pravilno parsiraju (type, subject, language, access, year_from, year_to)
  - [x] 6.15 View test: q parametar se sacuva kad se primeni filter
  - [x] 6.16 View test: HTMX request vraca partial sa filtriranim rezultatima
  - [x] 6.17 View test: "Obrisi sve filtere" link vodi na /search/?q=... bez filtera
  - [x] 6.18 View test: year_range u context-u sadrzi min i max godinu

## Dev Notes

### KRITICNO: Postojeci Search Pattern iz Story 4.2

Search results stranica (`/search/`) je VEC implementirana u Story 4.2. Ovaj story PROSIRUJE postojecu implementaciju - NE kreira novu stranicu. Kljucne tacke:

1. **URL ostaje `/search/`** - NE menjati
2. **Query parametar ostaje `q`** - NE menjati
3. **`ArticleSearchView(ListView)` se PROSIRUJE** - NE kreirati novi view
4. **`search_articles()` se PROSIRUJE** - NE kreirati novu funkciju
5. **`search_results.html` se MODIFIKUJE** - dodaje se filter sidebar
6. **`_search_results.html` partial se MODIFIKUJE** - dodaju se filter tagovi

### Referentna Implementacija: PublicationPublicListView (Story 2.5)

Publication listing (`/publications/`) VEC ima identican filter pattern koji MORAMO kopirati:

```python
# portal/views.py - PublicationPublicListView FILTER PATTERN:

def get_queryset(self):
    queryset = Publication.objects.select_related("publisher").order_by("title")

    # Filter by type (multi-select checkboxes)
    pub_types = self.request.GET.getlist("type")
    valid_types = [t for t in pub_types if t in [c[0] for c in PublicationType.choices]]
    if valid_types:
        queryset = queryset.filter(publication_type__in=valid_types)

    # ... isti pattern za subject, access, language
    return queryset

def get_context_data(self, **kwargs):
    context["publication_types"] = PublicationType.choices
    context["access_types"] = AccessType.choices
    context["subject_areas"] = Publication.objects.exclude(subject_area="").values_list("subject_area", flat=True).distinct()
    context["languages"] = Publication.objects.exclude(language="").values_list("language", flat=True).distinct()
    context["current_types"] = self.request.GET.getlist("type")
    # ... current_* za svaki filter
    context["has_active_filters"] = bool(...)
    return context
```

### Template Pattern: publication_list.html (Story 2.5)

Filter sidebar template VEC postoji u `portal/publications/publication_list.html` sa:
- `<aside class="col-lg-3 mb-4">` za sidebar
- `<div class="card">` wrapper
- `<fieldset>` sa `<legend>` za svaku filter grupu
- Multiselect checkbox-ovi sa HTMX atributima
- `hx-get`, `hx-trigger="change"`, `hx-target`, `hx-include`, `hx-push-url`
- "Obrisi sve filtere" link kad `has_active_filters` je True

**OVAJ IDENTICAN PATTERN MORAMO KORISTITI** za search results filter sidebar. Razlika:
- Filter URL je `/search/` umesto `/publications/`
- Mora se sacuvati `q` parametar u `hx-include`
- Dodati `year_from` i `year_to` filter (nema ga u publications)
- Filtriramo Articles (indirektno preko Issue -> Publication) umesto Publications direktno

### Prosirenje search_articles() Service

```python
# portal/services.py - PROSIRITI postojecu funkciju

def search_articles(
    query: str,
    filters: dict | None = None,
) -> QuerySet[Article]:
    """
    Search published articles with optional filters.

    FR39: Pretraga clanaka.
    FR40: Filtriranje po vrsti, oblasti, pristupu, jeziku.
    """
    if not query or len(query.strip()) < 3:
        return Article.objects.none()

    q = query.strip()[:200]

    # ... postojeca search logika (title, author, keywords, abstract) ...

    queryset = (
        Article.objects.filter(
            Q(status=ArticleStatus.PUBLISHED),
            Q(title__icontains=q) | Q(abstract__icontains=q)
            | Q(keywords__icontains=q) | Q(id__in=matching_author_article_ids),
        )
        .select_related("issue__publication__publisher")
        .prefetch_related("authors")
        .order_by("-published_at", "-created_at")
        .distinct()
    )

    # Apply filters
    if filters:
        if filters.get("types"):
            queryset = queryset.filter(
                issue__publication__publication_type__in=filters["types"]
            )
        if filters.get("subjects"):
            queryset = queryset.filter(
                issue__publication__subject_area__in=filters["subjects"]
            )
        if filters.get("languages"):
            queryset = queryset.filter(
                issue__publication__language__in=filters["languages"]
            )
        if filters.get("access_types"):
            queryset = queryset.filter(
                issue__publication__access_type__in=filters["access_types"]
            )
        if filters.get("year_from"):
            queryset = queryset.filter(
                issue__year__gte=filters["year_from"]
            )
        if filters.get("year_to"):
            queryset = queryset.filter(
                issue__year__lte=filters["year_to"]
            )

    return queryset
```

**VAZNO o filter putanjama:**
- Article -> Issue (FK) -> Publication (FK) -> publication_type, subject_area, language, access_type
- Article -> Issue (FK) -> year
- `select_related("issue__publication__publisher")` VEC pokriva ove join-ove, pa filtriranje ne pravi dodatne SQL upite

### Prosirenje ArticleSearchView

```python
# portal/views.py - PROSIRITI postojecu klasu

class ArticleSearchView(ListView):
    # ... postojeci atributi ...

    def _parse_filters(self) -> dict:
        """Parse filter parameters from GET request."""
        filters = {}

        pub_types = self.request.GET.getlist("type")
        valid_types = [t for t in pub_types if t in [c[0] for c in PublicationType.choices]]
        if valid_types:
            filters["types"] = valid_types

        subjects = self.request.GET.getlist("subject")
        if subjects:
            filters["subjects"] = subjects

        languages = self.request.GET.getlist("language")
        if languages:
            filters["languages"] = languages

        access_values = self.request.GET.getlist("access")
        valid_access = [a for a in access_values if a in [c[0] for c in AccessType.choices]]
        if valid_access:
            filters["access_types"] = valid_access

        year_from = self.request.GET.get("year_from")
        if year_from and year_from.isdigit():
            filters["year_from"] = int(year_from)

        year_to = self.request.GET.get("year_to")
        if year_to and year_to.isdigit():
            filters["year_to"] = int(year_to)

        return filters

    def get_queryset(self):
        """Return filtered search results."""
        query = self.request.GET.get("q", "").strip()[:200]
        if len(query) < 3:
            return Article.objects.none()
        filters = self._parse_filters()
        return search_articles(query, filters=filters)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # ... postojeci context (query, result_count, breadcrumbs) ...

        # Filter choices
        context["publication_types"] = PublicationType.choices
        context["access_types"] = AccessType.choices
        context["subject_areas"] = (
            Publication.objects.exclude(subject_area="")
            .values_list("subject_area", flat=True)
            .distinct().order_by("subject_area")
        )
        context["languages"] = (
            Publication.objects.exclude(language="")
            .values_list("language", flat=True)
            .distinct().order_by("language")
        )

        # Year range
        from doi_portal.issues.models import Issue, IssueStatus
        year_agg = Issue.objects.filter(
            status=IssueStatus.PUBLISHED
        ).aggregate(
            min_year=models.Min("year"),
            max_year=models.Max("year"),
        )
        context["year_range"] = {
            "min": year_agg["min_year"],
            "max": year_agg["max_year"],
        }

        # Active filter state
        context["current_types"] = self.request.GET.getlist("type")
        context["current_subjects"] = self.request.GET.getlist("subject")
        context["current_languages"] = self.request.GET.getlist("language")
        context["current_access"] = self.request.GET.getlist("access")
        context["current_year_from"] = self.request.GET.get("year_from", "")
        context["current_year_to"] = self.request.GET.get("year_to", "")

        context["has_active_filters"] = bool(
            context["current_types"]
            or context["current_subjects"]
            or context["current_languages"]
            or context["current_access"]
            or context["current_year_from"]
            or context["current_year_to"]
        )

        return context
```

### Azurirani search_results.html Template

```html
{% extends "portal/base.html" %}
{% load static %}
{% load portal_tags %}

{% block title %}Pretraga članaka{% if query %} - "{{ query }}"{% endif %}{% endblock title %}

{% block portal_content %}
<div class="row">
  <!-- Filter Sidebar (Desktop) / Offcanvas (Mobile) -->
  <aside class="col-lg-3 mb-4 d-none d-lg-block">
    {% include "portal/partials/_article_filter_sidebar.html" %}
  </aside>

  <!-- Mobile Filter Button -->
  <div class="d-lg-none mb-3">
    <button class="btn btn-outline-primary w-100"
            type="button"
            data-bs-toggle="offcanvas"
            data-bs-target="#filterOffcanvas"
            aria-controls="filterOffcanvas">
      <i class="bi bi-funnel"></i> Filteri
      {% if has_active_filters %}
        <span class="badge bg-primary ms-1">Aktivni</span>
      {% endif %}
    </button>
  </div>

  <!-- Mobile Offcanvas -->
  <div class="offcanvas offcanvas-start d-lg-none" tabindex="-1" id="filterOffcanvas"
       aria-labelledby="filterOffcanvasLabel">
    <div class="offcanvas-header">
      <h5 class="offcanvas-title" id="filterOffcanvasLabel">Filteri</h5>
      <button type="button" class="btn-close" data-bs-dismiss="offcanvas" aria-label="Zatvori"></button>
    </div>
    <div class="offcanvas-body">
      {% include "portal/partials/_article_filter_sidebar.html" %}
      <button type="button" class="btn btn-primary w-100 mt-3" data-bs-dismiss="offcanvas">
        Primeni filtere
      </button>
    </div>
  </div>

  <!-- Main Content -->
  <section class="col-lg-9">
    <h1 class="h3 mb-3">Pretraga članaka</h1>
    <!-- Search Form -->
    <form action="{% url 'article-search' %}" method="get" role="search" class="mb-4">
      <!-- ... isti search form ... -->
    </form>

    <!-- Results -->
    <div id="search-results" class="search-results" aria-live="polite">
      {% include "portal/partials/_search_results.html" %}
    </div>
  </section>
</div>
{% endblock portal_content %}
```

### Novi Partial: _article_filter_sidebar.html

```html
<!-- templates/portal/partials/_article_filter_sidebar.html -->
<div class="card">
  <div class="card-body">
    <h2 class="h5 card-title mb-3">Filteri</h2>

    <!-- Hidden search query -->
    <input type="hidden" name="q" value="{{ query }}">

    <!-- Type Filter -->
    <fieldset class="mb-3">
      <legend class="form-label fw-semibold h6">Tip publikacije</legend>
      {% for value, label in publication_types %}
      <div class="form-check">
        <input class="form-check-input" type="checkbox" name="type"
               id="type-{{ value }}" value="{{ value }}"
               {% if value in current_types %}checked{% endif %}
               hx-get="{% url 'article-search' %}"
               hx-trigger="change"
               hx-target="#search-results"
               hx-include="[name='q'],[name='type'],[name='subject'],[name='access'],[name='language'],[name='year_from'],[name='year_to']"
               hx-push-url="true">
        <label class="form-check-label" for="type-{{ value }}">{{ label }}</label>
      </div>
      {% endfor %}
    </fieldset>

    <hr>

    <!-- Subject Area Filter -->
    {% if subject_areas %}
    <fieldset class="mb-3">
      <legend class="form-label fw-semibold h6">Naučna oblast</legend>
      {% for area in subject_areas %}
      <div class="form-check">
        <input class="form-check-input" type="checkbox" name="subject"
               id="subject-{{ forloop.counter }}" value="{{ area }}"
               {% if area in current_subjects %}checked{% endif %}
               hx-get="{% url 'article-search' %}"
               hx-trigger="change"
               hx-target="#search-results"
               hx-include="[name='q'],[name='type'],[name='subject'],[name='access'],[name='language'],[name='year_from'],[name='year_to']"
               hx-push-url="true">
        <label class="form-check-label" for="subject-{{ forloop.counter }}">{{ area }}</label>
      </div>
      {% endfor %}
    </fieldset>
    <hr>
    {% endif %}

    <!-- Access Type Filter -->
    <fieldset class="mb-3">
      <legend class="form-label fw-semibold h6">Tip pristupa</legend>
      {% for value, label in access_types %}
      <div class="form-check">
        <input class="form-check-input" type="checkbox" name="access"
               id="access-{{ value }}" value="{{ value }}"
               {% if value in current_access %}checked{% endif %}
               hx-get="{% url 'article-search' %}"
               hx-trigger="change"
               hx-target="#search-results"
               hx-include="[name='q'],[name='type'],[name='subject'],[name='access'],[name='language'],[name='year_from'],[name='year_to']"
               hx-push-url="true">
        <label class="form-check-label" for="access-{{ value }}">{{ label }}</label>
      </div>
      {% endfor %}
    </fieldset>

    <hr>

    <!-- Language Filter -->
    {% if languages %}
    <fieldset class="mb-3">
      <legend class="form-label fw-semibold h6">Jezik</legend>
      {% for lang in languages %}
      <div class="form-check">
        <input class="form-check-input" type="checkbox" name="language"
               id="language-{{ lang }}" value="{{ lang }}"
               {% if lang in current_languages %}checked{% endif %}
               hx-get="{% url 'article-search' %}"
               hx-trigger="change"
               hx-target="#search-results"
               hx-include="[name='q'],[name='type'],[name='subject'],[name='access'],[name='language'],[name='year_from'],[name='year_to']"
               hx-push-url="true">
        <label class="form-check-label" for="language-{{ lang }}">{{ lang }}</label>
      </div>
      {% endfor %}
    </fieldset>
    <hr>
    {% endif %}

    <!-- Year Range Filter -->
    {% if year_range.min %}
    <fieldset class="mb-3">
      <legend class="form-label fw-semibold h6">Godina izdanja</legend>
      <div class="row g-2">
        <div class="col-6">
          <label for="year-from" class="form-label small">Od</label>
          <input type="number" class="form-control form-control-sm" id="year-from"
                 name="year_from" value="{{ current_year_from }}"
                 min="{{ year_range.min }}" max="{{ year_range.max }}"
                 placeholder="{{ year_range.min }}"
                 hx-get="{% url 'article-search' %}"
                 hx-trigger="change"
                 hx-target="#search-results"
                 hx-include="[name='q'],[name='type'],[name='subject'],[name='access'],[name='language'],[name='year_from'],[name='year_to']"
                 hx-push-url="true">
        </div>
        <div class="col-6">
          <label for="year-to" class="form-label small">Do</label>
          <input type="number" class="form-control form-control-sm" id="year-to"
                 name="year_to" value="{{ current_year_to }}"
                 min="{{ year_range.min }}" max="{{ year_range.max }}"
                 placeholder="{{ year_range.max }}"
                 hx-get="{% url 'article-search' %}"
                 hx-trigger="change"
                 hx-target="#search-results"
                 hx-include="[name='q'],[name='type'],[name='subject'],[name='access'],[name='language'],[name='year_from'],[name='year_to']"
                 hx-push-url="true">
        </div>
      </div>
    </fieldset>
    {% endif %}

    <!-- Clear All Filters -->
    {% if has_active_filters %}
    <hr>
    <a href="{% url 'article-search' %}?q={{ query }}" class="btn btn-outline-danger btn-sm w-100">
      <i class="bi bi-x-circle me-1" aria-hidden="true"></i>Obrišite sve filtere
    </a>
    {% endif %}
  </div>
</div>
```

### Srpski Karakteri (OBAVEZNO - videti project-context.md)

| Kontekst | ISPRAVNO |
|----------|----------|
| Sidebar naslov | "Filteri" |
| Tip publikacije | "Tip publikacije" |
| Naucna oblast | "Naučna oblast" |
| Tip pristupa | "Tip pristupa" |
| Jezik | "Jezik" |
| Godina | "Godina izdanja" |
| Od | "Od" |
| Do | "Do" |
| Clear dugme | "Obrišite sve filtere" |
| Mobile dugme | "Filteri" |
| Mobile primeni | "Primeni filtere" |
| Active badge | "Aktivni" |
| Zatvori offcanvas | "Zatvori" |
| Filter tag remove | aria-label="Ukloni filter" |

### Previous Story Learnings (Story 4.2 + Story 2.5)

1. **Filter sidebar pattern** iz `publication_list.html` (Story 2.5): `<aside class="col-lg-3">` sa `<div class="card">`, `<fieldset>/<legend>` grupisanje, multiselect checkbox-ovi sa HTMX atributima. KORISTITI IDENTICAN PATTERN.
2. **HTMX include pattern**: `hx-include="[name='search'],[name='type'],..."` - mora ukljuciti SVE filter parametre + search query. Za search page dodati `[name='q']`.
3. **HTMX target**: `hx-target="#search-results"` - isti ID kao u Story 4.2 `search_results.html` (`<div id="search-results">`).
4. **`hx-push-url="true"`** azurira browser URL sa filter parametrima - deljivi linkovi.
5. **SoftDeleteManager** automatski filtrira soft-deleted zapise. Ne treba dodavati `is_deleted=False` filter.
6. **Search query sacuvanje**: Kad se menja filter, `q` parametar MORA ostati u URL-u. Koristiti hidden input ili `hx-include`.
7. **`select_related("issue__publication__publisher")`** VEC pokriva join-ove potrebne za filtriranje. Nema dodatnih SQL upita.
8. **Portal CSS**: `static/css/portal.css` - VEC ukljucen u portal/base.html. Dodati filter stilove u OVAJ fajl.
9. **Pagination sa filterima**: Pagination linkovi moraju sacuvati sve filter parametre. `components/_pagination.html` vec koristi `request.GET.urlencode`.
10. **Test pattern**: pytest-django, `@pytest.mark.django_db`, Factory Boy. Koristiti `ArticleFactory`, `AuthorFactory`, `PublicationFactory`, `IssueFactory`.
11. **View pattern za filtere**: Validirati filter vrednosti pre primene - uporediti sa `PublicationType.choices` i `AccessType.choices`. Nevazece vrednosti IGNORISATI (ne bacati gresku).
12. **Dynamic filter options**: `subject_areas` i `languages` se citaju iz baze (Publication model) - prikazuju samo vrednosti koje postoje u sistemu.
13. **Year range filter** je NOV - nema ga u publication filter-u. Koristiti `Issue.objects.aggregate(Min/Max)` za odredjivanje opsega.
14. **Bootstrap 5 offcanvas** za mobile filtere - built-in Bootstrap komponenta, ne treba custom JS.
15. **Result count**: VEC postoji u `_search_results.html` partial - azurira se automatski kad HTMX zameni sadrzaj.
16. **Article card partial** (`_article_search_card.html`) NE treba menjati - vec prikazuje sve potrebne podatke.
17. **Test suite**: 1155 testova proslo u Story 4.2. Ne smemo imati regresije.
18. **Imports**: `PublicationType` i `AccessType` su VEC importovani u `portal/views.py` (linija 27-28).

### Git Commit Pattern

```
story-4-3: feat(portal): implementiraj Advanced Filtering za articles sa filter sidebar, HTMX filterima i mobile offcanvas (Story 4.3)
```

### Fajlovi za kreiranje (NOVI)

```
doi_portal/doi_portal/templates/portal/partials/_article_filter_sidebar.html  # Filter sidebar partial (reusable za desktop i mobile)
doi_portal/doi_portal/portal/tests/test_filters.py                            # Filter testovi (service + view)
```

### Fajlovi za modifikaciju (POSTOJECI)

```
doi_portal/doi_portal/portal/services.py                                      # Prosiriti search_articles() sa filters parametrom
doi_portal/doi_portal/portal/views.py                                         # Prosiriti ArticleSearchView sa filter context-om
doi_portal/doi_portal/templates/portal/search_results.html                    # Dodati filter sidebar layout i mobile offcanvas
doi_portal/doi_portal/templates/portal/partials/_search_results.html          # Dodati active filter tagove
doi_portal/doi_portal/static/css/portal.css                                   # Dodati filter sidebar i tag stilove
```

### Fajlovi koji se NE MENJAJU

```
doi_portal/doi_portal/templates/portal/base.html                               # VEC postoji - NE MENJATI
doi_portal/doi_portal/templates/portal/home.html                               # VEC postoji - NE MENJATI
doi_portal/doi_portal/templates/portal/partials/_article_search_card.html      # VEC postoji - NE MENJATI
doi_portal/doi_portal/templates/components/_pagination.html                    # VEC postoji - NE MENJATI (vec cuva GET parametre)
doi_portal/doi_portal/portal/templatetags/portal_tags.py                       # VEC postoji - NE MENJATI
doi_portal/doi_portal/articles/models.py                                       # VEC postoji - NE MENJATI
doi_portal/doi_portal/publications/models.py                                   # VEC postoji - NE MENJATI
doi_portal/doi_portal/issues/models.py                                         # VEC postoji - NE MENJATI
doi_portal/config/urls.py                                                      # VEC postoji - NE MENJATI (URL je vec /search/)
```

### Anti-Patterns (ZABRANJENO)

```python
# POGRESNO - Kreirati novu stranicu umesto prosiriti search
path("articles/filter/", ...)  # NE! Koristiti postojecu /search/ stranicu

# POGRESNO - Kreirati novu service funkciju umesto prosiriti
def filter_articles(filters):  # NE! Prosiriti search_articles() sa filters parametrom

# POGRESNO - Direktno filtrirati u view-u
def get_queryset(self):
    return Article.objects.filter(issue__publication__publication_type="JOURNAL")  # NE! Delegiraj u services.py

# POGRESNO - Zaboraviti sacuvati q parametar pri filtriranju
hx-include="[name='type'],[name='subject']"  # NE! Dodati [name='q']

# POGRESNO - Koristiti JavaScript umesto HTMX za filtere
fetch('/search/?type=JOURNAL')  # NE! HTMX hx-get pattern

# POGRESNO - Kreirati custom JavaScript za offcanvas
document.querySelector('#filterOffcanvas')...  # NE! Bootstrap 5 offcanvas sa data-bs-* atributima

# POGRESNO - Ne validirati filter vrednosti
queryset.filter(publication_type__in=request.GET.getlist("type"))  # NE! Validirati protiv choices

# POGRESNO - Filtrirati Article.language umesto Publication.language
queryset.filter(language__in=...)  # NE! Filtrirati po issue__publication__language

# POGRESNO - Kreirati novi partial za filter results
"portal/partials/_filtered_results.html"  # NE! Koristiti postojeci _search_results.html

# POGRESNO - Dodati novi URL route
path("search/filter/", ...)  # NE! Sve ide na /search/ sa GET parametrima

# POGRESNO - Koristiti full page reload za filtere
<form method="get" action="/search/">  # NE za filtere! Koristiti HTMX hx-get za inline update

# POGRESNO - Zaboraviti aria atribute
<div class="collapse">  # NE! Dodati aria-expanded, aria-controls
```

### Optimizacija Querysets (KRITICNO - NFR5)

```python
# ISPRAVNO - select_related VEC pokriva filter join-ove
articles = (
    Article.objects.filter(
        Q(status=ArticleStatus.PUBLISHED),
        Q(title__icontains=q) | ...,
    )
    .filter(issue__publication__publication_type__in=["JOURNAL"])  # Uses existing JOIN
    .select_related("issue__publication__publisher")  # VEC postoji
    .prefetch_related("authors")  # VEC postoji
    .distinct()
)

# ISPRAVNO - Dynamic filter options su lagani upiti
subject_areas = Publication.objects.exclude(subject_area="").values_list("subject_area", flat=True).distinct()
# Ovo je 1 mali SQL upit, ne utice na performanse

# ISPRAVNO - Year range aggregate
year_agg = Issue.objects.filter(status=IssueStatus.PUBLISHED).aggregate(
    min_year=Min("year"), max_year=Max("year")
)
# 1 SQL upit sa MIN/MAX, veoma brz
```

### Project Structure Notes

- Filter service logika ide u POSTOJECI `doi_portal/doi_portal/portal/services.py` (prosirenje `search_articles`)
- Filter view logika ide u POSTOJECI `doi_portal/doi_portal/portal/views.py` (prosirenje `ArticleSearchView`)
- Filter sidebar partial ide u `doi_portal/doi_portal/templates/portal/partials/_article_filter_sidebar.html` (NOVI fajl)
- Search results template se MODIFIKUJE: `doi_portal/doi_portal/templates/portal/search_results.html`
- HTMX partial se MODIFIKUJE: `doi_portal/doi_portal/templates/portal/partials/_search_results.html`
- Filter testovi idu u `doi_portal/doi_portal/portal/tests/test_filters.py` (NOVI fajl)
- Portal CSS azuriranje u postojecem `static/css/portal.css`

### Test Pattern

```python
# portal/tests/test_filters.py

import pytest
from django.db import models
from django.urls import reverse

from doi_portal.articles.models import ArticleStatus
from doi_portal.articles.tests.factories import ArticleFactory, AuthorFactory
from doi_portal.issues.models import IssueStatus
from doi_portal.issues.tests.factories import IssueFactory
from doi_portal.publications.models import AccessType, PublicationType
from doi_portal.publications.tests.factories import PublicationFactory
from doi_portal.publishers.tests.factories import PublisherFactory
from doi_portal.portal.services import search_articles


@pytest.mark.django_db
class TestSearchArticlesFilters:
    """Tests for search_articles() with filter parameters."""

    def _create_article(self, title, pub_type=PublicationType.JOURNAL,
                         subject="", language="sr", access=AccessType.OPEN,
                         year=2025):
        publisher = PublisherFactory()
        pub = PublicationFactory(
            publisher=publisher,
            publication_type=pub_type,
            subject_area=subject,
            language=language,
            access_type=access,
        )
        issue = IssueFactory(publication=pub, year=year, status=IssueStatus.PUBLISHED)
        return ArticleFactory(issue=issue, title=title, status=ArticleStatus.PUBLISHED)

    def test_filter_by_publication_type(self):
        """Filter returns only articles from matching publication type."""
        journal_art = self._create_article("Test Journal", pub_type=PublicationType.JOURNAL)
        conf_art = self._create_article("Test Conference", pub_type=PublicationType.CONFERENCE)
        results = search_articles("Test", filters={"types": [PublicationType.JOURNAL]})
        assert journal_art in results
        assert conf_art not in results

    def test_filter_by_subject_area(self):
        """Filter returns only articles from matching subject area."""
        math = self._create_article("Test Math", subject="Matematika")
        phys = self._create_article("Test Physics", subject="Fizika")
        results = search_articles("Test", filters={"subjects": ["Matematika"]})
        assert math in results
        assert phys not in results

    def test_filter_by_year_range(self):
        """Filter returns articles within year range."""
        old = self._create_article("Test Old", year=2020)
        new = self._create_article("Test New", year=2025)
        results = search_articles("Test", filters={"year_from": 2024, "year_to": 2026})
        assert new in results
        assert old not in results

    def test_combined_search_and_filter(self):
        """Search query and filters combine with AND logic."""
        match = self._create_article("Quantum Research", pub_type=PublicationType.JOURNAL)
        no_match = self._create_article("Quantum Conference", pub_type=PublicationType.CONFERENCE)
        results = search_articles("Quantum", filters={"types": [PublicationType.JOURNAL]})
        assert match in results
        assert no_match not in results

    def test_empty_filter_does_not_affect_results(self):
        """Empty filters dict does not affect results."""
        art = self._create_article("Test Article")
        results_no_filter = search_articles("Test")
        results_empty_filter = search_articles("Test", filters={})
        assert list(results_no_filter) == list(results_empty_filter)


@pytest.mark.django_db
class TestArticleSearchViewFilters:
    """Tests for ArticleSearchView filter context and behavior."""

    def test_filter_context_has_publication_types(self, client):
        """Context includes publication_types choices."""
        response = client.get(reverse("article-search"), {"q": "test"})
        assert "publication_types" in response.context

    def test_filter_context_has_access_types(self, client):
        """Context includes access_types choices."""
        response = client.get(reverse("article-search"), {"q": "test"})
        assert "access_types" in response.context

    def test_has_active_filters_false_by_default(self, client):
        """has_active_filters is False when no filters applied."""
        response = client.get(reverse("article-search"), {"q": "test"})
        assert response.context["has_active_filters"] is False

    def test_has_active_filters_true_with_filter(self, client):
        """has_active_filters is True when filter is applied."""
        response = client.get(reverse("article-search"), {"q": "test", "type": "JOURNAL"})
        assert response.context["has_active_filters"] is True

    def test_query_preserved_with_filters(self, client):
        """Search query q is preserved when filters are applied."""
        response = client.get(reverse("article-search"), {"q": "test", "type": "JOURNAL"})
        assert response.context["query"] == "test"

    def test_htmx_returns_partial_with_filters(self, client):
        """HTMX request returns partial template with filters applied."""
        response = client.get(
            reverse("article-search"),
            {"q": "test", "type": "JOURNAL"},
            HTTP_HX_REQUEST="true",
        )
        template_names = [t.name for t in response.templates]
        assert "portal/partials/_search_results.html" in template_names
```

### Dependencies (Python/Django)

Nema novih Python zavisnosti! Sve je vec instalirano:
- Django 5.2+ (ORM Q objects, ListView, aggregate Min/Max)
- Bootstrap 5 (CSS framework + offcanvas component)
- Bootstrap Icons (vec ukljuceni u portal/base.html CDN)
- HTMX 2.0.8 (vec ukljucen u portal/base.html)
- pytest-django + Factory Boy (vec u test setup-u)

### NFR Requirements

- **FR40:** Posetilac moze filtrirati publikacije po vrsti, oblasti, pristupu, jeziku - direktna implementacija
- **NFR5:** Pretraga < 2 sekunde - filter join-ovi koriste vec postojeci `select_related`, minimalni overhead
- **NFR2:** Javne stranice portala < 3 sekunde - HTMX inline update, bez full page reload
- **NFR14:** Semanticki HTML5 elementi - `<aside>`, `<fieldset>`, `<legend>`, `aria-live="polite"`
- **NFR17:** Keyboard navigacija - Tab through all filter checkboxes and inputs
- **NFR18:** Labels povezani sa input poljima - svaki checkbox ima `<label for="...">`

### References

- [Source: epics.md#Story 4.3: Advanced Filtering for Articles]
- [Source: epics.md#Epic 4: Public Portal Experience - FR40]
- [Source: prd.md#7. Public Portal - FR40 (Filtriranje publikacija)]
- [Source: prd.md#Performance - NFR5 (Pretraga < 2 sekunde)]
- [Source: architecture.md#Frontend Architecture - HTMX 2.0.8, Bootstrap 5]
- [Source: architecture.md#Implementation Patterns - naming conventions, HTMX patterns]
- [Source: ux-design-specification.md#Search & Filter Patterns - multiselect, collapsible, "Ocisti sve"]
- [Source: ux-design-specification.md#Filter Sidebar - Multiselect filtri, collapsible sekcije, clear all]
- [Source: ux-design-specification.md#Layout Adaptations - Filter sidebar: Sticky left desktop, Collapsible overlay mobile]
- [Source: ux-design-specification.md#Responsive Strategy - Mobile-first za portal]
- [Source: ux-design-specification.md#Accessibility - WCAG AA, keyboard nav, labels]
- [Source: project-context.md#Services Layer (Business Logic)]
- [Source: project-context.md#HTMX Pravila - partials sa _ prefix]
- [Source: project-context.md#Naming Konvencije - snake_case, PascalCase, kebab-case]
- [Source: project-context.md#Lokalizacija - Srpski Karakteri, sr-Latn]
- [Source: project-context.md#Testing (pytest-django) - Factory Boy]
- [Source: portal/views.py - Existing ArticleSearchView + PublicationPublicListView filter pattern]
- [Source: portal/services.py - Existing search_articles() function]
- [Source: portal/search_results.html - Existing search page template]
- [Source: portal/partials/_search_results.html - Existing HTMX partial]
- [Source: portal/publications/publication_list.html - Reference filter sidebar implementation]
- [Source: publications/models.py - PublicationType, AccessType, subject_area, language fields]
- [Source: issues/models.py - Issue.year field for year range filter]
- [Source: articles/models.py - Article model, status filtering]
- [Source: 4-2-article-search-functionality.md - Previous story learnings, search patterns]
- [Source: 4-1-portal-home-page.md - Portal home page patterns]

## Dev Agent Record

### Agent Model Used

Claude Opus 4.5 (claude-opus-4-5-20251101)

### Debug Log References

No blocking issues encountered.

### Completion Notes List

- Task 1: Extended `search_articles()` with `filters: dict | None = None` parameter. Implemented filtering by publication_type, subject_area, language, access_type, year_from, year_to via `issue__publication__*` and `issue__year__*` lookups. AND logic for combined filters. Empty/None filters gracefully ignored.
- Task 2: Extended `ArticleSearchView` with `_parse_filters()` method for parsing/validating GET params. Added filter choices (publication_types, access_types, subject_areas, languages), year_range (Min/Max from published Issues), active filter state (current_* variables), and `has_active_filters` boolean to context. Invalid year values (non-digit) are silently ignored.
- Task 3: Rewrote `search_results.html` with two-column layout (col-lg-3 sidebar + col-lg-9 content). Created `_article_filter_sidebar.html` partial with fieldset/legend groups for each filter type, HTMX attributes (hx-get, hx-trigger=change, hx-target, hx-include, hx-push-url), hidden q input, and clear-all-filters button. Added Bootstrap 5 offcanvas for mobile with "Filteri" toggle button and "Primeni filtere" close button.
- Task 4: Updated `_search_results.html` partial with active filter tags (color-coded badges with individual remove links), "(filtrirano)" suffix on result count when filters active.
- Task 5: Added CSS styles for `.filter-sidebar`, `.filter-tag` badges, mobile offcanvas adjustments.
- Task 6: Created 31 comprehensive tests in `test_filters.py`: 12 service tests (type, subject, language, access, year range, combined, empty, invalid, multi-select, None) + 19 view tests (filtered results, context fields, active filters state, URL params, query preservation, HTMX partial, clear link, year range, invalid years).
- All 176 portal tests pass. 1179/1193 total tests pass (11 pre-existing failures in test_pdf_upload.py unrelated to this story).

### File List

**New files:**
- `doi_portal/doi_portal/templates/portal/partials/_article_filter_sidebar.html` - Filter sidebar partial (reusable for desktop and mobile offcanvas)
- `doi_portal/doi_portal/portal/tests/test_filters.py` - 31 filter tests (service + view)

**Modified files:**
- `doi_portal/doi_portal/portal/services.py` - Extended search_articles() with filters parameter
- `doi_portal/doi_portal/portal/views.py` - Extended ArticleSearchView with _parse_filters() and filter context
- `doi_portal/doi_portal/templates/portal/search_results.html` - Two-column layout with filter sidebar + mobile offcanvas
- `doi_portal/doi_portal/templates/portal/partials/_search_results.html` - Active filter tags + filter info in result count
- `doi_portal/doi_portal/static/css/portal.css` - Filter sidebar and tag styles
- `_bmad-output/implementation-artifacts/sprint-status.yaml` - 4-3 status: ready-for-dev -> in-progress -> review
- `_bmad-output/implementation-artifacts/4-3-advanced-filtering-for-articles.md` - Task checkboxes, Dev Agent Record, status
