# Story 3.3: PDF Upload with Virus Scanning

Status: done

## Story

As a **Bibliotekar**,
I want **to upload a PDF file for the article with automatic virus scanning**,
So that **visitors can safely download the full-text article and the system is protected from malicious files**.

## Background

Ovo je treća priča u Epiku 3 (Article Workflow). Implementira PDF upload sa ClamAV virus skeniranjem putem Celery zadatka. Article model VEĆ ima `pdf_file` FileField (Story 3.1). Ova priča dodaje: upload UI u article_form.html (edit mode), Celery task za virus skeniranje, PDF status tracking, i HTMX polling za status prikaz.

**FR Pokrivenost:** FR25 (upload PDF fajla), NFR11 (virus scan pre prihvatanja)

**Zavisnosti (sve DONE):**
- Story 3.1: Article Model & Basic Metadata Entry - Article model sa `pdf_file` FileField, article_form.html, articles app infrastruktura
- Story 3.2: Author Management - article_form.html sa edit mode sekcijama, HTMX pattern, Alpine.js integracija
- Story 2.8: Row-Level Permissions - publisher-scoped mixins

**Blokira:**
- Story 3.5: Submit Article for Review - validacija "PDF uploaded" pre submit-a
- Story 4.6: PDF Download - PDF fajl mora postojati i biti clean

## Acceptance Criteria

1. **Given** Bibliotekar edituje članak (edit mode)
   **When** pregleda sekciju "PDF fajl"
   **Then** prikazan je trenutni PDF status: none, uploading, scanning, clean, infected
   **And** upload dugme/dropzone je prikazan
   **And** sekcija je ispod Author sekcije u article_form.html

2. **Given** Bibliotekar selektuje PDF fajl
   **When** fajl je manji od 100MB i ima PDF MIME tip
   **Then** progress bar se prikazuje tokom upload-a
   **And** fajl se upload-uje na lokalni/temporary storage
   **And** `enctype="multipart/form-data"` je na formi

3. **Given** PDF upload je završen
   **When** fajl je u temporary storage-u
   **Then** Celery task se pokreće za ClamAV virus skeniranje
   **And** Article.pdf_status se postavlja na "scanning"
   **And** UI prikazuje "Skeniranje u toku..." indikator
   **And** HTMX polling proverava status svake 3 sekunde

4. **Given** virus skeniranje završava uspešno (clean)
   **When** nema detektovanih pretnji
   **Then** fajl ostaje na mestu (lokalni storage za sada, S3 migracija je post-MVP)
   **And** Article.pdf_file polje se ažurira
   **And** Article.pdf_status se postavlja na "clean"
   **And** UI prikazuje "PDF uspešno otpremljen" sa informacijama o fajlu (naziv, veličina)

5. **Given** virus skeniranje detektuje pretnju
   **When** fajl je inficiran
   **Then** fajl se briše iz temporary storage-a
   **And** Article.pdf_status se postavlja na "infected"
   **And** korisnik je obavešten: "Fajl odbijen: detektovana bezbednosna pretnja"
   **And** incident se loguje (structlog)

6. **Given** Bibliotekar želi zameniti PDF
   **When** upload-uje novi fajl
   **Then** stari fajl se čuva dok novi ne prođe skeniranje
   **And** po uspešnom skeniranju novog fajla, stari se briše
   **And** članak održava kontinuiranu PDF dostupnost tokom zamene

7. **Given** ClamAV servis nije dostupan
   **When** Celery task ne može da se poveže
   **Then** task se ponovo pokušava do 3 puta sa 60s delay-om
   **And** nakon 3 neuspešna pokušaja, pdf_status se postavlja na "scan_failed"
   **And** korisnik vidi: "Skeniranje neuspešno, pokušajte ponovo kasnije"
   **And** fajl ostaje u temporary storage-u za ručno skeniranje

8. **Given** fajl koji se upload-uje nije PDF
   **When** klijentska ili serverska validacija detektuje
   **Then** upload se odbija sa porukom: "Dozvoljeni su samo PDF fajlovi"
   **And** validacija proverava i Content-Type i file extension

9. **Given** fajl je veći od 100MB
   **When** validacija proveri veličinu
   **Then** upload se odbija sa porukom: "Maksimalna veličina fajla je 100 MB"

10. **Given** PDF fajl i Article model postoje
    **When** se pdf_file upload ili status promeni
    **Then** sve operacije se beleže u audit log (auditlog)

## Tasks / Subtasks

- [x] Task 1: Dodati pdf_status polje na Article model (AC: #1, #3, #4, #5, #7)
  - [x] 1.1 Kreirati `PdfStatus` TextChoices enum (NONE="none", UPLOADING="uploading", SCANNING="scanning", CLEAN="clean", INFECTED="infected", SCAN_FAILED="scan_failed")
  - [x] 1.2 Dodati `pdf_status` CharField na Article model sa default=NONE
  - [x] 1.3 Dodati `pdf_original_filename` CharField na Article model (blank=True) - čuva originalno ime fajla za prikaz
  - [x] 1.4 Kreirati i izvršiti migracije: `0003_article_pdf_status.py`

- [x] Task 2: Kreirati PDF upload validator (AC: #8, #9)
  - [x] 2.1 U `articles/validators.py` kreirati `validate_pdf_file(file)` funkciju
  - [x] 2.2 Proveriti MIME tip: `application/pdf` (koristiti `python-magic` ili file extension fallback)
  - [x] 2.3 Proveriti veličinu: max 100MB (`100 * 1024 * 1024` bytes)
  - [x] 2.4 Proveriti file extension: `.pdf`
  - [x] 2.5 Srpske poruke grešaka sa ispravnim dijakritikama

- [x] Task 3: Kreirati Celery task za virus skeniranje (AC: #3, #4, #5, #7)
  - [x] 3.1 Kreirati `articles/tasks.py` sa `virus_scan_pdf_task(article_id)` Celery task
  - [x] 3.2 Koristiti `pyclamd` biblioteku za ClamAV komunikaciju
  - [x] 3.3 Implementirati retry logiku: `max_retries=3, default_retry_delay=60`
  - [x] 3.4 Na clean result: ažurirati `article.pdf_status = "clean"`, logirati uspeh
  - [x] 3.5 Na infected result: obrisati fajl, ažurirati `article.pdf_status = "infected"`, logirati incident
  - [x] 3.6 Na ClamAV connection error: retry ili `pdf_status = "scan_failed"` nakon max retries
  - [x] 3.7 Koristiti `structlog` za logiranje svih operacija
  - [x] 3.8 Dodati `CLAMAV_HOST` i `CLAMAV_PORT` u Django settings (default: "localhost", 3310)

- [x] Task 4: Kreirati PDF upload HTMX view (AC: #1, #2, #3, #6)
  - [x] 4.1 U `articles/views.py` dodati `pdf_upload(request, article_pk)` FBV
  - [x] 4.2 Prihvatiti POST sa multipart/form-data
  - [x] 4.3 Validirati fajl (tip, veličina) pre čuvanja
  - [x] 4.4 Sačuvati fajl u `articles/pdfs/` direktorijum (Article.pdf_file upload_to)
  - [x] 4.5 Pokrenuti `virus_scan_pdf_task.delay(article.id)`
  - [x] 4.6 Postaviti `article.pdf_status = "scanning"` i `pdf_original_filename`
  - [x] 4.7 Vratiti HTML fragment sa statusom

- [x] Task 5: Kreirati PDF status polling HTMX view (AC: #3, #4, #5, #7)
  - [x] 5.1 U `articles/views.py` dodati `pdf_status(request, article_pk)` FBV (GET)
  - [x] 5.2 Vratiti HTML fragment sa trenutnim `pdf_status`
  - [x] 5.3 Uključiti `hx-trigger="every 3s"` u fragment dok je status "scanning"
  - [x] 5.4 Zaustaviti polling kad je status: clean, infected, scan_failed, none

- [x] Task 6: Kreirati PDF delete HTMX view (AC: #6)
  - [x] 6.1 U `articles/views.py` dodati `pdf_delete(request, article_pk)` FBV (POST)
  - [x] 6.2 Obrisati fajl sa storage-a
  - [x] 6.3 Postaviti `article.pdf_file = ""`, `article.pdf_status = "none"`, `pdf_original_filename = ""`
  - [x] 6.4 Vratiti ažurirani HTML fragment

- [x] Task 7: Kreirati URL routes za PDF endpoints (AC: #1-#9)
  - [x] 7.1 U `articles/urls.py` dodati:
    - `<int:article_pk>/pdf/upload/` (name: pdf-upload) - POST
    - `<int:article_pk>/pdf/status/` (name: pdf-status) - GET
    - `<int:article_pk>/pdf/delete/` (name: pdf-delete) - POST

- [x] Task 8: Kreirati template-ove za PDF sekciju (AC: #1, #2, #3, #4, #5, #7)
  - [x] 8.1 Kreirati `templates/articles/partials/_pdf_upload.html` - kompletna PDF sekcija
  - [x] 8.2 Uključiti upload formu sa drag & drop zonu (Alpine.js)
  - [x] 8.3 Uključiti progress bar za upload
  - [x] 8.4 Uključiti status indikator (spinner za scanning, checkmark za clean, X za infected)
  - [x] 8.5 Uključiti file info prikaz kad je PDF uploadovan (naziv, veličina)
  - [x] 8.6 Uključiti "Ukloni PDF" dugme za postojeće fajlove
  - [x] 8.7 Ažurirati `article_form.html` - dodati PDF sekciju ispod Authors sekcije (edit mode)

- [x] Task 9: Instalirati pyclamd zavisnost (AC: #3)
  - [x] 9.1 `uv add pyclamd` za dodavanje u pyproject.toml
  - [x] 9.2 `uv lock` za ažuriranje lock fajla
  - [x] 9.3 Dodati CLAMAV settings u `config/settings/base.py`
  - [x] 9.4 Dodati CLAMAV mock settings u `config/settings/test.py`

- [x] Task 10: Ažurirati docker-compose za ClamAV (AC: #3)
  - [x] 10.1 Dodati ClamAV servis u `docker-compose.local.yml`
  - [x] 10.2 Koristiti `clamav/clamav:latest` Docker image
  - [x] 10.3 Expose port 3310 za clamd daemon
  - [x] 10.4 Dodati volume za virus definitions cache

- [x] Task 11: Kreirati testove (AC: #1-#10)
  - [x] 11.1 Model testovi: PdfStatus choices, pdf_status field, pdf_original_filename
  - [x] 11.2 Validator testovi: validate_pdf_file (tip, veličina, extension)
  - [x] 11.3 View testovi: pdf_upload sa raznim fajlovima (valid PDF, non-PDF, oversized)
  - [x] 11.4 View testovi: pdf_status polling, pdf_delete
  - [x] 11.5 Celery task testovi: virus_scan_pdf_task sa mock ClamAV (clean, infected, connection error)
  - [x] 11.6 Permission testovi: publisher scoping za PDF endpoints
  - [x] 11.7 Replacement testovi: zamena PDF-a dok stari postoji
  - [x] 11.8 Koristiti `CELERY_TASK_ALWAYS_EAGER=True` iz test settings

## Dev Notes

### KRITIČNO: Pratiti ustanovljene patterns iz Story 3.1 i 3.2

PDF upload MORA pratiti IDENTIČNE patterns kao ostatak articles app:

1. **View pattern**: FBV-ovi za HTMX endpoints (NE CBV) - snake_case, `HX-Request` header check
2. **Template pattern**: HTMX partials sa `_` prefix u `articles/partials/` direktorijumu
3. **Permission pattern**: `_check_article_permission(user, article)` - VEĆ postoji u views.py
4. **Auditlog**: Article je VEĆ registrovan sa auditlog - pdf_file promene se automatski beleže
5. **Test pattern**: Factory Boy, pytest-django, CELERY_TASK_ALWAYS_EAGER=True

### Article Model - Postojeće pdf_file polje

Article model VEĆ ima `pdf_file` FileField definisan u `articles/models.py`:

```python
# VEĆ POSTOJI - NE kreirati ponovo!
pdf_file = models.FileField(
    _("PDF fajl"),
    upload_to="articles/pdfs/",
    blank=True,
)
```

Potrebno DODATI samo nova polja:

```python
# articles/models.py - DODATI u Article model

class PdfStatus(models.TextChoices):
    """PDF processing status."""
    NONE = "none", _("Nema PDF-a")
    UPLOADING = "uploading", _("Otpremanje")
    SCANNING = "scanning", _("Skeniranje")
    CLEAN = "clean", _("Čist")
    INFECTED = "infected", _("Inficiran")
    SCAN_FAILED = "scan_failed", _("Skeniranje neuspešno")

# U Article modelu:
pdf_status = models.CharField(
    _("PDF status"),
    max_length=20,
    choices=PdfStatus.choices,
    default=PdfStatus.NONE,
)
pdf_original_filename = models.CharField(
    _("Originalni naziv fajla"),
    max_length=500,
    blank=True,
)
```

### PDF Upload View Pattern

```python
# articles/views.py - DODATI u postojeći fajl

@login_required
@require_POST
def pdf_upload(request, article_pk):
    """Upload PDF file for article via HTMX POST."""
    article = get_object_or_404(
        Article.objects.select_related(
            "issue", "issue__publication", "issue__publication__publisher"
        ),
        pk=article_pk,
    )
    _check_article_permission(request.user, article)

    pdf_file = request.FILES.get("pdf_file")
    if not pdf_file:
        return render(request, "articles/partials/_pdf_upload.html", {
            "article": article,
            "error": "Izaberite PDF fajl za otpremanje.",
        })

    # Validate file
    errors = validate_pdf_file(pdf_file)
    if errors:
        return render(request, "articles/partials/_pdf_upload.html", {
            "article": article,
            "error": errors[0],
        })

    # Save old file reference for cleanup after successful scan
    old_pdf = article.pdf_file.name if article.pdf_file else None

    # Save new file
    article.pdf_file = pdf_file
    article.pdf_original_filename = pdf_file.name
    article.pdf_status = PdfStatus.SCANNING
    article.save(update_fields=["pdf_file", "pdf_original_filename", "pdf_status"])

    # Trigger async virus scan
    from .tasks import virus_scan_pdf_task
    virus_scan_pdf_task.delay(article.id, old_pdf_path=old_pdf)

    return render(request, "articles/partials/_pdf_upload.html", {
        "article": article,
    })
```

### Celery Task za Virus Skeniranje

```python
# articles/tasks.py - NOVI FAJL

import structlog
from celery import shared_task
from django.conf import settings

logger = structlog.get_logger(__name__)

@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def virus_scan_pdf_task(self, article_id, old_pdf_path=None):
    """
    Scan uploaded PDF for viruses using ClamAV.

    Flow:
    1. Connect to ClamAV daemon
    2. Scan file
    3. Clean → keep file, update status to "clean"
    4. Infected → delete file, update status to "infected"
    5. Error → retry up to 3 times, then "scan_failed"
    """
    from doi_portal.articles.models import Article, PdfStatus

    try:
        article = Article.all_objects.get(pk=article_id)
    except Article.DoesNotExist:
        logger.error("article_not_found", article_id=article_id)
        return

    try:
        import pyclamd
        cd = pyclamd.ClamdNetworkSocket(
            host=getattr(settings, "CLAMAV_HOST", "localhost"),
            port=getattr(settings, "CLAMAV_PORT", 3310),
        )
        cd.ping()
    except Exception as exc:
        logger.warning(
            "clamav_connection_failed",
            article_id=article_id,
            error=str(exc),
            retry=self.request.retries,
        )
        try:
            raise self.retry(exc=exc)
        except self.MaxRetriesExceededError:
            article.pdf_status = PdfStatus.SCAN_FAILED
            article.save(update_fields=["pdf_status"])
            logger.error("clamav_max_retries_exceeded", article_id=article_id)
            return

    # Scan the file
    try:
        scan_result = cd.scan_stream(article.pdf_file.read())
        article.pdf_file.seek(0)  # Reset file pointer
    except Exception as exc:
        logger.error("clamav_scan_error", article_id=article_id, error=str(exc))
        try:
            raise self.retry(exc=exc)
        except self.MaxRetriesExceededError:
            article.pdf_status = PdfStatus.SCAN_FAILED
            article.save(update_fields=["pdf_status"])
            return

    if scan_result is None:
        # File is clean
        article.pdf_status = PdfStatus.CLEAN
        article.save(update_fields=["pdf_status"])
        logger.info("pdf_scan_clean", article_id=article_id)

        # Delete old PDF if this was a replacement
        if old_pdf_path:
            _delete_old_pdf(old_pdf_path)
    else:
        # File is infected
        virus_name = str(scan_result)
        file_path = article.pdf_file.name
        article.pdf_file.delete(save=False)
        article.pdf_file = ""
        article.pdf_original_filename = ""
        article.pdf_status = PdfStatus.INFECTED
        article.save(update_fields=["pdf_file", "pdf_original_filename", "pdf_status"])
        logger.error(
            "pdf_scan_infected",
            article_id=article_id,
            virus=virus_name,
            file_path=file_path,
        )


def _delete_old_pdf(file_path):
    """Delete old PDF file from storage."""
    from django.core.files.storage import default_storage
    try:
        if default_storage.exists(file_path):
            default_storage.delete(file_path)
    except Exception:
        pass  # Non-critical, log and move on
```

### PDF Status Polling View

```python
@login_required
@require_GET
def pdf_status(request, article_pk):
    """Return PDF status fragment for HTMX polling."""
    article = get_object_or_404(
        Article.objects.select_related(
            "issue", "issue__publication", "issue__publication__publisher"
        ),
        pk=article_pk,
    )
    _check_article_permission(request.user, article)

    return render(request, "articles/partials/_pdf_upload.html", {
        "article": article,
    })
```

### PDF Template - Status-Aware UI

```html
<!-- templates/articles/partials/_pdf_upload.html -->
<div id="pdf-section">
    {% if error %}
    <div class="alert alert-danger mb-3">
        <i class="bi bi-exclamation-triangle me-2"></i>{{ error }}
    </div>
    {% endif %}

    <!-- Status: Scanning - show spinner + polling -->
    {% if article.pdf_status == "scanning" %}
    <div class="d-flex align-items-center text-info mb-3"
         hx-get="{% url 'articles:pdf-status' article_pk=article.pk %}"
         hx-trigger="every 3s"
         hx-target="#pdf-section"
         hx-swap="outerHTML">
        <div class="spinner-border spinner-border-sm me-2" role="status"></div>
        <span>Skeniranje u toku...</span>
    </div>
    {% endif %}

    <!-- Status: Clean - show file info -->
    {% if article.pdf_status == "clean" %}
    <div class="d-flex align-items-center justify-content-between mb-3">
        <div>
            <i class="bi bi-file-earmark-pdf text-success me-2" style="font-size: 1.5rem;"></i>
            <span class="fw-bold">{{ article.pdf_original_filename }}</span>
            <span class="badge bg-success ms-2">
                <i class="bi bi-shield-check me-1"></i>Čist
            </span>
        </div>
        <button type="button" class="btn btn-sm btn-outline-danger"
                hx-post="{% url 'articles:pdf-delete' article_pk=article.pk %}"
                hx-target="#pdf-section"
                hx-swap="outerHTML"
                hx-confirm="Da li ste sigurni da želite ukloniti PDF?">
            <i class="bi bi-trash me-1"></i>Ukloni
        </button>
    </div>
    {% endif %}

    <!-- Status: Infected - show warning -->
    {% if article.pdf_status == "infected" %}
    <div class="alert alert-danger mb-3">
        <i class="bi bi-shield-exclamation me-2"></i>
        Fajl odbijen: detektovana bezbednosna pretnja. Izaberite drugi fajl.
    </div>
    {% endif %}

    <!-- Status: Scan Failed - show retry option -->
    {% if article.pdf_status == "scan_failed" %}
    <div class="alert alert-warning mb-3">
        <i class="bi bi-exclamation-triangle me-2"></i>
        Skeniranje neuspešno. Pokušajte ponovo kasnije.
    </div>
    {% endif %}

    <!-- Upload form (show when: none, infected, scan_failed, or clean for replacement) -->
    {% if article.pdf_status != "scanning" %}
    <form hx-post="{% url 'articles:pdf-upload' article_pk=article.pk %}"
          hx-target="#pdf-section"
          hx-swap="outerHTML"
          hx-encoding="multipart/form-data"
          x-data="pdfUpload()">
        {% csrf_token %}
        <div class="border rounded p-3 text-center"
             @dragover.prevent="isDragging = true"
             @dragleave.prevent="isDragging = false"
             @drop.prevent="handleDrop($event)"
             :class="isDragging ? 'border-primary bg-light' : 'border-dashed'">
            <i class="bi bi-cloud-upload" style="font-size: 2rem;"></i>
            <p class="mb-2">Prevucite PDF fajl ovde ili</p>
            <label class="btn btn-outline-primary btn-sm">
                <i class="bi bi-folder2-open me-1"></i>Izaberite fajl
                <input type="file" name="pdf_file" accept=".pdf,application/pdf"
                       class="d-none" @change="fileSelected($event)">
            </label>
            <p class="text-muted small mt-2 mb-0">Maksimalna veličina: 100 MB, samo PDF format</p>
        </div>
        <!-- Progress indicator (hidden until upload starts) -->
        <div x-show="uploading" class="mt-2">
            <div class="progress">
                <div class="progress-bar progress-bar-striped progress-bar-animated"
                     style="width: 100%">Otpremanje...</div>
            </div>
        </div>
    </form>
    {% endif %}
</div>
```

### Alpine.js PDF Upload Component

```javascript
// U article_form.html inline_javascript block (uz authorList)
function pdfUpload() {
    return {
        isDragging: false,
        uploading: false,
        handleDrop(event) {
            this.isDragging = false;
            const files = event.dataTransfer.files;
            if (files.length > 0) {
                const input = this.$el.querySelector('input[type="file"]');
                input.files = files;
                this.uploading = true;
                htmx.trigger(this.$el.closest('form'), 'submit');
            }
        },
        fileSelected(event) {
            if (event.target.files.length > 0) {
                this.uploading = true;
                htmx.trigger(event.target.closest('form'), 'submit');
            }
        }
    }
}
```

### URL Routes za PDF Endpoints

```python
# articles/urls.py - DODATI u postojeći urlpatterns

urlpatterns = [
    # ... postojeći article CRUD routes ...
    # ... postojeći author/affiliation routes ...

    # PDF HTMX endpoints (Story 3.3)
    path("<int:article_pk>/pdf/upload/", views.pdf_upload, name="pdf-upload"),
    path("<int:article_pk>/pdf/status/", views.pdf_status, name="pdf-status"),
    path("<int:article_pk>/pdf/delete/", views.pdf_delete, name="pdf-delete"),
]
```

### PDF Validator

```python
# articles/validators.py - DODATI

MAX_PDF_SIZE = 100 * 1024 * 1024  # 100 MB

def validate_pdf_file(file):
    """
    Validate uploaded PDF file.

    Checks:
    1. File extension is .pdf
    2. Content-Type is application/pdf
    3. File size <= 100 MB

    Returns: list of error strings (empty if valid)
    """
    errors = []

    # Check file extension
    if not file.name.lower().endswith('.pdf'):
        errors.append("Dozvoljeni su samo PDF fajlovi.")
        return errors

    # Check Content-Type
    if hasattr(file, 'content_type') and file.content_type != 'application/pdf':
        errors.append("Dozvoljeni su samo PDF fajlovi.")
        return errors

    # Check file size
    if file.size > MAX_PDF_SIZE:
        errors.append("Maksimalna veličina fajla je 100 MB.")
        return errors

    return errors
```

### article_form.html - Dodati PDF Sekciju

```html
<!-- U article_form.html, POSLE Author sekcije, UNUTAR is_edit bloka -->
{% if is_edit %}
<!-- ... Author Section (existing from Story 3.2) ... -->

<!-- PDF Upload Section (Story 3.3) -->
<div class="card mt-4">
    <div class="card-header">
        <h5 class="card-title mb-0">
            <i class="bi bi-file-earmark-pdf me-2"></i>PDF fajl
        </h5>
    </div>
    <div class="card-body">
        {% include "articles/partials/_pdf_upload.html" with article=object %}
    </div>
</div>
{% endif %}
```

### Django Settings za ClamAV

```python
# config/settings/base.py - DODATI na kraj fajla
# ClamAV Virus Scanning
# ------------------------------------------------------------------------------
CLAMAV_HOST = env("CLAMAV_HOST", default="localhost")
CLAMAV_PORT = env.int("CLAMAV_PORT", default=3310)
```

```python
# config/settings/test.py - DODATI
# ClamAV - disabled for tests (tasks run eager, ClamAV is mocked)
CLAMAV_HOST = "localhost"
CLAMAV_PORT = 3310
```

### Docker Compose - ClamAV servis

```yaml
# docker-compose.local.yml - DODATI servis
  clamav:
    image: clamav/clamav:latest
    ports:
      - "3310:3310"
    volumes:
      - clamav_data:/var/lib/clamav
    restart: unless-stopped

# U volumes sekciji dodati:
volumes:
  # ... postojeći volumes ...
  clamav_data: {}
```

### Publisher Scoping za PDF Endpoints

PDF endpoints koriste ISTU `_check_article_permission()` helper funkciju koja VEĆ postoji u `views.py` iz Story 3.2. NE kreirati novi helper.

### PDF Replace Flow (AC #6)

Kada se zamenjuje postojeći PDF:
1. Upload novog fajla → čuva se u `articles/pdfs/`
2. `old_pdf_path` se prosleđuje Celery tasku
3. Celery task skenira NOVI fajl
4. Ako je čist → briše se stari fajl (`_delete_old_pdf`)
5. Ako je inficiran → briši se novi fajl, stari OSTAJE netaknut

### Testovi - Mock ClamAV Pattern

```python
# articles/tests/test_pdf_upload.py

from unittest.mock import MagicMock, patch
import pytest
from django.core.files.uploadedfile import SimpleUploadedFile

@pytest.fixture
def pdf_file():
    """Create a simple PDF file for testing."""
    # Minimal valid PDF content
    content = b"%PDF-1.4\n1 0 obj\n<<\n>>\nendobj\nxref\n0 1\n0000000000 65535 f \ntrailer\n<<\n>>\nstartxref\n9\n%%EOF"
    return SimpleUploadedFile("test.pdf", content, content_type="application/pdf")

@pytest.fixture
def large_file():
    """Create a file that exceeds size limit."""
    return SimpleUploadedFile("large.pdf", b"x" * (101 * 1024 * 1024), content_type="application/pdf")

@pytest.fixture
def non_pdf_file():
    """Create a non-PDF file."""
    return SimpleUploadedFile("test.txt", b"not a pdf", content_type="text/plain")

@patch("doi_portal.articles.tasks.pyclamd")
def test_virus_scan_clean(mock_clamd, article):
    """Test clean PDF passes virus scan."""
    mock_cd = MagicMock()
    mock_cd.ping.return_value = True
    mock_cd.scan_stream.return_value = None  # None = clean
    mock_clamd.ClamdNetworkSocket.return_value = mock_cd

    from doi_portal.articles.tasks import virus_scan_pdf_task
    virus_scan_pdf_task(article.id)

    article.refresh_from_db()
    assert article.pdf_status == "clean"

@patch("doi_portal.articles.tasks.pyclamd")
def test_virus_scan_infected(mock_clamd, article):
    """Test infected PDF is detected and removed."""
    mock_cd = MagicMock()
    mock_cd.ping.return_value = True
    mock_cd.scan_stream.return_value = {"stream": ("FOUND", "Eicar-Test-Signature")}
    mock_clamd.ClamdNetworkSocket.return_value = mock_cd

    from doi_portal.articles.tasks import virus_scan_pdf_task
    virus_scan_pdf_task(article.id)

    article.refresh_from_db()
    assert article.pdf_status == "infected"
    assert not article.pdf_file
```

### Fajlovi za kreiranje (NOVI)

```
doi_portal/doi_portal/articles/tasks.py                           # Celery task za virus skeniranje
templates/articles/partials/_pdf_upload.html                       # PDF upload/status HTMX partial
```

### Fajlovi za modifikaciju (POSTOJEĆI)

- `doi_portal/doi_portal/articles/models.py` - Dodati PdfStatus enum, pdf_status i pdf_original_filename polja
- `doi_portal/doi_portal/articles/validators.py` - Dodati validate_pdf_file funkciju
- `doi_portal/doi_portal/articles/views.py` - Dodati pdf_upload, pdf_status, pdf_delete FBV-ove
- `doi_portal/doi_portal/articles/urls.py` - Dodati PDF routes
- `doi_portal/doi_portal/templates/articles/article_form.html` - Dodati PDF sekciju (edit mode)
- `doi_portal/doi_portal/articles/tests/factories.py` - Eventualno dodati pdf_file factory helper
- `doi_portal/config/settings/base.py` - Dodati CLAMAV_HOST, CLAMAV_PORT
- `doi_portal/config/settings/test.py` - Dodati CLAMAV test settings
- `doi_portal/docker-compose.local.yml` - Dodati ClamAV servis
- `doi_portal/pyproject.toml` / `uv.lock` - Dodati pyclamd zavisnost

### Srpski Karakteri (OBAVEZNO - videti project-context.md)

Svi UI tekstovi MORAJU koristiti ispravne srpske dijakritike:

| Kontekst | ISPRAVNO |
|----------|----------|
| Status NONE | "Nema PDF-a" |
| Status UPLOADING | "Otpremanje" |
| Status SCANNING | "Skeniranje" |
| Status CLEAN | "Čist" |
| Status INFECTED | "Inficiran" |
| Status SCAN_FAILED | "Skeniranje neuspešno" |
| Upload button | "Izaberite fajl" |
| Drag text | "Prevucite PDF fajl ovde ili" |
| Size limit | "Maksimalna veličina: 100 MB, samo PDF format" |
| Success | "PDF uspešno otpremljen" |
| Infected | "Fajl odbijen: detektovana bezbednosna pretnja" |
| Scan failed | "Skeniranje neuspešno, pokušajte ponovo kasnije" |
| Remove button | "Ukloni" |
| Remove confirm | "Da li ste sigurni da želite ukloniti PDF?" |
| Validation | "Dozvoljeni su samo PDF fajlovi." |
| Size validation | "Maksimalna veličina fajla je 100 MB." |
| Section header | "PDF fajl" |

### Anti-Patterns (ZABRANJENO)

```python
# POGREŠNO - Kreirati novi Django app za PDF upload
# doi_portal/uploads/  # NE! PDF upload ide u articles app

# POGREŠNO - Koristiti CBV za upload endpoint
class PdfUploadView(CreateView):  # NE! Koristi FBV

# POGREŠNO - Vraćati JSON za HTMX response
return JsonResponse({"status": "scanning"})  # NE! Vraćaj HTML fragment

# POGREŠNO - Sinhrani virus scan u view-u
def pdf_upload(request, article_pk):
    scan_result = clamd.scan(file)  # NE! Koristi Celery task

# POGREŠNO - Zaboraviti publisher scoping na PDF endpoints
def pdf_upload(request, article_pk):
    article = Article.objects.get(pk=article_pk)  # NE bez permission check!

# POGREŠNO - Brisati stari PDF pre nego što novi prođe skeniranje
# Stari PDF se briše TEK nakon uspešnog skeniranja novog

# POGREŠNO - Ignorisati ClamAV connection error
# UVEK retry sa exponential backoff, ili scan_failed status

# POGREŠNO - Čuvati fajl bez validacije tipa i veličine
# UVEK validirati pre čuvanja na disk

# POGREŠNO - Koristiti python-magic za MIME type detekciju
# python-magic zahteva libmagic system dependency - koristiti extension + content_type fallback

# POGREŠNO - Dodati novi Article migration bez navođenja rednog broja
# Migration MORA biti 0003_article_pdf_status.py (nakon 0002 iz Story 3.2)
```

### Previous Story Learnings (Story 3.1 i 3.2)

1. **`_check_article_permission()`** - VEĆ postoji u views.py. Koristi ga za sve PDF endpoints.
2. **HTMX CSRF token** - VEĆ rešeno u article_form.html (htmx:configRequest event listener). NE duplirati.
3. **Alpine.js CDN** - VEĆ uključen u article_form.html javascript block. NE duplirati.
4. **`enctype="multipart/form-data"`** - Potrebno za upload formu. Ovo je NOVA forma unutar PDF sekcije, ne modifikacija glavne article forme.
5. **SortableJS + htmx:afterSwap** - VEĆ postoji u article_form.html. Paziti da nova PDF sekcija ne konflikta sa autor sekcijom.
6. **Template include pattern** - `{% include %}` sa `with` za prosleđivanje context-a. Konzistentno sa `_author_list.html` pattern-om.
7. **`select_related` chain** - Uvek uključiti "issue", "issue__publication", "issue__publication__publisher" za publisher scoping.
8. **791 testova** prošlo u Story 3.2 - NE SME se regresirati.
9. **auditlog** - Article je VEĆ registrovan. Promene pdf_file i pdf_status se automatski beleže.
10. **admin_base.html** - VEĆ ima HTMX uključen. NE dodavati HTMX CDN ponovo.

### Git Commit Pattern

```
story-3-3: feat(articles): implementiraj PDF Upload sa ClamAV virus skeniranjem putem Celery taska (Story 3.3)
```

### NFR Requirements

- **NFR11:** Virus scan pre prihvatanja - ClamAV skenira svaki PDF pre trajnog čuvanja
- **NFR3:** Admin panel stranice < 5 sekundi - HTMX polling za status minimizira page load impact
- **NFR4:** PDF download - direktan link (priprema za Story 4.6)

### Dependencies (Python/Django)

Nova Python zavisnost:
- **pyclamd** - Python ClamAV daemon client (`uv add pyclamd`)

VEĆ postoje u projektu:
- Celery 5.6.2 (background tasks)
- structlog (logging)
- Redis (Celery broker)

Frontend dependencies (CDN):
- Alpine.js 3.15.3 - VEĆ u article_form.html
- HTMX 2.0.8 - VEĆ u admin_base.html
- Bootstrap Icons - VEĆ u admin_base.html

Docker:
- **clamav/clamav:latest** - ClamAV Docker image za lokalni development

### S3 Storage Napomena

Trenutna implementacija koristi lokalni Django FileField storage (`articles/pdfs/`). Migracija na S3 (django-storages + boto3) je planirana za produkciju ali NIJE deo ove priče. Kod je dizajniran da radi sa bilo kojim Django storage backend-om jer koristi:
- `article.pdf_file.read()` za čitanje (storage-agnostic)
- `article.pdf_file.delete()` za brisanje (storage-agnostic)
- `default_storage.exists()` i `default_storage.delete()` za stare fajlove

Kad se doda S3, samo treba promeniti `DEFAULT_FILE_STORAGE` u settings-u.

### Project Structure Notes

- Celery task ide u `doi_portal/doi_portal/articles/tasks.py` (NE u core/tasks.py - specifičan za articles)
- HTMX partial ide u `doi_portal/doi_portal/templates/articles/partials/_pdf_upload.html`
- PdfStatus enum ide u `doi_portal/doi_portal/articles/models.py` (uz ostale enume)
- PDF validator ide u `doi_portal/doi_portal/articles/validators.py` (uz ORCID validator)
- URL namespace ostaje `articles` (isti app)
- Migration fajl: `doi_portal/doi_portal/articles/migrations/0003_article_pdf_status.py`

### References

- [Source: epics.md#Story 3.3: PDF Upload with Virus Scanning]
- [Source: prd.md#5. Article Management - FR25 (Upload PDF)]
- [Source: prd.md#Security - NFR11 (Virus scan)]
- [Source: prd.md#Technical Constraints - Max File Size 100 MB]
- [Source: architecture.md#File Storage & Processing - Upload Flow]
- [Source: architecture.md#Infrastructure - ClamAV self-hosted]
- [Source: project-context.md#File Upload Flow]
- [Source: project-context.md#Celery Tasks - Retry Pattern]
- [Source: project-context.md#HTMX Pravila]
- [Source: project-context.md#Naming Konvencije]
- [Source: project-context.md#Lokalizacija - Srpski Karakteri]
- [Source: 3-2-author-management-with-drag-drop.md - HTMX FBV patterns, publisher scoping, template patterns]
- [Source: 3-1-article-model-basic-metadata-entry.md - Article model, article_form.html, Alpine.js patterns]
- [Source: articles/models.py - Article.pdf_file existing field]
- [Source: articles/views.py - _check_article_permission helper, existing FBV patterns]
- [Source: config/settings/base.py - Celery configuration]
- [Source: config/settings/test.py - CELERY_TASK_ALWAYS_EAGER=True]
- [Source: config/celery_app.py - Celery autodiscover_tasks]

## Dev Agent Record

### Agent Model Used

Claude Opus 4.5 (claude-opus-4-5-20251101)

### Debug Log References

- Celery retry tests required special handling: `CELERY_TASK_ALWAYS_EAGER=True` causes `self.retry()` to immediately re-execute, propagating exceptions. Resolved by using `patch.object` to simulate `MaxRetriesExceededError` directly.
- pyclamd module imported at module level in tasks.py to enable proper mocking via `@patch("doi_portal.articles.tasks.pyclamd")`.
- Tests require `uv run` to ensure pyclamd and structlog are available from the uv virtual environment.

### Completion Notes List

- Task 1: PdfStatus TextChoices enum added with 6 statuses. pdf_status and pdf_original_filename fields added to Article. Migration 0003 created.
- Task 2: validate_pdf_file() function added to validators.py checking extension, content_type, and size (100MB max).
- Task 3: virus_scan_pdf_task Celery task created in tasks.py with pyclamd integration, retry logic (max_retries=3, 60s delay), structlog logging.
- Task 4: pdf_upload FBV created - validates file, saves to Article, triggers async scan, returns HTMX fragment.
- Task 5: pdf_status FBV created - returns status fragment with HTMX polling (every 3s while scanning).
- Task 6: pdf_delete FBV created - deletes file from storage, resets all PDF fields.
- Task 7: URL routes added for pdf-upload, pdf-status, pdf-delete endpoints.
- Task 8: _pdf_upload.html template created with drag & drop (Alpine.js), progress bar, status indicators, Serbian UI text. article_form.html updated with PDF section below Authors.
- Task 9: pyclamd and structlog added via uv. ClamAV settings added to base.py and test.py.
- Task 10: ClamAV service added to docker-compose.local.yml with volume and celeryworker dependency.
- Task 11: 46 comprehensive tests covering models, validators, views, Celery tasks, permissions, URL routing.

### File List

**New Files:**
- `doi_portal/doi_portal/articles/tasks.py` - Celery task for ClamAV virus scanning
- `doi_portal/doi_portal/articles/migrations/0003_article_pdf_status.py` - Migration for pdf_status and pdf_original_filename
- `doi_portal/doi_portal/templates/articles/partials/_pdf_upload.html` - HTMX partial for PDF upload/status UI
- `doi_portal/doi_portal/articles/tests/test_pdf_upload.py` - 46 comprehensive tests

**Modified Files:**
- `doi_portal/doi_portal/articles/models.py` - Added PdfStatus enum, pdf_status and pdf_original_filename fields
- `doi_portal/doi_portal/articles/validators.py` - Added validate_pdf_file() function
- `doi_portal/doi_portal/articles/views.py` - Added pdf_upload, pdf_status, pdf_delete FBV views
- `doi_portal/doi_portal/articles/urls.py` - Added PDF HTMX endpoint routes
- `doi_portal/doi_portal/templates/articles/article_form.html` - Added PDF section in edit mode, pdfUpload() Alpine.js component
- `doi_portal/config/settings/base.py` - Added CLAMAV_HOST and CLAMAV_PORT settings
- `doi_portal/config/settings/test.py` - Added ClamAV test settings and CELERY_TASK_EAGER_PROPAGATES
- `doi_portal/docker-compose.local.yml` - Added ClamAV service with volume
- `doi_portal/pyproject.toml` - Added pyclamd and structlog dependencies
- `doi_portal/uv.lock` - Updated lock file
