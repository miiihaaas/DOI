---
stepsCompleted:
  - step-01-init
  - step-02-context
  - step-03-starter
  - step-04-decisions
  - step-05-patterns
  - step-06-structure
  - step-07-validation
  - step-08-complete
status: 'complete'
completedAt: '2026-01-25'
inputDocuments:
  - prd.md
  - ux-design-specification.md
workflowType: 'architecture'
project_name: 'DOI'
user_name: 'Mihas'
date: '2026-01-25'
---

# Architecture Decision Document

_This document builds collaboratively through step-by-step discovery. Sections are appended as we work through each architectural decision together._

## Project Context Analysis

### Requirements Overview

**Functional Requirements:**
50 funkcionalnih zahteva u 8 kategorija pokrivaju kompletan DOI portal - od korisnickog upravljanja, kroz CRUD za hijerarhiju sadrzaja (Izdavac → Publikacija → Izdanje → Clanak), do Crossref integracije i javnog portala. Kljucna funkcionalnost je generisanje validnog Crossref XML-a za DOI registraciju.

**Non-Functional Requirements:**
- Performance: FCP < 3s, pretraga < 2s, XML generisanje < 30s za 50 clanaka
- Security: HTTPS TLS 1.2+, password hashing (bcrypt/argon2), virus scan za upload, kompletni audit log
- Accessibility: WCAG AA standard, semanticki HTML5, kontrast 4.5:1
- Reliability: 99% uptime, dnevni backup sa 90+ dana retencije

**Scale & Complexity:**
- Primary domain: Full-stack MPA web aplikacija
- Complexity level: Medium-High
- Estimated architectural components: 12-15

### Technical Constraints & Dependencies

| Constraint | Vrednost |
|------------|----------|
| Framework | Django 5.2+ (Python 3.13) |
| Database | PostgreSQL 16+ |
| Cache/Session | Redis |
| Task Queue | Celery |
| File Storage | S3-compatible cloud |
| Containerization | Docker |
| PDF Max Size | 100 MB |

### Cross-Cutting Concerns Identified

1. **Audit Logging** - Svi CRUD eventi, login/logout, GDPR zahtevi
2. **Authorization** - RBAC (4 uloge), row-level permissions per izdavac
3. **File Management** - Secure upload, virus scan, S3 storage
4. **Caching Strategy** - Sessions (Redis), query cache, static files CDN
5. **Background Processing** - XML generisanje, email slanje, potencijalno virus scan
6. **Validation Layer** - Crossref XSD, ORCID format, business rules

## Starter Template Evaluation

### Primary Technology Domain

Full-stack MPA web aplikacija sa Django 5.2+ (Python 3.13)

### Starter Options Considered

| Opcija | Verzija | Docker | Celery | Redis | Baza | Odrzavanje |
|--------|---------|--------|--------|-------|------|------------|
| Cookiecutter Django | 2026.4.3 | ✅ | ✅ | ✅ | PostgreSQL | Aktivno |
| CC Django MySQL Fork | 2022.39.7 | ✅ | ✅ | ✅ | MySQL | Zastarelo |
| django-admin startproject | - | ❌ | ❌ | ❌ | Bilo koja | Django core |

### Selected Starter: Cookiecutter Django

**Rationale for Selection:**
- Production-ready konfiguracija za Docker, Celery, Redis
- Aktivno odrzavano (2026.4.3)
- Security best practices ukljucene
- CI/CD pipeline (GitHub Actions)
- User authentication (django-allauth)
- Cloud storage support (S3)

**Database Decision:**
PostgreSQL umesto MySQL - bolja Django podrska, aktivno odrzavano u cookiecutter-django, naprednije funkcionalnosti (JSON polja, full-text search, array polja).

**Initialization Command:**

```bash
pip install cookiecutter
cookiecutter gh:cookiecutter/cookiecutter-django
```

### Architectural Decisions Provided by Starter

**Language & Runtime:**
- Python 3.13
- Django 5.2+
- Type hints (mypy configured)

**Database:**
- PostgreSQL 16+
- django-environ za konfiguraciju

**Styling Solution:**
- Bootstrap 5 (opciono)
- Whitenoise za static files

**Build Tooling:**
- Docker + docker-compose
- Traefik za production reverse proxy
- GitHub Actions CI/CD

**Testing Framework:**
- pytest-django
- Coverage reporting

**Code Organization:**
- Apps u project_slug/ direktorijumu
- Config u config/ direktorijumu
- Requirements po environment-u (base, local, production)

**Development Experience:**
- Hot reload u Docker
- django-debug-toolbar
- Mailpit za lokalno testiranje email-a

**Note:** Project initialization using this command should be the first implementation story.

## Core Architectural Decisions

### Decision Priority Analysis

**Critical Decisions (Block Implementation):**
- RBAC + Row-level permissions: django-guardian
- Audit logging: django-auditlog
- Frontend interactivity: HTMX + Alpine.js

**Important Decisions (Shape Architecture):**
- File storage: AWS S3
- Virus scanning: ClamAV
- XML generation: lxml + Jinja2 templates

**Deferred Decisions (Post-MVP):**
- Crossref API integracija (Growth feature)
- AI/ML metadata extraction (Vision feature)

### Data Architecture

| Odluka | Izbor | Verzija | Obrazlozenje |
|--------|-------|---------|--------------|
| **RBAC Implementation** | Django Groups + django-guardian | 3.2.0 | Built-in Groups za 4 uloge + guardian za row-level permissions per izdavac |
| **Audit Logging** | django-auditlog | 3.4.1 | Automatski CRUD logging, GDPR compliance, JSON changes support |
| **Data Modeling** | Standard Django ORM | - | Hijerarhija: Publisher → Publication → Issue → Article |
| **Migrations** | Django migrations | - | Cookiecutter default, version controlled |

**RBAC Model:**
```
Superadmin  → Sve dozvole + user management
Administrator → CRUD svi izdavaci + Crossref + publish
Urednik → CRUD samo svoj izdavac + approve
Bibliotekar → CRUD samo svoj izdavac (bez publish)
```

**Row-Level Permissions:**
- Urednik/Bibliotekar vide samo publikacije svog izdavaca
- django-guardian ObjectPermission za Publisher model
- Filter queryset po user.publisher FK ili M2M

### Authentication & Security

| Odluka | Izbor | Obrazlozenje |
|--------|-------|--------------|
| **Authentication** | django-allauth | Cookiecutter default, email verification |
| **Password Hashing** | argon2 | Cookiecutter default, OWASP recommended |
| **Session Backend** | Redis | Cookiecutter default |
| **CSRF Protection** | Django middleware | Default enabled |
| **XSS Protection** | Django templates auto-escape | Default |

### Frontend Architecture

| Odluka | Izbor | Verzija | Obrazlozenje |
|--------|-------|---------|--------------|
| **AJAX/Dynamic Content** | HTMX | 2.0.8 | Server-driven, Django-friendly, manje JS koda |
| **Reactive UI** | Alpine.js | 3.15.3 | Drag&drop autori, inline validacija, lightweight |
| **CSS Framework** | Bootstrap 5 | 5.3+ | UX spec odluka |
| **Icons** | Bootstrap Icons | - | Konzistentnost |

**HTMX Use Cases:**
- Auto-save forme (hx-post, hx-trigger="change delay:2s")
- Inline ORCID validacija (hx-get validation endpoint)
- Status workflow transitions
- Infinite scroll za liste

**Alpine.js Use Cases:**
- Drag & drop author reordering (x-sort)
- Form state management (show/hide sekcije)
- Toast notifications
- Modal dialogs

### API & Communication Patterns

| Odluka | Izbor | Obrazlozenje |
|--------|-------|--------------|
| **External API** | Nije potrebno | MPA, server-rendered |
| **Internal AJAX** | HTMX endpoints | Django views sa HTML fragment responses |
| **Background Tasks** | Celery | XML generisanje, email, virus scan |
| **Email** | django-anymail + Mailgun | Cookiecutter default |

### File Storage & Processing

| Odluka | Izbor | Obrazlozenje |
|--------|-------|--------------|
| **PDF Storage** | AWS S3 | Cookiecutter podrska, skalabilno |
| **Virus Scanning** | ClamAV (self-hosted) | Open source, Celery task |
| **Max File Size** | 100 MB | PRD constraint |
| **Thumbnails** | Pillow | Issue cover images |

**Upload Flow:**
1. User upload → temp storage
2. Celery task → ClamAV scan
3. Clean → move to S3
4. Infected → delete + notify user

### Crossref Integration

| Odluka | Izbor | Obrazlozenje |
|--------|-------|--------------|
| **XML Generation** | lxml + Jinja2 templates | Fleksibilno, template-based |
| **XSD Validation** | lxml.etree.XMLSchema | Standardno, pouzdano |
| **XML Preview** | Syntax highlighted code block | Admin UI feature |

**Template Approach:**
- Jinja2 template za Crossref XML struktura
- Context: Issue + Articles data
- Render → Validate against XSD → Return/Error

### Infrastructure & Deployment

| Odluka | Izbor | Obrazlozenje |
|--------|-------|--------------|
| **Containerization** | Docker + docker-compose | Cookiecutter default |
| **Reverse Proxy** | Traefik | Cookiecutter default, LetsEncrypt |
| **CI/CD** | GitHub Actions | Cookiecutter default |
| **Monitoring** | Sentry | Error tracking |
| **Logging** | structlog | Structured logging |

### Decision Impact Analysis

**Implementation Sequence:**
1. Cookiecutter projekt inicijalizacija
2. Django apps setup (publishers, publications, issues, articles)
3. User model + RBAC (Groups + guardian)
4. CRUD views + templates (Bootstrap 5)
5. HTMX + Alpine.js integracija
6. S3 + ClamAV file handling
7. Crossref XML generation
8. Audit logging finalizacija

**Cross-Component Dependencies:**
- Guardian permissions → User model mora imati Publisher FK
- ClamAV → Celery worker mora imati ClamAV pristup
- HTMX → Svi CRUD views moraju podrzavati fragment responses

## Implementation Patterns & Consistency Rules

### Pattern Categories Defined

**Critical Conflict Points Identified:** 6 oblasti gde AI agenti mogu napraviti razlicite izbore - naming, structure, templates, HTMX, Alpine.js, i format patterns.

### Naming Patterns

**Django Models:**
```python
# OBAVEZNO: Singular, PascalCase
class Article(models.Model):
    pass

class Publisher(models.Model):
    pass
```

**Database Fields:**
```python
# OBAVEZNO: snake_case, deskriptivna imena
created_at = models.DateTimeField(auto_now_add=True)
updated_at = models.DateTimeField(auto_now=True)
is_published = models.BooleanField(default=False)
pdf_file = models.FileField(...)
```

**URL Patterns:**
```python
# OBAVEZNO: kebab-case, plural za liste
path('articles/', ArticleListView.as_view(), name='article-list'),
path('articles/<int:pk>/', ArticleDetailView.as_view(), name='article-detail'),
path('articles/<int:pk>/edit/', ArticleUpdateView.as_view(), name='article-update'),
```

**Views:**
```python
# Class-Based Views: PascalCase + akcija + View
class ArticleListView(ListView):
class ArticleDetailView(DetailView):
class ArticleCreateView(CreateView):

# Function-Based Views (HTMX endpoints): snake_case
def validate_orcid(request):
def article_autosave(request, pk):
```

### Structure Patterns

**Template Organization:**
```
templates/
├── base.html
├── components/              # Reusable UI components
│   ├── _toast.html
│   ├── _modal.html
│   └── _pagination.html
├── articles/
│   ├── article_list.html
│   ├── article_detail.html
│   ├── article_form.html
│   └── partials/           # HTMX fragments (prefixed with _)
│       ├── _article_row.html
│       ├── _article_card.html
│       └── _save_indicator.html
```

**Django App Organization:**
```
doi_portal/
├── config/                 # Cookiecutter config
├── doi_portal/             # Project apps
│   ├── users/
│   ├── publishers/
│   ├── publications/
│   ├── issues/
│   ├── articles/
│   ├── crossref/
│   └── core/               # Shared utilities
├── templates/
├── static/
└── tests/
    ├── conftest.py
    ├── factories.py
    └── test_{app}.py
```

### HTMX Patterns

**Partial Naming:** `_` prefix za sve HTMX fragments
```html
<!-- articles/partials/_article_row.html -->
<tr id="article-{{ article.pk }}">...</tr>
```

**Response Pattern:**
```python
def article_update(request, pk):
    # ... processing ...
    if request.headers.get('HX-Request'):
        return render(request, 'articles/partials/_article_row.html', {'article': article})
    return redirect('article-detail', pk=pk)
```

**Auto-save Pattern:**
```html
<form hx-post="{% url 'article-autosave' pk=article.pk %}"
      hx-trigger="change delay:2s, keyup delay:2s"
      hx-target="#save-indicator"
      hx-swap="innerHTML">
```

### Alpine.js Patterns

**Component Pattern:**
```html
<div x-data="authorList()">
  <template x-for="author in authors" :key="author.id">
    ...
  </template>
</div>

<script>
function authorList() {
  return {
    authors: [],
    addAuthor() { ... },
    removeAuthor(id) { ... }
  }
}
</script>
```

### Format Patterns

**Date Formats:**
- Database: Django default (timezone-aware datetime)
- API/JSON: ISO 8601 (`2026-01-25T10:30:00Z`)
- UI Display: Localized via Django (`{{ article.created_at|date:"d. F Y." }}`)

**HTMX Responses:**
- UVEK vracaj HTML fragment, NE JSON
- Koristi `render()` sa partial template

### Enforcement Guidelines

**Svi AI Agenti MORAJU:**
1. Koristiti singular PascalCase za Django modele
2. Koristiti snake_case za sva DB polja i Python funkcije
3. Koristiti kebab-case za URL paths
4. Prefixovati HTMX partials sa `_`
5. Proveravati `HX-Request` header za HTMX responses
6. Vracati HTML fragments za HTMX, nikad JSON

**Anti-Patterns (ZABRANJENO):**
```python
# LOSE
class Articles(models.Model):     # plural model name
path('article_list/', ...)        # snake_case u URL
def getArticleData(request):      # camelCase function
return JsonResponse({...})        # JSON za HTMX
```

## Project Structure & Boundaries

### Complete Project Directory Structure

```
doi_portal/
├── .envs/
│   ├── .local/
│   │   ├── .django
│   │   └── .postgres
│   └── .production/
│       ├── .django
│       └── .postgres
├── .github/
│   └── workflows/
│       └── ci.yml
├── config/
│   ├── __init__.py
│   ├── celery_app.py
│   ├── settings/
│   │   ├── __init__.py
│   │   ├── base.py
│   │   ├── local.py
│   │   ├── production.py
│   │   └── test.py
│   ├── urls.py
│   └── wsgi.py
├── doi_portal/
│   ├── __init__.py
│   ├── conftest.py
│   │
│   ├── users/                      # FR1-FR7: User Management
│   │   ├── __init__.py
│   │   ├── admin.py
│   │   ├── apps.py
│   │   ├── models.py               # Custom User + Publisher FK
│   │   ├── forms.py
│   │   ├── views.py
│   │   ├── urls.py
│   │   └── tests/
│   │
│   ├── publishers/                 # FR8-FR12: Publisher Management
│   │   ├── __init__.py
│   │   ├── admin.py
│   │   ├── apps.py
│   │   ├── models.py               # Publisher model + DOI prefix
│   │   ├── forms.py
│   │   ├── views.py
│   │   ├── urls.py
│   │   └── tests/
│   │
│   ├── publications/               # FR13-FR17: Publication Management
│   │   ├── __init__.py
│   │   ├── admin.py
│   │   ├── apps.py
│   │   ├── models.py               # Publication (casopis, zbornik, etc.)
│   │   ├── forms.py
│   │   ├── views.py
│   │   ├── urls.py
│   │   └── tests/
│   │
│   ├── issues/                     # FR18-FR21: Issue Management
│   │   ├── __init__.py
│   │   ├── admin.py
│   │   ├── apps.py
│   │   ├── models.py               # Issue (volume, broj, cover)
│   │   ├── forms.py
│   │   ├── views.py
│   │   ├── urls.py
│   │   └── tests/
│   │
│   ├── articles/                   # FR22-FR32: Article Management
│   │   ├── __init__.py
│   │   ├── admin.py
│   │   ├── apps.py
│   │   ├── models.py               # Article, Author (JSON/M2M)
│   │   ├── forms.py
│   │   ├── views.py                # CRUD + HTMX endpoints
│   │   ├── urls.py
│   │   ├── validators.py           # ORCID validation
│   │   ├── services.py             # Business logic
│   │   └── tests/
│   │
│   ├── crossref/                   # FR33-FR37: Crossref Integration
│   │   ├── __init__.py
│   │   ├── apps.py
│   │   ├── views.py                # XML preview, generation
│   │   ├── urls.py
│   │   ├── services.py             # XML generation logic
│   │   ├── validators.py           # XSD validation
│   │   ├── tasks.py                # Celery tasks
│   │   ├── templates/
│   │   │   └── crossref/
│   │   │       └── journal_article.xml.j2
│   │   └── tests/
│   │
│   ├── portal/                     # FR38-FR45: Public Portal
│   │   ├── __init__.py
│   │   ├── apps.py
│   │   ├── views.py                # Home, search, article landing
│   │   ├── urls.py
│   │   └── tests/
│   │
│   ├── core/                       # Shared utilities
│   │   ├── __init__.py
│   │   ├── apps.py
│   │   ├── mixins.py               # Audit, permissions mixins
│   │   ├── permissions.py          # Guardian permission helpers
│   │   ├── storage.py              # S3 storage configuration
│   │   ├── tasks.py                # Common Celery tasks (virus scan)
│   │   └── utils.py
│   │
│   └── static/
│       ├── css/
│       │   ├── portal.css
│       │   └── admin.css
│       ├── js/
│       │   ├── portal.js
│       │   ├── admin.js
│       │   └── components/
│       │       ├── author-list.js
│       │       └── autosave.js
│       └── images/
│
├── templates/
│   ├── base.html
│   ├── admin_base.html
│   ├── components/
│   │   ├── _toast.html
│   │   ├── _modal.html
│   │   ├── _pagination.html
│   │   ├── _status_badge.html
│   │   ├── _save_indicator.html
│   │   └── _breadcrumbs.html
│   ├── account/
│   ├── users/
│   ├── publishers/
│   ├── publications/
│   ├── issues/
│   ├── articles/
│   │   ├── article_list.html
│   │   ├── article_detail.html
│   │   ├── article_form.html
│   │   └── partials/
│   │       ├── _article_row.html
│   │       ├── _article_card.html
│   │       ├── _author_item.html
│   │       ├── _orcid_validation.html
│   │       └── _save_indicator.html
│   ├── crossref/
│   ├── portal/
│   │   ├── home.html
│   │   ├── publications.html
│   │   ├── publishers.html
│   │   ├── article_landing.html
│   │   ├── about.html
│   │   └── contact.html
│   └── dashboard/
│
├── tests/
│   ├── conftest.py
│   ├── factories.py
│   ├── test_permissions.py
│   └── test_integration.py
│
├── compose/
│   ├── local/
│   │   └── django/
│   │       └── Dockerfile
│   └── production/
│       ├── django/
│       │   └── Dockerfile
│       ├── traefik/
│       │   └── traefik.yml
│       └── clamav/
│           └── Dockerfile
│
├── requirements/
│   ├── base.txt
│   ├── local.txt
│   └── production.txt
│
├── docker-compose.yml
├── docker-compose.production.yml
├── manage.py
├── pyproject.toml
├── setup.cfg
└── README.md
```

### Requirements to Structure Mapping

| FR Kategorija | Django App | Kljucni Fajlovi |
|---------------|------------|-----------------|
| **FR1-FR7** User Management | `users/` | models.py (User+Publisher FK), views.py |
| **FR8-FR12** Publishers | `publishers/` | models.py (Publisher, doi_prefix) |
| **FR13-FR17** Publications | `publications/` | models.py (Publication types) |
| **FR18-FR21** Issues | `issues/` | models.py (volume, broj, cover) |
| **FR22-FR32** Articles | `articles/` | models.py, validators.py, services.py |
| **FR33-FR37** Crossref | `crossref/` | services.py, validators.py, templates/ |
| **FR38-FR45** Public Portal | `portal/` | views.py (home, landing, search) |
| **FR46-FR50** Dashboard | `dashboard/` templates | dashboard.html, audit views |

### Architectural Boundaries

**Data Flow:**
```
Posetilac → portal/views.py → Article model → S3 (PDF)
                                    ↓
Admin → articles/views.py → Article model → Celery (virus scan)
                                    ↓
            crossref/services.py → Jinja2 XML template → XSD validation
```

**Integration Boundaries:**

| Granica | Ulaz | Izlaz |
|---------|------|-------|
| **Portal → Articles** | DOI URL | HTML landing page |
| **Admin → Celery** | File upload | Scan result notification |
| **Crossref Service** | Issue + Articles data | Validated XML file |
| **S3 Storage** | PDF binary | Signed URL |
| **Guardian Permissions** | User + Publisher | Queryset filter |

### Cross-Cutting Concerns Location

| Concern | Lokacija | Opis |
|---------|----------|------|
| **Audit Logging** | `core/mixins.py` | AuditLogMixin za sve views |
| **Permissions** | `core/permissions.py` | Guardian helpers, queryset filters |
| **File Storage** | `core/storage.py` | S3 storage backend config |
| **Virus Scan** | `core/tasks.py` | Celery task za ClamAV |
| **ORCID Validation** | `articles/validators.py` | Reusable validator |
| **XML Generation** | `crossref/services.py` | Jinja2 + lxml logic |

## Architecture Validation Results

### Coherence Validation ✅

**Decision Compatibility:**
Sve tehnologije su medjusobno kompatibilne. Django 5.2+ podrzan od svih biblioteka (guardian 3.2.0, auditlog 3.4.1). HTMX i Alpine.js su komplementarni za frontend. Cookiecutter Django 2026.4.3 pruza production-ready osnovu.

**Pattern Consistency:**
Naming konvencije su konzistentne: snake_case za Python/DB, PascalCase za klase, kebab-case za URLs. HTMX partials koriste `_` prefix. Alpine.js komponente koriste function pattern.

**Structure Alignment:**
Projektna struktura direktno mapira funkcionalne kategorije na Django apps. Cross-cutting concerns centralizovani u `core/` app.

### Requirements Coverage Validation ✅

**Functional Requirements:**
Svih 50 FR pokriveno kroz 8 Django apps:
- users/ (FR1-FR7)
- publishers/ (FR8-FR12)
- publications/ (FR13-FR17)
- issues/ (FR18-FR21)
- articles/ (FR22-FR32)
- crossref/ (FR33-FR37)
- portal/ (FR38-FR45)
- dashboard/ (FR46-FR50)

**Non-Functional Requirements:**
- Performance: Redis cache, CDN ready, optimizovani templates
- Security: argon2 hashing, CSRF, XSS protection, virus scan
- Accessibility: WCAG AA (UX spec), Bootstrap 5 pristupacnost
- Reliability: Docker containerization, Traefik LB, backup strategy
- GDPR: Soft delete, audit logging, data retention

### Implementation Readiness Validation ✅

**Decision Completeness:**
Sve kriticne odluke dokumentovane sa verzijama i obrazlozenjem.

**Structure Completeness:**
Kompletna directory struktura sa 8 Django apps i 100+ fajlova.

**Pattern Completeness:**
Naming, structure, HTMX i Alpine.js patterns definisani sa primerima.

### Gap Analysis Results

**Critical Gaps:** Nema

**Important Gaps:** Data model dijagram (kreirati tokom implementacije)

**Nice-to-Have:** Postman collection, Storybook

### Architecture Completeness Checklist

**✅ Requirements Analysis**
- [x] Project context thoroughly analyzed
- [x] Scale and complexity assessed (Medium-High)
- [x] Technical constraints identified
- [x] Cross-cutting concerns mapped (6 concerns)

**✅ Architectural Decisions**
- [x] Critical decisions documented with versions
- [x] Technology stack fully specified
- [x] Integration patterns defined (HTMX, Celery, S3)
- [x] Performance considerations addressed

**✅ Implementation Patterns**
- [x] Naming conventions established
- [x] Structure patterns defined
- [x] Communication patterns specified (HTMX fragments)
- [x] Process patterns documented (upload flow)

**✅ Project Structure**
- [x] Complete directory structure defined
- [x] Component boundaries established
- [x] Integration points mapped
- [x] Requirements to structure mapping complete

### Architecture Readiness Assessment

**Overall Status:** READY FOR IMPLEMENTATION ✅

**Confidence Level:** HIGH

**Key Strengths:**
1. Cookiecutter Django pruza production-ready osnovu
2. Jasna mapiranje FR → Django apps
3. Kompletni patterns za HTMX/Alpine.js
4. RBAC i row-level permissions strategija definisana
5. Crossref XML pristup dokumentovan

**Areas for Future Enhancement:**
1. Data model ER dijagram
2. Performance benchmarks
3. Load testing strategy

### Implementation Handoff

**AI Agent Guidelines:**
- Pratiti sve arhitekturne odluke tacno kako su dokumentovane
- Koristiti implementation patterns konzistentno
- Postovati project structure i boundaries
- Konsultovati ovaj dokument za sva arhitekturna pitanja

**First Implementation Priority:**
```bash
pip install cookiecutter
cookiecutter gh:cookiecutter/cookiecutter-django
```

Zatim kreirati Django apps redom: publishers → publications → issues → articles

## Architecture Completion Summary

### Workflow Completion

**Architecture Decision Workflow:** COMPLETED ✅
**Total Steps Completed:** 8
**Date Completed:** 2026-01-25
**Document Location:** `_bmad-output/planning-artifacts/architecture.md`

### Final Architecture Deliverables

**Complete Architecture Document**
- Sve arhitekturne odluke dokumentovane sa specificnim verzijama
- Implementation patterns koji obezbedjuju AI agent konzistentnost
- Kompletna projektna struktura sa svim fajlovima i direktorijumima
- Mapiranje zahteva na arhitekturu
- Validacija koja potvrdjuje koherentnost i kompletnost

**Implementation Ready Foundation**
- 20+ arhitekturnih odluka doneseno
- 6 implementation patterns definisano
- 8 Django apps specifikovano
- 50 funkcionalnih zahteva podrzano

**AI Agent Implementation Guide**
- Tech stack sa verifikovanim verzijama
- Konzistencija pravila koja sprecavaju implementation konflikte
- Projektna struktura sa jasnim granicama
- Integration patterns i communication standardi

### Development Sequence

1. Inicijalizovati projekat koristeci Cookiecutter Django
2. Podesiti development environment prema arhitekturi
3. Implementirati core arhitekturne osnove (User model + RBAC)
4. Graditi features prateci ustanovljene patterns
5. Odrzavati konzistentnost sa dokumentovanim pravilima

### Project Success Factors

**Clear Decision Framework**
Svaki tehnoloski izbor donesen kolaborativno sa jasnim obrazlozenjem.

**Consistency Guarantee**
Implementation patterns i pravila obezbedjuju da vise AI agenata proizvodi kompatibilan, konzistentan kod.

**Complete Coverage**
Svi projektni zahtevi su arhitekturno podrzani sa jasnim mapiranjem.

**Solid Foundation**
Cookiecutter Django i arhitekturni patterns pruzaju production-ready osnovu.

---

**Architecture Status:** READY FOR IMPLEMENTATION ✅

**Next Phase:** Zapocni implementaciju koristeci arhitekturne odluke i patterns dokumentovane ovde.

**Document Maintenance:** Azuriraj ovu arhitekturu kada se donesu znacajne tehnicke odluke tokom implementacije.

