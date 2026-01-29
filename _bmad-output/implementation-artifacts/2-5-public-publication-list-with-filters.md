# Story 2.5: Public Publication List with Filters

Status: done

## Story

As a **visitor (posetilac)**,
I want **to browse and filter all publications on the public portal**,
So that **I can find publications relevant to my interests without needing to log in**.

## Background

Story 2.2 implementirala je javnu stranicu izdavača (PublisherPublicListView, PublisherPublicDetailView) u `portal/` app-u. Story 2.3/2.4 implementirale su Publication model sa type-specific poljima i admin CRUD. Ova priča dodaje javnu listu publikacija sa filterima u `portal/` app, koristeći uspostavljene pattern-e iz Story 2.2 za public views.

**FR Pokrivenost:** FR17 - Posetilac moze pregledati listu svih publikacija sa filterima
**FR40** (delimicno) - Posetilac moze filtrirati publikacije po vrsti, oblasti, pristupu, jeziku

## Acceptance Criteria

1. **Given** posetilac navigira na `/publications/`
   **When** se stranica ucita
   **Then** sve aktivne (non-deleted) publikacije su prikazane u card grid-u (3 kolone desktop, 2 tablet, 1 mobile)
   **And** svaki card prikazuje: naslovnu sliku (ili placeholder), naslov, tip ikonu, naziv izdavaca
   **And** stranica koristi javni portal Bootstrap 5 template (`portal/base.html`)

2. **Given** filter sidebar je prikazan
   **When** posetilac selektuje filtere
   **Then** publikacije se mogu filtrirati po: tipu (casopis, zbornik, knjiga, ostalo), naucnoj oblasti, tipu pristupa (otvoreni, ograniceni), jeziku
   **And** filteri koriste multiselect checkbox-ove
   **And** HTMX azurira rezultate bez reload-a cele stranice

3. **Given** posetilac unese termin pretrage
   **When** pretrazi u search box-u
   **Then** publikacije su filtrirane po naslovu
   **And** pretraga je debounced (300ms)
   **And** HTMX azurira rezultate

4. **Given** postoji vise od 12 publikacija
   **When** posetilac pregleda listu
   **Then** paginacija se prikazuje
   **And** aktivni filteri i pretraga se sacuvaju kroz stranice

5. **Given** posetilac klikne na publication card
   **When** navigira na detalj
   **Then** prikazuje se publication detail stranica sa listom izdanja (placeholder do Story 2.6/2.7)

6. **Given** ne postoje publikacije koje odgovaraju filterima
   **When** posetilac primeni filtere
   **Then** prikazuje se poruka "Nema publikacija koje odgovaraju kriterijumima pretrage."
   **And** dugme za resetovanje filtera je dostupno

7. **Given** navbar na portal/base.html
   **When** posetilac je na /publications/ stranici
   **Then** "Publikacije" link u navigaciji je aktivan (active class)

## Tasks / Subtasks

- [x] Task 1: Dodati URL route za public publications i HTMX podrška (AC: #1, #2, #3, #7)
  - [x] 1.1 Dodati `path("publications/", include("doi_portal.portal.urls_publications", namespace="portal-publications"))` u `config/urls.py`
  - [x] 1.2 Kreirati novi fajl `portal/urls_publications.py` sa `app_name = "portal-publications"` i URL patterns za `publication-list` i `publication-detail` (NE dodavati u postojeći `portal/urls.py` jer on koristi namespace "portal" za /publishers/)
  - [x] 1.3 Ažurirati `portal/base.html` navbar - dodati "Publikacije" link sa active class detektovanjem (između "Izdavači" i "O portalu")
  - [x] 1.4 **KRITIČNO:** Dodati HTMX `<script>` tag u `base.html` (ili `portal/base.html` css/javascript block) - HTMX 2.0.8 NIJE uključen ni u `base.html` ni u `portal/base.html`. Bez njega filteri i pretraga neće raditi. CDN: `<script src="https://unpkg.com/htmx.org@2.0.8" integrity="sha384-..." crossorigin="anonymous"></script>`

- [x] Task 2: Implementirati PublicationPublicListView u portal/views.py (AC: #1, #2, #3, #4, #6)
  - [x] 2.1 Kreirati `PublicationPublicListView(ListView)` - public, bez autentifikacije
  - [x] 2.2 `get_queryset()`: Publication.objects.select_related("publisher").order_by("title")
  - [x] 2.3 Filter po `publication_type` (GET param: `type`)
  - [x] 2.4 Filter po `subject_area` (GET param: `subject`)
  - [x] 2.5 Filter po `access_type` (GET param: `access`)
  - [x] 2.6 Filter po `language` (GET param: `language`)
  - [x] 2.7 Search po `title__icontains` (GET param: `search`)
  - [x] 2.8 Paginacija: `paginate_by = 12` (deljivo sa 3 za grid)
  - [x] 2.9 `get_context_data()`: breadcrumbs, filter choices, active filter values, unique subject_areas and languages iz baze

- [x] Task 3: Implementirati PublicationPublicDetailView u portal/views.py (AC: #5)
  - [x] 3.1 Kreirati `PublicationPublicDetailView(DetailView)` - public, slug lookup
  - [x] 3.2 Prikazati sve publication polja ukljucujuci type-specific
  - [x] 3.3 Breadcrumbs: Početna > Publikacije > {Publication Title}
  - [x] 3.4 Placeholder za listu izdanja (prazna lista, Story 2.6/2.7 ce popuniti)
  - [x] 3.5 Link ka izdavacu (publisher detail page)

- [x] Task 4: Kreirati template publication_list.html (AC: #1, #2, #3, #4, #6)
  - [x] 4.1 Extends `portal/base.html`
  - [x] 4.2 Dvo-kolonski layout: sidebar (col-lg-3) sa filterima + main (col-lg-9) sa grid-om
  - [x] 4.3 Search box sa HTMX: `hx-get`, `hx-trigger="keyup changed delay:300ms"`, `hx-target="#publication-results"`
  - [x] 4.4 Filter sidebar: checkbox grupe za tip, oblast, pristup, jezik sa HTMX
  - [x] 4.5 Card grid: `row-cols-1 row-cols-md-2 row-cols-lg-3`
  - [x] 4.6 Card: cover_image ili placeholder ikona, naslov, tip badge sa ikonom, publisher name
  - [x] 4.7 Paginacija sa sacuvanim filter parametrima
  - [x] 4.8 Empty state poruka sa reset dugmetom
  - [x] 4.9 Meta title i description za SEO

- [x] Task 5: Kreirati HTMX partial template _publication_grid.html (AC: #2, #3)
  - [x] 5.1 Kreirati `templates/portal/publications/partials/_publication_grid.html`
  - [x] 5.2 Sadrzi samo card grid + pagination (za HTMX swap)
  - [x] 5.3 View detektuje `HX-Request` header i vraca partial umesto full page

- [x] Task 6: Kreirati template publication_detail.html (AC: #5)
  - [x] 6.1 Extends `portal/base.html`
  - [x] 6.2 Prikazuje publication metadata (title, type, publisher, description, cover_image)
  - [x] 6.3 Type-specific fields sekcija (ISSN za journal, conference info za conference, ISBN za book)
  - [x] 6.4 Izdanja sekcija sa placeholder ("Izdanja će biti dostupna uskoro." do Story 2.6/2.7)
  - [x] 6.5 Link na publisher detail page
  - [x] 6.6 Meta title i description za SEO

- [x] Task 7: Ažurirati PublisherPublicDetailView placeholder (AC: indirektno, Story 2.2 popunjavanje)
  - [x] 7.1 Ažurirati `portal/views.py` - `PublisherPublicDetailView.get_context_data()`: zameniti `context["publications"] = []` sa `Publication.objects.filter(publisher=self.object).select_related("publisher").order_by("title")`
  - [x] 7.2 Ažurirati `publisher_detail.html` template da prikazuje realne publication card-ove sa linkovima na publication detail

- [x] Task 8: Napisati testove (AC: #1-#7)
  - [x] 8.1 Test publication list prikazuje sve aktivne publikacije
  - [x] 8.2 Test soft-deleted publikacije su sakrivene
  - [x] 8.3 Test filter po publication_type
  - [x] 8.4 Test filter po access_type
  - [x] 8.5 Test filter po subject_area
  - [x] 8.6 Test filter po language
  - [x] 8.7 Test search po naslovu
  - [x] 8.8 Test kombinacija filtera i pretrage
  - [x] 8.9 Test paginacija (12 per page)
  - [x] 8.10 Test HTMX request vraca partial template
  - [x] 8.11 Test non-HTMX request vraca full page
  - [x] 8.12 Test publication detail prikazuje type-specific fields
  - [x] 8.13 Test publication detail za deleted publication vraca 404
  - [x] 8.14 Test breadcrumbs na list i detail stranici
  - [x] 8.15 Test empty state kad nema rezultata
  - [x] 8.16 Test navbar active class za "Publikacije"
  - [x] 8.17 Test publisher detail sada prikazuje realne publikacije (Task 7)

## Dev Notes

### CRITICAL: Ovo je PUBLIC view - BEZ autentifikacije

Ova prica implementira JAVNE views u `portal/` app-u. Nema LoginRequiredMixin, nema permission check-ova. Slicno Story 2.2 (PublisherPublicListView/DetailView).

### Postojeći fajlovi koje treba modifikovati

- `doi_portal/config/urls.py` - Dodati publications public route (novi include za portal-publications)
- `doi_portal/doi_portal/portal/views.py` - Dodati PublicationPublicListView, PublicationPublicDetailView + ažurirati PublisherPublicDetailView placeholder
- `doi_portal/doi_portal/templates/portal/base.html` - Dodati "Publikacije" nav link
- `doi_portal/doi_portal/templates/base.html` - Dodati HTMX 2.0.8 script tag (HTMX NIJE uključen)
- `doi_portal/doi_portal/templates/portal/publishers/publisher_detail.html` - Ažurirati sa realnim publication card-ovima

**NE modifikovati:** `doi_portal/doi_portal/portal/urls.py` - postojeći fajl ostaje nepromenjen (samo publisher routes)

### Novi fajlovi

- `doi_portal/doi_portal/portal/urls_publications.py` - Novi URL fajl za public publications (namespace: portal-publications)
- `doi_portal/doi_portal/templates/portal/publications/publication_list.html`
- `doi_portal/doi_portal/templates/portal/publications/publication_detail.html`
- `doi_portal/doi_portal/templates/portal/publications/partials/_publication_grid.html`
- `doi_portal/doi_portal/portal/tests/test_views.py` - Dodati public publication tests (fajl već postoji sa publisher testovima)

### URL Routing Design (ODLUKA: Poseban URL fajl)

Postojeći `portal/urls.py` koristi `app_name = "portal"` i servira publisher routes pod `/publishers/`. Publikacije trebaju biti pod `/publications/` sa posebnim namespace-om. Rešenje: kreirati novi `portal/urls_publications.py`.

**config/urls.py** - Dodati NOV entry (pored postojećeg `portal` include-a):
```python
# config/urls.py - DODATI (pored postojećeg)
path("publishers/", include("doi_portal.portal.urls", namespace="portal")),  # Postojeće (Story 2.2)
path("publications/", include("doi_portal.portal.urls_publications", namespace="portal-publications")),  # NOVO
```

**portal/urls_publications.py** - KREIRATI NOV fajl:
```python
"""Public portal URL configuration for publications."""
from django.urls import path

from doi_portal.portal import views

app_name = "portal-publications"

urlpatterns = [
    path("", views.PublicationPublicListView.as_view(), name="publication-list"),
    path("<slug:slug>/", views.PublicationPublicDetailView.as_view(), name="publication-detail"),
]
```

**URL namespace reference u template-ovima:** `{% url 'portal-publications:publication-list' %}` i `{% url 'portal-publications:publication-detail' pub.slug %}`

### View Pattern (Sledi Story 2.2 pattern tacno)

```python
# portal/views.py - DODATI

class PublicationPublicListView(ListView):
    """
    Public listing of all active publications with filters.
    FR17: Posetilac moze pregledati listu svih publikacija sa filterima.
    """
    model = Publication
    template_name = "portal/publications/publication_list.html"
    context_object_name = "publications"
    paginate_by = 12

    def get_queryset(self):
        queryset = Publication.objects.select_related("publisher").order_by("title")

        # Filter by type
        pub_type = self.request.GET.get("type")
        if pub_type and pub_type in [c[0] for c in PublicationType.choices]:
            queryset = queryset.filter(publication_type=pub_type)

        # Filter by subject area
        subject = self.request.GET.get("subject")
        if subject:
            queryset = queryset.filter(subject_area=subject)

        # Filter by access type
        access = self.request.GET.get("access")
        if access and access in [c[0] for c in AccessType.choices]:
            queryset = queryset.filter(access_type=access)

        # Filter by language
        language = self.request.GET.get("language")
        if language:
            queryset = queryset.filter(language=language)

        # Search by title
        search = self.request.GET.get("search")
        if search:
            queryset = queryset.filter(title__icontains=search)

        return queryset

    def get_template_names(self):
        """Return partial template for HTMX requests."""
        if self.request.headers.get("HX-Request"):
            return ["portal/publications/partials/_publication_grid.html"]
        return [self.template_name]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["breadcrumbs"] = [
            {"label": "Početna", "url": reverse("home")},
            {"label": "Publikacije", "url": None},
        ]
        context["publication_types"] = PublicationType.choices
        context["access_types"] = AccessType.choices

        # Dynamic filter options from database
        context["subject_areas"] = (
            Publication.objects
            .exclude(subject_area="")
            .values_list("subject_area", flat=True)
            .distinct()
            .order_by("subject_area")
        )
        context["languages"] = (
            Publication.objects
            .values_list("language", flat=True)
            .distinct()
            .order_by("language")
        )

        # Active filters for UI state
        context["current_type"] = self.request.GET.get("type", "")
        context["current_subject"] = self.request.GET.get("subject", "")
        context["current_access"] = self.request.GET.get("access", "")
        context["current_language"] = self.request.GET.get("language", "")
        context["search_query"] = self.request.GET.get("search", "")

        return context
```

### HTMX Pattern (KRITICHNO - pratiti project-context.md)

**Pravilo:** HTMX responses UVEK vracaju HTML, NIKAD JSON.

```html
<!-- Search box sa HTMX -->
<input type="text"
       name="search"
       class="form-control"
       placeholder="Pretrazite publikacije..."
       value="{{ search_query }}"
       hx-get="{% url 'portal-publications:publication-list' %}"
       hx-trigger="keyup changed delay:300ms"
       hx-target="#publication-results"
       hx-include="[name='type'],[name='subject'],[name='access'],[name='language']"
       hx-push-url="true">

<!-- Filter checkboxes sa HTMX -->
<input type="checkbox"
       name="type"
       value="JOURNAL"
       hx-get="{% url 'portal-publications:publication-list' %}"
       hx-trigger="change"
       hx-target="#publication-results"
       hx-include="[name='search'],[name='type'],[name='subject'],[name='access'],[name='language']">
```

### Publication Card Design

```html
<article class="card h-100 publication-card">
    {% if publication.cover_image %}
    <img src="{{ publication.cover_image.url }}"
         class="card-img-top"
         alt="{{ publication.title }} naslovna slika"
         loading="lazy">
    {% else %}
    <div class="card-img-placeholder text-center py-4 bg-light">
        <i class="{{ publication.type_icon }} display-4 text-muted" aria-hidden="true"></i>
    </div>
    {% endif %}
    <div class="card-body">
        <div class="mb-2">
            <span class="badge bg-secondary">
                <i class="{{ publication.type_icon }} me-1" aria-hidden="true"></i>
                {{ publication.type_display }}
            </span>
            {% if publication.access_type == "OPEN" %}
            <span class="badge bg-success ms-1">
                <i class="bi bi-unlock me-1" aria-hidden="true"></i>Otvoreni pristup
            </span>
            {% endif %}
        </div>
        <h3 class="h6 card-title">
            <a href="{% url 'portal-publications:publication-detail' publication.slug %}"
               class="text-decoration-none stretched-link">
                {{ publication.title }}
            </a>
        </h3>
        <p class="card-text text-muted small mb-0">
            <i class="bi bi-building me-1" aria-hidden="true"></i>
            {{ publication.publisher.name }}
        </p>
    </div>
</article>
```

### Srpski Karakteri (OBAVEZNO - videti project-context.md)

Svi UI tekstovi MORAJU koristiti ispravne srpske dijakritičke znake: `č`, `ć`, `š`, `đ`, `ž` (i velika: `Č`, `Ć`, `Š`, `Đ`, `Ž`).

**KRITIČNI srpski tekstovi za ovu priču (tačne vrednosti za template-ove):**

| Kontekst | ISPRAVNO (sa dijakritikama) |
|----------|----------------------------|
| Naslov stranice | "Publikacije" |
| Search placeholder | "Pretražite publikacije..." |
| Filter label - tip | "Tip publikacije" |
| Filter label - oblast | "Naučna oblast" |
| Filter label - pristup | "Tip pristupa" |
| Filter label - jezik | "Jezik" |
| Empty state poruka | "Nema publikacija koje odgovaraju kriterijumima pretrage." |
| Reset dugme | "Obrišite sve filtere" |
| Breadcrumb početna | "Početna" (sa č - isto kao Story 2.2) |
| Paginacija prethodna | "Prethodna" |
| Paginacija sledeća | "Sledeća" |
| Izdanja placeholder | "Izdanja će biti dostupna uskoro." |

**NAPOMENA:** Story 2.2 `portal/views.py` već koristi `"Početna"` sa ispravnom dijakritikom. Slediti isti pattern u svim novim view-ovima i template-ovima.

### SEO Meta Tags Pattern (iz Story 2.2)

```html
{% block title %}Publikacije - DOI Portal{% endblock title %}
{% block meta_description %}Pregledajte sve naučne publikacije na DOI Portalu. Filtrirajte po tipu, oblasti, jeziku i pristupu.{% endblock meta_description %}
```

### Accessibility (NFR14-NFR18)

- Koristiti `<article>` tag za svaki card (semanticki HTML5)
- Alt tekst za sve slike
- ARIA labels na filter kontrolama
- `aria-live="polite"` na `#publication-results` div za HTMX updates
- Keyboard navigacija za filtere

### Paginacija Pattern

```html
{% if is_paginated %}
<nav aria-label="Navigacija stranica">
    <ul class="pagination justify-content-center mt-4">
        {% if page_obj.has_previous %}
        <li class="page-item">
            <a class="page-link" href="?page={{ page_obj.previous_page_number }}{% for key, val in request.GET.items %}{% if key != 'page' %}&{{ key }}={{ val }}{% endif %}{% endfor %}">
                Prethodna
            </a>
        </li>
        {% endif %}
        <!-- page numbers -->
        {% if page_obj.has_next %}
        <li class="page-item">
            <a class="page-link" href="?page={{ page_obj.next_page_number }}{% for key, val in request.GET.items %}{% if key != 'page' %}&{{ key }}={{ val }}{% endif %}{% endfor %}">
                Sledeća
            </a>
        </li>
        {% endif %}
    </ul>
</nav>
{% endif %}
```

### Publisher Detail Update (Story 2.2 popunjavanje)

Story 2.2 `PublisherPublicDetailView.get_context_data()` ima placeholder:
```python
context["publications"] = []  # Story 2.3 will populate
```

Ova prica TREBA azurirati ovo da vraca stvarne publikacije:
```python
context["publications"] = Publication.objects.filter(
    publisher=self.object
).select_related("publisher").order_by("title")
```

Takodje azurirati `publisher_detail.html` template da koristi realne publication card-ove sa linkovima.

### Testing Strategy

Koristiti iste factory pattern-e kao u `portal/tests/test_views.py` i `publications/tests/factories.py`.

```python
# portal/tests/test_views.py - DODATI

@pytest.mark.django_db
class TestPublicationPublicListView:
    def test_list_shows_active_publications(self, client, publication_factory):
        pub = publication_factory(title="Test Casopis")
        response = client.get(reverse("portal-publications:publication-list"))
        assert response.status_code == 200
        assert "Test Casopis" in response.content.decode()

    def test_deleted_publications_hidden(self, client, publication_factory):
        pub = publication_factory(title="Obrisana", is_deleted=True)
        response = client.get(reverse("portal-publications:publication-list"))
        assert "Obrisana" not in response.content.decode()

    def test_filter_by_type(self, client, publication_factory):
        pub_j = publication_factory(publication_type="JOURNAL", title="Casopis")
        pub_b = publication_factory(publication_type="BOOK", title="Knjiga")
        response = client.get(reverse("portal-publications:publication-list") + "?type=JOURNAL")
        content = response.content.decode()
        assert "Casopis" in content
        assert "Knjiga" not in content

    def test_htmx_returns_partial(self, client, publication_factory):
        publication_factory(title="HTMX Test")
        response = client.get(
            reverse("portal-publications:publication-list"),
            HTTP_HX_REQUEST="true",
        )
        assert response.status_code == 200
        # Partial should NOT contain <html> or extend base
        content = response.content.decode()
        assert "<!DOCTYPE" not in content
```

### Project Structure Notes

- Svi portal views: `doi_portal/doi_portal/portal/views.py`
- Portal URLs: `doi_portal/doi_portal/portal/urls.py` (publishers) + `portal/urls_publications.py` (publications)
- Portal templates: `doi_portal/doi_portal/templates/portal/publications/`
- HTMX partials: `doi_portal/doi_portal/templates/portal/publications/partials/` (sa `_` prefix)
- Testovi: `doi_portal/doi_portal/portal/tests/test_views.py`
- Config URLs: `doi_portal/config/urls.py`

### NFR Requirements Addressed

- **NFR2:** Javne stranice portala < 3 sekunde - `select_related("publisher")` za optimizaciju
- **NFR5:** Pretraga < 2 sekunde - `title__icontains` sa DB indeksom
- **NFR14:** Semanticki HTML5 - `<article>`, `<nav>`, `<main>`
- **NFR15:** Alt tekst za sve slike - cover images i placeholder-i
- **NFR16:** Kontrast 4.5:1 - Bootstrap 5 default
- **NFR17:** Keyboard navigacija - filter kontrole i linkovi

### Anti-Patterns to Avoid

```python
# POGRESNO - JSON response za HTMX
return JsonResponse({"publications": [...]})

# ISPRAVNO - HTML partial
return render(request, "portal/publications/partials/_publication_grid.html", context)

# POGRESNO - Login required na public view
class PublicationPublicListView(LoginRequiredMixin, ListView):

# ISPRAVNO - Bez autentifikacije
class PublicationPublicListView(ListView):

# POGRESNO - Hardkodovan tip bez validacije
pub_type = request.GET.get("type")
queryset = queryset.filter(publication_type=pub_type)

# ISPRAVNO - Validacija gegen choices
if pub_type and pub_type in [c[0] for c in PublicationType.choices]:
    queryset = queryset.filter(publication_type=pub_type)

# POGRESNO - Stavljati views u publications/views.py
# Ovo su ADMIN views, ne public

# ISPRAVNO - Public views idu u portal/views.py
# Admin views ostaju u publications/views.py
```

### Git Commit Pattern

```
story-2-5: feat(portal): implementiraj Public Publication List sa filterima i HTMX pretragom (Story 2.5)
```

### Dependencies

**Zavisi od:**
- Story 2.1 (Publisher Model) - DONE
- Story 2.2 (Public Publisher Page - uspostavlja portal/ patterns) - DONE
- Story 2.3 (Publication Model) - DONE
- Story 2.3a (Crossref fields) - DONE
- Story 2.4 (Publication Admin - model properties) - DONE

**Blokira:**
- Story 2.6 (Issue Model) - publication detail ce prikazati issues
- Story 2.7 (Public Issue List & Detail) - publication detail -> issue navigation
- Story 4.1 (Portal Home Page) - moze koristiti publication cards pattern

### Previous Story Learnings (Story 2.2 / 2.4)

1. **Portal base template** = `portal/base.html` - extends `base.html`, dodaje header, nav, footer
2. **SoftDeleteManager** - automatski iskljucuje is_deleted=True, ne treba explicitni filter
3. **Breadcrumbs format**: `[{"label": "...", "url": "..."}, {"label": "...", "url": None}]`
4. **Card pattern**: `<article class="card h-100">` sa card-img-top, card-body, card-footer
5. **Publisher detail placeholder**: `context["publications"] = []` - TREBA popuniti u ovoj prici
6. **URL namespace**: portal app koristi `app_name = "portal"`, novi URL fajl koristi `app_name = "portal-publications"`
7. **Template location**: Portal templates su u `templates/portal/` subdirektorijumu, NE `templates/publications/` (to su admin templates)
8. **Audit log nije potreban** za public views - nema izmena podataka
9. **Serbian diacritics** - KRITIČNO: koristiti `č`, `ć`, `š`, `đ`, `ž` (sa dijakritikama) - videti tabelu iznad u sekciji "Srpski Karakteri"
10. **HTMX CDN** - proveriti da li je HTMX vec ukljucen u `portal/base.html` ili `base.html`; ako nije, dodati

### HTMX Availability Check - KONFIRMOVANO: HTMX NIJE UKLJUČEN

**VERIFIKOVANO:** Ni `base.html` ni `portal/base.html` NE uključuju HTMX skriptu. Trenutno `base.html` uključuje samo Bootstrap 5 JS i Alpine.js. Ova priča MORA dodati HTMX u `base.html` (javascript block) ili u `portal/base.html` (css/javascript override block):

```html
<!-- HTMX 2.0.8 (per project-context.md) -->
<script src="https://unpkg.com/htmx.org@2.0.8"
        integrity="sha384-..."
        crossorigin="anonymous"></script>
```

**PREPORUKA:** Dodati u `base.html` javascript block (pored Alpine.js) jer će HTMX trebati i admin panel-u u budućim pričama. Alternativno, dodati samo u `portal/base.html` ako želimo ograničiti scope.

Ovo je pokriveno u Task 1.4.

### References

- [Source: epics.md#Story 2.5: Public Publication List with Filters]
- [Source: prd.md#FR17 - Posetilac moze pregledati listu svih publikacija sa filterima]
- [Source: prd.md#FR40 - Posetilac moze filtrirati publikacije po vrsti, oblasti, pristupu, jeziku]
- [Source: architecture.md#Frontend Architecture - HTMX Use Cases]
- [Source: architecture.md#Structure Patterns - Template Organization]
- [Source: project-context.md#HTMX Pravila]
- [Source: project-context.md#Lokalizacija - Srpski Karakteri]
- [Source: project-context.md#Template Struktura]
- [Source: 2-2-public-publisher-page.md - Portal public view patterns]
- [Source: 2-4-publication-admin-list-edit.md - Publication model properties, type_icon, type_display]

## Dev Agent Record

### Agent Model Used

Claude Opus 4.5 (claude-opus-4-5-20251101)

### Debug Log References

- All 66 portal tests passing (428 total project tests, 0 failures)
- Full regression test suite: 428 passed, 3 skipped

### Completion Notes List

- Task 1: Added URL route in config/urls.py, created urls_publications.py, updated navbar with active class detection, added HTMX 2.0.8 script to base.html
- Task 2: PublicationPublicListView with 5 filters (type, subject, access, language, search), pagination (12/page), HTMX partial support via get_template_names()
- Task 3: PublicationPublicDetailView with slug lookup, breadcrumbs, type-specific fields rendering, issues placeholder
- Task 4: publication_list.html - two-column layout with sidebar filters, HTMX search (300ms debounce), radio button filters with reset, empty state
- Task 5: _publication_grid.html partial - card grid + pagination, used for HTMX swap
- Task 6: publication_detail.html - journal/conference/book specific sections, publisher link, issues placeholder, SEO meta
- Task 7: Updated PublisherPublicDetailView to return real publications queryset, updated publisher_detail.html with publication cards
- Task 8: 38 new tests for Story 2.5 (all passing), updated 1 existing test (publications placeholder -> queryset)
- All Serbian text uses proper diacritics (č, ć, š, đ, ž)
- No authentication on public views
- Filter validation: invalid type/access values ignored (no 500 errors)

### File List

**Modified:**
- `doi_portal/config/urls.py` - Added publications URL include
- `doi_portal/doi_portal/portal/views.py` - Added PublicationPublicListView, PublicationPublicDetailView, updated PublisherPublicDetailView
- `doi_portal/doi_portal/templates/base.html` - Added HTMX 2.0.8 script tag
- `doi_portal/doi_portal/templates/portal/base.html` - Added "Publikacije" nav link with active class
- `doi_portal/doi_portal/templates/portal/publishers/publisher_detail.html` - Updated with real publication cards
- `doi_portal/doi_portal/portal/tests/factories.py` - Added PublicationFactory
- `doi_portal/doi_portal/portal/tests/test_views.py` - Added 38 Story 2.5 tests, updated 1 existing test

**Created:**
- `doi_portal/doi_portal/portal/urls_publications.py` - New URL config for public publications
- `doi_portal/doi_portal/templates/portal/publications/publication_list.html` - Publication list template
- `doi_portal/doi_portal/templates/portal/publications/publication_detail.html` - Publication detail template
- `doi_portal/doi_portal/templates/portal/publications/partials/_publication_grid.html` - HTMX partial for card grid
