# Story 4.4: Article Landing Page (Defining Experience)

Status: done

## Story

As a **visitor arriving via DOI link**,
I want **to see article details and access the PDF immediately**,
So that **I get what I need within 3 seconds**.

## Background

Ovo je cetvrta prica u Epiku 4 (Public Portal Experience). Story 4.3 je implementirala Advanced Filtering na `/search/` stranici. Ovaj story kreira **Article Landing Page** - javnu stranicu za prikaz jednog clanka sa svim metapodacima. Ova stranica je "lice" portala jer posetioci dolaze preko DOI linkova i moraju videti sve informacije o clanku u roku od 3 sekunde. Stranica koristi Clean Academic dizajn stil (Frontiers/MDPI pattern) sa two-column layout-om.

**FR Pokrivenost:**
- FR41: Posetilac moze videti landing stranicu clanka sa svim metapodacima

**NFR Pokrivenost:**
- NFR1: Landing stranica clanka - First Contentful Paint < 3 sekunde
- NFR2: Javne stranice portala - ucitavanje < 3 sekunde
- NFR14-NFR18: Accessibility (semanticki HTML5, alt tekst, kontrast, keyboard, labels)

**Zavisnosti (sve DONE):**
- Story 4.1: Portal Home Page - portal/base.html, portal.css, portal nav
- Story 4.2: Article Search Functionality - `ArticleSearchView`, `_article_search_card.html` (link ka landing page)
- Story 4.3: Advanced Filtering - filter sidebar, search results stranica
- Story 3.1: Article Model - `Article`, `ArticleStatus`, `Author`, `Affiliation` modeli
- Story 3.7: Article Publishing & Withdrawal - `PUBLISHED` i `WITHDRAWN` statusi, `withdrawal_reason`, `withdrawn_at`
- Story 2.3: Publication Model - `Publication`, `PublicationType`, `AccessType`
- Story 2.6: Issue Model - `Issue`, `IssueStatus`
- Story 2.1: Publisher Model - `Publisher`, `doi_prefix`

**Blokira:**
- Story 4.5: Floating Action Bar - dodaje PDF/Share/Cite dugmad na article landing page
- Story 4.6: PDF Download - PDF download funkionalnost
- Story 4.7: Citation Modal - citiranje u vise formata

## Acceptance Criteria

1. **Given** posetilac navigira na article landing page via DOI ili direktan link
   **When** stranica se ucita
   **Then** First Contentful Paint je ispod 3 sekunde
   **And** stranica koristi Clean Academic dizajn stil

2. **Given** article landing page je prikazana
   **When** posetilac pregleda layout
   **Then** two-column layout na desktopu: main content (col-lg-8) + sidebar (col-lg-4)
   **And** breadcrumbs prikazuju: Pocetna > Publikacije > {Publikacija} > {Izdanje} > {Clanak}

3. **Given** main content oblast je prikazana
   **When** posetilac pregleda detalje clanka
   **Then** naslov i podnaslov su prominentno prikazani (H1)
   **And** autori su izlistani sa afilijacijama i ORCID linkovima
   **And** apstrakt je prikazan u celosti
   **And** kljucne reci su prikazane kao tagovi
   **And** metapodaci clanka su prikazani: DOI, stranice, jezik, licenca

4. **Given** sidebar je prikazan
   **When** posetilac pregleda sadrzaj sidebar-a
   **Then** kartica sa info o publikaciji prikazuje: naslov, volumen/izdanje
   **And** kartica sa info o izdavacu prikazuje: logo, naziv
   **And** cover image publikacije je prikazana (ako postoji)

5. **Given** clanak je WITHDRAWN
   **When** posetilac pregleda stranicu
   **Then** prominentan "POVUCENO" baner je prikazan na vrhu
   **And** datum povlacenja i razlog su prikazani
   **And** metapodaci ostaju vidljivi

6. **Given** clanak je PUBLISHED (nije WITHDRAWN)
   **When** posetilac pregleda stranicu
   **Then** status badge prikazuje "Objavljeno"
   **And** datum objave je prikazan

7. **Given** clanak ne postoji ili je obrisan (soft-deleted) ili nije PUBLISHED/WITHDRAWN
   **When** posetilac pokusa da pristupi stranici
   **Then** vraca se 404 Not Found

8. **Given** posetilac je na mobilnom uredaju
   **When** pregleda article landing page
   **Then** layout se prebacuje na single-column (sidebar ispod)
   **And** svi metapodaci ostaju vidljivi i dostupni

9. **Given** stranica je ucitana
   **When** analiziramo pristupacnost
   **Then** semanticki HTML5 elementi su korisceni (`<article>`, `<aside>`, `<section>`)
   **And** ORCID linkovi imaju `rel="external"` i `aria-label`
   **And** slike imaju `alt` tekst
   **And** kontrast zadovoljava WCAG AA (4.5:1)

10. **Given** posetilac dolazi sa search results stranice
    **When** klikne na clanak u rezultatima pretrage
    **Then** link vodi na article landing page

## Tasks / Subtasks

- [x] Task 1: Kreirati `get_article_for_landing()` service funkciju (AC: #1, #3, #4, #5, #6, #7)
  - [x] 1.1 Kreirati novu service funkciju u `portal/services.py`
  - [x] 1.2 Primiti `article_pk: int` kao parametar
  - [x] 1.3 Vratiti Article sa `select_related("issue__publication__publisher")` i `prefetch_related("authors__affiliations")`
  - [x] 1.4 Filtrirati samo `status__in=[ArticleStatus.PUBLISHED, ArticleStatus.WITHDRAWN]` - ostali statusi vracaju None
  - [x] 1.5 SoftDeleteManager VEC iskljucuje is_deleted=True
  - [x] 1.6 Vratiti `None` ako clanak ne postoji ili nije dozvoljen status

- [x] Task 2: Kreirati `ArticleLandingView` u `portal/views.py` (AC: #1, #2, #3, #4, #5, #6, #7)
  - [x] 2.1 Kreirati klasu `ArticleLandingView(DetailView)` u `portal/views.py`
  - [x] 2.2 `model = Article`, `template_name = "portal/article_detail.html"`, `context_object_name = "article"`
  - [x] 2.3 `get_queryset()`: filtrirati `Article.objects.filter(status__in=[ArticleStatus.PUBLISHED, ArticleStatus.WITHDRAWN]).select_related("issue__publication__publisher").prefetch_related("authors__affiliations")`
  - [x] 2.4 `get_context_data()`: dodati breadcrumbs (Pocetna > Publikacije > Publikacija > Izdanje > Clanak)
  - [x] 2.5 Dodati `is_withdrawn` boolean u context
  - [x] 2.6 Dodati `full_doi` string u context: `f"{article.issue.publication.publisher.doi_prefix}/{article.doi_suffix}"`
  - [x] 2.7 Dodati `doi_url` string u context: `f"https://doi.org/{full_doi}"`

- [x] Task 3: Registrovati URL route za article landing page (AC: #1, #10)
  - [x] 3.1 Kreirati `portal/urls_articles.py` sa `app_name = "portal-articles"` i pattern: `<int:pk>/` -> `ArticleLandingView`
  - [x] 3.2 Dodati include u `config/urls.py`: `path("articles/", include("doi_portal.portal.urls_articles", namespace="portal-articles"))`
  - [x] 3.3 URL name: `article-detail`
  - [x] 3.4 Finalna URL putanja: `/articles/<pk>/`

- [x] Task 4: Kreirati `article_detail.html` template (AC: #2, #3, #4, #5, #6, #8, #9)
  - [x] 4.1 Extends `portal/base.html`
  - [x] 4.2 Title block: `{naslov} - {publikacija} - DOI Portal`
  - [x] 4.3 Meta description block sa apstraktom
  - [x] 4.4 WITHDRAWN banner na vrhu (ako `is_withdrawn`): `alert-danger` sa ikonom, datumom i razlogom
  - [x] 4.5 Two-column layout: `<div class="row">` sa `col-lg-8` (main) i `col-lg-4` (sidebar)
  - [x] 4.6 Main content u `<article>` tagu
  - [x] 4.7 H1: naslov + podnaslov (ako postoji)
  - [x] 4.8 Status badge: "Objavljeno" (success) ili "Povuceno" (danger)
  - [x] 4.9 Datum objave (published_at) formatiran kao `d.m.Y.`
  - [x] 4.10 Autori sekcija: ime, prezime, afilijacije, ORCID link (ikonica), corresponding badge
  - [x] 4.11 Apstrakt sekcija u `<section>` tagu sa H2 "Apstrakt"
  - [x] 4.12 Kljucne reci kao tagovi (`<span class="badge">`)
  - [x] 4.13 Metapodaci sekcija: DOI (sa linkom na doi.org), stranice (od-do), jezik, licenca URL, tip sadrzaja
  - [x] 4.14 Sidebar `<aside>`: Publication info card (naslov, tip, volume/issue, cover image)
  - [x] 4.15 Sidebar: Publisher info card (naziv, logo, link na publisher stranicu)

- [x] Task 5: Azurirati `_article_search_card.html` da koristi named URL (AC: #10)
  - [x] 5.1 Promeniti hardcoded `href="/articles/{{ article.pk }}/"` u `href="{% url 'portal-articles:article-detail' article.pk %}"`

- [x] Task 6: Azurirati `issue_detail.html` da koristi linkove na article landing page (AC: #10)
  - [x] 6.1 U articles sekciji, dodati link na article landing page za svaki clanak
  - [x] 6.2 Prikazati samo PUBLISHED/WITHDRAWN clanke (ne DRAFT/REVIEW/READY)
  - [x] 6.3 Promeniti placeholder context `articles = []` u real queryset u `IssuePublicDetailView.get_context_data()`

- [x] Task 7: Dodati CSS stilove za article landing page (AC: #1, #2, #8)
  - [x] 7.1 Stilovi za article-header (naslov + subtitle) u `portal.css`
  - [x] 7.2 Stilovi za author-list (inline lista sa afilijacijama)
  - [x] 7.3 Stilovi za ORCID ikonica (zelena, mala)
  - [x] 7.4 Stilovi za withdrawn-banner (prominentan alert)
  - [x] 7.5 Stilovi za metadata section (dl/dd layout)
  - [x] 7.6 Stilovi za keyword tags
  - [x] 7.7 Responsive: sidebar ispod na mobile (col-lg-4 vec to radi automatski)

- [x] Task 8: Kreirati testove (AC: #1-#10)
  - [x] 8.1 Service test: `get_article_for_landing()` vraca PUBLISHED clanak
  - [x] 8.2 Service test: `get_article_for_landing()` vraca WITHDRAWN clanak
  - [x] 8.3 Service test: `get_article_for_landing()` vraca None za DRAFT clanak
  - [x] 8.4 Service test: `get_article_for_landing()` vraca None za REVIEW clanak
  - [x] 8.5 Service test: `get_article_for_landing()` vraca None za READY clanak
  - [x] 8.6 Service test: `get_article_for_landing()` vraca None za nepostojeci PK
  - [x] 8.7 Service test: `get_article_for_landing()` vraca None za soft-deleted clanak
  - [x] 8.8 View test: GET /articles/{pk}/ za PUBLISHED clanak vraca 200
  - [x] 8.9 View test: GET /articles/{pk}/ za WITHDRAWN clanak vraca 200
  - [x] 8.10 View test: GET /articles/{pk}/ za DRAFT clanak vraca 404
  - [x] 8.11 View test: GET /articles/{pk}/ za nepostojeci PK vraca 404
  - [x] 8.12 View test: context sadrzi `breadcrumbs` sa 5 stavki
  - [x] 8.13 View test: context sadrzi `is_withdrawn` = True za WITHDRAWN clanak
  - [x] 8.14 View test: context sadrzi `is_withdrawn` = False za PUBLISHED clanak
  - [x] 8.15 View test: context sadrzi `full_doi` sa pravilnim formatom
  - [x] 8.16 View test: context sadrzi `doi_url` sa https://doi.org/ prefiksom
  - [x] 8.17 View test: template sadrzi naslov clanka u response content
  - [x] 8.18 View test: WITHDRAWN clanak prikazuje withdrawn banner
  - [x] 8.19 View test: PUBLISHED clanak NE prikazuje withdrawn banner
  - [x] 8.20 View test: authors sa afilijacijama su prikazani
  - [x] 8.21 View test: keywords su prikazani kao tagovi
  - [x] 8.22 View test: breadcrumbs sadrze pravilnu hijerarhiju

## Dev Notes

### KRITICNO: Ovo je "Lice" Portala (Clean Academic dizajn)

Article Landing Page je NAJVAZNIJA stranica javnog portala. Posetilac dolazi sa DOI linka (doi.org resolves na ovu stranicu) i mora videti sve informacije o clanku u roku od 3 sekunde (NFR1). Dizajn treba da bude u Frontiers/MDPI stilu: profesionalan, cist, akademski.

**Key Design Decisions:**
- Two-column layout: col-lg-8 (main) + col-lg-4 (sidebar) - isti pattern kao `issue_detail.html`
- Samo PUBLISHED i WITHDRAWN clanci su vidljivi na javnom portalu
- WITHDRAWN clanci imaju prominentan baner ali metapodaci ostaju vidljivi
- Sidebar prikazuje kontekst (publikacija + izdavac) za posetioca koji dolazi sa DOI linka

### URL Pattern

```
/articles/<pk>/  ->  ArticleLandingView  (name: "portal-articles:article-detail")
```

**NAPOMENA:** `_article_search_card.html` VEC koristi hardcoded `/articles/{{ article.pk }}/` putanju (linija 6). Ovaj story MORA:
1. Registrovati URL route koji matchuje ovaj pattern
2. Azurirati `_article_search_card.html` da koristi Django `{% url %}` tag umesto hardcoded URL-a

### Postojeci Patterns koje MORAMO slediti

**Portal base.html pattern** (VEC implementirano):
- `{% extends "portal/base.html" %}`
- `{% block title %}...{% endblock title %}`
- `{% block portal_content %}...{% endblock portal_content %}`
- Breadcrumbs se renderuju iz `breadcrumbs` context varijable
- `portal.css` je VEC ucitan u base.html
- Bootstrap Icons CDN je VEC ukljucen

**Issue detail pattern** (referentna implementacija za two-column layout):
- `issue_detail.html` VEC koristi `col-lg-8` + `col-lg-4` layout
- Sidebar sa Publication info card i Publisher info card - ISTI PATTERN

**DetailView pattern iz portal views:**
```python
class IssuePublicDetailView(DetailView):
    model = Issue
    template_name = "portal/publications/issue_detail.html"
    context_object_name = "issue"

    def get_queryset(self):
        return Issue.objects.filter(
            status=IssueStatus.PUBLISHED,
        ).select_related("publication", "publication__publisher")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["breadcrumbs"] = [...]
        return context
```

### Nova Service Funkcija

```python
# portal/services.py - DODATI novu funkciju

def get_article_for_landing(article_pk: int) -> Article | None:
    """
    Get article for public landing page display.

    FR41: Posetilac moze videti landing stranicu clanka sa svim metapodacima.
    Only PUBLISHED and WITHDRAWN articles are visible on public portal.

    Args:
        article_pk: Primary key of the article.

    Returns:
        Article with related data or None if not found/not public.
    """
    try:
        return (
            Article.objects.filter(
                pk=article_pk,
                status__in=[ArticleStatus.PUBLISHED, ArticleStatus.WITHDRAWN],
            )
            .select_related("issue__publication__publisher")
            .prefetch_related("authors__affiliations")
            .get()
        )
    except Article.DoesNotExist:
        return None
```

### ArticleLandingView

```python
# portal/views.py - DODATI novu klasu

class ArticleLandingView(DetailView):
    """
    Public article landing page.

    FR41: Posetilac moze videti landing stranicu clanka sa svim metapodacima.
    NFR1: First Contentful Paint < 3 sekunde.
    Only PUBLISHED and WITHDRAWN articles are visible.
    """

    model = Article
    template_name = "portal/article_detail.html"
    context_object_name = "article"

    def get_queryset(self):
        """Return only PUBLISHED and WITHDRAWN articles with related data."""
        return (
            Article.objects.filter(
                status__in=[ArticleStatus.PUBLISHED, ArticleStatus.WITHDRAWN],
            )
            .select_related("issue__publication__publisher")
            .prefetch_related("authors__affiliations")
        )

    def get_context_data(self, **kwargs):
        """Add article-specific context."""
        context = super().get_context_data(**kwargs)
        article = self.object
        issue = article.issue
        publication = issue.publication
        publisher = publication.publisher

        # Breadcrumbs: Home > Publications > Publication > Issue > Article
        context["breadcrumbs"] = [
            {"label": "Početna", "url": reverse("home")},
            {
                "label": "Publikacije",
                "url": reverse("portal-publications:publication-list"),
            },
            {
                "label": publication.title,
                "url": reverse(
                    "portal-publications:publication-detail",
                    kwargs={"slug": publication.slug},
                ),
            },
            {
                "label": f"Vol. {issue.volume}, No. {issue.issue_number} ({issue.year})",
                "url": reverse(
                    "portal-publications:issue-detail",
                    kwargs={"slug": publication.slug, "pk": issue.pk},
                ),
            },
            {"label": article.title[:80], "url": None},
        ]

        context["is_withdrawn"] = article.status == ArticleStatus.WITHDRAWN
        context["full_doi"] = f"{publisher.doi_prefix}/{article.doi_suffix}"
        context["doi_url"] = f"https://doi.org/{publisher.doi_prefix}/{article.doi_suffix}"

        return context
```

### URL Registration

```python
# portal/urls_articles.py - NOVI FAJL
from django.urls import path
from doi_portal.portal import views

app_name = "portal-articles"

urlpatterns = [
    path(
        "<int:pk>/",
        views.ArticleLandingView.as_view(),
        name="article-detail",
    ),
]
```

```python
# config/urls.py - DODATI:
path("articles/", include("doi_portal.portal.urls_articles", namespace="portal-articles")),
```

### Template Struktura: article_detail.html

```html
{% extends "portal/base.html" %}
{% load static i18n %}

{% block title %}{{ article.title }} - {{ article.issue.publication.title }} - DOI Portal{% endblock title %}

{% block meta_description %}{{ article.abstract|truncatewords:30 }}{% endblock meta_description %}

{% block portal_content %}
<!-- WITHDRAWN Banner -->
{% if is_withdrawn %}
<div class="alert alert-danger d-flex align-items-start mb-4" role="alert">
  <i class="bi bi-exclamation-triangle-fill me-3 fs-4" aria-hidden="true"></i>
  <div>
    <h2 class="alert-heading h5 mb-1">Povučen članak</h2>
    <p class="mb-1">Ovaj članak je povučen{% if article.withdrawn_at %} dana {{ article.withdrawn_at|date:"d.m.Y." }}{% endif %}.</p>
    {% if article.withdrawal_reason %}
    <p class="mb-0"><strong>Razlog:</strong> {{ article.withdrawal_reason }}</p>
    {% endif %}
  </div>
</div>
{% endif %}

<div class="row">
  <!-- Main Content -->
  <article class="col-lg-8">
    <!-- Title -->
    <h1 class="article-title mb-2">{{ article.title }}</h1>
    {% if article.subtitle %}
    <p class="article-subtitle text-muted lead mb-3">{{ article.subtitle }}</p>
    {% endif %}

    <!-- Status & Date -->
    <div class="mb-3">
      <span class="badge {{ article.status_badge_class }}">{{ article.get_status_display }}</span>
      {% if article.published_at %}
      <span class="text-muted ms-2">
        <i class="bi bi-calendar3 me-1" aria-hidden="true"></i>
        {{ article.published_at|date:"d.m.Y." }}
      </span>
      {% endif %}
    </div>

    <!-- Authors -->
    <section class="article-authors mb-4" aria-labelledby="authors-heading">
      <h2 id="authors-heading" class="h5 mb-3">Autori</h2>
      {% for author in article.authors.all %}
      <div class="author-entry mb-2">
        <span class="fw-semibold">
          {{ author.given_name }} {{ author.surname }}{% if author.suffix %} {{ author.suffix }}{% endif %}
        </span>
        {% if author.is_corresponding %}
        <span class="badge bg-info ms-1" title="Korespondentni autor">
          <i class="bi bi-envelope-fill" aria-hidden="true"></i> Korespondent
        </span>
        {% endif %}
        {% if author.orcid %}
        <a href="https://orcid.org/{{ author.orcid }}"
           class="orcid-link ms-1"
           rel="external"
           target="_blank"
           aria-label="ORCID profil za {{ author.given_name }} {{ author.surname }}: {{ author.orcid }}">
          <img src="https://info.orcid.org/wp-content/uploads/2019/11/orcid_16x16.png"
               alt="ORCID" width="16" height="16">
          {{ author.orcid }}
        </a>
        {% endif %}
        {% for affiliation in author.affiliations.all %}
        <div class="text-muted small ms-3">
          {{ affiliation.institution_name }}{% if affiliation.department %}, {{ affiliation.department }}{% endif %}
        </div>
        {% endfor %}
      </div>
      {% empty %}
      <p class="text-muted">Nema podataka o autorima.</p>
      {% endfor %}
    </section>

    <!-- Abstract -->
    {% if article.abstract %}
    <section class="article-abstract mb-4" aria-labelledby="abstract-heading">
      <h2 id="abstract-heading" class="h5 mb-3">Apstrakt</h2>
      <p>{{ article.abstract }}</p>
    </section>
    {% endif %}

    <!-- Keywords -->
    {% if article.keywords %}
    <section class="article-keywords mb-4" aria-labelledby="keywords-heading">
      <h2 id="keywords-heading" class="h5 mb-3">Ključne reči</h2>
      <div>
        {% for kw in article.keywords %}
        <span class="badge bg-light text-dark border me-1 mb-1">{{ kw }}</span>
        {% endfor %}
      </div>
    </section>
    {% endif %}

    <!-- Article Metadata -->
    <section class="article-metadata mb-4" aria-labelledby="metadata-heading">
      <h2 id="metadata-heading" class="h5 mb-3">Metapodaci</h2>
      <dl class="row">
        <dt class="col-sm-4">DOI</dt>
        <dd class="col-sm-8">
          <a href="{{ doi_url }}" rel="external" target="_blank">{{ full_doi }}</a>
        </dd>

        {% if article.first_page %}
        <dt class="col-sm-4">Stranice</dt>
        <dd class="col-sm-8">{{ article.first_page }}{% if article.last_page %}&ndash;{{ article.last_page }}{% endif %}</dd>
        {% endif %}

        <dt class="col-sm-4">Jezik</dt>
        <dd class="col-sm-8">{{ article.language }}</dd>

        <dt class="col-sm-4">Tip sadržaja</dt>
        <dd class="col-sm-8">{{ article.get_publication_type_display }}</dd>

        {% if article.license_url %}
        <dt class="col-sm-4">Licenca</dt>
        <dd class="col-sm-8">
          <a href="{{ article.license_url }}" rel="external" target="_blank">{{ article.license_url }}</a>
        </dd>
        {% endif %}

        {% if article.free_to_read %}
        <dt class="col-sm-4">Pristup</dt>
        <dd class="col-sm-8">
          <span class="badge bg-success">
            <i class="bi bi-unlock-fill me-1" aria-hidden="true"></i>Slobodan pristup
          </span>
        </dd>
        {% endif %}
      </dl>
    </section>
  </article>

  <!-- Sidebar -->
  <aside class="col-lg-4">
    <!-- Publication Info Card -->
    <div class="card mb-3">
      <div class="card-body">
        <h2 class="h5 card-title">Publikacija</h2>
        {% if article.issue.publication.cover_image %}
        <img src="{{ article.issue.publication.cover_image.url }}"
             class="img-fluid rounded mb-2"
             alt="Naslovna: {{ article.issue.publication.title }}"
             style="max-height: 200px;">
        {% endif %}
        <p class="mb-2">
          <a href="{% url 'portal-publications:publication-detail' article.issue.publication.slug %}">
            {{ article.issue.publication.title }}
          </a>
        </p>
        <p class="small text-muted mb-2">
          <a href="{% url 'portal-publications:issue-detail' slug=article.issue.publication.slug pk=article.issue.pk %}">
            Vol. {{ article.issue.volume }}, No. {{ article.issue.issue_number }} ({{ article.issue.year }})
          </a>
        </p>
        <span class="badge bg-secondary">
          {{ article.issue.publication.get_publication_type_display }}
        </span>
      </div>
    </div>

    <!-- Publisher Info Card -->
    <div class="card mb-3">
      <div class="card-body">
        <h2 class="h5 card-title">Izdavač</h2>
        {% if article.issue.publication.publisher.logo %}
        <img src="{{ article.issue.publication.publisher.logo.url }}"
             class="img-fluid mb-2"
             alt="Logo: {{ article.issue.publication.publisher.name }}"
             style="max-height: 60px;">
        {% endif %}
        <p class="mb-0">
          <i class="bi bi-building me-2" aria-hidden="true"></i>
          <a href="{% url 'portal:publisher-detail' article.issue.publication.publisher.slug %}">
            {{ article.issue.publication.publisher.name }}
          </a>
        </p>
      </div>
    </div>
  </aside>
</div>
{% endblock portal_content %}
```

### Azuriranje _article_search_card.html

```html
<!-- Promeniti liniju 6 -->
<!-- STARO: -->
<a href="/articles/{{ article.pk }}/" class="text-decoration-none">

<!-- NOVO: -->
<a href="{% url 'portal-articles:article-detail' article.pk %}" class="text-decoration-none">
```

### Azuriranje IssuePublicDetailView

```python
# U portal/views.py, IssuePublicDetailView.get_context_data():
# Promeniti placeholder:
context["articles"] = []

# U:
from doi_portal.articles.models import Article, ArticleStatus
context["articles"] = (
    Article.objects.filter(
        issue=self.object,
        status__in=[ArticleStatus.PUBLISHED, ArticleStatus.WITHDRAWN],
    )
    .select_related("issue__publication__publisher")
    .prefetch_related("authors")
    .order_by("first_page", "title")
)
```

### Azuriranje issue_detail.html Articles Section

```html
<!-- Promeniti placeholder article list u issue_detail.html -->
{% if articles %}
<div class="list-group">
    {% for article in articles %}
    <a href="{% url 'portal-articles:article-detail' article.pk %}"
       class="list-group-item list-group-item-action">
        <div class="d-flex justify-content-between align-items-start">
            <div>
                <h3 class="h6 mb-1">{{ article.title }}</h3>
                <p class="small text-muted mb-0">
                    {% for author in article.authors.all|slice:":3" %}
                        {{ author.surname }} {{ author.given_name|default:"" }}{% if not forloop.last %}, {% endif %}
                    {% endfor %}
                    {% if article.authors.all|length > 3 %}
                        <span>i dr.</span>
                    {% endif %}
                </p>
            </div>
            <div class="text-end">
                {% if article.first_page %}
                <span class="text-muted small">str. {{ article.first_page }}{% if article.last_page %}-{{ article.last_page }}{% endif %}</span>
                {% endif %}
                {% if article.status == "WITHDRAWN" %}
                <br><span class="badge bg-danger">Povučen</span>
                {% endif %}
            </div>
        </div>
    </a>
    {% endfor %}
</div>
{% else %}
<p class="text-muted mb-0">Članci će biti dostupni uskoro.</p>
{% endif %}
```

### Srpski Karakteri (OBAVEZNO - videti project-context.md)

| Kontekst | ISPRAVNO |
|----------|----------|
| Naslov sekcije | "Autori" |
| Korespondent badge | "Korespondent" |
| Apstrakt naslov | "Apstrakt" |
| Kljucne reci | "Ključne reči" |
| Metapodaci naslov | "Metapodaci" |
| DOI label | "DOI" |
| Stranice label | "Stranice" |
| Jezik label | "Jezik" |
| Tip sadrzaja | "Tip sadržaja" |
| Licenca label | "Licenca" |
| Pristup badge | "Slobodan pristup" |
| Publikacija card | "Publikacija" |
| Izdavac card | "Izdavač" |
| Withdrawn banner | "Povučen članak" |
| Withdrawn text | "Ovaj članak je povučen" |
| Razlog label | "Razlog:" |
| Nema autora | "Nema podataka o autorima." |
| Status published | "Objavljeno" |
| Status withdrawn | "Povučeno" |
| Breadcrumb Home | "Početna" |
| Breadcrumb Publications | "Publikacije" |

### Previous Story Learnings (Story 4.3 + Story 4.2 + Story 2.7)

1. **Portal base.html pattern**: Extends `portal/base.html`, koristi `{% block portal_content %}`, breadcrumbs se automatski renderuju iz context varijable.
2. **Two-column layout**: `issue_detail.html` koristi `col-lg-8` + `col-lg-4` layout - ISTI PATTERN koristiti.
3. **DetailView pattern**: `IssuePublicDetailView` je referentna implementacija: `get_queryset()` sa `select_related`, `get_context_data()` sa breadcrumbs.
4. **SoftDeleteManager**: Automatski filtrira soft-deleted zapise. Ne treba dodavati `is_deleted=False` filter.
5. **Named URL pattern**: Koristiti `reverse()` za sve linkove. `_article_search_card.html` MORA biti azuriran da koristi `{% url %}` tag.
6. **Bootstrap Icons**: VEC ukljuceni u `portal/base.html` kao CDN. Koristiti `bi-*` klase.
7. **Portal CSS**: `static/css/portal.css` - VEC ukljucen u `portal/base.html`. Dodati article-specific stilove u OVAJ fajl.
8. **Publisher sidebar pattern**: `issue_detail.html` VEC ima Publication i Publisher info cards u sidebar-u - KOPIRATI PATTERN.
9. **Status badge**: `article.status_badge_class` property VEC postoji na Article modelu. `article.get_status_display` za srpski tekst.
10. **Template tag**: `portal_tags.py` sa `highlight_search` filterom postoji - nije potreban za article detail.
11. **Test pattern**: pytest-django, `@pytest.mark.django_db`, Factory Boy. `ArticleFactory`, `AuthorFactory`, `AffiliationFactory`, `IssueFactory`, `PublicationFactory`, `PublisherFactory` su VEC dostupni.
12. **URL namespace pattern**: Portal koristi odvojene URL fajlove: `urls.py` (portal namespace, publishers), `urls_publications.py` (portal-publications namespace). Kreirati `urls_articles.py` (portal-articles namespace) po ISTOM PATTERNU.
13. **ArticleStatus imports**: `ArticleStatus` je VEC importovan u `portal/services.py` (linija 14). U `portal/views.py` NIJE importovan - dodati import.
14. **Article model fields za landing page**: `title`, `subtitle`, `abstract`, `keywords` (JSONField - lista stringova), `doi_suffix`, `first_page`, `last_page`, `language`, `publication_type` (choices), `license_url`, `free_to_read`, `status`, `published_at`, `withdrawal_reason`, `withdrawn_at`.
15. **Author model fields**: `given_name`, `surname`, `suffix`, `orcid`, `email`, `is_corresponding`, `order`. Related: `affiliations` (reverse FK sa `institution_name`, `department`).
16. **Publisher.doi_prefix**: Sluzi za konstruisanje kompletnog DOI-ja: `{doi_prefix}/{doi_suffix}`.
17. **Test suite**: Story 4.3 ima 1179/1193 ukupnih testova (11 pre-existing failures u test_pdf_upload.py). Ne smemo imati regresije.
18. **select_related chain**: `select_related("issue__publication__publisher")` pokriva sve join-ove od Article do Publisher u jednom SQL upitu.
19. **prefetch_related za autore**: `prefetch_related("authors__affiliations")` - 2 dodatna SQL upita (autori + afilijacije) umesto N+1.

### Git Commit Pattern

```
story-4-4: feat(portal): implementiraj Article Landing Page sa two-column layout, author/metadata display i withdrawn banner (Story 4.4)
```

### Fajlovi za kreiranje (NOVI)

```
doi_portal/doi_portal/portal/urls_articles.py                         # URL routing za article landing page
doi_portal/doi_portal/templates/portal/article_detail.html             # Article landing page template
doi_portal/doi_portal/portal/tests/test_article_landing.py             # Article landing page testovi
```

### Fajlovi za modifikaciju (POSTOJECI)

```
doi_portal/doi_portal/portal/services.py                               # Dodati get_article_for_landing() funkciju
doi_portal/doi_portal/portal/views.py                                  # Dodati ArticleLandingView, azurirati IssuePublicDetailView
doi_portal/config/urls.py                                              # Dodati articles URL include
doi_portal/doi_portal/templates/portal/partials/_article_search_card.html  # Azurirati hardcoded URL u named URL
doi_portal/doi_portal/templates/portal/publications/issue_detail.html  # Azurirati articles sekciju sa linkovima
doi_portal/doi_portal/static/css/portal.css                            # Dodati article landing page stilove
```

### Fajlovi koji se NE MENJAJU

```
doi_portal/doi_portal/templates/portal/base.html                       # VEC postoji - NE MENJATI
doi_portal/doi_portal/templates/portal/home.html                       # VEC postoji - NE MENJATI
doi_portal/doi_portal/templates/portal/search_results.html             # VEC postoji - NE MENJATI
doi_portal/doi_portal/templates/portal/partials/_search_results.html   # VEC postoji - NE MENJATI
doi_portal/doi_portal/templates/portal/partials/_article_filter_sidebar.html  # VEC postoji - NE MENJATI
doi_portal/doi_portal/articles/models.py                               # VEC postoji - NE MENJATI
doi_portal/doi_portal/publications/models.py                           # VEC postoji - NE MENJATI
doi_portal/doi_portal/issues/models.py                                 # VEC postoji - NE MENJATI
doi_portal/doi_portal/publishers/models.py                             # VEC postoji - NE MENJATI
doi_portal/doi_portal/portal/urls.py                                   # VEC postoji - NE MENJATI
doi_portal/doi_portal/portal/urls_publications.py                      # VEC postoji - NE MENJATI
```

### Anti-Patterns (ZABRANJENO)

```python
# POGRESNO - Kreirati novi model za article landing
class ArticleLanding(models.Model):  # NE! Koristiti postojeci Article model

# POGRESNO - Prikazivati DRAFT/REVIEW/READY clanke na javnom portalu
Article.objects.all()  # NE! Filtrirati po status__in=[PUBLISHED, WITHDRAWN]

# POGRESNO - Koristiti Django Admin za javni prikaz
from django.contrib import admin  # NE za portal views!

# POGRESNO - Hardcoded DOI URL
doi_url = "https://doi.org/10.1234/article-1"  # NE! Konstruisati iz publisher.doi_prefix + article.doi_suffix

# POGRESNO - N+1 queries za autore i afilijacije
for author in article.authors.all():
    for aff in author.affiliations.all():  # NE! Koristiti prefetch_related("authors__affiliations")

# POGRESNO - Koristiti FBV umesto CBV za DetailView
def article_detail(request, pk):  # NE! Koristiti DetailView klasu

# POGRESNO - Staviti business logiku u template
{% if article.status == "PUBLISHED" or article.status == "WITHDRAWN" %}  # NE! Filtrirati u view queryset

# POGRESNO - Kreirati URL bez namespace-a
path("articles/<int:pk>/", ArticleLandingView.as_view(), name="article-detail")  # NE! Koristiti include sa namespace

# POGRESNO - Ne koristiti select_related za FK chain
Article.objects.get(pk=pk)  # NE! Koristiti select_related("issue__publication__publisher")

# POGRESNO - Zaboraviti srpske karaktere sa dijakriticima
"Kljucne reci"  # POGRESNO!
"Ključne reči"  # ISPRAVNO!

# POGRESNO - Hardcoded link u search card-u
href="/articles/{{ article.pk }}/"  # NE! Koristiti {% url 'portal-articles:article-detail' article.pk %}
```

### Performance (NFR1 - FCP < 3s)

```python
# Minimizovati SQL upite:
# 1. select_related("issue__publication__publisher") - 1 JOIN upit
# 2. prefetch_related("authors__affiliations") - 2 dodatna upita
# Ukupno: 3 SQL upita za kompletnu stranicu

# Ne koristiti:
# - Lazy loading za related objekte
# - Template tag-ove koji prave dodatne upite
# - JavaScript koji blokira renderovanje
```

### Test Pattern

```python
# portal/tests/test_article_landing.py

import pytest
from django.urls import reverse

from doi_portal.articles.models import ArticleStatus
from doi_portal.articles.tests.factories import ArticleFactory, AuthorFactory, AffiliationFactory
from doi_portal.issues.models import IssueStatus
from doi_portal.issues.tests.factories import IssueFactory
from doi_portal.publications.tests.factories import PublicationFactory
from doi_portal.publishers.tests.factories import PublisherFactory


@pytest.mark.django_db
class TestArticleLandingView:
    """Tests for ArticleLandingView."""

    def _create_published_article(self):
        publisher = PublisherFactory(doi_prefix="10.9999")
        pub = PublicationFactory(publisher=publisher)
        issue = IssueFactory(publication=pub, status=IssueStatus.PUBLISHED)
        article = ArticleFactory(
            issue=issue,
            title="Test Clanak",
            doi_suffix="test-001",
            status=ArticleStatus.PUBLISHED,
        )
        author = AuthorFactory(article=article, given_name="Petar", surname="Petrovic", orcid="0000-0001-2345-6789")
        AffiliationFactory(author=author, institution_name="Univerzitet u Beogradu")
        return article

    def test_published_article_returns_200(self, client):
        article = self._create_published_article()
        response = client.get(reverse("portal-articles:article-detail", kwargs={"pk": article.pk}))
        assert response.status_code == 200

    def test_withdrawn_article_returns_200(self, client):
        article = self._create_published_article()
        article.status = ArticleStatus.WITHDRAWN
        article.save()
        response = client.get(reverse("portal-articles:article-detail", kwargs={"pk": article.pk}))
        assert response.status_code == 200

    def test_draft_article_returns_404(self, client):
        publisher = PublisherFactory()
        pub = PublicationFactory(publisher=publisher)
        issue = IssueFactory(publication=pub, status=IssueStatus.PUBLISHED)
        article = ArticleFactory(issue=issue, status=ArticleStatus.DRAFT)
        response = client.get(reverse("portal-articles:article-detail", kwargs={"pk": article.pk}))
        assert response.status_code == 404

    def test_nonexistent_article_returns_404(self, client):
        response = client.get(reverse("portal-articles:article-detail", kwargs={"pk": 99999}))
        assert response.status_code == 404

    def test_context_has_breadcrumbs(self, client):
        article = self._create_published_article()
        response = client.get(reverse("portal-articles:article-detail", kwargs={"pk": article.pk}))
        assert len(response.context["breadcrumbs"]) == 5

    def test_context_has_full_doi(self, client):
        article = self._create_published_article()
        response = client.get(reverse("portal-articles:article-detail", kwargs={"pk": article.pk}))
        assert response.context["full_doi"] == "10.9999/test-001"

    def test_context_has_doi_url(self, client):
        article = self._create_published_article()
        response = client.get(reverse("portal-articles:article-detail", kwargs={"pk": article.pk}))
        assert response.context["doi_url"] == "https://doi.org/10.9999/test-001"

    def test_is_withdrawn_true_for_withdrawn(self, client):
        article = self._create_published_article()
        article.status = ArticleStatus.WITHDRAWN
        article.save()
        response = client.get(reverse("portal-articles:article-detail", kwargs={"pk": article.pk}))
        assert response.context["is_withdrawn"] is True

    def test_is_withdrawn_false_for_published(self, client):
        article = self._create_published_article()
        response = client.get(reverse("portal-articles:article-detail", kwargs={"pk": article.pk}))
        assert response.context["is_withdrawn"] is False
```

### Dependencies (Python/Django)

Nema novih Python zavisnosti! Sve je vec instalirano:
- Django 5.2+ (DetailView, reverse, select_related, prefetch_related)
- Bootstrap 5 (CSS framework - two-column layout, cards, badges, alerts)
- Bootstrap Icons (vec ukljuceni u portal/base.html CDN)
- pytest-django + Factory Boy (vec u test setup-u)

### NFR Requirements

- **FR41:** Posetilac moze videti landing stranicu clanka sa svim metapodacima - direktna implementacija
- **NFR1:** Landing stranica clanka - First Contentful Paint < 3 sekunde - minimalni SQL (3 upita), no JS blocking
- **NFR2:** Javne stranice portala - ucitavanje < 3 sekunde - server-rendered HTML, no SPA overhead
- **NFR14:** Semanticki HTML5 elementi - `<article>`, `<aside>`, `<section>`, `<dl>/<dt>/<dd>`
- **NFR15:** Alt tekst za slike - cover image, publisher logo, ORCID ikonica
- **NFR16:** Kontrast minimum 4.5:1 - Bootstrap 5 default paleta zadovoljava
- **NFR17:** Keyboard navigacija - Tab through all links, badges, buttons
- **NFR18:** Labels povezani sa input poljima - N/A (nema input polja na landing page)

### References

- [Source: epics.md#Story 4.4: Article Landing Page (Defining Experience)]
- [Source: epics.md#Epic 4: Public Portal Experience - FR41]
- [Source: prd.md#7. Public Portal - FR41 (Landing stranica clanka)]
- [Source: prd.md#Performance - NFR1 (FCP < 3 sekunde)]
- [Source: architecture.md#Frontend Architecture - HTMX 2.0.8, Bootstrap 5]
- [Source: architecture.md#Implementation Patterns - naming conventions]
- [Source: ux-design-specification.md#Article Landing Layout (Frontiers stil)]
- [Source: ux-design-specification.md#Journey 3: Posetilac pristupa clanku - DOI link -> Landing (<3s)]
- [Source: ux-design-specification.md#Layout Adaptations - Article landing: 2 kolone desktop, 1 kolona mobile]
- [Source: ux-design-specification.md#Custom Components - Floating Action Bar]
- [Source: ux-design-specification.md#Responsive Strategy - Desktop-first, mobile adaptation]
- [Source: project-context.md#Services Layer (Business Logic)]
- [Source: project-context.md#HTMX Pravila - partials sa _ prefix]
- [Source: project-context.md#Naming Konvencije - snake_case, PascalCase, kebab-case]
- [Source: project-context.md#Lokalizacija - Srpski Karakteri, sr-Latn]
- [Source: project-context.md#Testing (pytest-django) - Factory Boy]
- [Source: project-context.md#Django Apps Struktura - portal app za FR38-FR45]
- [Source: portal/views.py - Existing IssuePublicDetailView two-column pattern]
- [Source: portal/services.py - Existing search_articles() pattern]
- [Source: portal/base.html - Portal base template with nav, breadcrumbs, footer]
- [Source: portal/partials/_article_search_card.html - Hardcoded /articles/ URL na liniji 6]
- [Source: portal/publications/issue_detail.html - Reference two-column layout + sidebar pattern]
- [Source: articles/models.py - Article, Author, Affiliation models]
- [Source: issues/models.py - Issue model with publication FK]
- [Source: publishers/models.py - Publisher.doi_prefix field]
- [Source: config/urls.py - URL registration pattern for portal routes]
- [Source: portal/urls_publications.py - Reference URL namespace pattern]
- [Source: 4-3-advanced-filtering-for-articles.md - Previous story learnings]

## Dev Agent Record

### Agent Model Used

Claude Opus 4.5 (claude-opus-4-5-20251101)

### Debug Log References

- All 32 story-specific tests pass (7 service + 25 view tests)
- Full suite: 1177 passed, 3 skipped (excluding 11 pre-existing test_pdf_upload failures)
- Updated existing test `test_context_has_articles_empty_list` -> `test_context_has_articles_empty_queryset` to adapt to QuerySet return type change in IssuePublicDetailView

### Completion Notes List

- Task 1: `get_article_for_landing()` service function added to `portal/services.py` with select_related/prefetch_related optimization
- Task 2: `ArticleLandingView(DetailView)` created with get_queryset filtering, breadcrumbs, is_withdrawn, full_doi, doi_url context
- Task 3: `portal/urls_articles.py` created with portal-articles namespace, registered in `config/urls.py` at `/articles/<pk>/`
- Task 4: `article_detail.html` template with two-column layout, WITHDRAWN banner, authors+ORCID, abstract, keywords, metadata, sidebar
- Task 5: `_article_search_card.html` updated from hardcoded URL to `{% url 'portal-articles:article-detail' article.pk %}`
- Task 6: `issue_detail.html` updated with real article links and `IssuePublicDetailView` now returns real PUBLISHED/WITHDRAWN articles queryset
- Task 7: CSS styles added for article-title, article-subtitle, author-entry, orcid-link, withdrawn-banner, article-metadata, keyword-tag
- Task 8: 32 comprehensive tests (7 service + 25 view) covering all ACs

### File List

**New files:**
- `doi_portal/doi_portal/portal/urls_articles.py` - URL routing for article landing page
- `doi_portal/doi_portal/templates/portal/article_detail.html` - Article landing page template
- `doi_portal/doi_portal/portal/tests/test_article_landing.py` - Article landing page tests (32 tests)

**Modified files:**
- `doi_portal/doi_portal/portal/services.py` - Added `get_article_for_landing()` function
- `doi_portal/doi_portal/portal/views.py` - Added `ArticleLandingView`, updated `IssuePublicDetailView` with real articles queryset
- `doi_portal/config/urls.py` - Added articles URL include
- `doi_portal/doi_portal/templates/portal/partials/_article_search_card.html` - Updated hardcoded URL to named URL
- `doi_portal/doi_portal/templates/portal/publications/issue_detail.html` - Updated articles section with real article links
- `doi_portal/doi_portal/static/css/portal.css` - Added article landing page styles
- `doi_portal/doi_portal/portal/tests/test_views.py` - Fixed existing test for QuerySet return type
- `_bmad-output/implementation-artifacts/sprint-status.yaml` - Updated status to in-progress -> review
- `_bmad-output/implementation-artifacts/4-4-article-landing-page.md` - Marked all tasks [x], updated Dev Agent Record
