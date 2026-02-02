# Story 4.2: Article Search Functionality

Status: done

## Story

As a **visitor (posetilac)**,
I want **to search for articles by title, author, or keywords**,
So that **I can find specific content I'm looking for**.

## Background

Ovo je druga prica u Epiku 4 (Public Portal Experience). Story 4.1 je implementirala Portal Home Page sa hero search bar-om koji ima `action="/search/"` i `name="q"` input. Ovaj story kreira search results stranicu na koju korisnik biva preusmeren nakon pretrage. Pretraga pretrazuje PUBLISHED clanke po: naslovu, imenima autora, kljucnim recima i apstraktu. Rezultati se prikazuju kao article kartice sa paginacijom.

**FR Pokrivenost:**
- FR39: Posetilac moze pretrazivati clanke po nazivu, autoru i kljucnim recima

**NFR Pokrivenost:**
- NFR5: Pretraga - Rezultati < 2 sekunde
- NFR2: Javne stranice portala - ucitavanje < 3 sekunde
- NFR14-NFR18: Accessibility (semanticki HTML5, alt tekst, kontrast, keyboard, labels)

**Zavisnosti (sve DONE):**
- Story 4.1: Portal Home Page - hero search bar sa `action="/search/"` i `name="q"`
- Story 3.1: Article Model - `Article`, `ArticleStatus`, `Author` modeli
- Story 2.2: Public Publisher Page - `portal/base.html` template sa sticky header, breadcrumbs, footer
- Story 2.5: Public Publication List - HTMX filter pattern, pagination pattern

**Blokira:**
- Story 4.3: Advanced Filtering for Articles - dodaje filter sidebar na search results stranicu

## Acceptance Criteria

1. **Given** posetilac navigira na search ili koristi search bar
   **When** unese search query
   **Then** search prihvata minimum 3 karaktera
   **And** search je debounced (300ms delay) za HTMX live search (opciono - primarno je form submit)

2. **Given** search query je submitovan
   **When** rezultati se procesiraju
   **Then** clanci se pretrazuju po: naslov (title), imena autora (given_name, surname), kljucne reci (keywords JSON), apstrakt (abstract)
   **And** rezultati se ucitavaju za manje od 2 sekunde (NFR5)
   **And** pretrazuju se SAMO clanci sa statusom PUBLISHED

3. **Given** rezultati pretrage su prikazani
   **When** posetilac pregleda stranicu rezultata
   **Then** rezultati se prikazuju kao article kartice sa: naslov, autori, publikacija, godina
   **And** search term je istaknut (highlight) u rezultatima
   **And** prikazan je ukupan broj rezultata

4. **Given** nema rezultata pretrage
   **When** posetilac pregleda prazne rezultate
   **Then** prikazuje se poruka: "Nema pronađenih članaka za '{query}'"
   **And** ponudjeni su predlozi (proverite pravopis, pokušajte druge ključne reči)

5. **Given** postoji mnogo rezultata
   **When** posetilac skroluje rezultate
   **Then** paginacija je prikazana (20 rezultata po stranici)
   **And** prikazana je trenutna stranica i ukupan broj stranica

6. **Given** posetilac klikne na rezultat pretrage
   **When** navigira na clanak
   **Then** otvara se article landing stranica (placeholder link za Story 4.4)

7. **Given** posetilac pristupi /search/ bez query parametra
   **When** stranica se ucitava
   **Then** prikazuje se search forma sa uputstvom
   **And** ne izvrsava se prazna pretraga

8. **Given** stranica se ucitava
   **When** analiziramo pristupacnost
   **Then** semanticki HTML5 elementi su korisceni
   **And** search input ima aria-label
   **And** rezultati koriste `<article>` elemente
   **And** paginacija ima aria-label i current page oznaku

## Tasks / Subtasks

- [x] Task 1: Kreirati search service u `portal/services.py` (AC: #2, #7)
  - [x] 1.1 Dodati `search_articles(query: str, page: int = 1, per_page: int = 20)` funkciju
  - [x] 1.2 Pretraga po title (icontains), author surname/given_name, keywords (JSON contains), abstract (icontains)
  - [x] 1.3 Filtrirati SAMO `status=ArticleStatus.PUBLISHED` clanke
  - [x] 1.4 SoftDeleteManager vec filtrira is_deleted=True - ne dodavati dodatni filter
  - [x] 1.5 Koristiti `select_related("issue__publication__publisher")` za N+1 prevenciju
  - [x] 1.6 Koristiti `prefetch_related("authors")` za N+1 prevenciju na autorima
  - [x] 1.7 Koristiti Django Q objects za OR kombinaciju search polja
  - [x] 1.8 Vratiti QuerySet (paginacija se radi u view-u sa Django Paginator)

- [x] Task 2: Kreirati `ArticleSearchView` u `portal/views.py` (AC: #1, #2, #3, #4, #5, #7)
  - [x] 2.1 Kreirati `ArticleSearchView(ListView)` klasu
  - [x] 2.2 Template: `portal/search_results.html`
  - [x] 2.3 `paginate_by = 20`
  - [x] 2.4 Citati query iz `request.GET.get("q", "").strip()`
  - [x] 2.5 Ako je query prazan ili < 3 karaktera, prikazati praznu stranicu sa formom
  - [x] 2.6 Ako je query validan, delegirati u `search_articles()` service
  - [x] 2.7 Context: `query`, `result_count`, `breadcrumbs`
  - [x] 2.8 HTMX podrska: `get_template_names()` vraca partial za HX-Request

- [x] Task 3: Dodati URL route za search (AC: #1)
  - [x] 3.1 U `config/urls.py` dodati: `path("search/", ArticleSearchView.as_view(), name="article-search")`
  - [x] 3.2 Importovati `ArticleSearchView` iz `doi_portal.portal.views`
  - [x] 3.3 URL MORA biti `/search/` - hero search bar u home.html vec koristi `action="/search/"`

- [x] Task 4: Kreirati `portal/search_results.html` template (AC: #3, #4, #5, #7, #8)
  - [x] 4.1 Extend `portal/base.html`
  - [x] 4.2 Override `portal_content` block
  - [x] 4.3 Search header sa search input formom (prepopulated sa query)
  - [x] 4.4 Broj rezultata: "Pronađeno X članaka za '{query}'"
  - [x] 4.5 Article kartice u grid layout-u (1 kolona - lista)
  - [x] 4.6 Svaka kartica: naslov, autori (max 3 + "i dr."), publikacija ime, godina, kljucne reci kao tagovi
  - [x] 4.7 Prazan state: "Nema pronađenih članaka za '{query}'" sa predlozima
  - [x] 4.8 Prazan state bez query: "Unesite pojam za pretragu" sa search formom
  - [x] 4.9 Paginacija: koristiti Bootstrap pagination component
  - [x] 4.10 Breadcrumbs: Pocetna > Pretraga

- [x] Task 5: Kreirati `portal/partials/_search_results.html` partial za HTMX (AC: #1)
  - [x] 5.1 Sadrzi samo rezultate i paginaciju (bez header/breadcrumbs)
  - [x] 5.2 Koristi se za HTMX inline update rezultata (opcionalno za Story 4.3)

- [x] Task 6: Kreirati `portal/partials/_article_search_card.html` partial (AC: #3, #6)
  - [x] 6.1 Article kartica za search rezultate
  - [x] 6.2 Prikazuje: naslov (link na article detail), autori, publikacija, godina, kljucne reci
  - [x] 6.3 Link na article landing page: placeholder URL `/articles/{pk}/` (Story 4.4 ce dodati pravi URL)
  - [x] 6.4 Search term highlight u naslovu i apstraktu (Django template filter ili custom)

- [x] Task 7: Highlight search terms (AC: #3)
  - [x] 7.1 Kreirati custom template filter `highlight_search` u `portal/templatetags/portal_tags.py`
  - [x] 7.2 Filter wrapa matching text u `<mark>` tag za vizuelni highlight
  - [x] 7.3 Filter je case-insensitive
  - [x] 7.4 Filter escapeuje HTML pre wrappinga (XSS prevencija)

- [x] Task 8: Responsivnost i pristupacnost (AC: #8)
  - [x] 8.1 Search results: full-width lista na svim velicinama
  - [x] 8.2 Article kartice: responsive padding
  - [x] 8.3 Search form: full-width na mobile
  - [x] 8.4 Semanticki HTML: `<main>`, `<section>`, `<article>` za svaki rezultat
  - [x] 8.5 Search input ima `role="search"` na form i `aria-label` na input
  - [x] 8.6 Paginacija: `aria-label="Navigacija stranica"`, `aria-current="page"` za aktivnu
  - [x] 8.7 Keyboard navigacija: Tab kroz rezultate i pagination
  - [x] 8.8 Touch targets min 44px na mobile

- [x] Task 9: Kreirati testove (AC: #1-#8)
  - [x] 9.1 Service test: `search_articles("test")` vraca clanke sa "test" u naslovu
  - [x] 9.2 Service test: search vraca clanke po prezimenu autora
  - [x] 9.3 Service test: search vraca clanke po kljucnim recima (JSON field)
  - [x] 9.4 Service test: search vraca clanke po apstraktu
  - [x] 9.5 Service test: search NE vraca DRAFT/REVIEW/READY clanke (samo PUBLISHED)
  - [x] 9.6 Service test: search NE vraca soft-deleted clanke
  - [x] 9.7 Service test: search sa praznim query vraca prazan QuerySet
  - [x] 9.8 Service test: search koristi select_related i prefetch_related (query count test)
  - [x] 9.9 View test: GET /search/ vraca 200
  - [x] 9.10 View test: koristi portal/search_results.html template
  - [x] 9.11 View test: GET /search/?q=test vraca rezultate u context-u
  - [x] 9.12 View test: context sadrzi `query` i `result_count`
  - [x] 9.13 View test: prazan query prikazuje formu bez rezultata
  - [x] 9.14 View test: query < 3 karaktera prikazuje poruku o minimalnoj duzini
  - [x] 9.15 View test: paginacija funkcionise (page=2)
  - [x] 9.16 View test: nema rezultata prikazuje prazan state sa porukom
  - [x] 9.17 View test: breadcrumbs sadrze "Pocetna" i "Pretraga"
  - [x] 9.18 View test: nema autentifikacije - javna stranica
  - [x] 9.19 View test: HTMX request vraca partial template
  - [x] 9.20 Template filter test: `highlight_search` wrapa match u `<mark>` tag
  - [x] 9.21 Template filter test: highlight je case-insensitive
  - [x] 9.22 Template filter test: highlight escapeuje HTML input (XSS)

## Dev Notes

### KRITICNO: Search URL vec definisan u Story 4.1

Home page hero search bar (implementiran u Story 4.1) vec koristi:
```html
<form action="/search/" method="get" class="mx-auto" style="max-width: 600px;">
  <div class="input-group input-group-lg">
    <input type="search" name="q" class="form-control"
           placeholder="Pretražite članke po naslovu, autoru, ključnim rečima..."
           aria-label="Pretraga članaka">
    <button type="submit" class="btn btn-light">
      <i class="bi bi-search"></i>
    </button>
  </div>
</form>
```

URL MORA biti `/search/` i query parametar MORA biti `q`. Promena bi slomila home page search.

### Portal Base Template (VEC POSTOJI)

`portal/base.html` je kreiran u Story 2.2 i sadrzi:
- Sticky header sa navbar (DOI Portal brand, Izdavaci, Publikacije, O portalu, Prijava/Dashboard)
- Breadcrumbs sekcija (conditional prikazivanje)
- Main content area: `{% block portal_content %}`
- Footer sa info o portalu
- Bootstrap Icons CDN
- Portal CSS: `{% static 'css/portal.css' %}`

Search results template MORA da extenduje `portal/base.html` i koristi `{% block portal_content %}`.

### Services Layer Pattern

Sva business logika za pretragu ide u `portal/services.py`. View DELEGIRA u service sloj. Service vec postoji sa `get_portal_statistics()` i `get_recent_publications()` iz Story 4.1.

```python
# portal/services.py - DODATI novu funkciju

from django.db.models import Q, QuerySet

from doi_portal.articles.models import Article, ArticleStatus, Author


def search_articles(query: str) -> QuerySet[Article]:
    """
    Search published articles by title, author names, keywords, and abstract.

    FR39: Posetilac moze pretrazivati clanke po nazivu, autoru i kljucnim recima.
    NFR5: Rezultati < 2 sekunde.

    Only PUBLISHED articles are searched.
    SoftDeleteManager already excludes is_deleted=True records.

    Args:
        query: Search term (minimum 3 characters expected, caller validates).

    Returns:
        QuerySet of matching Article objects with related data pre-fetched.
    """
    if not query or len(query.strip()) < 3:
        return Article.objects.none()

    q = query.strip()

    # Find author IDs matching the search query
    matching_author_article_ids = (
        Author.objects.filter(
            Q(given_name__icontains=q) | Q(surname__icontains=q)
        )
        .values_list("article_id", flat=True)
        .distinct()
    )

    return (
        Article.objects.filter(
            Q(status=ArticleStatus.PUBLISHED),
            Q(title__icontains=q)
            | Q(abstract__icontains=q)
            | Q(keywords__icontains=q)
            | Q(id__in=matching_author_article_ids),
        )
        .select_related("issue__publication__publisher")
        .prefetch_related("authors")
        .order_by("-published_at", "-created_at")
        .distinct()
    )
```

**VAZNO o keywords JSON pretrazivanju:**
- `keywords` je `JSONField(default=list)` - cuva listu stringova: `["keyword1", "keyword2"]`
- `keywords__icontains` radi na PostgreSQL jer pretrazuje JSON text representation
- Alternativno moze se koristiti `keywords__contains` za egzaktni match jednog elementa

**VAZNO o Author pretrazivanju:**
- Author je ForeignKey na Article (ne M2M), sa `related_name="authors"`
- Pretraga po imenu autora zahteva subquery ili annotation
- Najcistiji pristup: pronaci article_ids gde autori matchuju, pa koristiti `id__in=...`
- `Author.objects` NEMA SoftDeleteManager - ne treba filtrirati za is_deleted

### ArticleSearchView

```python
# portal/views.py - DODATI novu klasu

from django.views.generic import ListView

from doi_portal.portal.services import search_articles


class ArticleSearchView(ListView):
    """
    Public article search view.

    FR39: Posetilac moze pretrazivati clanke po nazivu, autoru i kljucnim recima.
    Public view - no authentication required.
    """

    template_name = "portal/search_results.html"
    context_object_name = "articles"
    paginate_by = 20

    def get_queryset(self):
        query = self.request.GET.get("q", "").strip()
        if len(query) < 3:
            return Article.objects.none()
        return search_articles(query)

    def get_template_names(self):
        """Return partial template for HTMX requests."""
        if self.request.headers.get("HX-Request"):
            return ["portal/partials/_search_results.html"]
        return [self.template_name]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        query = self.request.GET.get("q", "").strip()
        context["query"] = query
        context["result_count"] = context["paginator"].count if context.get("paginator") else 0
        context["min_query_length"] = 3
        context["breadcrumbs"] = [
            {"label": "Početna", "url": reverse("home")},
            {"label": "Pretraga", "url": None},
        ]
        return context
```

### URL Routing

```python
# config/urls.py - DODATI:
from doi_portal.portal.views import ArticleSearchView

path("search/", ArticleSearchView.as_view(), name="article-search"),
```

### Search Results Template

```html
<!-- templates/portal/search_results.html -->
{% extends "portal/base.html" %}
{% load static %}
{% load portal_tags %}

{% block title %}Pretraga članaka{% if query %} - "{{ query }}"{% endif %}{% endblock title %}

{% block portal_content %}
<section class="mb-4">
  <h1 class="h3 mb-3">Pretraga članaka</h1>

  <!-- Search Form -->
  <form action="{% url 'article-search' %}" method="get" role="search" class="mb-4">
    <div class="input-group">
      <input type="search" name="q" value="{{ query }}" class="form-control"
             placeholder="Pretražite članke po naslovu, autoru, ključnim rečima..."
             aria-label="Pretraga članaka"
             minlength="3">
      <button type="submit" class="btn btn-primary">
        <i class="bi bi-search"></i> Pretraži
      </button>
    </div>
    {% if query and query|length < min_query_length %}
    <div class="form-text text-warning mt-1">
      Unesite najmanje {{ min_query_length }} karaktera za pretragu.
    </div>
    {% endif %}
  </form>

  <!-- Results -->
  {% if query and query|length >= min_query_length %}
    <p class="text-muted mb-3">
      Pronađeno <strong>{{ result_count }}</strong> članaka za "<em>{{ query }}</em>"
    </p>

    {% if articles %}
      {% for article in articles %}
        {% include "portal/partials/_article_search_card.html" with article=article query=query %}
      {% endfor %}

      <!-- Pagination -->
      {% include "components/_pagination.html" %}
    {% else %}
      <div class="text-center text-muted py-5">
        <i class="bi bi-search display-4 d-block mb-3"></i>
        <h2 class="h5">Nema pronađenih članaka za "{{ query }}"</h2>
        <p class="mb-0">Proverite pravopis ili pokušajte sa drugim ključnim rečima.</p>
      </div>
    {% endif %}

  {% elif not query %}
    <div class="text-center text-muted py-5">
      <i class="bi bi-search display-4 d-block mb-3"></i>
      <h2 class="h5">Pretražite članke</h2>
      <p class="mb-0">Unesite pojam za pretragu iznad - naslov, ime autora ili ključne reči.</p>
    </div>
  {% endif %}
</section>
{% endblock portal_content %}
```

### Article Search Card Partial

```html
<!-- templates/portal/partials/_article_search_card.html -->
{% load portal_tags %}

<article class="card mb-3 shadow-sm">
  <div class="card-body">
    <h3 class="h5 card-title mb-1">
      <a href="/articles/{{ article.pk }}/" class="text-decoration-none">
        {{ article.title|highlight_search:query }}
      </a>
    </h3>
    {% if article.subtitle %}
    <p class="text-muted small mb-2">{{ article.subtitle }}</p>
    {% endif %}

    <!-- Authors -->
    <p class="small mb-2">
      {% for author in article.authors.all|slice:":3" %}
        {{ author.surname }} {{ author.given_name|default:"" }}{% if not forloop.last %}, {% endif %}
      {% endfor %}
      {% if article.authors.count > 3 %}
        <span class="text-muted">i dr.</span>
      {% endif %}
    </p>

    <!-- Publication info -->
    <p class="small text-muted mb-2">
      <i class="bi bi-journal-text"></i>
      {{ article.issue.publication.title }} &mdash;
      Vol. {{ article.issue.volume }}, No. {{ article.issue.issue_number }} ({{ article.issue.year }})
    </p>

    <!-- Keywords -->
    {% if article.keywords %}
    <div class="mb-0">
      {% for kw in article.keywords|slice:":5" %}
        <span class="badge bg-light text-dark border me-1">{{ kw }}</span>
      {% endfor %}
    </div>
    {% endif %}
  </div>
</article>
```

### Custom Template Filter: highlight_search

```python
# portal/templatetags/portal_tags.py

from django import template
from django.utils.html import escape
from django.utils.safestring import mark_safe
import re

register = template.Library()


@register.filter(name="highlight_search")
def highlight_search(text, query):
    """
    Highlight search term in text by wrapping matches in <mark> tags.

    Case-insensitive. HTML-escapes input before wrapping to prevent XSS.

    Usage: {{ article.title|highlight_search:query }}
    """
    if not query or not text:
        return text

    # Escape HTML first (XSS prevention)
    escaped_text = escape(str(text))
    escaped_query = escape(str(query))

    # Case-insensitive replacement with <mark> wrapper
    pattern = re.compile(re.escape(escaped_query), re.IGNORECASE)
    highlighted = pattern.sub(
        lambda m: f"<mark>{m.group()}</mark>",
        escaped_text,
    )
    return mark_safe(highlighted)
```

**VAZNO:** Templatetags direktorijum mora imati `__init__.py` fajl. Proveriti da li vec postoji `portal/templatetags/` direktorijum - ako ne, kreirati ga sa `__init__.py`.

### Srpski Karakteri (OBAVEZNO - videti project-context.md)

| Kontekst | ISPRAVNO |
|----------|----------|
| Page title | "Pretraga članaka" |
| Search placeholder | "Pretražite članke po naslovu, autoru, ključnim rečima..." |
| Search dugme | "Pretraži" |
| Result count | "Pronađeno X članaka za '{query}'" |
| Prazan state (sa query) | "Nema pronađenih članaka za '{query}'" |
| Prazan state predlozi | "Proverite pravopis ili pokušajte sa drugim ključnim rečima." |
| Prazan state (bez query) | "Pretražite članke" |
| Prazan state opis | "Unesite pojam za pretragu iznad - naslov, ime autora ili ključne reči." |
| Min length poruka | "Unesite najmanje 3 karaktera za pretragu." |
| Authors overflow | "i dr." |
| Breadcrumbs | "Početna" > "Pretraga" |

### Previous Story Learnings (Story 4.1 + Epic 2-3)

1. **Portal base template** (`portal/base.html`) VEC postoji. Koristi ga kao parent template. Blok za content: `{% block portal_content %}`. (Story 2.2)
2. **SoftDeleteManager** automatski filtrira soft-deleted zapise. Ne treba dodavati `is_deleted=False` filter za Article.objects querysets. (Story 2.3)
3. **HTMX pattern** za partial response: `request.headers.get("HX-Request")` check. Koristiti `get_template_names()` override u ListView. (Story 2.5)
4. **Breadcrumbs** pattern: dict lista sa `label` i `url`. Portal base.html vec ima conditional prikaz: `{% if breadcrumbs %}`. (Story 2.2)
5. **Pagination** pattern: Bootstrap 5 pagination component. Proveriti da li postoji `components/_pagination.html` reusable partial - ako ne, kreirati ga. (Story 2.5)
6. **`select_related`** za clanke: ukljuciti `"issue__publication__publisher"` da se izbegne N+1. (Story 2.5)
7. **`prefetch_related`** za autore: `"authors"` je related_name na Article model. (Story 3.2)
8. **Portal CSS**: `static/css/portal.css` - vec ukljucen u portal/base.html. Dodati stilove za search rezultate u ovaj fajl. (Story 2.2)
9. **Test pattern**: pytest-django, `@pytest.mark.django_db`, Factory Boy. Koristiti `ArticleFactory`, `AuthorFactory` iz `articles/tests/factories.py`. (Story 3.1)
10. **URL name "home"**: VEC se koristi svuda u breadcrumbs sa `reverse("home")`. (Story 2.2)
11. **Home page search form**: `action="/search/"`, `name="q"` - NE MENJATI ove vrednosti. (Story 4.1)
12. **Article status filter**: Samo `ArticleStatus.PUBLISHED` clanci su vidljivi na javnom portalu. (Story 3.7)
13. **Author model**: `Author` je ForeignKey na Article sa `related_name="authors"`. Nema SoftDeleteManager. Ima `given_name`, `surname`, `orcid` polja. (Story 3.2)
14. **Keywords field**: `JSONField(default=list)` - cuva listu stringova. (Story 3.1)
15. **Article card**: Koristiti za search rezultate: naslov, autori, publikacija, godina, kljucne reci. Article landing page URL ce biti definisan u Story 4.4 - za sada koristiti placeholder `/articles/{pk}/`. (Story 4.4 backlog)
16. **portal/services.py**: VEC postoji sa `get_portal_statistics()` i `get_recent_publications()`. DODATI novu funkciju, ne kreirati novi fajl.
17. **portal/views.py**: VEC postoji sa PublisherPublicListView, PublicationPublicListView, IssuePublicDetailView, PortalHomeView. DODATI novu klasu, ne kreirati novi fajl.
18. **Test suite**: 1128 testova proslo u Story 4.1. Ne smemo imati regresije.

### Git Commit Pattern

```
story-4-2: feat(portal): implementiraj Article Search sa pretragom po naslovu, autoru, kljucnim recima i paginacijom (Story 4.2)
```

### Fajlovi za kreiranje (NOVI)

```
doi_portal/doi_portal/templates/portal/search_results.html            # Search results full page template
doi_portal/doi_portal/templates/portal/partials/_search_results.html   # HTMX partial za search results
doi_portal/doi_portal/templates/portal/partials/_article_search_card.html  # Article card za search
doi_portal/doi_portal/portal/templatetags/__init__.py                  # Templatetags package init (ako ne postoji)
doi_portal/doi_portal/portal/templatetags/portal_tags.py               # Custom template filters (highlight_search)
doi_portal/doi_portal/portal/tests/test_search.py                      # Search testovi (service + view + template filter)
```

### Fajlovi za modifikaciju (POSTOJECI)

```
doi_portal/config/urls.py                                              # Dodati search URL route
doi_portal/doi_portal/portal/views.py                                  # Dodati ArticleSearchView klasu
doi_portal/doi_portal/portal/services.py                               # Dodati search_articles() funkciju
doi_portal/doi_portal/static/css/portal.css                            # Stilovi za search rezultate i highlight
```

### Fajlovi koji se NE MENJAJU

```
doi_portal/doi_portal/templates/portal/base.html                       # VEC postoji - NE MENJATI
doi_portal/doi_portal/templates/portal/home.html                       # VEC postoji - NE MENJATI
doi_portal/doi_portal/portal/urls.py                                   # Publisher routes - NE MENJATI
doi_portal/doi_portal/portal/urls_publications.py                      # Publication routes - NE MENJATI
doi_portal/doi_portal/articles/models.py                               # Article model - NE MENJATI
```

### Pagination Component

Proveriti da li postoji `templates/components/_pagination.html`. Ako ne postoji, kreirati ga:

```html
<!-- templates/components/_pagination.html -->
{% if is_paginated %}
<nav aria-label="Navigacija stranica" class="mt-4">
  <ul class="pagination justify-content-center">
    {% if page_obj.has_previous %}
    <li class="page-item">
      <a class="page-link" href="?{{ request.GET.urlencode }}&page={{ page_obj.previous_page_number }}"
         aria-label="Prethodna">
        <span aria-hidden="true">&laquo;</span>
      </a>
    </li>
    {% endif %}

    {% for num in page_obj.paginator.page_range %}
      {% if num == page_obj.number %}
      <li class="page-item active" aria-current="page">
        <span class="page-link">{{ num }}</span>
      </li>
      {% elif num > page_obj.number|add:"-3" and num < page_obj.number|add:"3" %}
      <li class="page-item">
        <a class="page-link" href="?{{ request.GET.urlencode }}&page={{ num }}">{{ num }}</a>
      </li>
      {% endif %}
    {% endfor %}

    {% if page_obj.has_next %}
    <li class="page-item">
      <a class="page-link" href="?{{ request.GET.urlencode }}&page={{ page_obj.next_page_number }}"
         aria-label="Sledeća">
        <span aria-hidden="true">&raquo;</span>
      </a>
    </li>
    {% endif %}
  </ul>
</nav>
{% endif %}
```

**VAZNO:** Pagination link mora SACUVATI query parametar `q` u URL-u. Koristiti `request.GET.urlencode` ili manuelno dodati `q={{ query }}` u linkove. Proveriti da li vec postoji pagination partial i kako se koristi (Story 2.5 ga mozda vec koristi).

### Anti-Patterns (ZABRANJENO)

```python
# POGRESNO - Koristiti pages/ umesto portal/ template
template_name = "pages/search.html"  # NE! Koristi portal/search_results.html

# POGRESNO - Extendovati base.html umesto portal/base.html
{% extends "base.html" %}  # NE! Koristi portal/base.html

# POGRESNO - Koristiti {% block content %} umesto {% block portal_content %}
{% block content %}  # NE! portal/base.html koristi {% block portal_content %}

# POGRESNO - Business logika u view-u
def get_queryset(self):
    return Article.objects.filter(title__icontains=q)  # NE! Delegiraj u services.py

# POGRESNO - Pretrazivati sve statuse
Article.objects.filter(title__icontains=q)  # NE! Dodaj status=PUBLISHED filter

# POGRESNO - Zaboraviti select_related/prefetch_related
Article.objects.filter(...)  # NE! Dodaj .select_related("issue__publication__publisher").prefetch_related("authors")

# POGRESNO - Promeniti search URL
path("articles/search/", ...)  # NE! Mora biti /search/ (home.html ocekuje to)

# POGRESNO - Promeniti query parametar
request.GET.get("search")  # NE! Mora biti "q" (home.html koristi name="q")

# POGRESNO - Dodati LoginRequiredMixin
class ArticleSearchView(LoginRequiredMixin, ListView):  # NE! Javna stranica

# POGRESNO - Vracati JSON za rezultate
return JsonResponse(results)  # NE! Server-rendered HTML

# POGRESNO - Ne escapovati HTML u highlight filteru
mark_safe(text.replace(query, f"<mark>{query}</mark>"))  # NE! XSS ranjivost! Escape pre wrappinga

# POGRESNO - Kreirati novi models.py za search
# Search je read-only - NEMA modele, samo services.py i views.py

# POGRESNO - Koristiti Django full-text search (SearchVector)
# Projekat koristi PostgreSQL ali za MVP icontains je dovoljno i jednostavnije
# Full-text search moze doci kao optimizacija u buducnosti
```

### Optimizacija Querysets (KRITICNO - NFR5)

```python
# ISPRAVNO - Jedna query sa joins i prefetch
articles = (
    Article.objects.filter(
        Q(status=ArticleStatus.PUBLISHED),
        Q(title__icontains=q) | Q(abstract__icontains=q) | Q(keywords__icontains=q) | Q(id__in=author_article_ids)
    )
    .select_related("issue__publication__publisher")
    .prefetch_related("authors")
    .distinct()
    .order_by("-published_at", "-created_at")
)

# Ovo ce generisati:
# 1. Jedan SQL za article IDs gde autori matchuju
# 2. Jedan SQL za clanke sa JOIN na issue, publication, publisher
# 3. Jedan SQL za prefetch autora
# Total: 3 upita, nezavisno od broja rezultata
```

### Project Structure Notes

- Search service funkcija ide u POSTOJECI `doi_portal/doi_portal/portal/services.py`
- Search view klasa ide u POSTOJECI `doi_portal/doi_portal/portal/views.py`
- Search template ide u `doi_portal/doi_portal/templates/portal/search_results.html` (novi fajl)
- HTMX partial ide u `doi_portal/doi_portal/templates/portal/partials/` (novi direktorijum ako ne postoji - proveriti)
- Article search card partial ide u isti partials direktorijum
- Template tags idu u `doi_portal/doi_portal/portal/templatetags/portal_tags.py` (novi fajl)
- Search testovi idu u `doi_portal/doi_portal/portal/tests/test_search.py` (novi fajl)
- URL route se DODAJE u postojeci `config/urls.py`
- Portal CSS azuriranje u postojecem `static/css/portal.css`

### Test Pattern

```python
# portal/tests/test_search.py

import pytest
from django.urls import reverse

from doi_portal.articles.models import ArticleStatus
from doi_portal.articles.tests.factories import ArticleFactory, AuthorFactory
from doi_portal.portal.services import search_articles


@pytest.mark.django_db
class TestSearchArticles:
    """Tests for search_articles service function."""

    def test_search_by_title(self):
        """Finds articles matching title."""
        article = ArticleFactory(title="Quantum Computing Research", status=ArticleStatus.PUBLISHED)
        results = search_articles("Quantum")
        assert article in results

    def test_search_by_author_surname(self):
        """Finds articles by author surname."""
        article = ArticleFactory(status=ArticleStatus.PUBLISHED)
        AuthorFactory(article=article, surname="Petrović")
        results = search_articles("Petrović")
        assert article in results

    def test_search_by_keywords(self):
        """Finds articles by keywords JSON field."""
        article = ArticleFactory(
            keywords=["machine learning", "AI"],
            status=ArticleStatus.PUBLISHED,
        )
        results = search_articles("machine learning")
        assert article in results

    def test_search_by_abstract(self):
        """Finds articles matching abstract text."""
        article = ArticleFactory(
            abstract="This paper explores deep learning techniques.",
            status=ArticleStatus.PUBLISHED,
        )
        results = search_articles("deep learning")
        assert article in results

    def test_excludes_non_published(self):
        """Only PUBLISHED articles are returned."""
        ArticleFactory(title="Draft Article", status=ArticleStatus.DRAFT)
        ArticleFactory(title="Review Article", status=ArticleStatus.REVIEW)
        ArticleFactory(title="Ready Article", status=ArticleStatus.READY)
        pub = ArticleFactory(title="Published Article", status=ArticleStatus.PUBLISHED)
        results = search_articles("Article")
        assert list(results) == [pub]

    def test_excludes_soft_deleted(self):
        """Soft-deleted articles excluded."""
        article = ArticleFactory(title="Deleted Research", status=ArticleStatus.PUBLISHED)
        article.soft_delete()
        results = search_articles("Deleted")
        assert article not in results

    def test_empty_query_returns_none(self):
        """Empty query returns empty queryset."""
        ArticleFactory(status=ArticleStatus.PUBLISHED)
        results = search_articles("")
        assert results.count() == 0

    def test_short_query_returns_none(self):
        """Query < 3 chars returns empty queryset."""
        ArticleFactory(title="AB", status=ArticleStatus.PUBLISHED)
        results = search_articles("AB")
        assert results.count() == 0


@pytest.mark.django_db
class TestArticleSearchView:
    """Tests for ArticleSearchView."""

    def test_search_page_returns_200(self, client):
        """Search page returns 200."""
        response = client.get(reverse("article-search"))
        assert response.status_code == 200

    def test_search_uses_correct_template(self, client):
        """Uses portal/search_results.html template."""
        response = client.get(reverse("article-search"))
        template_names = [t.name for t in response.templates]
        assert "portal/search_results.html" in template_names

    def test_search_with_query(self, client):
        """Search with valid query returns results in context."""
        ArticleFactory(title="Quantum Test", status=ArticleStatus.PUBLISHED)
        response = client.get(reverse("article-search"), {"q": "Quantum"})
        assert "articles" in response.context
        assert response.context["query"] == "Quantum"

    def test_search_no_auth_required(self, client):
        """Public page - no login required."""
        response = client.get(reverse("article-search"))
        assert response.status_code == 200

    def test_empty_query_shows_form(self, client):
        """Empty query shows search form without results."""
        response = client.get(reverse("article-search"))
        content = response.content.decode()
        assert "Pretražite članke" in content

    def test_short_query_message(self, client):
        """Query < 3 chars shows minimum length message."""
        response = client.get(reverse("article-search"), {"q": "AB"})
        assert response.context["query"] == "AB"

    def test_no_results_message(self, client):
        """No results shows empty state message."""
        response = client.get(reverse("article-search"), {"q": "nonexistent12345"})
        content = response.content.decode()
        assert "Nema pronađenih članaka" in content

    def test_breadcrumbs(self, client):
        """Breadcrumbs include Početna and Pretraga."""
        response = client.get(reverse("article-search"))
        breadcrumbs = response.context["breadcrumbs"]
        assert breadcrumbs[0]["label"] == "Početna"
        assert breadcrumbs[1]["label"] == "Pretraga"

    def test_pagination(self, client):
        """Pagination works with many results."""
        for i in range(25):
            ArticleFactory(title=f"Test Article {i}", status=ArticleStatus.PUBLISHED)
        response = client.get(reverse("article-search"), {"q": "Test Article"})
        assert response.context["is_paginated"] is True

    def test_htmx_returns_partial(self, client):
        """HTMX request returns partial template."""
        response = client.get(
            reverse("article-search"),
            {"q": "test"},
            HTTP_HX_REQUEST="true",
        )
        template_names = [t.name for t in response.templates]
        assert "portal/partials/_search_results.html" in template_names
```

### Dependencies (Python/Django)

Nema novih Python zavisnosti! Sve je vec instalirano:
- Django 5.2+ (ORM Q objects, ListView, Paginator, template tags)
- Bootstrap 5 (CSS framework - vec u portal/base.html)
- Bootstrap Icons (vec ukljuceni u portal/base.html CDN)
- pytest-django + Factory Boy (vec u test setup-u)

### NFR Requirements

- **FR39:** Posetilac moze pretrazivati clanke po nazivu, autoru i kljucnim recima - direktna implementacija
- **NFR5:** Pretraga < 2 sekunde - optimizovani upiti sa select_related/prefetch_related, max 3 SQL upita
- **NFR2:** Javne stranice portala < 3 sekunde - lightweight template, no heavy assets
- **NFR14:** Semanticki HTML5 elementi - `<section>`, `<article>`, `<form role="search">`
- **NFR15:** Alt tekst za sve slike - nema slika u search rezultatima (text only)
- **NFR16:** Kontrast minimum 4.5:1 za tekst - Bootstrap default boje
- **NFR17:** Keyboard navigacija - Tab through results and pagination
- **NFR18:** Labels povezani sa input poljima - aria-label na search input

### References

- [Source: epics.md#Story 4.2: Article Search Functionality]
- [Source: epics.md#Epic 4: Public Portal Experience - FR39]
- [Source: prd.md#7. Public Portal - FR39 (Pretraga clanaka)]
- [Source: prd.md#Performance - NFR5 (Pretraga < 2 sekunde)]
- [Source: architecture.md#Project Structure - portal/ app, FR38-FR45 mapping]
- [Source: architecture.md#Frontend Architecture - Bootstrap 5, HTMX patterns]
- [Source: architecture.md#Implementation Patterns - naming conventions, structure patterns]
- [Source: architecture.md#Data Architecture - PostgreSQL full-text search potential]
- [Source: ux-design-specification.md#Search & Filter Patterns - debounced 300ms, min 3 char]
- [Source: ux-design-specification.md#Article Card - Compact variant for lists]
- [Source: ux-design-specification.md#Empty States - centered message, icon, CTA]
- [Source: ux-design-specification.md#Navigation Patterns - Pagination < 50 items]
- [Source: ux-design-specification.md#Responsive Strategy - Mobile-first za portal]
- [Source: ux-design-specification.md#Accessibility - WCAG AA, contrast 4.5:1, focus states]
- [Source: project-context.md#Services Layer (Business Logic)]
- [Source: project-context.md#HTMX Pravila - partials sa _ prefix]
- [Source: project-context.md#Naming Konvencije - snake_case, PascalCase, kebab-case]
- [Source: project-context.md#Lokalizacija - Srpski Karakteri, sr-Latn]
- [Source: project-context.md#Testing (pytest-django) - Factory Boy]
- [Source: portal/base.html - Parent template sa navbar, breadcrumbs, footer]
- [Source: portal/views.py - Existing portal views (publisher, publication, issue, home)]
- [Source: portal/services.py - Existing service functions (stats, recent pubs)]
- [Source: portal/home.html - Hero search form with action="/search/" name="q"]
- [Source: config/urls.py - Current URL routes, no /search/ yet]
- [Source: articles/models.py - Article, Author, ArticleStatus, keywords JSONField]
- [Source: articles/tests/factories.py - ArticleFactory, AuthorFactory]
- [Source: 4-1-portal-home-page.md - Previous story learnings, portal patterns]

## Dev Agent Record

### Agent Model Used

Claude Opus 4.5 (claude-opus-4-5-20251101)

### Debug Log References

- Query count test initially expected 3 queries but Django ORM inlines the author subquery into the main query, resulting in only 2 queries (1 main + 1 prefetch). Fixed test to assert 2.

### Completion Notes List

- Implemented `search_articles()` service function in `portal/services.py` using Q objects for OR search across title, abstract, keywords, and author names. Uses select_related/prefetch_related for optimal 2-query execution.
- Implemented `ArticleSearchView(ListView)` in `portal/views.py` with paginate_by=20, HTMX partial support, breadcrumbs, and min 3-char query validation.
- Added URL route `path("search/", ...)` in `config/urls.py` matching the existing home page hero search bar form action.
- Created full search results template extending `portal/base.html` with search form, result count, article cards, empty states, and pagination.
- Created HTMX partial `_search_results.html` for inline result updates.
- Created `_article_search_card.html` partial with article title (linked to placeholder `/articles/{pk}/`), authors (max 3 + "i dr."), publication info, and keyword badges.
- Created `highlight_search` custom template filter in `portal/templatetags/portal_tags.py` with HTML escaping (XSS prevention) and case-insensitive mark wrapping.
- Created reusable `components/_pagination.html` Bootstrap pagination component preserving query params.
- Added search-specific CSS styles and mobile responsive adjustments in `portal.css`.
- All 26 new tests pass. Full suite: 1155 passed, 3 skipped, 0 failures.

### File List

**New files:**
- `doi_portal/doi_portal/portal/tests/test_search.py` - 26 tests (service + view + template filter)
- `doi_portal/doi_portal/portal/templatetags/__init__.py` - Package init
- `doi_portal/doi_portal/portal/templatetags/portal_tags.py` - highlight_search filter
- `doi_portal/doi_portal/templates/portal/search_results.html` - Full search page template
- `doi_portal/doi_portal/templates/portal/partials/_search_results.html` - HTMX partial
- `doi_portal/doi_portal/templates/portal/partials/_article_search_card.html` - Article card partial
- `doi_portal/doi_portal/templates/components/_pagination.html` - Reusable pagination component

**Modified files:**
- `doi_portal/doi_portal/portal/services.py` - Added search_articles() function
- `doi_portal/doi_portal/portal/views.py` - Added ArticleSearchView class
- `doi_portal/config/urls.py` - Added /search/ URL route
- `doi_portal/doi_portal/static/css/portal.css` - Added search result and highlight styles
