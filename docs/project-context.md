# DOI Portal - Project Context

> **CITAJ OVO PRVO** - Ovaj fajl sadrzi kriticna pravila koja AI agenti moraju pratiti pri implementaciji.

---

## Tech Stack (Verzije su OBAVEZNE)

| Komponenta | Verzija | Napomena |
|------------|---------|----------|
| Python | 3.13 | - |
| Django | 5.2+ | Cookiecutter Django 2026.4.3 |
| PostgreSQL | 16+ | NE MySQL |
| Redis | latest | Sessions, cache, Celery broker |
| Celery | latest | Background tasks |
| HTMX | 2.0.8 | CDN ili npm |
| Alpine.js | 3.15.3 | CDN ili npm |
| Bootstrap | 5.3+ | CSS framework |
| django-guardian | 3.2.0 | Row-level permissions |
| django-auditlog | 3.4.1 | Audit logging |

---

## Naming Konvencije (OBAVEZNO)

```python
# Models: Singular, PascalCase
class Article(models.Model):  # ISPRAVNO
class Articles(models.Model):  # POGRESNO

# DB fields: snake_case
created_at = models.DateTimeField()  # ISPRAVNO
createdAt = models.DateTimeField()   # POGRESNO

# URLs: kebab-case, plural za liste
path('articles/', ...)           # ISPRAVNO
path('article_list/', ...)       # POGRESNO

# CBV: PascalCase + Action + View
class ArticleCreateView(CreateView):  # ISPRAVNO

# FBV (HTMX endpoints): snake_case
def validate_orcid(request):  # ISPRAVNO
def validateOrcid(request):   # POGRESNO
```

---

## HTMX Pravila (KRITICNO)

1. **Partials**: UVEK koristi `_` prefix za HTMX fragments
   ```
   templates/articles/partials/_article_row.html
   ```

2. **Response**: UVEK vracaj HTML, NIKAD JSON
   ```python
   def article_update(request, pk):
       if request.headers.get('HX-Request'):
           return render(request, 'articles/partials/_article_row.html', ctx)
       return redirect('article-detail', pk=pk)
   ```

3. **Auto-save pattern**:
   ```html
   <form hx-post="{% url 'article-autosave' pk=article.pk %}"
         hx-trigger="change delay:2s"
         hx-target="#save-indicator">
   ```

4. **Inline validation**:
   ```html
   <input name="orcid"
          hx-get="{% url 'validate-orcid' %}"
          hx-trigger="blur"
          hx-target="#orcid-feedback">
   ```

---

## Django Apps Struktura

```
doi_portal/
├── users/        # FR1-FR7: User Management
├── publishers/   # FR8-FR12: Publisher CRUD
├── publications/ # FR13-FR17: Publication types
├── issues/       # FR18-FR21: Volume, broj, cover
├── articles/     # FR22-FR32: Article CRUD + authors
├── crossref/     # FR33-FR37: XML generation
├── portal/       # FR38-FR45: Public website
└── core/         # Shared: mixins, permissions, storage
```

---

## RBAC Model (django-guardian)

```
Superadmin    → Sve dozvole + user management
Administrator → CRUD svi izdavaci + Crossref + publish
Urednik       → CRUD samo svoj izdavac + approve
Bibliotekar   → CRUD samo svoj izdavac (bez publish)
```

**Row-level permissions**: Koristi `django-guardian` ObjectPermission na Publisher modelu.

---

## Services Layer (Business Logic)

**Pravilo:** Kompleksna business logika ide u `services.py`, NE u views.

```python
# articles/services.py
def submit_article_for_review(article: Article, user: User) -> Article:
    """Submit article for editorial review."""
    if article.status != ArticleStatus.DRAFT:
        raise InvalidStatusTransition("Only drafts can be submitted")

    article.status = ArticleStatus.REVIEW
    article.submitted_by = user
    article.submitted_at = timezone.now()
    article.save()
    return article

# articles/views.py - DELEGIRAJ u service
def submit_for_review(request, pk):
    article = get_object_or_404(Article, pk=pk)
    submit_article_for_review(article, request.user)
    return redirect('article-detail', pk=pk)
```

---

## Forms & Validation

**ModelForm naming:** `{Model}Form`
```python
class ArticleForm(forms.ModelForm):
    class Meta:
        model = Article
        fields = ['title', 'abstract', 'keywords']
```

**Custom validators:**
```python
# articles/validators.py
def validate_orcid(value: str) -> None:
    """Validate ORCID format: 0000-0000-0000-000X"""
    pattern = r'^\d{4}-\d{4}-\d{4}-\d{3}[\dX]$'
    if not re.match(pattern, value):
        raise ValidationError("Invalid ORCID format")
```

---

## Testing (pytest-django)

**Konfiguracija:**
```bash
pytest --ds=config.settings.test --reuse-db
```

**Test file naming:**
```python
# ISPRAVNO
tests/test_articles.py
tests/test_publishers.py

# POGRESNO
tests/articles_tests.py
```

**Coverage:** Minimum 80%, exclude migrations i tests/

**Factory pattern:**
```python
# Koristi Factory Boy za test data
from factory.django import DjangoModelFactory
import factory

class ArticleFactory(DjangoModelFactory):
    class Meta:
        model = Article
    title = factory.Faker('sentence')
    abstract = factory.Faker('paragraph')
```

---

## Code Quality Tools

**Ruff** (linter - zamena za flake8):
```bash
ruff check .
ruff format .
```

**Mypy** (type checking):
```bash
mypy doi_portal --python-version 3.13
```

**djLint** (template linting):
```bash
djlint templates/ --profile=django
```

---

## Celery Tasks (Background Jobs)

**Naming:** `{app}_{action}_task`
```python
# crossref/tasks.py
@shared_task
def crossref_generate_xml_task(issue_id: int) -> str:
    """Generate Crossref XML for issue."""
    ...
```

**Retry pattern:**
```python
@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def virus_scan_task(self, file_id: int):
    try:
        scan_file(file_id)
    except ClamAVError as e:
        raise self.retry(exc=e)
```

**Testing:** `CELERY_TASK_ALWAYS_EAGER=True` u test settings.

---

## Error Handling

**Custom exceptions:**
```python
# core/exceptions.py
class DOIPortalException(Exception):
    """Base exception for DOI Portal."""
    pass

class InvalidStatusTransition(DOIPortalException):
    """Raised when article status transition is invalid."""
    pass
```

**View error handling:**
```python
from django.contrib import messages

def publish_article(request, pk):
    try:
        publish(article, request.user)
        messages.success(request, "Clanak objavljen.")
    except InvalidStatusTransition as e:
        messages.error(request, str(e))
    return redirect('article-detail', pk=pk)
```

---

## Kljucne Integracije

| Integracija | Pristup |
|-------------|---------|
| File Storage | AWS S3 via django-storages |
| Virus Scan | ClamAV, Celery task |
| XML Generation | lxml + Jinja2 templates |
| XSD Validation | lxml.etree.XMLSchema |
| Email | django-anymail + Mailgun |

---

## File Upload Flow

1. User upload → temp storage
2. Celery task → ClamAV scan
3. Clean → move to S3
4. Infected → delete + notify user

---

## Template Struktura

```
templates/
├── base.html
├── components/           # Reusable: _toast, _modal, _pagination
├── {app}/
│   ├── {model}_list.html
│   ├── {model}_detail.html
│   ├── {model}_form.html
│   └── partials/         # HTMX fragments sa _ prefix
│       └── _{model}_row.html
```

---

## Audit Logging

Koristi `django-auditlog` za automatski CRUD logging. Registruj sve modele koji zahtevaju audit trail.

```python
from auditlog.registry import auditlog
auditlog.register(Article)
auditlog.register(Publisher)
auditlog.register(Publication)
auditlog.register(Issue)
```

---

## Anti-Patterns (ZABRANJENO)

```python
# NE RADI OVO:
class Articles(models.Model):      # plural model
path('article_list/', ...)         # snake_case URL
def getArticleData(request):       # camelCase function
return JsonResponse({...})         # JSON za HTMX response
article.save()                     # Direktno u view umesto service
```

---

**Referentni dokumenti:**
- `_bmad-output/planning-artifacts/architecture.md`
- `_bmad-output/planning-artifacts/prd.md`
- `_bmad-output/test-design-system.md`
