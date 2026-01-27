# Story 2.3: Publication Model with Type-Specific Fields

Status: done

## Story

As an **Administrator**,
I want **to create publications with type-specific metadata fields**,
So that **each publication type (journal, conference, book) has appropriate Crossref-required fields**.

## Acceptance Criteria

1. **Given** the Publication model is created
   **When** reviewing the model structure
   **Then** it includes common fields: title, slug, publisher (FK), description, cover_image, language, subject_area, access_type, created_at, updated_at
   **And** type field is enum: JOURNAL, CONFERENCE, BOOK, OTHER

2. **Given** publication type is JOURNAL
   **When** viewing/editing the publication
   **Then** additional fields are available: issn_print, issn_online, abbreviation, frequency

3. **Given** publication type is CONFERENCE
   **When** viewing/editing the publication
   **Then** additional fields are available: conference_name, conference_acronym, conference_location, conference_date, series_issn

4. **Given** publication type is BOOK
   **When** viewing/editing the publication
   **Then** additional fields are available: isbn_print, isbn_online, edition, series_title

5. **Given** Administrator creates a new publication
   **When** selecting publication type
   **Then** form dynamically shows/hides type-specific fields
   **And** HTMX is used for dynamic form updates

6. **Given** valid publication data is submitted
   **When** the form is processed
   **Then** publication is created with publisher association
   **And** type-specific fields are validated (e.g., ISSN format)
   **And** django-guardian assigns object permissions if needed

## Tasks / Subtasks

- [x] Task 1: Create Publication Model (AC: #1, #2, #3, #4)
  - [x] 1.1 Create `publications` Django app with proper structure
  - [x] 1.2 Define PublicationType enum: JOURNAL, CONFERENCE, BOOK, OTHER
  - [x] 1.3 Create Publication model with common fields
  - [x] 1.4 Add Journal-specific fields (nullable for non-journals)
  - [x] 1.5 Add Conference-specific fields (nullable)
  - [x] 1.6 Add Book-specific fields (nullable)
  - [x] 1.7 Implement SoftDeleteMixin (reuse from Publisher)
  - [x] 1.8 Add ISSN/ISBN validators
  - [x] 1.9 Run migrations

- [x] Task 2: Create Publication Admin Forms (AC: #5, #6)
  - [x] 2.1 Create PublicationForm with dynamic field handling
  - [x] 2.2 Create HTMX endpoint for type-specific fields partial
  - [x] 2.3 Implement type-specific field validation
  - [x] 2.4 Add ISSN format validation (####-####)
  - [x] 2.5 Add ISBN format validation

- [x] Task 3: Create Publication Admin Views (AC: #5, #6)
  - [x] 3.1 Create PublicationListView with filtering by type/publisher
  - [x] 3.2 Create PublicationCreateView with dynamic HTMX form
  - [x] 3.3 Create PublicationUpdateView
  - [x] 3.4 Create PublicationDeleteView (soft delete)
  - [x] 3.5 Create htmx_type_fields view for dynamic form partial

- [x] Task 4: Create Publication Admin Templates (AC: #5)
  - [x] 4.1 Create `publications/publication_list.html` with type icons
  - [x] 4.2 Create `publications/publication_form.html` with HTMX sections
  - [x] 4.3 Create `publications/partials/_type_fields_journal.html`
  - [x] 4.4 Create `publications/partials/_type_fields_conference.html`
  - [x] 4.5 Create `publications/partials/_type_fields_book.html`
  - [x] 4.6 Add type icons (casopis, zbornik, monografija)

- [x] Task 5: Configure URL Routes
  - [x] 5.1 Create `publications/urls.py` with admin routes
  - [x] 5.2 Add HTMX endpoint route for type fields
  - [x] 5.3 Register in config/urls.py

- [x] Task 6: Update Publisher Model for Reverse Relation
  - [x] 6.1 Ensure publication_count property works with new Publication model

- [x] Task 7: Write Unit Tests (AC: #1-#6)
  - [x] 7.1 Test Publication model creation with all types
  - [x] 7.2 Test type-specific field validation
  - [x] 7.3 Test ISSN format validation
  - [x] 7.4 Test ISBN format validation
  - [x] 7.5 Test soft delete functionality
  - [x] 7.6 Test HTMX type fields endpoint
  - [x] 7.7 Test form dynamic behavior
  - [x] 7.8 Test publisher association

## Dev Notes

### CRITICAL: Reuse Existing Infrastructure

**Publisher Model (Story 2-1):**
Located at `doi_portal/doi_portal/publishers/models.py`. Reuse:
- `SoftDeleteManager` - Copy or import for Publication
- `validate_doi_prefix` pattern for ISSN/ISBN validators
- Soft delete fields pattern: `is_deleted`, `deleted_at`, `deleted_by`

**Public Portal (Story 2-2):**
Portal app exists at `doi_portal/doi_portal/portal/`. Publication public views will be added in Story 2.5.

### Publication Model Design

```python
# publications/models.py

from django.db import models
from django.utils.translation import gettext_lazy as _

from doi_portal.publishers.models import Publisher, SoftDeleteManager


class PublicationType(models.TextChoices):
    """Publication type choices for Crossref XML structure selection."""
    JOURNAL = 'JOURNAL', _('Časopis')
    CONFERENCE = 'CONFERENCE', _('Zbornik')
    BOOK = 'BOOK', _('Monografija')
    OTHER = 'OTHER', _('Ostalo')


class AccessType(models.TextChoices):
    """Access type choices."""
    OPEN = 'OPEN', _('Otvoreni pristup')
    RESTRICTED = 'RESTRICTED', _('Ograničeni pristup')


class Publication(models.Model):
    """
    Publication model with type-specific fields for Crossref compliance.

    Supports: Journal, Conference proceedings, Book/Monograph, Other.
    Each type has specific fields required by Crossref schema 5.4.0.
    """

    # === COMMON FIELDS (All types) ===
    title = models.CharField(
        _("Naslov"),
        max_length=500,
        help_text=_("Puni naslov publikacije"),
    )
    slug = models.SlugField(
        _("Slug"),
        max_length=500,
        unique=True,
        blank=True,
    )
    publisher = models.ForeignKey(
        Publisher,
        on_delete=models.PROTECT,
        related_name='publications',
        verbose_name=_("Izdavač"),
    )
    publication_type = models.CharField(
        _("Tip publikacije"),
        max_length=20,
        choices=PublicationType.choices,
        default=PublicationType.JOURNAL,
    )
    description = models.TextField(
        _("Opis"),
        blank=True,
    )
    cover_image = models.ImageField(
        _("Naslovna slika"),
        upload_to="publications/covers/",
        blank=True,
        null=True,
    )
    language = models.CharField(
        _("Jezik"),
        max_length=10,
        default='sr',
        help_text=_("ISO 639-1 kod jezika (npr. 'sr', 'en')"),
    )
    subject_area = models.CharField(
        _("Naučna oblast"),
        max_length=255,
        blank=True,
    )
    access_type = models.CharField(
        _("Tip pristupa"),
        max_length=20,
        choices=AccessType.choices,
        default=AccessType.OPEN,
    )

    # === JOURNAL-SPECIFIC FIELDS ===
    issn_print = models.CharField(
        _("ISSN (štampano)"),
        max_length=9,
        blank=True,
        validators=[validate_issn],
        help_text=_("Format: ####-####"),
    )
    issn_online = models.CharField(
        _("ISSN (online)"),
        max_length=9,
        blank=True,
        validators=[validate_issn],
        help_text=_("Format: ####-####"),
    )
    abbreviation = models.CharField(
        _("Skraćenica"),
        max_length=50,
        blank=True,
        help_text=_("ISO skraćenica časopisa"),
    )
    frequency = models.CharField(
        _("Učestalost izlaženja"),
        max_length=50,
        blank=True,
        help_text=_("npr. 'Kvartalno', 'Godišnje'"),
    )

    # === CONFERENCE-SPECIFIC FIELDS ===
    conference_name = models.CharField(
        _("Naziv konferencije"),
        max_length=500,
        blank=True,
    )
    conference_acronym = models.CharField(
        _("Akronim konferencije"),
        max_length=50,
        blank=True,
    )
    conference_location = models.CharField(
        _("Lokacija konferencije"),
        max_length=255,
        blank=True,
    )
    conference_date = models.DateField(
        _("Datum konferencije"),
        blank=True,
        null=True,
    )
    series_issn = models.CharField(
        _("ISSN serije"),
        max_length=9,
        blank=True,
        validators=[validate_issn],
    )

    # === BOOK-SPECIFIC FIELDS ===
    isbn_print = models.CharField(
        _("ISBN (štampano)"),
        max_length=17,
        blank=True,
        validators=[validate_isbn],
        help_text=_("Format: 978-X-XXXX-XXXX-X"),
    )
    isbn_online = models.CharField(
        _("ISBN (online)"),
        max_length=17,
        blank=True,
        validators=[validate_isbn],
    )
    edition = models.CharField(
        _("Izdanje"),
        max_length=50,
        blank=True,
        help_text=_("npr. '1. izdanje', '2. dopunjeno izdanje'"),
    )
    series_title = models.CharField(
        _("Naslov serije"),
        max_length=500,
        blank=True,
    )

    # === TIMESTAMPS ===
    created_at = models.DateTimeField(_("Kreirano"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Ažurirano"), auto_now=True)

    # === SOFT DELETE ===
    is_deleted = models.BooleanField(_("Obrisano"), default=False)
    deleted_at = models.DateTimeField(_("Vreme brisanja"), null=True, blank=True)
    deleted_by = models.ForeignKey(
        "users.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="deleted_publications",
    )

    # === MANAGERS ===
    objects = SoftDeleteManager()
    all_objects = models.Manager()

    class Meta:
        verbose_name = _("Publikacija")
        verbose_name_plural = _("Publikacije")
        ordering = ["title"]

    def __str__(self):
        return self.title

    @property
    def issue_count(self):
        """Return count of issues (Story 2.6)."""
        if hasattr(self, 'issues'):
            return self.issues.count()
        return 0
```

### ISSN/ISBN Validators

```python
# publications/validators.py

import re
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _


def validate_issn(value: str) -> None:
    """
    Validate ISSN format: ####-####.

    ISSN has check digit validation but we'll keep it simple for now.
    """
    if not value:
        return  # Blank is allowed

    pattern = r'^\d{4}-\d{3}[\dX]$'
    if not re.match(pattern, value):
        raise ValidationError(
            _("ISSN mora biti u formatu '####-####' (npr. '1234-5678')"),
            code="invalid_issn",
        )


def validate_isbn(value: str) -> None:
    """
    Validate ISBN-13 format: 978-X-XXXX-XXXX-X or without hyphens.

    ISBN-13 starts with 978 or 979.
    """
    if not value:
        return  # Blank is allowed

    # Remove hyphens for validation
    clean_isbn = value.replace('-', '')

    # Must be 13 digits
    if not re.match(r'^\d{13}$', clean_isbn):
        raise ValidationError(
            _("ISBN mora imati 13 cifara (npr. '978-86-7549-123-4')"),
            code="invalid_isbn",
        )

    # Must start with 978 or 979
    if not clean_isbn.startswith(('978', '979')):
        raise ValidationError(
            _("ISBN-13 mora početi sa '978' ili '979'"),
            code="invalid_isbn_prefix",
        )
```

### HTMX Dynamic Form Pattern

```python
# publications/views.py

from django.views.generic import ListView, CreateView, UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.http import HttpResponse
from django.shortcuts import render

from .models import Publication, PublicationType
from .forms import PublicationForm


class PublicationCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    """Create new publication with dynamic type-specific fields."""
    model = Publication
    form_class = PublicationForm
    template_name = 'publications/publication_form.html'
    permission_required = 'publications.add_publication'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Nova publikacija'
        context['breadcrumbs'] = [
            {'label': 'Početna', 'url': '/admin/'},
            {'label': 'Publikacije', 'url': '/admin/publications/'},
            {'label': 'Nova publikacija', 'url': None},
        ]
        return context


def htmx_type_fields(request):
    """
    HTMX endpoint for dynamic type-specific fields.

    Called when publication_type select changes.
    Returns appropriate partial template.
    """
    publication_type = request.GET.get('type', PublicationType.JOURNAL)

    template_map = {
        PublicationType.JOURNAL: 'publications/partials/_type_fields_journal.html',
        PublicationType.CONFERENCE: 'publications/partials/_type_fields_conference.html',
        PublicationType.BOOK: 'publications/partials/_type_fields_book.html',
        PublicationType.OTHER: 'publications/partials/_type_fields_other.html',
    }

    template = template_map.get(publication_type, 'publications/partials/_type_fields_other.html')

    # Pass form instance if editing existing publication
    context = {
        'publication_type': publication_type,
    }

    return render(request, template, context)
```

### Template with HTMX

```html
<!-- publications/publication_form.html -->
{% extends "admin_base.html" %}
{% load crispy_forms_tags %}

{% block content %}
<div class="card">
    <div class="card-header">
        <h5 class="mb-0">{{ page_title }}</h5>
    </div>
    <div class="card-body">
        <form method="post" enctype="multipart/form-data">
            {% csrf_token %}

            <!-- Common fields -->
            {{ form.title|as_crispy_field }}
            {{ form.publisher|as_crispy_field }}

            <!-- Type selector with HTMX -->
            <div class="mb-3">
                <label for="id_publication_type" class="form-label">Tip publikacije *</label>
                <select name="publication_type"
                        id="id_publication_type"
                        class="form-select"
                        hx-get="{% url 'publications:htmx-type-fields' %}"
                        hx-target="#type-specific-fields"
                        hx-trigger="change"
                        hx-include="[name='publication_type']">
                    {% for value, label in form.fields.publication_type.choices %}
                    <option value="{{ value }}" {% if form.publication_type.value == value %}selected{% endif %}>
                        {{ label }}
                    </option>
                    {% endfor %}
                </select>
            </div>

            <!-- Dynamic type-specific fields -->
            <div id="type-specific-fields">
                {% include "publications/partials/_type_fields_journal.html" %}
            </div>

            <!-- More common fields -->
            {{ form.description|as_crispy_field }}
            {{ form.cover_image|as_crispy_field }}
            {{ form.language|as_crispy_field }}
            {{ form.subject_area|as_crispy_field }}
            {{ form.access_type|as_crispy_field }}

            <div class="d-flex justify-content-between mt-4">
                <a href="{% url 'publications:publication-list' %}" class="btn btn-secondary">
                    Otkaži
                </a>
                <button type="submit" class="btn btn-primary">
                    Sačuvaj publikaciju
                </button>
            </div>
        </form>
    </div>
</div>
{% endblock %}
```

### Type-Specific Partials

```html
<!-- publications/partials/_type_fields_journal.html -->
<div class="type-fields-section border rounded p-3 mb-3 bg-light">
    <h6 class="text-muted mb-3">
        <i class="bi bi-journal-text me-2"></i>Polja za časopis
    </h6>
    <div class="row">
        <div class="col-md-6">
            <div class="mb-3">
                <label for="id_issn_print" class="form-label">ISSN (štampano)</label>
                <input type="text" name="issn_print" id="id_issn_print"
                       class="form-control" placeholder="####-####"
                       pattern="\d{4}-\d{3}[\dX]">
                <div class="form-text">Format: 1234-5678</div>
            </div>
        </div>
        <div class="col-md-6">
            <div class="mb-3">
                <label for="id_issn_online" class="form-label">ISSN (online)</label>
                <input type="text" name="issn_online" id="id_issn_online"
                       class="form-control" placeholder="####-####"
                       pattern="\d{4}-\d{3}[\dX]">
            </div>
        </div>
    </div>
    <div class="row">
        <div class="col-md-6">
            <div class="mb-3">
                <label for="id_abbreviation" class="form-label">Skraćenica</label>
                <input type="text" name="abbreviation" id="id_abbreviation"
                       class="form-control" placeholder="npr. J. Sci. Res.">
            </div>
        </div>
        <div class="col-md-6">
            <div class="mb-3">
                <label for="id_frequency" class="form-label">Učestalost izlaženja</label>
                <input type="text" name="frequency" id="id_frequency"
                       class="form-control" placeholder="npr. Kvartalno">
            </div>
        </div>
    </div>
</div>
```

### App Structure

```
doi_portal/
└── doi_portal/
    └── publications/          # NEW APP - FR13-FR17
        ├── __init__.py
        ├── admin.py           # Django admin registration (optional)
        ├── apps.py
        ├── forms.py           # PublicationForm with dynamic validation
        ├── models.py          # Publication model
        ├── urls.py            # Admin + HTMX routes
        ├── validators.py      # ISSN, ISBN validators
        ├── views.py           # CRUD views + HTMX endpoint
        └── tests/
            ├── __init__.py
            ├── factories.py   # PublicationFactory
            └── test_models.py
            └── test_views.py
            └── test_validators.py
```

### URL Configuration

```python
# publications/urls.py

from django.urls import path
from . import views

app_name = 'publications'

urlpatterns = [
    # Admin routes (require authentication)
    path('', views.PublicationListView.as_view(), name='publication-list'),
    path('create/', views.PublicationCreateView.as_view(), name='publication-create'),
    path('<slug:slug>/', views.PublicationDetailView.as_view(), name='publication-detail'),
    path('<slug:slug>/edit/', views.PublicationUpdateView.as_view(), name='publication-update'),
    path('<slug:slug>/delete/', views.PublicationDeleteView.as_view(), name='publication-delete'),

    # HTMX endpoints
    path('htmx/type-fields/', views.htmx_type_fields, name='htmx-type-fields'),
]
```

```python
# config/urls.py - Add to existing

urlpatterns = [
    # ... existing patterns ...

    # Publications admin (requires auth)
    path('admin/publications/', include('doi_portal.publications.urls', namespace='publications')),
]
```

### Testing Patterns

```python
# publications/tests/test_models.py

import pytest
from django.core.exceptions import ValidationError

from doi_portal.publications.models import Publication, PublicationType
from doi_portal.publications.validators import validate_issn, validate_isbn
from tests.factories import PublisherFactory


@pytest.mark.django_db
class TestPublicationModel:
    """Test Publication model."""

    def test_create_journal_publication(self, db):
        """Test creating a journal publication."""
        publisher = PublisherFactory()
        publication = Publication.objects.create(
            title='Naučni časopis',
            publisher=publisher,
            publication_type=PublicationType.JOURNAL,
            issn_print='1234-5678',
        )
        assert publication.pk is not None
        assert publication.publication_type == PublicationType.JOURNAL
        assert publication.issn_print == '1234-5678'

    def test_create_conference_publication(self, db):
        """Test creating a conference publication."""
        publisher = PublisherFactory()
        publication = Publication.objects.create(
            title='Zbornik radova',
            publisher=publisher,
            publication_type=PublicationType.CONFERENCE,
            conference_name='Naučna konferencija 2026',
            conference_location='Beograd, Srbija',
        )
        assert publication.publication_type == PublicationType.CONFERENCE
        assert publication.conference_name == 'Naučna konferencija 2026'

    def test_create_book_publication(self, db):
        """Test creating a book/monograph publication."""
        publisher = PublisherFactory()
        publication = Publication.objects.create(
            title='Monografija',
            publisher=publisher,
            publication_type=PublicationType.BOOK,
            isbn_print='978-86-7549-123-4',
            edition='1. izdanje',
        )
        assert publication.publication_type == PublicationType.BOOK
        assert publication.isbn_print == '978-86-7549-123-4'

    def test_soft_delete(self, db):
        """Test soft delete excludes from default queryset."""
        publisher = PublisherFactory()
        publication = Publication.objects.create(
            title='Test',
            publisher=publisher,
        )
        publication.is_deleted = True
        publication.save()

        assert Publication.objects.count() == 0
        assert Publication.all_objects.count() == 1


@pytest.mark.django_db
class TestValidators:
    """Test ISSN and ISBN validators."""

    def test_valid_issn(self):
        """Test valid ISSN passes."""
        validate_issn('1234-5678')
        validate_issn('0000-000X')  # X is valid check digit

    def test_invalid_issn_format(self):
        """Test invalid ISSN raises ValidationError."""
        with pytest.raises(ValidationError):
            validate_issn('12345678')  # Missing hyphen

        with pytest.raises(ValidationError):
            validate_issn('1234-567')  # Too short

    def test_valid_isbn(self):
        """Test valid ISBN-13 passes."""
        validate_isbn('978-86-7549-123-4')
        validate_isbn('9788675491234')  # Without hyphens

    def test_invalid_isbn_prefix(self):
        """Test ISBN not starting with 978/979 fails."""
        with pytest.raises(ValidationError):
            validate_isbn('123-45-6789-012-3')
```

### Previous Story Learnings (Story 2-2)

From Story 2-2 implementation:
1. **SoftDeleteManager** - Already implemented in publishers, reuse pattern
2. **Slug auto-generation** - Copy `save()` method pattern from Publisher
3. **Serbian diacritics** - CRITICAL: Use `č`, `ć`, `š`, `đ`, `ž` properly
4. **Template structure** - Use `admin_base.html` for admin views
5. **Breadcrumbs** - Pass `breadcrumbs` list to context
6. **HTMX pattern** - Check `HX-Request` header, return HTML fragment

### Git Commit Pattern

Recent commits follow pattern: `story-X-Y: feat(module): description`

Expected commit:
```
story-2-3: feat(publications): implementiraj Publication Model sa type-specific fields (Story 2.3)
```

### Files to Create

- `doi_portal/doi_portal/publications/__init__.py`
- `doi_portal/doi_portal/publications/admin.py`
- `doi_portal/doi_portal/publications/apps.py`
- `doi_portal/doi_portal/publications/forms.py`
- `doi_portal/doi_portal/publications/models.py`
- `doi_portal/doi_portal/publications/urls.py`
- `doi_portal/doi_portal/publications/validators.py`
- `doi_portal/doi_portal/publications/views.py`
- `doi_portal/doi_portal/publications/tests/__init__.py`
- `doi_portal/doi_portal/publications/tests/factories.py`
- `doi_portal/doi_portal/publications/tests/test_models.py`
- `doi_portal/doi_portal/publications/tests/test_validators.py`
- `doi_portal/doi_portal/publications/tests/test_views.py`
- `doi_portal/doi_portal/templates/publications/publication_list.html`
- `doi_portal/doi_portal/templates/publications/publication_form.html`
- `doi_portal/doi_portal/templates/publications/publication_detail.html`
- `doi_portal/doi_portal/templates/publications/partials/_type_fields_journal.html`
- `doi_portal/doi_portal/templates/publications/partials/_type_fields_conference.html`
- `doi_portal/doi_portal/templates/publications/partials/_type_fields_book.html`
- `doi_portal/doi_portal/templates/publications/partials/_type_fields_other.html`
- `doi_portal/doi_portal/templates/publications/partials/_publication_row.html`

### Files to Modify

- `doi_portal/config/urls.py` - Add publications URLs
- `doi_portal/config/settings/base.py` - Add publications to INSTALLED_APPS

### Anti-Patterns to Avoid

```python
# WRONG - Creating separate models for each type
class Journal(models.Model): ...
class Conference(models.Model): ...

# CORRECT - Single model with type field
class Publication(models.Model):
    publication_type = models.CharField(choices=PublicationType.choices)

# WRONG - JSON response for HTMX
return JsonResponse({'html': rendered})

# CORRECT - HTML fragment for HTMX
return render(request, 'partials/_type_fields.html', context)

# WRONG - Hardcoded URLs
href="/admin/publications/"

# CORRECT - URL reverse
href="{% url 'publications:publication-list' %}"

# WRONG - ASCII Serbian
label = "Casopis"

# CORRECT - Proper Serbian diacritics
label = "Časopis"

# WRONG - Forgetting PROTECT for publisher FK
publisher = models.ForeignKey(Publisher, on_delete=models.CASCADE)

# CORRECT - Use PROTECT to prevent orphan publications
publisher = models.ForeignKey(Publisher, on_delete=models.PROTECT)
```

### NFR Requirements Addressed

- **NFR3:** Admin panel stranice < 5 sekundi load time
- **NFR12:** Audit log - will be registered with django-auditlog
- **NFR14:** Semanticki HTML5 elementi
- **NFR15:** Alt tekst za slike (cover_image)
- **NFR16:** Kontrast minimum 4.5:1

### Crossref XML Implications

This model structure directly maps to Crossref XML schema 5.4.0:

| Publication Type | Crossref Container | Key Fields |
|-----------------|-------------------|------------|
| JOURNAL | `<journal>` | ISSN required |
| CONFERENCE | `<conference>` | conference_name, event_metadata |
| BOOK | `<book>` | ISBN or NOISBN required |

Story 5.1 (Crossref Service Infrastructure) will use these fields for XML generation.

### References

- [Source: architecture.md#Data Architecture - Publication model]
- [Source: architecture.md#Django Apps Struktura - publications/]
- [Source: architecture.md#HTMX Patterns - Dynamic form updates]
- [Source: epics.md#Story 2.3: Publication Model with Type-Specific Fields]
- [Source: prd.md#FR13-FR17 Publication Management]
- [Source: project-context.md#Naming Konvencije - model naming]
- [Source: project-context.md#HTMX Pravila - partials prefix]
- [Source: ux-design-specification.md#Design System - Bootstrap 5]
- [Source: 2-1-publisher-model-admin-crud.md - SoftDeleteManager pattern]
- [Source: 2-2-public-publisher-page.md - Portal template patterns]

## Dev Agent Record

### Agent Model Used

Claude Opus 4.5 (claude-opus-4-5-20251101)

### Debug Log References

N/A

### Completion Notes List

1. Created `publications` Django app with complete Publication model supporting JOURNAL, CONFERENCE, BOOK, OTHER types
2. Implemented SoftDeleteManager pattern (reused from Publisher model)
3. Created ISSN validator (####-#### format) and ISBN-13 validator (978/979 prefix)
4. Implemented HTMX dynamic form with type-specific field partials
5. All views (List, Create, Update, Detail, Delete) with proper permission checks
6. 82 tests written covering models, validators, views, and HTMX endpoint
7. All 353 project tests pass (82 new + existing)
8. Serbian diacritics used in all UI text

### File List

**Created:**
- `doi_portal/doi_portal/publications/__init__.py`
- `doi_portal/doi_portal/publications/admin.py`
- `doi_portal/doi_portal/publications/apps.py`
- `doi_portal/doi_portal/publications/forms.py`
- `doi_portal/doi_portal/publications/models.py`
- `doi_portal/doi_portal/publications/urls.py`
- `doi_portal/doi_portal/publications/validators.py`
- `doi_portal/doi_portal/publications/views.py`
- `doi_portal/doi_portal/publications/tests/__init__.py`
- `doi_portal/doi_portal/publications/tests/factories.py`
- `doi_portal/doi_portal/publications/tests/test_models.py`
- `doi_portal/doi_portal/publications/tests/test_validators.py`
- `doi_portal/doi_portal/publications/tests/test_views.py`
- `doi_portal/doi_portal/templates/publications/publication_list.html`
- `doi_portal/doi_portal/templates/publications/publication_form.html`
- `doi_portal/doi_portal/templates/publications/publication_detail.html`
- `doi_portal/doi_portal/templates/publications/publication_confirm_delete.html`
- `doi_portal/doi_portal/templates/publications/partials/_type_fields_journal.html`
- `doi_portal/doi_portal/templates/publications/partials/_type_fields_conference.html`
- `doi_portal/doi_portal/templates/publications/partials/_type_fields_book.html`
- `doi_portal/doi_portal/templates/publications/partials/_type_fields_other.html`
- `doi_portal/doi_portal/templates/publications/partials/_publication_row.html`
- `doi_portal/doi_portal/publications/migrations/0001_initial.py`

**Modified:**
- `doi_portal/config/settings/base.py` - Added publications to INSTALLED_APPS
- `doi_portal/config/urls.py` - Added publications URL routes

## Senior Developer Review (AI)

**Review Date:** 2026-01-26
**Reviewer:** Dev Agent (Claude Opus 4.5)
**Review Type:** Adversarial Code Review

### Issues Found & Fixed

| # | Severity | Issue | Resolution |
|---|----------|-------|------------|
| 1 | MEDIUM | HTMX endpoint `htmx_type_fields` lacked `@login_required` decorator | Added `@login_required` decorator to views.py:227 |
| 2 | MEDIUM | HTMX attribute `hx-vals='{"type": "event.target.value"}'` was invalid JS string literal | Changed to `hx-include="this"` for proper form field inclusion |
| 3 | MEDIUM | HTMX endpoint only accepted `type` param but form sends `publication_type` | Updated endpoint to accept both `publication_type` and `type` params |
| 4 | LOW | Missing test for filter by publisher in list view | Added `test_list_filter_by_publisher` test |
| 5 | LOW | Missing test for HTMX endpoint authentication requirement | Added `test_htmx_requires_login` test |
| 6 | LOW | Missing test for `publication_type` parameter handling | Added `test_htmx_accepts_publication_type_param` test |

### Files Modified During Review

- `doi_portal/doi_portal/publications/views.py` - Added `@login_required` decorator, updated param handling
- `doi_portal/doi_portal/templates/publications/publication_form.html` - Fixed HTMX attribute, simplified JS
- `doi_portal/doi_portal/publications/tests/test_views.py` - Added 3 new tests

### Test Results After Fixes

- **Publications tests:** 85 passed (82 original + 3 new)
- **Full test suite:** 356 passed, 3 skipped, 0 failures

### Definition of Done (DoD) Checklist

- [x] All Acceptance Criteria implemented and verified
- [x] All Tasks/Subtasks marked complete ([x])
- [x] Unit tests written and passing (85 tests)
- [x] Full test suite passing (356 tests)
- [x] Serbian diacritics used correctly in all UI text
- [x] HTMX patterns comply with project-context.md
- [x] Code follows naming conventions (snake_case, PascalCase)
- [x] Views have proper authentication/authorization
- [x] Audit logging registered (auditlog.register in apps.py)
- [x] Soft delete pattern implemented correctly
- [x] No security vulnerabilities identified

### Verdict: APPROVED

Story 2.3 passes code review. All issues identified were fixed and verified with passing tests.
