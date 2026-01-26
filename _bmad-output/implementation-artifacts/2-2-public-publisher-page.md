# Story 2.2: Public Publisher Page

Status: done

## Story

As a **visitor**,
I want **to view a publisher's page with their publications**,
So that **I can browse content from a specific publisher**.

## Acceptance Criteria

1. **Given** a published publisher exists
   **When** visitor navigates to /publishers/{slug}/
   **Then** publisher details are displayed (name, logo, description, contact info)
   **And** list of publications by this publisher is shown
   **And** page uses public portal Bootstrap 5 template

2. **Given** visitor is on publishers listing page
   **When** viewing /publishers/
   **Then** all active publishers are listed with logos and names
   **And** each publisher links to their detail page

3. **Given** publisher has no published publications
   **When** viewing publisher page
   **Then** appropriate message is shown ("Nema publikacija")

4. **Given** a deleted or inactive publisher
   **When** visitor attempts to access the page
   **Then** 404 Not Found is returned

## Tasks / Subtasks

- [x] Task 1: Create Public Base Template (AC: #1, #2)
  - [x] 1.1 Create `templates/portal/base.html` extending base.html with public portal layout
  - [x] 1.2 Add Bootstrap 5 public theme styling (Clean Academic)
  - [x] 1.3 Add header with navigation (sticky)
  - [x] 1.4 Add footer with portal info
  - [x] 1.5 Include breadcrumbs component

- [x] Task 2: Create Publisher Public Views (AC: #1, #2, #3, #4)
  - [x] 2.1 Create `portal/views.py` with PublisherPublicListView
  - [x] 2.2 Create PublisherPublicDetailView with slug lookup
  - [x] 2.3 Filter out is_deleted=True publishers in queryset
  - [x] 2.4 Add publication list (empty for now - placeholder for Story 2.3)
  - [x] 2.5 Return 404 for deleted/inactive publishers

- [x] Task 3: Create Publisher Public Templates (AC: #1, #2, #3)
  - [x] 3.1 Create `templates/portal/publishers/publisher_list.html` - card grid layout
  - [x] 3.2 Create `templates/portal/publishers/publisher_detail.html` - detail page
  - [x] 3.3 Add publisher card component with logo, name, description preview
  - [x] 3.4 Add "Nema publikacija" empty state message
  - [x] 3.5 Add breadcrumbs: Početna > Izdavači > {Publisher Name}

- [x] Task 4: Configure Public URL Routes (AC: #1, #2)
  - [x] 4.1 Create `portal/urls.py` with public routes
  - [x] 4.2 Add path `publishers/` for listing
  - [x] 4.3 Add path `publishers/<slug:slug>/` for detail
  - [x] 4.4 Register portal URLs in config/urls.py (public routes, no auth required)

- [x] Task 5: Add Static Assets for Public Portal (AC: #1, #2)
  - [x] 5.1 Create `static/css/portal.css` with public theme variables
  - [x] 5.2 Style publisher cards (3-column grid on desktop, responsive)
  - [x] 5.3 Style publisher detail page (Clean Academic layout)

- [x] Task 6: Write Unit Tests (AC: #1, #2, #3, #4)
  - [x] 6.1 Test publisher list view returns 200
  - [x] 6.2 Test publisher detail view returns 200 for active publisher
  - [x] 6.3 Test publisher detail view returns 404 for deleted publisher
  - [x] 6.4 Test publisher detail view returns 404 for non-existent slug
  - [x] 6.5 Test deleted publishers excluded from list
  - [x] 6.6 Test template rendering with logo and without logo
  - [x] 6.7 Test empty publications message displayed

## Dev Notes

### CRITICAL: Build on Existing Publisher Infrastructure

**Existing Publisher Model (Story 2-1):**
The Publisher model is fully implemented at `doi_portal/doi_portal/publishers/models.py` with all fields needed:
- name, slug, logo, description, contact_email, contact_phone, website, doi_prefix
- is_deleted, deleted_at, deleted_by (soft delete)
- SoftDeleteManager that excludes deleted records by default

**Key Model Methods Available:**
```python
Publisher.objects.all()  # Excludes soft-deleted (use this for public)
Publisher.all_objects.all()  # Includes soft-deleted
publisher.publication_count  # Returns 0 for now (until Story 2.3)
```

### Public Portal Architecture

This is the FIRST public-facing view. Establishes patterns for all Epic 4 stories.

**Key Differences from Admin Panel:**
- NO authentication required
- Uses `portal/base.html` template (NOT `admin_base.html`)
- Mobile-first responsive design
- "Clean Academic" visual style (per UX spec)
- SEO-friendly with semantic HTML

### Portal App Structure

Create new `portal` app or add public views to publishers:

**Option A (Recommended - Use Portal App):**
```
doi_portal/
└── doi_portal/
    └── portal/              # FR38-FR45: Public Portal
        ├── __init__.py
        ├── apps.py
        ├── views.py         # Public views
        ├── urls.py          # Public URL routes
        └── tests/
            └── test_views.py
```

**Option B (Simpler - Extend Publishers):**
Add public views to existing publishers app with separate URL namespace.

### URL Configuration

```python
# config/urls.py - Public routes (NO auth)
urlpatterns = [
    # ... existing patterns ...

    # Public portal routes (no authentication)
    path('publishers/', include('doi_portal.portal.urls', namespace='portal-publishers')),
]

# portal/urls.py
from django.urls import path
from . import views

app_name = 'portal'

urlpatterns = [
    path('', views.PublisherPublicListView.as_view(), name='publisher-list'),
    path('<slug:slug>/', views.PublisherPublicDetailView.as_view(), name='publisher-detail'),
]
```

### Public View Implementation

```python
# portal/views.py

from django.views.generic import ListView, DetailView
from django.shortcuts import get_object_or_404

from doi_portal.publishers.models import Publisher


class PublisherPublicListView(ListView):
    """
    Public listing of all active publishers.

    AC: #2 - Lists all active publishers with logos and names.
    """
    model = Publisher
    template_name = 'portal/publishers/publisher_list.html'
    context_object_name = 'publishers'

    def get_queryset(self):
        # SoftDeleteManager already excludes is_deleted=True
        return Publisher.objects.all()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['breadcrumbs'] = [
            {'label': 'Početna', 'url': '/'},
            {'label': 'Izdavači', 'url': None},
        ]
        return context


class PublisherPublicDetailView(DetailView):
    """
    Public view of a single publisher with their publications.

    AC: #1, #3, #4 - Shows publisher details and publications.
    """
    model = Publisher
    template_name = 'portal/publishers/publisher_detail.html'
    context_object_name = 'publisher'
    slug_url_kwarg = 'slug'

    def get_queryset(self):
        # SoftDeleteManager excludes deleted - raises 404 for deleted publishers
        return Publisher.objects.all()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['breadcrumbs'] = [
            {'label': 'Početna', 'url': '/'},
            {'label': 'Izdavači', 'url': '/publishers/'},
            {'label': self.object.name, 'url': None},
        ]
        # Publications placeholder - empty for now, Story 2.3 will populate
        context['publications'] = []
        return context
```

### Public Portal Base Template

```html
<!-- templates/portal/base.html -->
{% extends "base.html" %}
{% load static %}

{% block extra_css %}
<link rel="stylesheet" href="{% static 'css/portal.css' %}">
{% endblock %}

{% block content %}
<!-- Sticky Header -->
<header class="portal-header sticky-top bg-white shadow-sm">
    <nav class="navbar navbar-expand-lg">
        <div class="container">
            <a class="navbar-brand" href="/">DOI Portal</a>
            <button class="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#navbarNav">
                <span class="navbar-toggler-icon"></span>
            </button>
            <div class="collapse navbar-collapse" id="navbarNav">
                <ul class="navbar-nav ms-auto">
                    <li class="nav-item">
                        <a class="nav-link" href="/publishers/">Izdavači</a>
                    </li>
                    <li class="nav-item">
                        <a class="nav-link" href="/publications/">Publikacije</a>
                    </li>
                    <li class="nav-item">
                        <a class="nav-link" href="/about/">O portalu</a>
                    </li>
                    <li class="nav-item">
                        <a class="nav-link" href="/contact/">Kontakt</a>
                    </li>
                </ul>
            </div>
        </div>
    </nav>
</header>

<!-- Breadcrumbs -->
{% if breadcrumbs %}
<nav aria-label="breadcrumb" class="bg-light py-2">
    <div class="container">
        <ol class="breadcrumb mb-0">
            {% for crumb in breadcrumbs %}
                {% if crumb.url %}
                <li class="breadcrumb-item"><a href="{{ crumb.url }}">{{ crumb.label }}</a></li>
                {% else %}
                <li class="breadcrumb-item active" aria-current="page">{{ crumb.label }}</li>
                {% endif %}
            {% endfor %}
        </ol>
    </div>
</nav>
{% endif %}

<!-- Main Content -->
<main class="portal-content py-4">
    <div class="container">
        {% block portal_content %}{% endblock %}
    </div>
</main>

<!-- Footer -->
<footer class="portal-footer bg-dark text-light py-4 mt-auto">
    <div class="container">
        <div class="row">
            <div class="col-md-6">
                <h5>DOI Portal</h5>
                <p class="text-muted">Portal za registraciju DOI identifikatora naučnih publikacija.</p>
            </div>
            <div class="col-md-6 text-md-end">
                <p class="mb-0">&copy; 2026 DOI Portal</p>
            </div>
        </div>
    </div>
</footer>
{% endblock %}
```

### Publisher List Template

```html
<!-- templates/portal/publishers/publisher_list.html -->
{% extends "portal/base.html" %}

{% block title %}Izdavaci - DOI Portal{% endblock %}

{% block portal_content %}
<h1 class="h2 mb-4">Izdavači</h1>

{% if publishers %}
<div class="row row-cols-1 row-cols-md-2 row-cols-lg-3 g-4">
    {% for publisher in publishers %}
    <div class="col">
        <div class="card h-100 publisher-card">
            {% if publisher.logo %}
            <img src="{{ publisher.logo.url }}" class="card-img-top p-3" alt="{{ publisher.name }} logo" style="height: 120px; object-fit: contain;">
            {% else %}
            <div class="card-img-top bg-light d-flex align-items-center justify-content-center" style="height: 120px;">
                <i class="bi bi-building text-muted" style="font-size: 3rem;"></i>
            </div>
            {% endif %}
            <div class="card-body">
                <h5 class="card-title">
                    <a href="{% url 'portal:publisher-detail' publisher.slug %}" class="text-decoration-none">
                        {{ publisher.name }}
                    </a>
                </h5>
                {% if publisher.description %}
                <p class="card-text text-muted small">{{ publisher.description|truncatewords:30 }}</p>
                {% endif %}
            </div>
            <div class="card-footer bg-transparent border-top-0">
                <small class="text-muted">
                    <code>{{ publisher.doi_prefix }}</code>
                </small>
            </div>
        </div>
    </div>
    {% endfor %}
</div>
{% else %}
<div class="text-center py-5">
    <i class="bi bi-building display-1 text-muted"></i>
    <p class="lead text-muted mt-3">Nema registrovanih izdavača.</p>
</div>
{% endif %}
{% endblock %}
```

### Publisher Detail Template

```html
<!-- templates/portal/publishers/publisher_detail.html -->
{% extends "portal/base.html" %}

{% block title %}{{ publisher.name }} - DOI Portal{% endblock %}

{% block portal_content %}
<div class="row">
    <!-- Publisher Info -->
    <div class="col-lg-4 mb-4">
        <div class="card">
            {% if publisher.logo %}
            <img src="{{ publisher.logo.url }}" class="card-img-top p-4" alt="{{ publisher.name }} logo">
            {% endif %}
            <div class="card-body">
                <h1 class="h4 card-title">{{ publisher.name }}</h1>

                {% if publisher.description %}
                <p class="card-text">{{ publisher.description }}</p>
                {% endif %}

                <hr>

                <ul class="list-unstyled small">
                    {% if publisher.contact_email %}
                    <li class="mb-2">
                        <i class="bi bi-envelope me-2"></i>
                        <a href="mailto:{{ publisher.contact_email }}">{{ publisher.contact_email }}</a>
                    </li>
                    {% endif %}

                    {% if publisher.contact_phone %}
                    <li class="mb-2">
                        <i class="bi bi-telephone me-2"></i>
                        {{ publisher.contact_phone }}
                    </li>
                    {% endif %}

                    {% if publisher.website %}
                    <li class="mb-2">
                        <i class="bi bi-globe me-2"></i>
                        <a href="{{ publisher.website }}" target="_blank" rel="noopener">{{ publisher.website }}</a>
                    </li>
                    {% endif %}

                    <li class="mb-2">
                        <i class="bi bi-link-45deg me-2"></i>
                        <code>{{ publisher.doi_prefix }}</code>
                    </li>
                </ul>
            </div>
        </div>
    </div>

    <!-- Publications -->
    <div class="col-lg-8">
        <h2 class="h4 mb-4">Publikacije</h2>

        {% if publications %}
        <div class="row row-cols-1 row-cols-md-2 g-3">
            {% for publication in publications %}
            <!-- Publication cards will be added in Story 2.3 -->
            <div class="col">
                <div class="card">
                    <div class="card-body">
                        {{ publication.title }}
                    </div>
                </div>
            </div>
            {% endfor %}
        </div>
        {% else %}
        <div class="alert alert-secondary text-center py-4">
            <i class="bi bi-journal-text display-6 text-muted d-block mb-3"></i>
            <p class="mb-0 text-muted">Nema publikacija za ovog izdavača.</p>
        </div>
        {% endif %}
    </div>
</div>
{% endblock %}
```

### CSS Styling (portal.css)

```css
/* static/css/portal.css */

/* ===========================
   DOI Portal - Public Theme
   Style: Clean Academic
   =========================== */

:root {
    --portal-primary: #1a365d;
    --portal-secondary: #3182ce;
    --portal-text: #1a202c;
    --portal-text-muted: #4a5568;
    --portal-bg: #ffffff;
    --portal-bg-secondary: #f7fafc;
    --portal-border: #e2e8f0;
}

/* Header */
.portal-header {
    border-bottom: 1px solid var(--portal-border);
}

.portal-header .navbar-brand {
    font-weight: 700;
    color: var(--portal-primary);
}

.portal-header .nav-link {
    color: var(--portal-text);
    font-weight: 500;
}

.portal-header .nav-link:hover {
    color: var(--portal-secondary);
}

/* Cards */
.publisher-card {
    transition: box-shadow 0.2s ease;
}

.publisher-card:hover {
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.publisher-card .card-title a {
    color: var(--portal-primary);
}

.publisher-card .card-title a:hover {
    color: var(--portal-secondary);
}

/* Footer */
.portal-footer {
    background-color: var(--portal-primary) !important;
}

/* Responsive adjustments */
@media (max-width: 767px) {
    .portal-content {
        padding-top: 1rem;
        padding-bottom: 1rem;
    }
}
```

### Testing Patterns

```python
# portal/tests/test_publisher_views.py

import pytest
from django.urls import reverse

from doi_portal.publishers.models import Publisher
from tests.factories import PublisherFactory


@pytest.mark.django_db
class TestPublisherPublicListView:
    """Test public publisher list view."""

    def test_list_returns_200(self, client):
        """Test publisher list returns 200 status."""
        url = reverse('portal:publisher-list')
        response = client.get(url)
        assert response.status_code == 200

    def test_list_excludes_deleted_publishers(self, client, db):
        """Test deleted publishers not shown in list."""
        active = PublisherFactory(name='Active Publisher', doi_prefix='10.1111')
        deleted = PublisherFactory(name='Deleted Publisher', doi_prefix='10.2222', is_deleted=True)

        url = reverse('portal:publisher-list')
        response = client.get(url)

        assert 'Active Publisher' in response.content.decode()
        assert 'Deleted Publisher' not in response.content.decode()

    def test_list_shows_publisher_logos(self, client, db):
        """Test publisher logos displayed in list."""
        publisher = PublisherFactory(name='With Logo', doi_prefix='10.3333')

        url = reverse('portal:publisher-list')
        response = client.get(url)

        assert 'With Logo' in response.content.decode()


@pytest.mark.django_db
class TestPublisherPublicDetailView:
    """Test public publisher detail view."""

    def test_detail_returns_200(self, client, db):
        """Test publisher detail returns 200 for active publisher."""
        publisher = PublisherFactory(name='Test Publisher', doi_prefix='10.4444')

        url = reverse('portal:publisher-detail', kwargs={'slug': publisher.slug})
        response = client.get(url)

        assert response.status_code == 200
        assert 'Test Publisher' in response.content.decode()

    def test_detail_returns_404_for_deleted(self, client, db):
        """Test 404 returned for deleted publisher."""
        publisher = PublisherFactory(
            name='Deleted Publisher',
            doi_prefix='10.5555',
            is_deleted=True
        )

        url = reverse('portal:publisher-detail', kwargs={'slug': publisher.slug})
        response = client.get(url)

        assert response.status_code == 404

    def test_detail_returns_404_for_nonexistent(self, client, db):
        """Test 404 returned for non-existent slug."""
        url = reverse('portal:publisher-detail', kwargs={'slug': 'does-not-exist'})
        response = client.get(url)

        assert response.status_code == 404

    def test_detail_shows_empty_publications_message(self, client, db):
        """Test empty publications message shown."""
        publisher = PublisherFactory(name='No Pubs', doi_prefix='10.6666')

        url = reverse('portal:publisher-detail', kwargs={'slug': publisher.slug})
        response = client.get(url)

        assert 'Nema publikacija' in response.content.decode()

    def test_detail_shows_contact_info(self, client, db):
        """Test contact information displayed."""
        publisher = PublisherFactory(
            name='Contact Info',
            doi_prefix='10.7777',
            contact_email='test@example.com',
            website='https://example.com',
        )

        url = reverse('portal:publisher-detail', kwargs={'slug': publisher.slug})
        response = client.get(url)

        content = response.content.decode()
        assert 'test@example.com' in content
        assert 'https://example.com' in content

    def test_no_authentication_required(self, client, db):
        """Test public access - no login required."""
        publisher = PublisherFactory(name='Public', doi_prefix='10.8888')

        # No login, just direct access
        url = reverse('portal:publisher-detail', kwargs={'slug': publisher.slug})
        response = client.get(url)

        assert response.status_code == 200  # NOT 302 redirect to login
```

### Project Structure Notes

**Actual file paths (nested doi_portal structure):**
- `doi_portal/doi_portal/portal/` - New portal app
- `doi_portal/doi_portal/templates/portal/` - Portal templates
- `doi_portal/static/css/portal.css` - Portal CSS

**Or extend publishers app:**
- `doi_portal/doi_portal/publishers/views_public.py` - Public views
- `doi_portal/doi_portal/templates/portal/publishers/` - Public templates

### Previous Story Learnings (Story 2-1)

From Story 2-1 implementation:
1. **Slug lookup** - Use `slug_url_kwarg = 'slug'` for URL slug parameter
2. **Soft delete filtering** - SoftDeleteManager already handles filtering
3. **Breadcrumbs** - Pass `breadcrumbs` list to context
4. **Serbian diacritics** - CRITICAL: Use `č`, `ć`, `š`, `đ`, `ž` properly
5. **Template structure** - Extend appropriate base template
6. **Test fixtures** - Use PublisherFactory from existing tests

### Git Commit Pattern

Recent commits follow pattern: `story-X-Y: feat(module): description`

Expected commit:
```
story-2-2: feat(portal): implementiraj Public Publisher Page (Story 2.2)
```

### Files to Create

- `doi_portal/doi_portal/portal/__init__.py`
- `doi_portal/doi_portal/portal/apps.py`
- `doi_portal/doi_portal/portal/views.py`
- `doi_portal/doi_portal/portal/urls.py`
- `doi_portal/doi_portal/portal/tests/__init__.py`
- `doi_portal/doi_portal/portal/tests/test_views.py`
- `doi_portal/doi_portal/templates/portal/base.html`
- `doi_portal/doi_portal/templates/portal/publishers/publisher_list.html`
- `doi_portal/doi_portal/templates/portal/publishers/publisher_detail.html`
- `doi_portal/static/css/portal.css`

### Files to Modify

- `doi_portal/config/urls.py` - Add portal URLs
- `doi_portal/config/settings/base.py` - Add portal to INSTALLED_APPS

### Anti-Patterns to Avoid

```python
# WRONG - Requiring authentication for public pages
class PublisherPublicView(LoginRequiredMixin, DetailView):  # NO!

# WRONG - Using admin base template for public
{% extends "admin_base.html" %}  # NO! Use portal/base.html

# WRONG - Not filtering soft-deleted
Publisher.all_objects.all()  # Use Publisher.objects.all()

# WRONG - Hardcoding URLs
href="/publishers/{{ publisher.slug }}/"  # Use {% url %} tag

# WRONG - ASCII Serbian
"Nema publikacija za ovog izdavaca"  # Use proper diacritics: "izdavača"

# CORRECT
class PublisherPublicView(DetailView):  # No LoginRequiredMixin
{% extends "portal/base.html" %}
Publisher.objects.all()  # Uses SoftDeleteManager
href="{% url 'portal:publisher-detail' publisher.slug %}"
"Nema publikacija za ovog izdavača"  # Proper Serbian
```

### NFR Requirements Addressed

- **NFR1:** Landing stranica < 3 sekunde (simple template, no heavy queries)
- **NFR2:** Javne stranice < 3 sekunde load time
- **NFR14:** Semanticki HTML5 elementi
- **NFR15:** Alt tekst za sve slike (logos)
- **NFR16:** Kontrast minimum 4.5:1 (Bootstrap 5 defaults)

### References

- [Source: architecture.md#Project Structure - portal/ app location]
- [Source: architecture.md#Template Organization - portal/base.html]
- [Source: architecture.md#URL Patterns - kebab-case]
- [Source: ux-design-specification.md#Design Direction - Clean Academic]
- [Source: ux-design-specification.md#Layout Patterns - Javni Portal]
- [Source: project-context.md#Lokalizacija - Srpski karakteri]
- [Source: epics.md#Story 2.2: Public Publisher Page]
- [Source: 2-1-publisher-model-admin-crud.md#Dev Notes - Publisher model details]

## Dev Agent Record

### Agent Model Used

Claude Opus 4.5 (claude-opus-4-5-20251101)

### Debug Log References

- All tests passing: 270 passed, 3 skipped
- Portal-specific tests: 27 passed

### Completion Notes List

1. **Task 1 (Public Base Template)**: Created `templates/portal/base.html` extending base.html with Bootstrap 5 styling, sticky header navigation, breadcrumbs component, and footer with portal info. Uses "Clean Academic" visual style per UX spec.

2. **Task 2 (Publisher Public Views)**: Created `portal/views.py` with:
   - `PublisherPublicListView` - lists all active publishers, excludes soft-deleted
   - `PublisherPublicDetailView` - shows publisher details with slug lookup, returns 404 for deleted/non-existent publishers

3. **Task 3 (Publisher Public Templates)**: Created:
   - `publisher_list.html` - 3-column responsive card grid with logo/placeholder, name, description preview, DOI prefix
   - `publisher_detail.html` - full publisher info with contact details and "Nema publikacija" empty state

4. **Task 4 (URL Routes)**: Created `portal/urls.py` and registered in `config/urls.py`:
   - `/publishers/` - publisher list (portal:publisher-list)
   - `/publishers/<slug>/` - publisher detail (portal:publisher-detail)

5. **Task 5 (Static Assets)**: Created `static/css/portal.css` with CSS variables for Clean Academic theme, publisher card hover effects, responsive breakpoints, and accessibility features.

6. **Task 6 (Unit Tests)**: Created 27 comprehensive tests covering all AC requirements:
   - List view returns 200, excludes deleted publishers, shows links to detail
   - Detail view returns 200 for active, 404 for deleted/non-existent
   - Template rendering with/without logo
   - Empty publications message displayed
   - No authentication required (public access)

### File List

**Created Files:**
- `doi_portal/doi_portal/portal/__init__.py`
- `doi_portal/doi_portal/portal/apps.py`
- `doi_portal/doi_portal/portal/views.py`
- `doi_portal/doi_portal/portal/urls.py`
- `doi_portal/doi_portal/portal/tests/__init__.py`
- `doi_portal/doi_portal/portal/tests/factories.py`
- `doi_portal/doi_portal/portal/tests/test_views.py`
- `doi_portal/doi_portal/templates/portal/base.html`
- `doi_portal/doi_portal/templates/portal/publishers/publisher_list.html`
- `doi_portal/doi_portal/templates/portal/publishers/publisher_detail.html`
- `doi_portal/doi_portal/static/css/portal.css`

**Modified Files:**
- `doi_portal/config/urls.py` - added portal URLs
- `doi_portal/config/settings/base.py` - added portal to INSTALLED_APPS

## Code Review Record

### Reviewer Model
Claude Opus 4.5 (claude-opus-4-5-20251101) - Fresh context adversarial review

### Review Date
2026-01-26

### Issues Found: 10

| # | Severity | Category | Description | Fixed |
|---|----------|----------|-------------|-------|
| 1 | MEDIUM | Security | Missing CSRF exemption documentation in views.py | YES |
| 2 | MEDIUM | Accessibility | Missing skip-to-content link (NFR15) | YES |
| 3 | HIGH | Lokalizacija | Serbian diacritics missing in test strings ("Izdavac" -> "Izdavač") | YES |
| 4 | N/A | Security | External links - already has rel="noopener noreferrer" | N/A |
| 5 | MEDIUM | Security | CDN Bootstrap Icons missing SRI hash | YES |
| 6 | LOW | Code Quality | Factory duplication - acceptable for test isolation | WONTFIX |
| 7 | N/A | Accessibility | lang attribute - already inherited from base.html | N/A |
| 8 | LOW | Testing | Missing test for alphabetical ordering | YES |
| 9 | LOW | Code Quality | Hardcoded URLs in views.py breadcrumbs | YES |
| 10 | MEDIUM | SEO | Missing meta description blocks | YES |

### Fixes Applied

1. **views.py**: Added docstring explaining CSRF handling, replaced hardcoded URLs with `reverse()` for breadcrumbs
2. **templates/portal/base.html**: Added skip-to-content link with `id="main-content"` target, added SRI hash for Bootstrap Icons CDN
3. **test_views.py**: Fixed all Serbian diacritics ("Izdavac" -> "Izdavač"), added new test `test_list_publishers_ordered_by_name`
4. **templates/base.html**: Added `{% block meta_description %}` for SEO override capability
5. **publisher_list.html** and **publisher_detail.html**: Added meta_description blocks with proper Serbian SEO text

### Test Results After Review
- Portal tests: 28 passed
- Full suite: 271 passed, 3 skipped
- No regressions

### Definition of Done Checklist

- [x] All acceptance criteria met (AC #1, #2, #3, #4)
- [x] All unit tests passing (28 portal tests)
- [x] No regressions in existing tests (271 total passed)
- [x] Code follows project-context.md standards
- [x] Serbian diacritics properly used
- [x] No hardcoded URLs (using {% url %} and reverse())
- [x] Accessibility features implemented (skip link, aria labels)
- [x] SEO meta descriptions added
- [x] Security: SRI hash for external CDN
- [x] Code reviewed and issues fixed
