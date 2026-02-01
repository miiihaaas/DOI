# Story 4.1: Portal Home Page

Status: done

## Story

As a **visitor**,
I want **to see an attractive home page with portal overview**,
So that **I can understand what the portal offers and start browsing**.

## Background

Ovo je prva prica u Epiku 4 (Public Portal Experience). Portal home page je ulazna tacka za sve posetioce - dolaze direktno ili sa pretrazivaca. Stranica mora prikazati hero sekciju sa pretragom, istaknute/najnovije publikacije, statistiku portala i brze linkove. Trenutna pocetna stranica (`pages/home.html`) je prazan Cookiecutter placeholder koji samo extenduje `base.html` bez ikakvog sadrzaja.

**FR Pokrivenost:**
- FR38: Posetilac moze videti pocetnu stranu portala

**NFR Pokrivenost:**
- NFR2: Javne stranice portala - ucitavanje < 3 sekunde
- NFR14-NFR18: Accessibility (semanticki HTML5, alt tekst, kontrast, keyboard, labels)

**Zavisnosti (sve DONE):**
- Story 1.1: Cookiecutter Django - bazni `base.html` template
- Story 2.2: Public Publisher Page - portal/base.html template sa sticky header, breadcrumbs, footer, navbar
- Story 2.5: Public Publication List - `PublicationPublicListView`, HTMX filter pattern
- Story 2.7: Public Issue List - `IssuePublicDetailView`
- Story 3.1: Article Model - `Article`, `ArticleStatus` enum
- Story 3.8: Dashboard Statistics - aggregate query pattern

**Blokira:**
- Story 4.2: Article Search Functionality - hero search bar navigira na search results

## Acceptance Criteria

1. **Given** posetilac navigira na root URL portala (/)
   **When** pocetna strana se ucitava
   **Then** stranica se ucitava za manje od 3 sekunde (FCP target)
   **And** koristi se Bootstrap 5 javni template (portal/base.html) sa doi.rs brendingom

2. **Given** sadrzaj pocetne strane je prikazan
   **When** posetilac pregleda stranicu
   **Then** hero sekcija prikazuje naziv portala i search bar
   **And** sekcija istaknutih/najnovijih publikacija je prikazana
   **And** statistike portala su prikazane (ukupno publikacija, clanaka, izdavaca)
   **And** brzi linkovi ka glavnim sekcijama su vidljivi

3. **Given** posetilac koristi hero search bar
   **When** unese termin za pretragu i pritisne Enter ili klikne dugme
   **Then** korisnik je preusmeren na stranicu rezultata pretrage (placeholder za Story 4.2)

4. **Given** posetilac je na mobilnom uredaju
   **When** pregleda pocetnu stranu
   **Then** responsivan layout se pravilno prilagodava
   **And** navigacija se skuplja u hamburger meni
   **And** touch targeti su najmanje 44px

5. **Given** pocetna strana prikazuje statistike
   **When** podaci se ucitavaju
   **Then** statistike prikazuju tacne brojeve iz baze
   **And** upiti koriste optimizovane querysets (aggregate)

6. **Given** pocetna strana prikazuje najnovije publikacije
   **When** postoje aktivne publikacije
   **Then** prikazuje se maksimalno 6 najnovijih publikacija
   **And** svaka publikacija prikazuje: naslov, tip (ikona), naziv izdavaca
   **And** klik vodi na stranicu publikacije

7. **Given** nema publikacija u sistemu
   **When** posetilac pregleda pocetnu stranu
   **Then** prikazuje se odgovarajuca poruka umesto prazne sekcije

8. **Given** stranica se ucitava
   **When** analiziramo pristupacnost
   **Then** semanticki HTML5 elementi su korisceni
   **And** svi linkovi imaju deskriptivan tekst
   **And** kontrast je minimum 4.5:1 za tekst
   **And** keyboard navigacija funkcionise

## Tasks / Subtasks

- [x] Task 1: Kreirati portal home page view u `portal/views.py` (AC: #1, #2, #5)
  - [x] 1.1 Kreirati `PortalHomeView(TemplateView)` klasu u `doi_portal/portal/views.py`
  - [x] 1.2 Template: `portal/home.html` (koristi portal/base.html, NE pages/home.html)
  - [x] 1.3 Implementirati `get_context_data()` sa:
    - `stats`: portal statistike (ukupno publikacija, clanaka, izdavaca)
    - `recent_publications`: 6 najnovijih publikacija sa select_related("publisher")
    - `breadcrumbs`: samo "Pocetna" (prazan jer je root)
  - [x] 1.4 Kreirati `portal/services.py` sa:
    - `get_portal_statistics()`: vraca dict sa total_publications, total_articles, total_publishers, published_articles_count
    - `get_recent_publications(limit=6)`: vraca najnovijih N publikacija
  - [x] 1.5 Statistike koristiti aggregate() pattern (jedan SQL upit, isti pattern kao dashboard/services.py)

- [x] Task 2: Azurirati URL routing za portal home page (AC: #1)
  - [x] 2.1 U `config/urls.py` zameniti Cookiecutter placeholder home view sa `PortalHomeView`
  - [x] 2.2 Importovati `PortalHomeView` iz `doi_portal.portal.views`
  - [x] 2.3 Zadrzati isti URL name `"home"` - VEC se koristi u portal/base.html navigaciji
  - [x] 2.4 OBRISATI ili zakomentarisati stari TemplateView za `pages/home.html`

- [x] Task 3: Kreirati `portal/home.html` template - hero sekcija (AC: #2, #3, #8)
  - [x] 3.1 Extend `portal/base.html` (NE base.html direktno)
  - [x] 3.2 Override `portal_content` block (NE `content`)
  - [x] 3.3 Hero sekcija:
    - Naslov portala: "DOI Portal" sa kratkim opisom
    - Search form: `<form>` sa input poljem i submit dugmetom
    - Form action: `/search/` (placeholder URL za Story 4.2)
    - Submit: Enter ili klik na dugme sa ikonom pretrage
  - [x] 3.4 Hero pozadina: blaga gradient boja ili solid boja, NE slika (performanse)
  - [x] 3.5 Search input: `name="q"`, placeholder "Pretrazite clanke po naslovu, autoru, kljucnim recima..."

- [x] Task 4: Kreirati `portal/home.html` template - statistike sekcija (AC: #2, #5)
  - [x] 4.1 Tri statisticke kartice u redu (col-md-4):
    - Publikacije: bi-journal-text ikona, `{{ stats.total_publications }}`
    - Clanci: bi-file-earmark-text ikona, `{{ stats.published_articles_count }}`
    - Izdavaci: bi-building ikona, `{{ stats.total_publishers }}`
  - [x] 4.2 Kartice koriste Bootstrap 5 card shadow-sm pattern
  - [x] 4.3 Svaka kartica je klikabilna (link na odgovarajucu listu)

- [x] Task 5: Kreirati `portal/home.html` template - najnovije publikacije sekcija (AC: #2, #6, #7)
  - [x] 5.1 Sekcija naslov: "Najnovije publikacije"
  - [x] 5.2 Grid layout: 3 kolone na desktop-u (col-md-4), 1 kolona na mobile
  - [x] 5.3 Svaka publikacija kao kartica sa:
    - Cover slika ili placeholder ikona za tip
    - Naslov publikacije (link na detail)
    - Ikona tipa publikacije (casopis/zbornik/knjiga)
    - Naziv izdavaca
  - [x] 5.4 Prazan state: "Nema dostupnih publikacija." sa info ikonom
  - [x] 5.5 "Prikazi sve publikacije" link na dnu sekcije

- [x] Task 6: Kreirati `portal/home.html` template - brzi linkovi sekcija (AC: #2)
  - [x] 6.1 Sekcija sa brzim linkovima na kljucne delove portala:
    - "Publikacije" -> /publications/
    - "Izdavaci" -> /publishers/
    - "O portalu" -> /about/
  - [x] 6.2 Koristiti Bootstrap list-group ili card-deck sa ikonama

- [x] Task 7: Responsivnost i pristupacnost (AC: #4, #8)
  - [x] 7.1 Hero sekcija: full-width, padding responsive
  - [x] 7.2 Statistike: 3 kolone na desktop, stacked na mobile
  - [x] 7.3 Publikacije grid: 3 -> 2 -> 1 kolona responsive
  - [x] 7.4 Search form: full-width na mobile
  - [x] 7.5 Semanticki HTML: `<header>`, `<main>`, `<section>`, `<h1>`-`<h2>` hijerarhija
  - [x] 7.6 Svi linkovi imaju deskriptivan tekst (ne "kliknite ovde")
  - [x] 7.7 Skip-to-content link (vec u portal/base.html)
  - [x] 7.8 Touch targets min 44px na mobile

- [x] Task 8: Kreirati testove (AC: #1-#8)
  - [x] 8.1 View test: home page vraca 200 na GET /
  - [x] 8.2 View test: koristi portal/home.html template
  - [x] 8.3 View test: context sadrzi `stats` dict sa ocekivanim kljucevima
  - [x] 8.4 View test: context sadrzi `recent_publications` queryset
  - [x] 8.5 View test: nema autentifikacije - javna stranica
  - [x] 8.6 Service test: `get_portal_statistics()` vraca tacne brojeve
  - [x] 8.7 Service test: `get_portal_statistics()` sa praznom bazom vraca nule
  - [x] 8.8 Service test: `get_recent_publications()` vraca max 6 publikacija
  - [x] 8.9 Service test: `get_recent_publications()` sortira po created_at desc
  - [x] 8.10 Service test: `get_recent_publications()` iskljucuje soft-deleted
  - [x] 8.11 View test: statistike prikazane u HTML-u (broj publikacija vidljiv)
  - [x] 8.12 View test: najnovije publikacije prikazane kao kartice
  - [x] 8.13 View test: prazan state prikazan kad nema publikacija
  - [x] 8.14 View test: hero search form ima action="/search/" i input name="q"
  - [x] 8.15 View test: breadcrumbs ne prikazuju se na home page (root stranica)
  - [x] 8.16 Integration test: klik na publikaciju vodi na publication detail
  - [x] 8.17 SEO test: stranica ima odgovarajuci `<title>` tag

## Dev Notes

### KRITICNO: Zamena Cookiecutter Home Page Placeholder

Trenutna pocetna stranica je Cookiecutter default placeholder na `/`:
```python
# config/urls.py - TRENUTNO STANJE
path("", TemplateView.as_view(template_name="pages/home.html"), name="home"),
```

`pages/home.html` je prazan template koji samo extenduje `base.html`. Ovaj view se ZAMENJUJE novim `PortalHomeView`.

**VAZNO:** URL name `"home"` MORA ostati isti jer se vec koristi u:
- `portal/base.html` linija 23: `{% url 'home' %}` (navbar brand link)
- `portal/base.html` breadcrumbs: `{"label": "Pocetna", "url": reverse("home")}`
- Svi portal views (publishers, publications, issues) koriste `reverse("home")` za breadcrumbs

### Portal Base Template (VEC POSTOJI)

`portal/base.html` je kreiran u Story 2.2 i sadrzi:
- Sticky header sa navbar (DOI Portal brand, Izdavaci, Publikacije, O portalu, Prijava/Dashboard)
- Breadcrumbs sekcija (conditional prikazivanje)
- Main content area: `{% block portal_content %}`
- Footer sa info o portalu
- Bootstrap Icons CDN
- Portal CSS: `{% static 'css/portal.css' %}`
- Skip-to-content link za pristupacnost

Home page template MORA da extenduje `portal/base.html` i koristi `{% block portal_content %}`.

### Services Layer Pattern

Sva business logika za statistike i query-je ide u `portal/services.py`. View DELEGIRA u service sloj, isto kao sto radi `dashboard/services.py` za admin dashboard.

```python
# portal/services.py

from django.db.models import Count, Q

from doi_portal.articles.models import Article, ArticleStatus
from doi_portal.publications.models import Publication
from doi_portal.publishers.models import Publisher


def get_portal_statistics() -> dict:
    """
    Get portal-wide statistics for home page.

    Uses aggregate() for single SQL query (same pattern as dashboard/services.py).
    """
    article_counts = Article.objects.aggregate(
        total=Count("id"),
        published=Count("id", filter=Q(status=ArticleStatus.PUBLISHED)),
    )
    return {
        "total_publications": Publication.objects.count(),
        "total_articles": article_counts["total"],
        "published_articles_count": article_counts["published"],
        "total_publishers": Publisher.objects.count(),
    }


def get_recent_publications(limit: int = 6):
    """
    Get most recent active publications for home page.

    SoftDeleteManager already excludes is_deleted=True records.
    """
    return (
        Publication.objects.select_related("publisher")
        .order_by("-created_at")[:limit]
    )
```

### PortalHomeView

```python
# portal/views.py - DODATI novu klasu

from django.views.generic import TemplateView

from doi_portal.portal.services import get_portal_statistics, get_recent_publications


class PortalHomeView(TemplateView):
    """
    Portal home page view.

    FR38: Posetilac moze videti pocetnu stranu portala.
    Public view - no authentication required.
    """

    template_name = "portal/home.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["stats"] = get_portal_statistics()
        context["recent_publications"] = get_recent_publications()
        # No breadcrumbs on home page (it IS the root)
        return context
```

### URL Routing Azuriranje

```python
# config/urls.py - ZAMENA:
# STARO:
# path("", TemplateView.as_view(template_name="pages/home.html"), name="home"),
# NOVO:
from doi_portal.portal.views import PortalHomeView

path("", PortalHomeView.as_view(), name="home"),
```

### Template Struktura

```html
<!-- templates/portal/home.html -->
{% extends "portal/base.html" %}
{% load static %}

{% block title %}DOI Portal - Pocetna{% endblock title %}

{% block portal_content %}
<!-- Hero Section -->
<section class="hero-section bg-primary bg-gradient text-white py-5 mb-4 rounded-3">
  <div class="text-center py-4">
    <h1 class="display-4 fw-bold">DOI Portal</h1>
    <p class="lead mb-4">Portal za registraciju DOI identifikatora naucnih publikacija</p>
    <form action="/search/" method="get" class="mx-auto" style="max-width: 600px;">
      <div class="input-group input-group-lg">
        <input type="search" name="q" class="form-control"
               placeholder="Pretrazite clanke po naslovu, autoru, kljucnim recima..."
               aria-label="Pretraga clanaka">
        <button type="submit" class="btn btn-light">
          <i class="bi bi-search"></i>
          <span class="visually-hidden">Pretrazi</span>
        </button>
      </div>
    </form>
  </div>
</section>

<!-- Statistics Cards -->
<section class="mb-5">
  <div class="row g-4">
    <div class="col-md-4">
      <a href="{% url 'portal-publications:publication-list' %}" class="text-decoration-none">
        <div class="card shadow-sm h-100 text-center">
          <div class="card-body">
            <i class="bi bi-journal-text display-4 text-primary mb-2"></i>
            <h2 class="display-6 fw-bold">{{ stats.total_publications }}</h2>
            <p class="text-muted mb-0">Publikacije</p>
          </div>
        </div>
      </a>
    </div>
    <!-- ... articles, publishers cards ... -->
  </div>
</section>

<!-- Recent Publications -->
<section class="mb-5">
  <div class="d-flex justify-content-between align-items-center mb-3">
    <h2 class="h4 mb-0">Najnovije publikacije</h2>
    <a href="{% url 'portal-publications:publication-list' %}">Prikazi sve &rarr;</a>
  </div>
  {% if recent_publications %}
  <div class="row g-4">
    {% for pub in recent_publications %}
    <div class="col-md-4">
      <!-- Publication card -->
    </div>
    {% endfor %}
  </div>
  {% else %}
  <div class="text-center text-muted py-4">
    <i class="bi bi-journal-text display-6 mb-2 d-block"></i>
    Nema dostupnih publikacija.
  </div>
  {% endif %}
</section>

<!-- Quick Links -->
<section class="mb-4">
  <!-- Quick link cards -->
</section>
{% endblock portal_content %}
```

### Srpski Karakteri (OBAVEZNO - videti project-context.md)

| Kontekst | ISPRAVNO |
|----------|----------|
| Portal naslov | "DOI Portal" |
| Portal opis | "Portal za registraciju DOI identifikatora naučnih publikacija" |
| Search placeholder | "Pretražite članke po naslovu, autoru, ključnim rečima..." |
| Search dugme sr-only | "Pretraži" |
| Stat: publikacije | "Publikacije" |
| Stat: clanci | "Objavljeni članci" |
| Stat: izdavaci | "Izdavači" |
| Sekcija naslov | "Najnovije publikacije" |
| Prazan state | "Nema dostupnih publikacija." |
| Link svi | "Prikaži sve" |
| Brzi linkovi | "Brzi linkovi" |
| Link publikacije | "Publikacije" |
| Link izdavaci | "Izdavači" |
| Link o portalu | "O portalu" |
| Title tag | "DOI Portal - Početna strana" |
| Meta opis | "DOI Portal - Pregledajte naučne publikacije i članke" |

### Previous Story Learnings (Epic 2-3)

1. **Portal base template** (`portal/base.html`) VEC postoji. Koristi ga kao parent template. Blok za content: `{% block portal_content %}`. (Story 2.2)
2. **Publication model** koristi `SoftDeleteManager` koji automatski filtrira soft-deleted zapise. Ne treba dodavati `is_deleted=False` filter. (Story 2.3)
3. **PublicationType enum** za ikonice: `JOURNAL`, `CONFERENCE`, `BOOK`, `OTHER`. Koristiti razlicite bi-icon-e za svaki tip. (Story 2.3)
4. **HTMX pattern** za filter/search: `HX-Request` header check za partial response. Za home page NIJE potreban HTMX (staticka strana). (Story 2.5)
5. **Breadcrumbs** pattern: dict lista sa `label` i `url`. Na home page NE prikazivati breadcrumbs (root nivo). Portal base.html vec ima conditional prikaz: `{% if breadcrumbs %}`. (Story 2.2)
6. **Aggregate pattern** za statistike: koristiti `Article.objects.aggregate(Count + filter=Q)` za jedan SQL upit. Isti pattern kao u `dashboard/services.py`. (Story 3.8)
7. **`select_related`** za publikacije: uvek ukljuciti `"publisher"` za izbegavanje N+1 upita. (Story 2.5)
8. **Portal CSS**: `static/css/portal.css` - vec ukljucen u portal/base.html. Dodati custom stilove za hero sekciju u ovaj fajl. (Story 2.2)
9. **Navbar active klasa**: portal/base.html vec ima conditional active klasu baziranu na `request.resolver_match`. Home page nema posebnu active klasu na nav-u. (Story 2.2)
10. **Test pattern**: pytest-django, `@pytest.mark.django_db`, Factory Boy. Koristiti `PublisherFactory`, `PublicationFactory` iz `portal/tests/factories.py`. (Story 2.2)
11. **SEO**: Koristiti `{% block title %}` za naslov i `<meta name="description">` tag. (Story 2.5)
12. **URL name "home"**: VEC se koristi svuda u portal/base.html i svim breadcrumbs. NE MENJATI ime. (Story 2.2)

### Git Commit Pattern

```
story-4-1: feat(portal): implementiraj Portal Home Page sa hero pretragom, statistikama i najnovijim publikacijama (Story 4.1)
```

### Fajlovi za kreiranje (NOVI)

```
doi_portal/doi_portal/portal/services.py                    # Portal service funkcije (statistike, recent publications)
doi_portal/doi_portal/templates/portal/home.html             # Home page template
doi_portal/doi_portal/portal/tests/test_home.py              # Home page testovi (view + service)
```

### Fajlovi za modifikaciju (POSTOJECI)

```
doi_portal/config/urls.py                                    # Zameniti TemplateView sa PortalHomeView
doi_portal/doi_portal/portal/views.py                        # Dodati PortalHomeView klasu
```

### Fajlovi koji se NE MENJAJU

```
doi_portal/doi_portal/templates/portal/base.html             # VEC postoji, NE MENJATI (parent template)
doi_portal/doi_portal/templates/pages/home.html              # Stari placeholder - ostaje ali se ne koristi
doi_portal/doi_portal/portal/urls.py                         # Publisher routes - NE MENJATI
doi_portal/doi_portal/portal/urls_publications.py            # Publication routes - NE MENJATI
```

### Optimizacija Querysets (KRITICNO - NFR2)

Sve statistike se dohvataju u minimalno SQL upita:

```python
# ISPRAVNO - Jedan upit za article statistike
article_counts = Article.objects.aggregate(
    total=Count("id"),
    published=Count("id", filter=Q(status=ArticleStatus.PUBLISHED)),
)

# ISPRAVNO - Jedan upit za ostale statistike
total_publications = Publication.objects.count()
total_publishers = Publisher.objects.count()

# ISPRAVNO - Jedan upit za najnovije publikacije sa join-om
recent = Publication.objects.select_related("publisher").order_by("-created_at")[:6]

# POGRESNO - Vise pojedinacnih count() poziva
total_articles = Article.objects.count()
published = Article.objects.filter(status=ArticleStatus.PUBLISHED).count()
```

### Anti-Patterns (ZABRANJENO)

```python
# POGRESNO - Koristiti pages/home.html umesto portal/home.html
template_name = "pages/home.html"  # NE! Koristi portal/home.html

# POGRESNO - Extendovati base.html umesto portal/base.html
{% extends "base.html" %}  # NE! Koristi portal/base.html

# POGRESNO - Koristiti {% block content %} umesto {% block portal_content %}
{% block content %}  # NE! portal/base.html koristi {% block portal_content %}

# POGRESNO - Business logika u view-u
def get_context_data(self, **kwargs):
    context["total"] = Publication.objects.count()  # NE! Delegiraj u services.py

# POGRESNO - Promeniti URL name "home"
path("", PortalHomeView.as_view(), name="portal-home"),  # NE! Mora biti name="home"

# POGRESNO - Dodati LoginRequiredMixin
class PortalHomeView(LoginRequiredMixin, TemplateView):  # NE! Javna stranica

# POGRESNO - Vracati JSON za statistike
return JsonResponse(stats)  # NE! Ovo je server-rendered HTML

# POGRESNO - Hardcode-ovati statistike
context["stats"]["total_publications"] = 42  # NE! Uvek iz baze

# POGRESNO - Koristiti camelCase
def getPortalStats():  # NE! Koristi snake_case

# POGRESNO - Kreirati nove modele za portal home page
# Home page je read-only - NEMA modele, samo services.py
```

### Project Structure Notes

- Portal services idu u `doi_portal/doi_portal/portal/services.py` (novi fajl)
- Home page template ide u `doi_portal/doi_portal/templates/portal/home.html` (novi fajl)
- Home page testovi idu u `doi_portal/doi_portal/portal/tests/test_home.py` (novi fajl)
- PortalHomeView se DODAJE u postojeci `portal/views.py` (vec sadrzi publisher/publication views)
- URL route se MENJA u postojecem `config/urls.py` (zamena TemplateView-a)

### Test Pattern

```python
# portal/tests/test_home.py

import pytest
from django.urls import reverse

from doi_portal.portal.services import get_portal_statistics, get_recent_publications
from doi_portal.portal.tests.factories import PublicationFactory, PublisherFactory


@pytest.mark.django_db
class TestPortalStatistics:
    """Tests for get_portal_statistics."""

    def test_returns_correct_counts(self):
        """Stats include total publications, articles, publishers."""
        PublisherFactory.create_batch(2)
        PublicationFactory.create_batch(3)
        # Articles created via ArticleFactory

        stats = get_portal_statistics()

        assert "total_publications" in stats
        assert "total_publishers" in stats
        assert "published_articles_count" in stats
        assert stats["total_publishers"] == 2
        assert stats["total_publications"] == 3

    def test_empty_database_returns_zeros(self):
        """Stats return zeros when database is empty."""
        stats = get_portal_statistics()
        assert stats["total_publications"] == 0
        assert stats["total_publishers"] == 0
        assert stats["published_articles_count"] == 0


@pytest.mark.django_db
class TestRecentPublications:
    """Tests for get_recent_publications."""

    def test_returns_max_6(self):
        """Returns max 6 publications."""
        publisher = PublisherFactory()
        for _ in range(10):
            PublicationFactory(publisher=publisher)

        result = get_recent_publications()
        assert len(result) <= 6

    def test_excludes_soft_deleted(self):
        """Soft-deleted publications excluded."""
        pub = PublicationFactory(title="Active")
        deleted = PublicationFactory(title="Deleted")
        deleted.soft_delete()

        result = get_recent_publications()
        titles = [p.title for p in result]
        assert "Active" in titles
        assert "Deleted" not in titles


@pytest.mark.django_db
class TestPortalHomeView:
    """Tests for PortalHomeView."""

    def test_home_returns_200(self, client):
        """Home page returns 200."""
        response = client.get(reverse("home"))
        assert response.status_code == 200

    def test_home_uses_portal_template(self, client):
        """Home page uses portal/home.html template."""
        response = client.get(reverse("home"))
        template_names = [t.name for t in response.templates]
        assert "portal/home.html" in template_names

    def test_home_context_has_stats(self, client):
        """Context includes stats dict."""
        response = client.get(reverse("home"))
        assert "stats" in response.context

    def test_home_context_has_recent_publications(self, client):
        """Context includes recent_publications."""
        response = client.get(reverse("home"))
        assert "recent_publications" in response.context

    def test_home_no_auth_required(self, client):
        """Public page - no login required (200, not 302)."""
        response = client.get(reverse("home"))
        assert response.status_code == 200

    def test_home_search_form(self, client):
        """Home page has search form with action and input."""
        response = client.get(reverse("home"))
        content = response.content.decode()
        assert 'name="q"' in content
        assert '/search/' in content

    def test_home_empty_publications_message(self, client):
        """Shows empty message when no publications."""
        response = client.get(reverse("home"))
        content = response.content.decode()
        assert "Nema dostupnih publikacija" in content

    def test_home_shows_publications(self, client):
        """Shows recent publications when they exist."""
        pub = PublicationFactory(title="Test Casopis")
        response = client.get(reverse("home"))
        content = response.content.decode()
        assert "Test Casopis" in content
```

### Dependencies (Python/Django)

Nema novih Python zavisnosti! Sve je vec instalirano:
- Django 5.2+ (ORM aggregate, Q objects, TemplateView)
- Bootstrap 5 (CSS framework - vec u portal/base.html)
- Bootstrap Icons (vec ukljuceni u portal/base.html CDN)
- pytest-django + Factory Boy (vec u test setup-u)

### NFR Requirements

- **FR38:** Posetilac moze videti pocetnu stranu portala - direktna implementacija
- **NFR2:** Javne stranice portala < 3 sekunde - optimizovani aggregate upiti, select_related, nema velikih slika
- **NFR14:** Semanticki HTML5 elementi - `<header>`, `<main>`, `<section>`, `<footer>`, `<nav>`, `<h1>`-`<h2>`
- **NFR15:** Alt tekst za sve slike - cover slike imaju alt sa naslovom publikacije
- **NFR16:** Kontrast minimum 4.5:1 za tekst - Bootstrap default boje
- **NFR17:** Keyboard navigacija - sve interaktivne elemente se mogu dohvatiti Tab-om
- **NFR18:** Labels povezani sa input poljima - search input ima aria-label

### References

- [Source: epics.md#Story 4.1: Portal Home Page]
- [Source: epics.md#Epic 4: Public Portal Experience - FR38]
- [Source: prd.md#7. Public Portal - FR38 (Pocetna strana portala)]
- [Source: architecture.md#Project Structure - portal/ app, FR38-FR45 mapping]
- [Source: architecture.md#Frontend Architecture - Bootstrap 5, HTMX patterns]
- [Source: architecture.md#Implementation Patterns - naming conventions, structure patterns]
- [Source: ux-design-specification.md#Design Direction - Clean Academic for portal]
- [Source: ux-design-specification.md#Layout Patterns - Hero sekcija sa pretragom, 3-column card grid]
- [Source: ux-design-specification.md#Responsive Strategy - Mobile-first za portal]
- [Source: ux-design-specification.md#Color System - Primary #1a365d, Secondary #3182ce]
- [Source: ux-design-specification.md#Accessibility - WCAG AA, contrast 4.5:1, focus states]
- [Source: project-context.md#Services Layer (Business Logic)]
- [Source: project-context.md#HTMX Pravila - partials sa _ prefix]
- [Source: project-context.md#Naming Konvencije - snake_case, PascalCase, kebab-case]
- [Source: project-context.md#Lokalizacija - Srpski Karakteri, sr-Latn]
- [Source: project-context.md#Testing (pytest-django) - Factory Boy]
- [Source: portal/base.html - Parent template sa navbar, breadcrumbs, footer]
- [Source: portal/views.py - Existing portal views (PublisherPublic, PublicationPublic)]
- [Source: portal/tests/factories.py - PublisherFactory, PublicationFactory]
- [Source: config/urls.py - Current home route at "/", name="home"]
- [Source: dashboard/services.py - Aggregate query pattern for statistics]
- [Source: 3-8-dashboard-statistics-pending-items.md - Previous story learnings, aggregate pattern]

## Dev Agent Record

### Agent Model Used

Claude Opus 4.5 (claude-opus-4-5-20251101)

### Debug Log References

- Factory sequence conflict with `--reuse-db`: PublisherFactory `doi_prefix` Sequence counter resets but DB retains old data. Fixed by providing explicit unique doi_prefix values in test.

### Completion Notes List

- Implemented `PortalHomeView(TemplateView)` in `portal/views.py` - delegates to service layer for stats and recent publications
- Created `portal/services.py` with `get_portal_statistics()` using aggregate() pattern (1 SQL query for article counts) and `get_recent_publications()` with select_related("publisher") for N+1 prevention
- Replaced Cookiecutter placeholder home view in `config/urls.py` with `PortalHomeView`, preserving URL name `"home"`
- Created `portal/home.html` template extending `portal/base.html` with: hero section (gradient background, search form), statistics cards (3x col-md-4), recent publications grid (3->2->1 responsive), quick links section
- All UI text uses proper Serbian diacritical characters (č, ć, š, đ, ž)
- Added hero section CSS styles and card hover effects to `portal.css`
- Responsive layout: Bootstrap grid handles col-md-4/col-sm-6 breakpoints, mobile padding, min 48px touch targets
- Semantic HTML5: `<section>` elements with `aria-labelledby`, `role="search"` on form, `aria-label` on search input, `visually-hidden` labels
- 18 tests written covering all 17 story test cases plus 1 additional (custom limit parameter)
- Full test suite: 1128 passed, 3 skipped, 0 failures - no regressions

### File List

**New files:**
- `doi_portal/doi_portal/portal/services.py` - Portal service functions (statistics, recent publications)
- `doi_portal/doi_portal/templates/portal/home.html` - Home page template with hero, stats, publications, quick links
- `doi_portal/doi_portal/portal/tests/test_home.py` - 18 tests (service + view + integration)

**Modified files:**
- `doi_portal/doi_portal/portal/views.py` - Added PortalHomeView class
- `doi_portal/config/urls.py` - Replaced TemplateView placeholder with PortalHomeView
- `doi_portal/doi_portal/static/css/portal.css` - Added hero section, stat card, publication card styles
- `_bmad-output/implementation-artifacts/sprint-status.yaml` - Status update
- `_bmad-output/implementation-artifacts/4-1-portal-home-page.md` - Task checkboxes, Dev Agent Record
