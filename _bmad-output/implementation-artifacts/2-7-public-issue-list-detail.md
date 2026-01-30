# Story 2.7: Public Issue List & Detail

Status: done

## Story

As a **visitor (posetilac)**,
I want **to browse issues of a publication and view issue details with article listings**,
So that **I can find articles from a specific volume or issue without needing to log in**.

## Background

Story 2.5 implementirala je javnu listu publikacija sa filterima u `portal/` app-u. Story 2.6 kreirala je `issues` Django app sa Issue modelom i admin CRUD-om, i azurirala `PublicationPublicDetailView` da prikazuje listu objavljenih izdanja (PUBLISHED status) na publication detail stranici. Ova prica dodaje **linkove na issue detail** stranicu i kreira **Issue public detail view** sa listom clanaka (placeholder do Epic 3). Takodje azurira postojecu issue listu na publication detail da bude klikabilna.

**FR Pokrivenost:**
- FR21: Posetilac moze pregledati sva izdanja publikacije
- FR17 (prosirenje): Publication detail sada prikazuje klikabilna izdanja sa navigacijom na detalje

**Napomena:** Clanci (articles) u issue detail-u ce biti placeholder do Story 3.1 (Epic 3). Trenutno article_count property na Issue modelu vraca 0.

## Acceptance Criteria

1. **Given** posetilac pregleda publication detail stranicu
   **When** se stranica ucita
   **Then** objavljena izdanja (PUBLISHED status) su prikazana hronoloski (najnovije prvo)
   **And** svako izdanje prikazuje: volume, number, year, cover thumbnail (ako postoji), article count
   **And** svako izdanje je klikabilno i vodi na issue detail stranicu
   **And** draft/scheduled/archive izdanja NISU vidljiva

2. **Given** posetilac klikne na izdanje
   **When** navigira na `/publications/{pub-slug}/issues/{issue-id}/`
   **Then** issue detail stranica prikazuje sve podatke o izdanju
   **And** prikazuje se lista objavljenih clanaka u izdanju (placeholder: "Clanci ce biti dostupni uskoro.")
   **And** stranica koristi javni portal Bootstrap 5 template (`portal/base.html`)

3. **Given** izdanje ima status DRAFT, SCHEDULED ili ARCHIVE
   **When** posetilac pokusa da pristupi direktno putem URL-a
   **Then** vraca se 404 Not Found (neobjavljeni sadrzaj nije javan)

4. **Given** hijerarhija breadcrumbs
   **When** posetilac pregleda bilo koji nivo (publication, issue)
   **Then** breadcrumbs prikazuju: Pocetna > Publikacije > {Naziv Publikacije} > Vol. X, No. Y (YYYY)

5. **Given** posetilac pregleda issue detail stranicu
   **When** izdanje ima naslovnu sliku
   **Then** naslovna slika se prikazuje na stranici
   **And** alt tekst sadrzi opis izdanja

6. **Given** posetilac pregleda issue detail stranicu
   **When** publikacija je tipa CONFERENCE
   **Then** proceedings polja su prikazana (naslov zbornika, izdavac, mesto) ako su popunjena

7. **Given** publikacija nema objavljena izdanja
   **When** posetilac pregleda publication detail
   **Then** prikazuje se poruka "Nema objavljenih izdanja."

8. **Given** SEO meta tagovi
   **When** posetilac pregleda issue detail stranicu
   **Then** title tag sadrzi: "{Publication Title} - Vol. X, No. Y ({Year}) - DOI Portal"
   **And** meta description sadrzi informacije o izdanju

## Tasks / Subtasks

- [x] Task 1: Dodati nested URL route za public issue detail u portal/urls_publications.py (AC: #2, #4)
  - [x] 1.1 U `portal/urls_publications.py` dodati nested URL pattern:
    `path("<slug:slug>/issues/<int:pk>/", views.IssuePublicDetailView.as_view(), name="issue-detail")`
  - [x] 1.2 URL pattern: `/publications/{pub-slug}/issues/{issue-id}/` - NESTED pod publication slug
  - [x] 1.3 View prima `slug` (publication slug) i `pk` (issue ID) - koristiti oba za queryset filtering

- [x] Task 2: Implementirati IssuePublicDetailView u portal/views.py (AC: #2, #3, #4, #5, #6, #8)
  - [x] 2.1 Kreirati `IssuePublicDetailView(DetailView)` - public, BEZ autentifikacije
  - [x] 2.2 `model = Issue`, `template_name = "portal/publications/issue_detail.html"`, `context_object_name = "issue"`
  - [x] 2.3 `get_queryset()`: filtrirati samo PUBLISHED status i is_deleted=False, koristiti `select_related("publication", "publication__publisher")`
  - [x] 2.4 `get_context_data()`: breadcrumbs (Pocetna > Publikacije > {Publication} > {Issue}), articles placeholder (prazan queryset/lista)
  - [x] 2.5 VALIDACIJA: Proveriti da issue.publication.slug odgovara `pub_slug` iz URL-a (opciono ali preporuceno za URL consistency)

- [x] Task 3: Kreirati template issue_detail.html (AC: #2, #4, #5, #6, #8)
  - [x] 3.1 Extends `portal/base.html`
  - [x] 3.2 Meta title: `"{{ issue.publication.title }} - Vol. {{ issue.volume }}, No. {{ issue.issue_number }} ({{ issue.year }}) - DOI Portal"`
  - [x] 3.3 Meta description za SEO
  - [x] 3.4 Issue metadata: volume, issue_number, year, title (ako postoji), publication_date, status badge
  - [x] 3.5 Cover image (ako postoji) sa alt tekstom
  - [x] 3.6 Conference proceedings polja (samo za CONFERENCE tip publikacije)
  - [x] 3.7 Articles sekcija: placeholder poruka "Članci će biti dostupni uskoro." (do Story 3.1)
  - [x] 3.8 Link nazad na publication detail: `{% url 'portal-publications:publication-detail' issue.publication.slug %}`
  - [x] 3.9 Link na publisher: `{% url 'portal:publisher-detail' issue.publication.publisher.slug %}`
  - [x] 3.10 Breadcrumbs koristeci portal/base.html breadcrumb pattern

- [x] Task 4: Azurirati publication_detail.html - issue lista sa linkovima (AC: #1, #7)
  - [x] 4.1 Azurirati issue list items u `portal/publications/publication_detail.html` da budu klikabilni linkovi na issue detail
  - [x] 4.2 Svaki issue item linkuje na: `{% url 'portal-publications:issue-detail' slug=publication.slug pk=issue.pk %}`
  - [x] 4.3 Dodati article count prikaz za svako izdanje (article_count property, trenutno 0)
  - [x] 4.4 Dodati cover thumbnail (malo) ako postoji
  - [x] 4.5 Sacuvati poruku "Nema objavljenih izdanja." za prazan slucaj (vec postoji)

- [x] Task 5: Napisati testove (AC: #1-#8)
  - [x] 5.1 Test issue detail prikazuje podatke o objavljenom izdanju
  - [x] 5.2 Test draft issue vraca 404
  - [x] 5.3 Test scheduled issue vraca 404
  - [x] 5.4 Test archive issue vraca 404
  - [x] 5.5 Test soft-deleted issue vraca 404
  - [x] 5.6 Test breadcrumbs na issue detail stranici
  - [x] 5.7 Test cover image prikaz na issue detail
  - [x] 5.8 Test proceedings polja prikazana samo za CONFERENCE tip
  - [x] 5.9 Test SEO meta tagovi (title, description)
  - [x] 5.10 Test publication detail prikazuje klikabilne linkove na issues
  - [x] 5.11 Test publication detail ne prikazuje draft issues
  - [x] 5.12 Test publication bez izdanja prikazuje "Nema objavljenih izdanja."
  - [x] 5.13 Test issue detail za nepostojeci publication slug vraca 404
  - [x] 5.14 Test articles placeholder poruka je prikazana
  - [x] 5.15 Test issue detail prikazuje article_count (0 za sada)

## Dev Notes

### CRITICAL: Ovo je PUBLIC view - BEZ autentifikacije

Ova prica implementira JAVNE views u `portal/` app-u. Nema LoginRequiredMixin, nema permission check-ova. Isti pattern kao Story 2.2 (PublisherPublicListView/DetailView) i Story 2.5 (PublicationPublicListView/DetailView).

### Postojeci fajlovi koje treba modifikovati

- `doi_portal/doi_portal/portal/views.py` - Dodati IssuePublicDetailView
- `doi_portal/doi_portal/portal/urls_publications.py` - Dodati issue-detail URL pattern (nested pod publication slug)
- `doi_portal/doi_portal/templates/portal/publications/publication_detail.html` - Azurirati issue listu sa klikabilnim linkovima

**NE modifikovati:**
- `doi_portal/doi_portal/portal/urls.py` - ostaje nepromenjen (samo publisher routes)
- `doi_portal/doi_portal/issues/views.py` - to su ADMIN views, ne public
- `doi_portal/config/urls.py` - nema novih top-level routes, issue detail je nested pod postojeci `portal-publications` namespace

### Novi fajlovi za kreiranje

- `doi_portal/doi_portal/templates/portal/publications/issue_detail.html` - Issue detail template

### URL Routing Design (ODLUKA: Nested pod publications)

Epics specificiraju URL: `/publications/{pub-slug}/issues/{issue-id}/`. Ovo se implementira kao nested URL u postojecem `portal-publications` namespace-u:

**portal/urls_publications.py** - AZURIRATI (dodati novu rutu):
```python
"""Public portal URL configuration for publications."""
from django.urls import path

from doi_portal.portal import views

app_name = "portal-publications"

urlpatterns = [
    # Publication list - /publications/
    path("", views.PublicationPublicListView.as_view(), name="publication-list"),
    # Publication detail - /publications/<slug>/
    path("<slug:slug>/", views.PublicationPublicDetailView.as_view(), name="publication-detail"),
    # Issue detail - /publications/<slug>/issues/<pk>/  (Story 2.7)
    path("<slug:slug>/issues/<int:pk>/", views.IssuePublicDetailView.as_view(), name="issue-detail"),
]
```

**URL namespace reference u template-ovima:** `{% url 'portal-publications:issue-detail' slug=publication.slug pk=issue.pk %}`

### View Pattern (Sledi Story 2.2/2.5 pattern tacno)

```python
# portal/views.py - DODATI

from doi_portal.issues.models import Issue
from doi_portal.issues.models import IssueStatus

class IssuePublicDetailView(DetailView):
    """
    Public view of a single published issue with its articles.

    FR21: Posetilac moze pregledati sva izdanja publikacije.
    Only PUBLISHED issues are visible to the public.
    """
    model = Issue
    template_name = "portal/publications/issue_detail.html"
    context_object_name = "issue"

    def get_queryset(self):
        """
        Return queryset of published, non-deleted issues.

        Only PUBLISHED status issues are visible to the public.
        SoftDeleteManager already excludes is_deleted=True records.
        Additional filter for publication slug to ensure URL consistency.
        """
        return (
            Issue.objects
            .filter(status=IssueStatus.PUBLISHED)
            .select_related("publication", "publication__publisher")
        )

    def get_object(self, queryset=None):
        """
        Get issue by pk AND verify publication slug matches.

        This ensures URL consistency - /publications/wrong-slug/issues/5/ returns 404
        if issue 5 doesn't belong to the publication with 'wrong-slug'.
        """
        if queryset is None:
            queryset = self.get_queryset()

        pk = self.kwargs.get("pk")
        slug = self.kwargs.get("slug")

        queryset = queryset.filter(pk=pk, publication__slug=slug)
        return queryset.get()  # Raises Http404 via DetailView

    def get_context_data(self, **kwargs):
        """Add breadcrumbs and articles placeholder to context."""
        context = super().get_context_data(**kwargs)
        issue = self.object
        publication = issue.publication

        context["breadcrumbs"] = [
            {"label": "Početna", "url": reverse("home")},
            {"label": "Publikacije", "url": reverse("portal-publications:publication-list")},
            {"label": publication.title, "url": reverse("portal-publications:publication-detail", kwargs={"slug": publication.slug})},
            {"label": f"Vol. {issue.volume}, No. {issue.issue_number} ({issue.year})", "url": None},
        ]
        # Placeholder until Story 3.1 - Article model doesn't exist yet
        context["articles"] = []
        return context
```

**VAZNO - get_object() override:** Standardni DetailView koristi samo `pk` za lookup. Mi moramo overrajdovati `get_object()` da proveri i `slug` (publication slug) za URL consistency. Ako issue ne pripada publikaciji sa datim slug-om, vraca se 404. Koristiti `get_object_or_404` pattern ili `queryset.get()` sa try/except koji DetailView vec handluje.

**ALTERNATIVNO** (jednostavniji pristup): Umesto `get_object()` override, mozete filtirati u `get_queryset()`:

```python
def get_queryset(self):
    slug = self.kwargs.get("slug")
    return (
        Issue.objects
        .filter(status=IssueStatus.PUBLISHED, publication__slug=slug)
        .select_related("publication", "publication__publisher")
    )
```

Ovaj pristup je jednostavniji jer DetailView automatski filtrira po `pk` iz URL kwargs.

### Issue Detail Template Design

```html
{% extends "portal/base.html" %}
{% load static i18n %}

{% block title %}{{ issue.publication.title }} - Vol. {{ issue.volume }}, No. {{ issue.issue_number }} ({{ issue.year }}) - DOI Portal{% endblock title %}

{% block meta_description %}Izdanje Vol. {{ issue.volume }}, No. {{ issue.issue_number }} ({{ issue.year }}) publikacije {{ issue.publication.title }} na DOI Portalu.{% endblock meta_description %}

{% block portal_content %}
<div class="row">
    <div class="col-lg-8">
        <article>
            <h1 class="h3 mb-3">
                {{ issue.publication.title }}
                <small class="text-muted d-block mt-1">
                    Vol. {{ issue.volume }}, No. {{ issue.issue_number }} ({{ issue.year }})
                </small>
            </h1>

            {% if issue.title %}
            <p class="lead">{{ issue.title }}</p>
            {% endif %}

            <div class="mb-3">
                <span class="badge {{ issue.status_badge_class }}">{{ issue.get_status_display }}</span>
                {% if issue.publication_date %}
                <span class="text-muted ms-2">
                    <i class="bi bi-calendar3 me-1" aria-hidden="true"></i>
                    {{ issue.publication_date|date:"d.m.Y." }}
                </span>
                {% endif %}
            </div>

            {% if issue.cover_image %}
            <div class="mb-4">
                <img src="{{ issue.cover_image.url }}"
                     class="img-fluid rounded"
                     alt="Naslovna slika: {{ issue.publication.title }} Vol. {{ issue.volume }}, No. {{ issue.issue_number }}"
                     style="max-height: 300px;">
            </div>
            {% endif %}

            <!-- Conference Proceedings (samo za CONFERENCE tip) -->
            {% if issue.publication.publication_type == "CONFERENCE" %}
            {% if issue.proceedings_title or issue.proceedings_publisher_name or issue.proceedings_publisher_place %}
            <div class="card mb-4">
                <div class="card-body">
                    <h2 class="h5 card-title">
                        <i class="bi bi-people me-2" aria-hidden="true"></i>Podaci o zborniku
                    </h2>
                    <dl class="row mb-0">
                        {% if issue.proceedings_title %}
                        <dt class="col-sm-4">Naslov zbornika</dt>
                        <dd class="col-sm-8">{{ issue.proceedings_title }}</dd>
                        {% endif %}
                        {% if issue.proceedings_publisher_name %}
                        <dt class="col-sm-4">Izdavač zbornika</dt>
                        <dd class="col-sm-8">{{ issue.proceedings_publisher_name }}</dd>
                        {% endif %}
                        {% if issue.proceedings_publisher_place %}
                        <dt class="col-sm-4">Mesto izdavanja</dt>
                        <dd class="col-sm-8">{{ issue.proceedings_publisher_place }}</dd>
                        {% endif %}
                    </dl>
                </div>
            </div>
            {% endif %}
            {% endif %}

            <!-- Articles Section (placeholder until Story 3.1) -->
            <div class="card mb-4">
                <div class="card-body">
                    <h2 class="h5 card-title">
                        <i class="bi bi-file-earmark-text me-2" aria-hidden="true"></i>Članci
                    </h2>
                    {% if articles %}
                    <!-- Story 3.1 ce popuniti ovu sekciju sa realnim clancima -->
                    <div class="list-group">
                        {% for article in articles %}
                        <div class="list-group-item">
                            {{ article.title }}
                        </div>
                        {% endfor %}
                    </div>
                    {% else %}
                    <p class="text-muted mb-0">Članci će biti dostupni uskoro.</p>
                    {% endif %}
                </div>
            </div>

            <!-- Back to Publication -->
            <a href="{% url 'portal-publications:publication-detail' issue.publication.slug %}"
               class="btn btn-outline-secondary">
                <i class="bi bi-arrow-left me-1" aria-hidden="true"></i>
                Nazad na publikaciju
            </a>
        </article>
    </div>

    <!-- Sidebar -->
    <div class="col-lg-4">
        <!-- Publication Info Card -->
        <div class="card mb-3">
            <div class="card-body">
                <h2 class="h5 card-title">Publikacija</h2>
                <p class="mb-2">
                    <a href="{% url 'portal-publications:publication-detail' issue.publication.slug %}">
                        {{ issue.publication.title }}
                    </a>
                </p>
                <span class="badge bg-secondary">
                    <i class="{{ issue.publication.type_icon }} me-1" aria-hidden="true"></i>
                    {{ issue.publication.type_display }}
                </span>
            </div>
        </div>

        <!-- Publisher Info Card -->
        <div class="card">
            <div class="card-body">
                <h2 class="h5 card-title">Izdavač</h2>
                <p class="mb-2">
                    <i class="bi bi-building me-2" aria-hidden="true"></i>
                    <a href="{% url 'portal:publisher-detail' issue.publication.publisher.slug %}">
                        {{ issue.publication.publisher.name }}
                    </a>
                </p>
            </div>
        </div>
    </div>
</div>
{% endblock portal_content %}
```

### Publication Detail Template Update (klikabilni issue linkovi)

Azurirati issue listu u `portal/publications/publication_detail.html` da budu linkovi:

```html
<!-- Issues Section - AZURIRATI -->
<div class="card mb-4">
    <div class="card-body">
        <h2 class="h5 card-title">
            <i class="bi bi-collection me-2" aria-hidden="true"></i>Izdanja
        </h2>
        {% if issues %}
        <div class="list-group">
            {% for issue in issues %}
            <a href="{% url 'portal-publications:issue-detail' slug=publication.slug pk=issue.pk %}"
               class="list-group-item list-group-item-action">
                <div class="d-flex justify-content-between align-items-center">
                    <div>
                        <strong>Vol. {{ issue.volume }}, No. {{ issue.issue_number }}</strong>
                        <span class="text-muted ms-2">({{ issue.year }})</span>
                        {% if issue.title %}
                        <br><span class="text-muted">{{ issue.title }}</span>
                        {% endif %}
                    </div>
                    <div class="text-end">
                        {% if issue.publication_date %}
                        <small class="text-muted d-block">{{ issue.publication_date|date:"d.m.Y." }}</small>
                        {% endif %}
                        <small class="text-muted">
                            <i class="bi bi-file-earmark-text me-1" aria-hidden="true"></i>
                            {{ issue.article_count }} članak{{ issue.article_count|pluralize:"a,a" }}
                        </small>
                    </div>
                </div>
            </a>
            {% endfor %}
        </div>
        {% else %}
        <p class="text-muted mb-0">Nema objavljenih izdanja.</p>
        {% endif %}
    </div>
</div>
```

**NAPOMENA za pluralize:** Django `pluralize` filter ne podrzava srpski nastavak perfektno. Jednostavnije resenje: prikazati samo broj `{{ issue.article_count }}` ili koristiti `{% if issue.article_count == 1 %}članak{% else %}članaka{% endif %}`.

### Srpski Karakteri (OBAVEZNO - videti project-context.md)

Svi UI tekstovi MORAJU koristiti ispravne srpske dijakritike: `č`, `ć`, `š`, `đ`, `ž` (i velika: `Č`, `Ć`, `Š`, `Đ`, `Ž`).

| Kontekst | ISPRAVNO (sa dijakritikama) |
|----------|----------------------------|
| Naslov stranice | Sadrzi publication title + Vol/No/Year |
| Breadcrumb pocetna | "Početna" |
| Breadcrumb publikacije | "Publikacije" |
| Clanci heading | "Članci" |
| Clanci placeholder | "Članci će biti dostupni uskoro." |
| Nazad dugme | "Nazad na publikaciju" |
| Izdanja heading | "Izdanja" |
| Publikacija label | "Publikacija" |
| Izdavac label | "Izdavač" |
| Nema izdanja | "Nema objavljenih izdanja." |
| Podaci o zborniku | "Podaci o zborniku" |
| Naslov zbornika | "Naslov zbornika" |
| Izdavac zbornika | "Izdavač zbornika" |
| Mesto izdavanja | "Mesto izdavanja" |

### SEO Meta Tags Pattern (iz Story 2.2/2.5)

```html
{% block title %}{{ issue.publication.title }} - Vol. {{ issue.volume }}, No. {{ issue.issue_number }} ({{ issue.year }}) - DOI Portal{% endblock title %}
{% block meta_description %}Izdanje Vol. {{ issue.volume }}, No. {{ issue.issue_number }} ({{ issue.year }}) publikacije {{ issue.publication.title }} na DOI Portalu.{% endblock meta_description %}
```

### Accessibility (NFR14-NFR18)

- Koristiti `<article>` tag za issue content (semanticki HTML5)
- Alt tekst za cover image: opisni tekst sa publication i volume/number info
- ARIA labels na linkovima gde je potrebno
- Breadcrumbs sa `aria-current="page"` na poslednjoj stavki (vec handluje portal/base.html)
- Keyboard navigacija: svi linkovi i dugmad su tabbable

### Testing Strategy

Koristiti iste factory pattern-e kao u `portal/tests/test_views.py` i `issues/tests/factories.py`.

```python
# portal/tests/test_views.py - DODATI

from doi_portal.issues.tests.factories import IssueFactory
from doi_portal.issues.models import IssueStatus

@pytest.mark.django_db
class TestIssuePublicDetailView:
    def test_published_issue_detail(self, client):
        issue = IssueFactory(status=IssueStatus.PUBLISHED)
        url = reverse(
            "portal-publications:issue-detail",
            kwargs={"slug": issue.publication.slug, "pk": issue.pk},
        )
        response = client.get(url)
        assert response.status_code == 200
        assert f"Vol. {issue.volume}" in response.content.decode()

    def test_draft_issue_returns_404(self, client):
        issue = IssueFactory(status=IssueStatus.DRAFT)
        url = reverse(
            "portal-publications:issue-detail",
            kwargs={"slug": issue.publication.slug, "pk": issue.pk},
        )
        response = client.get(url)
        assert response.status_code == 404

    def test_wrong_publication_slug_returns_404(self, client):
        issue = IssueFactory(status=IssueStatus.PUBLISHED)
        url = reverse(
            "portal-publications:issue-detail",
            kwargs={"slug": "wrong-slug", "pk": issue.pk},
        )
        response = client.get(url)
        assert response.status_code == 404

    def test_breadcrumbs_hierarchy(self, client):
        issue = IssueFactory(status=IssueStatus.PUBLISHED)
        url = reverse(
            "portal-publications:issue-detail",
            kwargs={"slug": issue.publication.slug, "pk": issue.pk},
        )
        response = client.get(url)
        content = response.content.decode()
        assert "Početna" in content
        assert "Publikacije" in content
        assert issue.publication.title in content

    def test_articles_placeholder(self, client):
        issue = IssueFactory(status=IssueStatus.PUBLISHED)
        url = reverse(
            "portal-publications:issue-detail",
            kwargs={"slug": issue.publication.slug, "pk": issue.pk},
        )
        response = client.get(url)
        assert "Članci će biti dostupni uskoro." in response.content.decode()

    def test_proceedings_fields_for_conference(self, client):
        """Proceedings fields shown only for CONFERENCE type publications."""
        from doi_portal.publications.tests.factories import PublicationFactory
        pub = PublicationFactory(publication_type="CONFERENCE")
        issue = IssueFactory(
            publication=pub,
            status=IssueStatus.PUBLISHED,
            proceedings_title="Test Proceedings",
        )
        url = reverse(
            "portal-publications:issue-detail",
            kwargs={"slug": pub.slug, "pk": issue.pk},
        )
        response = client.get(url)
        assert "Test Proceedings" in response.content.decode()
        assert "Podaci o zborniku" in response.content.decode()

    def test_seo_meta_tags(self, client):
        issue = IssueFactory(status=IssueStatus.PUBLISHED, volume="5", issue_number="2", year=2026)
        url = reverse(
            "portal-publications:issue-detail",
            kwargs={"slug": issue.publication.slug, "pk": issue.pk},
        )
        response = client.get(url)
        content = response.content.decode()
        assert f"Vol. 5, No. 2 (2026)" in content
        assert "DOI Portal" in content
```

### Project Structure Notes

- Svi portal views: `doi_portal/doi_portal/portal/views.py`
- Portal publications URLs: `doi_portal/doi_portal/portal/urls_publications.py` (namespace: `portal-publications`)
- Portal templates: `doi_portal/doi_portal/templates/portal/publications/`
- Issue model: `doi_portal/doi_portal/issues/models.py` (vec kreiran u Story 2.6)
- IssueStatus enum: `doi_portal/doi_portal/issues/models.py` - IssueStatus.PUBLISHED
- Testovi: `doi_portal/doi_portal/portal/tests/test_views.py`
- Config URLs: `doi_portal/config/urls.py` - NE menjati (issue detail je nested pod portal-publications)
- IssueFactory: `doi_portal/doi_portal/issues/tests/factories.py` (vec kreiran u Story 2.6)

### NFR Requirements Addressed

- **NFR2:** Javne stranice portala < 3 sekunde - `select_related("publication", "publication__publisher")` za optimizaciju
- **NFR14:** Semanticki HTML5 - `<article>`, `<nav>`, `<main>`
- **NFR15:** Alt tekst za sve slike - cover image sa opisom
- **NFR16:** Kontrast 4.5:1 - Bootstrap 5 default
- **NFR17:** Keyboard navigacija - linkovi i dugmad
- **NFR18:** Labels povezani sa input poljima (nema formi na ovoj stranici)

### Anti-Patterns to Avoid

```python
# POGRESNO - Login required na public view
class IssuePublicDetailView(LoginRequiredMixin, DetailView):

# ISPRAVNO - Bez autentifikacije
class IssuePublicDetailView(DetailView):

# POGRESNO - Prikazivanje draft/scheduled/archive izdanja javnosti
Issue.objects.all()

# ISPRAVNO - Samo PUBLISHED
Issue.objects.filter(status=IssueStatus.PUBLISHED)

# POGRESNO - Ne proveravati publication slug u URL-u
def get_queryset(self):
    return Issue.objects.filter(status=IssueStatus.PUBLISHED)
# Ovo bi dozvolilo pristup sa pogresnim slug-om: /publications/wrong-slug/issues/5/

# ISPRAVNO - Filtrirati i po publication slug-u
def get_queryset(self):
    slug = self.kwargs.get("slug")
    return Issue.objects.filter(
        status=IssueStatus.PUBLISHED,
        publication__slug=slug,
    ).select_related("publication", "publication__publisher")

# POGRESNO - Stavljati view u issues/views.py
# To su ADMIN views

# ISPRAVNO - Public views idu u portal/views.py

# POGRESNO - JSON response za HTMX/public
return JsonResponse({"issue": {...}})

# ISPRAVNO - HTML response
return render(request, "portal/publications/issue_detail.html", context)

# POGRESNO - Kreirati novi URL fajl za issues
# portal/urls_issues.py  NE!

# ISPRAVNO - Dodati nested route u postojeci portal/urls_publications.py
# URL pattern: /publications/<slug>/issues/<pk>/
```

### Git Commit Pattern

```
story-2-7: feat(portal): implementiraj Public Issue List & Detail sa nested URL rutiranjem (Story 2.7)
```

### Dependencies

**Zavisi od:**
- Story 2.1 (Publisher Model) - DONE
- Story 2.2 (Public Publisher Page - portal patterns) - DONE
- Story 2.3 (Publication Model) - DONE
- Story 2.5 (Public Publication List - portal views, urls_publications.py) - DONE
- Story 2.6 (Issue Model & Admin CRUD - Issue model, IssueStatus, IssueFactory) - DONE

**Blokira:**
- Story 3.1 (Article Model) - article listing u issue detail
- Story 4.4 (Article Landing Page) - breadcrumb hierarhija

### Previous Story Learnings (Story 2.5, 2.6)

1. **Portal base template** = `portal/base.html` - extends `base.html`, dodaje header, nav, footer, breadcrumbs
2. **SoftDeleteManager** - automatski iskljucuje is_deleted=True, ne treba explicitni filter za is_deleted
3. **Breadcrumbs format**: `[{"label": "...", "url": "..."}, {"label": "...", "url": None}]` - poslednji je active (bez URL-a)
4. **Publication detail VEC prikazuje issues** - Story 2.6 dodala je `context["issues"]` sa filter `status="PUBLISHED"` i issue list u template-u. Ovoj prici treba samo dodati LINKOVE na issue detail.
5. **URL namespace**: `portal-publications` je vec registrovan, dodati nested issue-detail rutu tu
6. **Template location**: Portal templates su u `templates/portal/publications/` - NE `templates/issues/` (to su admin templates)
7. **select_related pattern**: Za Issue koristiti `select_related("publication", "publication__publisher")` jer se oba koriste u breadcrumbs i sidebar-u
8. **Serbian diacritics** - OBAVEZNO: `č`, `ć`, `š`, `đ`, `ž` - videti tabelu iznad
9. **HTMX** je vec ukljucen u `base.html` (dodato u Story 2.5) - ali ova prica ne koristi HTMX (static detail page)
10. **IssueFactory** vec postoji u `issues/tests/factories.py` (kreiran u Story 2.6) - koristiti ga u testovima
11. **IssueStatus** enum: DRAFT, SCHEDULED, PUBLISHED, ARCHIVE - samo PUBLISHED je javan
12. **Issue.article_count** property vraca 0 (placeholder do Story 3.1)
13. **Issue nema slug** - koristi pk/id za lookup. URL format: `/publications/{pub-slug}/issues/{pk}/`
14. **Portal views su u `portal/views.py`** - NE u `issues/views.py` (to su admin views)
15. **PublicationPublicDetailView** vec ima `context["issues"]` queryset - samo template treba azurirati za linkove

### References

- [Source: epics.md#Story 2.7: Public Issue List & Detail]
- [Source: prd.md#FR21 - Posetilac moze pregledati sva izdanja publikacije]
- [Source: architecture.md#Frontend Architecture - HTMX Use Cases]
- [Source: architecture.md#Structure Patterns - Template Organization]
- [Source: project-context.md#Lokalizacija - Srpski Karakteri]
- [Source: project-context.md#Template Struktura]
- [Source: project-context.md#Naming Konvencije - URLs kebab-case]
- [Source: 2-5-public-publication-list-with-filters.md - Portal public view patterns, urls_publications.py]
- [Source: 2-6-issue-model-admin-crud.md - Issue model, IssueStatus, IssueFactory, proceedings fields]
- [Source: portal/views.py - PublicationPublicDetailView already has issues queryset]
- [Source: portal/urls_publications.py - existing namespace portal-publications]
- [Source: portal/publications/publication_detail.html - existing issue list template]
- [Source: issues/models.py - Issue model, IssueStatus enum, article_count property]

## Dev Agent Record

### Agent Model Used

Claude Opus 4.5 (claude-opus-4-5-20251101)

### Debug Log References

No debug issues encountered. All tests passed on first run.

### Completion Notes List

1. **Task 1 - URL Route**: Added nested URL pattern `<slug:slug>/issues/<int:pk>/` in `portal/urls_publications.py` under the existing `portal-publications` namespace. URL resolves to `/publications/{pub-slug}/issues/{pk}/`.

2. **Task 2 - IssuePublicDetailView**: Created `IssuePublicDetailView(DetailView)` in `portal/views.py`. Public view (no auth). `get_queryset()` filters by `IssueStatus.PUBLISHED` AND `publication__slug` for URL consistency. Uses `select_related("publication", "publication__publisher")` for query optimization (NFR2). Context includes 4-level breadcrumbs and empty articles list placeholder.

3. **Task 3 - issue_detail.html Template**: Created `portal/publications/issue_detail.html` extending `portal/base.html`. Includes SEO meta tags (title + description), cover image with alt text (NFR15), conference proceedings section (conditional on CONFERENCE type), articles placeholder ("Clanci ce biti dostupni uskoro."), sidebar with publication and publisher cards, back button, and all Serbian diacritics.

4. **Task 4 - publication_detail.html Update**: Converted issue list items from `<div>` to `<a>` tags with `list-group-item-action` class for clickable navigation. Added cover thumbnail display, article count, and kept "Nema objavljenih izdanja." empty state.

5. **Task 5 - Tests**: Wrote 22 tests in `TestIssuePublicDetailView` class + 1 in `TestIssueURLPatterns`. All 15 story subtasks covered plus 7 additional tests (template, auth, context, publisher link, back link, proceedings not shown for journal). Full test suite: 532 passed, 3 skipped, 0 failed.

### File List

**Modified:**
- `doi_portal/doi_portal/portal/views.py` - Added IssuePublicDetailView, imported Issue/IssueStatus
- `doi_portal/doi_portal/portal/urls_publications.py` - Added issue-detail URL pattern
- `doi_portal/doi_portal/templates/portal/publications/publication_detail.html` - Converted issue list to clickable links with article count and cover thumbnail
- `doi_portal/doi_portal/portal/tests/test_views.py` - Added 23 Story 2.7 tests (TestIssuePublicDetailView + TestIssueURLPatterns)
- `_bmad-output/implementation-artifacts/sprint-status.yaml` - Status: ready-for-dev -> in-progress -> review
- `_bmad-output/implementation-artifacts/2-7-public-issue-list-detail.md` - All checkboxes marked [x], status: review

**Created:**
- `doi_portal/doi_portal/templates/portal/publications/issue_detail.html` - Issue detail template (Bootstrap 5, portal/base.html)
