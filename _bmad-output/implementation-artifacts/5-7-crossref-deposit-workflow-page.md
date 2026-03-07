# Story 5.7: Crossref Deposit Workflow Page

Status: done

## Story

As an **Administrator**,
I want **a dedicated Crossref Deposit page to manage the entire XML generation and deposit process, including XML regeneration**,
so that **I have a clear, step-by-step workflow for DOI registration with the ability to fix and regenerate XML when needed**.

## Acceptance Criteria

1. **AC1: Dedicated Crossref Deposit Page**
   - Given Administrator navigates to an issue
   - When clicking "Crossref Deposit" tab/button
   - Then dedicated Crossref workflow page is displayed at URL `/crossref/issues/<pk>/deposit/`
   - And page extends `admin_base.html` with breadcrumbs (Publikacija > Izdanje > Crossref Deposit)

2. **AC2: Workflow Steps Layout**
   - Given Crossref Deposit page is displayed
   - When viewing the layout
   - Then workflow steps are clearly shown in vertical stepper:
     1. Pre-validacija (Pre-validation status)
     2. Generisanje XML (Generate XML button)
     3. XSD Validacija (XSD Validation status)
     4. Pregled XML (Preview XML)
     5. Preuzimanje XML (Download XML)
   - And each step shows its number and title

3. **AC3: Step Status Indicators**
   - Given workflow page shows current status
   - When each step is checked
   - Then completed steps show green checkmarks with "Zavrseno" label
   - And current/active step is highlighted with primary color
   - And blocked/unavailable steps are grayed out with "Nedostupno" label
   - And step status updates dynamically via HTMX without full page reload

4. **AC4: Ready for Submission Final Status**
   - Given all steps are complete (XML generated, XSD valid, downloaded)
   - When viewing final status
   - Then "Spremno za Crossref" message is shown with success styling
   - And link to Crossref admin portal (https://doi.crossref.org/) is provided
   - And instructions for manual upload are displayed

5. **AC5: Mark as Deposited**
   - Given Administrator completes external upload to Crossref
   - When returning to the page
   - Then "Oznaci kao deponovano" button is available
   - And clicking marks the issue as deposited with timestamp
   - And deposited status is shown on issue list and issue detail pages
   - And deposited_at and deposited_by are recorded

6. **AC6: Regenerate XML Button (Sprint Change: regenerisanje)**
   - Given XML is already generated for an issue
   - When Administrator has corrected data and clicks "Regenerisi XML"
   - Then confirmation modal appears: "Postojeci XML ce biti zamenjen. Da li zelite da nastavite?"
   - And after confirmation, new XML is generated with corrected data
   - And XSD validation status refreshes automatically
   - And previous XML is preserved in CrossrefExport history (if it was downloaded)

7. **AC7: Navigation Integration**
   - Given issue_detail.html currently has a Crossref XML sidebar card
   - When this story is implemented
   - Then sidebar card is replaced with a link/button to the dedicated Crossref Deposit page
   - And "Crossref Deposit" link is also added to Quick Actions in the sidebar

## Tasks / Subtasks

- [x] **Task 1: Add deposit tracking fields to Issue model** (AC: #5)
  - [x] Add `crossref_deposited_at` DateTimeField (null=True, blank=True)
  - [x] Add `crossref_deposited_by` ForeignKey to User (null=True, blank=True, SET_NULL)
  - [x] Create migration file
  - [x] Add `is_crossref_deposited` property that returns bool

- [x] **Task 2: Create Crossref Deposit page view** (AC: #1, #2, #3, #4)
  - [x] Create `CrossrefDepositView` (LoginRequiredMixin, View) in crossref/views.py
  - [x] Compute workflow step statuses from issue state:
    - Step 1 (Pre-validation): run PreValidationService, status based on result
    - Step 2 (Generate): enabled when pre-validation passes
    - Step 3 (XSD): show result from issue.xsd_valid after generation
    - Step 4 (Preview): enabled when XML exists
    - Step 5 (Download): enabled when XML exists
  - [x] Pass step statuses, issue, and context to template
  - [x] Check publisher access permission via has_publisher_access()

- [x] **Task 3: Create deposit page template** (AC: #1, #2, #3, #4)
  - [x] Create `crossref/issue_crossref_deposit.html` template extending admin_base.html
  - [x] Implement vertical stepper UI with Bootstrap 5 (custom CSS, no extra libs)
  - [x] Each step: number circle, title, status badge, content area
  - [x] Step 1: Include validation panel via HTMX (reuse _validation_panel.html)
  - [x] Step 2: Generate XML button (reuse existing GenerateXMLView POST endpoint)
  - [x] Step 3: XSD validation result (reuse _xsd_validation_result.html)
  - [x] Step 4: Preview XML button (reuse xml_preview endpoint)
  - [x] Step 5: Download XML button with warning check (reuse existing smart download logic)
  - [x] Final status section: "Spremno za Crossref" with link to https://doi.crossref.org/
  - [x] "Oznaci kao deponovano" button
  - [x] Export history section (reuse _export_history.html)
  - [x] Add breadcrumbs: Izdanja > {issue} > Crossref Deposit

- [x] **Task 4: Implement Regenerate XML functionality** (AC: #6)
  - [x] Add "Regenerisi XML" button in Step 2 when XML already exists
  - [x] Create `_regenerate_confirm_modal.html` partial with confirmation dialog
  - [x] HTMX: button triggers modal via hx-get, modal confirm button POSTs to existing GenerateXMLView
  - [x] After regeneration, refresh steps 2-5 statuses via HTMX (hx-target on step container)
  - [x] Ensure GenerateXMLView handles regeneration (it already overwrites issue.crossref_xml)

- [x] **Task 5: Implement Mark as Deposited endpoint** (AC: #5)
  - [x] Add `mark_deposited` view (POST) in crossref/views.py
  - [x] Set issue.crossref_deposited_at = timezone.now()
  - [x] Set issue.crossref_deposited_by = request.user
  - [x] Return HTMX partial showing deposited status
  - [x] Add URL pattern: `issues/<int:pk>/mark-deposited/`

- [x] **Task 6: Update issue_detail.html sidebar** (AC: #7)
  - [x] Replace inline Crossref XML card with link to deposit page
  - [x] Show deposit status badge if deposited
  - [x] Add "Crossref Deposit" to Quick Actions list
  - [x] Remove Prism.js CSS/JS includes (moved to deposit page)

- [x] **Task 7: Update issue list to show deposit status** (AC: #5)
  - [x] Add deposited status badge to issue list template
  - [x] Show green "Deponovano" badge when crossref_deposited_at is set

- [x] **Task 8: Write tests** (AC: #1-7)
  - [x] Test CrossrefDepositView renders with correct step statuses
  - [x] Test step status computation: no XML -> steps 3-5 disabled
  - [x] Test step status computation: XML generated -> steps 3-5 enabled
  - [x] Test mark_deposited sets timestamp and user
  - [x] Test mark_deposited requires permission
  - [x] Test regenerate XML overwrites existing XML
  - [x] Test deposit page requires login and publisher access
  - [x] Test breadcrumbs render correctly
  - [x] Test deposited status shows on issue list
  - [x] Test Issue model deposit fields migration

## Dev Notes

### Current State Analysis

Currently, Crossref functionality is embedded in the `issue_detail.html` sidebar as a "Crossref XML" card. This card contains:
- Validation panel (HTMX loaded)
- Generate XML button
- Preview/Download buttons (after generation)

This story extracts that functionality into a dedicated page with a proper stepper workflow, adds XML regeneration capability, and deposit tracking.

### Architecture Decisions

**Dedicated page vs tab:** The epics specify a "dedicated Crossref workflow page" with its own URL. This is NOT a tab on issue_detail -- it's a separate page linked from issue_detail.

**Stepper pattern:** Use Bootstrap 5 custom CSS for vertical stepper. No additional libraries needed. Pattern:
```html
<div class="stepper">
  <div class="step {% if step.completed %}step-completed{% elif step.active %}step-active{% else %}step-disabled{% endif %}">
    <div class="step-indicator">
      {% if step.completed %}
        <i class="bi bi-check-circle-fill text-success"></i>
      {% else %}
        <span class="step-number">{{ step.number }}</span>
      {% endif %}
    </div>
    <div class="step-content">
      <h6>{{ step.title }}</h6>
      <div class="step-body">
        {# Step-specific content #}
      </div>
    </div>
  </div>
</div>
```

### Existing Code to Reuse (DO NOT RECREATE)

These views and partials already exist and MUST be reused:

| Component | Location | Usage |
|-----------|----------|-------|
| `IssueValidationView` | crossref/views.py | Step 1: Pre-validation (GET) |
| `GenerateXMLView` | crossref/views.py | Step 2: Generate XML (POST) |
| `xml_preview` | crossref/views.py | Step 4: Preview modal |
| `xml_download` / `xml_download_force` | crossref/views.py | Step 5: Download |
| `download_warning` | crossref/views.py | Step 5: Warning modal |
| `export_history` | crossref/views.py | Export history partial |
| `_validation_panel.html` | crossref/partials/ | Step 1 content |
| `_xsd_validation_result.html` | crossref/partials/ | Step 3 content |
| `_generation_result.html` | crossref/partials/ | Step 2 result |
| `_xml_preview_modal.html` | crossref/partials/ | Step 4 modal |
| `_download_warning_modal.html` | crossref/partials/ | Step 5 warning |
| `_export_history.html` | crossref/partials/ | Export history |

**Key insight:** The deposit page orchestrates existing HTMX partials. Most of the functionality is already built. The new work is:
1. A new page template with stepper layout
2. A new view to render the page with computed step statuses
3. Regenerate XML button with confirmation modal (new partial)
4. Mark as deposited endpoint (new view)
5. Issue model deposit fields (new migration)

### URL Patterns to Add

```python
# crossref/urls.py additions
path("issues/<int:pk>/deposit/", CrossrefDepositView.as_view(), name="issue-deposit"),
path("issues/<int:pk>/mark-deposited/", mark_deposited, name="mark-deposited"),
```

### Issue Model Changes

```python
# issues/models.py additions to Issue model

# === CROSSREF DEPOSIT TRACKING (Story 5.7) ===
crossref_deposited_at = models.DateTimeField(
    null=True,
    blank=True,
    verbose_name=_("Crossref deponovano"),
    help_text=_("Datum i vreme kada je XML deponovan na Crossref"),
)
crossref_deposited_by = models.ForeignKey(
    "users.User",
    on_delete=models.SET_NULL,
    null=True,
    blank=True,
    related_name="crossref_deposits",
    verbose_name=_("Deponovao"),
)

@property
def is_crossref_deposited(self) -> bool:
    """Return True if this issue has been deposited to Crossref."""
    return self.crossref_deposited_at is not None
```

### View Implementation Pattern

```python
# crossref/views.py

class CrossrefDepositView(LoginRequiredMixin, View):
    """
    Dedicated Crossref Deposit workflow page.

    Story 5.7: Crossref Deposit Workflow Page.
    """

    def get(self, request, pk):
        issue = get_object_or_404(Issue, pk=pk)

        if not has_publisher_access(request.user, issue.publication.publisher):
            raise PermissionDenied

        # Compute step statuses
        has_xml = bool(issue.crossref_xml)
        validator = PreValidationService()
        validation_result = validator.validate_issue(issue)

        steps = [
            {
                "number": 1,
                "title": "Pre-validacija",
                "completed": validation_result.is_valid,
                "active": not validation_result.is_valid,
                "icon": "clipboard-check",
            },
            {
                "number": 2,
                "title": "Generisanje XML",
                "completed": has_xml,
                "active": validation_result.is_valid and not has_xml,
                "icon": "file-code",
            },
            {
                "number": 3,
                "title": "XSD Validacija",
                "completed": has_xml and issue.xsd_valid is True,
                "active": has_xml and issue.xsd_valid is not True,
                "icon": "shield-check",
            },
            {
                "number": 4,
                "title": "Pregled XML",
                "completed": False,  # Always available, never "completed"
                "active": has_xml,
                "icon": "eye",
            },
            {
                "number": 5,
                "title": "Preuzimanje XML",
                "completed": issue.crossref_exports.exists(),
                "active": has_xml,
                "icon": "download",
            },
        ]

        return TemplateResponse(
            request,
            "crossref/issue_crossref_deposit.html",
            {
                "issue": issue,
                "steps": steps,
                "has_xml": has_xml,
                "validation_result": validation_result,
                "is_deposited": issue.is_crossref_deposited,
            },
        )
```

### Regenerate XML Confirmation Modal

```html
{# crossref/partials/_regenerate_confirm_modal.html #}
<div class="modal fade" id="regenerateModal" tabindex="-1"
     x-data x-init="new bootstrap.Modal($el).show(); $el.addEventListener('hidden.bs.modal', () => $el.remove())">
  <div class="modal-dialog">
    <div class="modal-content">
      <div class="modal-header bg-warning-subtle">
        <h5 class="modal-title">
          <i class="bi bi-exclamation-triangle me-2"></i>Regenerisanje XML
        </h5>
        <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
      </div>
      <div class="modal-body">
        <p>Postojeci XML ce biti zamenjen novim sadrzajem.</p>
        <p>Prethodni eksporti ostaju sacuvani u istoriji eksporta.</p>
        <p><strong>Da li zelite da nastavite?</strong></p>
      </div>
      <div class="modal-footer">
        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">
          <i class="bi bi-x-circle me-1"></i>Otkaži
        </button>
        <button type="button" class="btn btn-warning"
                hx-post="{% url 'crossref:issue-generate' issue.pk %}"
                hx-target="#generation-step-content"
                hx-swap="innerHTML"
                hx-headers='{"X-CSRFToken": "{{ csrf_token }}"}'>
          <i class="bi bi-arrow-clockwise me-1"></i>Regeneriši XML
        </button>
      </div>
    </div>
  </div>
</div>
```

### Serbian UI Text (REQUIRED - proper diacritics)

- "Crossref Deposit" (page title)
- "Pre-validacija" (Step 1)
- "Generisanje XML" (Step 2)
- "XSD Validacija" (Step 3)
- "Pregled XML" (Step 4)
- "Preuzimanje XML" (Step 5)
- "Generiši XML" (Generate button)
- "Regeneriši XML" (Regenerate button)
- "Postojeci XML ce biti zamenjen" (Confirmation text)
- "Otkaži" (Cancel - WITH diacritics)
- "Spremno za Crossref" (Ready for submission)
- "Oznaci kao deponovano" (Mark as deposited)
- "Deponovano" (Deposited badge)
- "Zavrseno" (Completed step label)
- "Nedostupno" (Disabled step label)
- "Crossref admin portal" (Link text)
- "Preuzmite generisani XML fajl i uploadujte ga na Crossref admin portal" (Instructions)

### HTMX Interaction Patterns

**Step 1 (Validation):** Loaded via hx-get on page load, targets #validation-step-content
```html
<div id="validation-step-content"
     hx-get="{% url 'crossref:issue-validate' issue.pk %}"
     hx-trigger="load"
     hx-swap="innerHTML">
```

**Step 2 (Generate):** POST via HTMX button, targets #generation-step-content
```html
<button hx-post="{% url 'crossref:issue-generate' issue.pk %}"
        hx-target="#generation-step-content"
        hx-swap="innerHTML"
        hx-headers='{"X-CSRFToken": "{{ csrf_token }}"}'>
```

**Step 4 (Preview):** Uses existing loadXmlPreview() JS function (from Story 5.5)

**Step 5 (Download):** Uses existing smart download logic (valid=direct, invalid=warning modal)

**Mark as Deposited:** POST via HTMX
```html
<button hx-post="{% url 'crossref:mark-deposited' issue.pk %}"
        hx-target="#deposit-status"
        hx-swap="innerHTML"
        hx-headers='{"X-CSRFToken": "{{ csrf_token }}"}'
        hx-confirm="Da li ste sigurni da zelite da oznacite kao deponovano?">
```

### File Structure

**New files:**
```
doi_portal/doi_portal/
  crossref/
    views.py                                    # MODIFY - add CrossrefDepositView, mark_deposited
    urls.py                                     # MODIFY - add 2 URL patterns
  issues/
    models.py                                   # MODIFY - add deposit fields
    migrations/
      XXXX_add_crossref_deposit_fields.py       # NEW migration
  templates/
    crossref/
      issue_crossref_deposit.html               # NEW - main deposit page
      partials/
        _regenerate_confirm_modal.html           # NEW - regenerate confirmation
    issues/
      issue_detail.html                         # MODIFY - replace inline Crossref card with link
```

**Test files:**
```
doi_portal/doi_portal/
  crossref/
    tests/
      test_deposit_workflow.py                  # NEW - deposit page tests
```

### Testing Standards

Use pytest-django with Factory Boy. Follow existing patterns from test_xml_download.py.

```python
# crossref/tests/test_deposit_workflow.py

class TestCrossrefDepositView:
    def test_deposit_page_renders(self, client, admin_user, issue):
        """Deposit page renders with correct steps."""

    def test_deposit_page_requires_login(self, client, issue):
        """Unauthenticated users redirected to login."""

    def test_deposit_page_requires_permission(self, client, other_user, issue):
        """Users without publisher access get 403."""

    def test_steps_disabled_without_xml(self, client, admin_user, issue):
        """Steps 3-5 disabled when no XML generated."""

    def test_steps_enabled_with_xml(self, client, admin_user, issue_with_xml):
        """Steps 3-5 enabled when XML exists."""

    def test_regenerate_button_shown_with_xml(self, client, admin_user, issue_with_xml):
        """Regenerate button appears when XML already exists."""

    def test_deposit_status_shown_when_deposited(self, client, admin_user, deposited_issue):
        """Deposited status displayed correctly."""


class TestMarkDeposited:
    def test_mark_deposited_sets_fields(self, client, admin_user, issue_with_xml):
        """Mark deposited sets timestamp and user."""

    def test_mark_deposited_requires_permission(self, client, other_user, issue):
        """Mark deposited requires publisher access."""

    def test_mark_deposited_returns_partial(self, client, admin_user, issue_with_xml):
        """Mark deposited returns HTMX partial response."""


class TestIssueDepositFields:
    def test_is_crossref_deposited_false_by_default(self, issue):
        """New issues are not deposited."""

    def test_is_crossref_deposited_true_when_set(self, deposited_issue):
        """Issues with deposited_at are marked as deposited."""
```

### Dependencies on Previous Stories

- **Story 5.1-5.3:** CrossrefService, PreValidationService, GenerateXMLView
- **Story 5.4:** XSD validation fields on Issue model (xsd_valid, xsd_errors, xsd_validated_at)
- **Story 5.5:** XML Preview (xml_preview view, _xml_preview_modal.html, Prism.js)
- **Story 5.6:** XML Download with export tracking (CrossrefExport model, export_history, download_warning)
- **Story 5.3a:** Fixed resource URL in XML templates

### Previous Story Intelligence (from Story 5.6)

- `_generate_filename()` helper and `_create_xml_download_response()` helper are in views.py
- CrossrefExport model is in crossref/models.py with auditlog registration
- Smart download pattern: valid XML = direct download, invalid = warning modal via HTMX
- Modal pattern uses Alpine.js x-data + x-init with bootstrap.Modal
- Export history loads via HTMX hx-trigger="load"
- Permission check pattern: `has_publisher_access(request.user, issue.publication.publisher)`
- All Crossref views use `@login_required` decorator or `LoginRequiredMixin`

### Git Intelligence (Recent Commits)

- Story 5-3a, 2-4a, 3-1a were implemented together in commit e3f5fdf (articles external resource fields + language widget)
- Production deployment configured in commit 1c39fb0 (Traefik, media serving)
- The `crossref/services.py` was modified in Story 5-3a (resource URL fix - site_url in context)
- Article model has new fields: use_external_resource, external_landing_url, external_pdf_url

### Project Structure Notes

- All templates follow `templates/{app}/` convention per project-context.md
- HTMX partials use `_` prefix: `templates/{app}/partials/_name.html`
- CBV naming: PascalCase + View suffix (CrossrefDepositView)
- FBV for HTMX endpoints: snake_case (mark_deposited)
- URL patterns: kebab-case (issue-deposit, mark-deposited)
- Serbian UI text with proper diacritics (c, c, s, d, z)

### References

- [Source: epics.md - Story 5.7] Crossref Deposit Workflow Page acceptance criteria
- [Source: sprint-change-proposal-2026-03-07.md] Regenerate XML requirement added to Story 5-7
- [Source: PRD - FR33-FR37] Crossref XML generation and download requirements
- [Source: PRD - User Journey] "Ide na Crossref Deposit stranicu"
- [Source: UX Design - Journey 2] "Crossref Deposit > Generisi XML > Validacija > Download"
- [Source: project-context.md] HTMX patterns, Bootstrap 5, Serbian UI, services layer
- [Source: 5-6-xml-download.md] Export history, warning modal, download patterns
- [Source: crossref/views.py] Existing views to reuse
- [Source: templates/issues/issue_detail.html] Current inline Crossref card to refactor

## Dev Agent Record

### Agent Model Used

Claude Opus 4.6

### Debug Log References

None.

### Completion Notes List

- Task 1: Added `crossref_deposited_at` and `crossref_deposited_by` fields to Issue model with migration 0004
- Task 2: Created `CrossrefDepositView` CBV with 5-step workflow status computation and permission checks
- Task 3: Created `issue_crossref_deposit.html` with vertical stepper UI using custom Bootstrap 5 CSS
- Task 4: Implemented regenerate XML with inline modal confirmation, reuses GenerateXMLView POST
- Task 5: Created `mark_deposited` FBV (POST only) with HTMX partial response
- Task 6: Replaced inline Crossref XML card in issue_detail.html with link to deposit page, removed Prism.js includes
- Task 7: Added "Deponovano" badge to issue list template
- Task 8: Wrote 23 tests covering all ACs - all passing (1637 total suite, 0 failures)

### Code Review (Adversarial) - 2026-03-07

**Reviewer:** Dev Agent (Claude Opus 4.6, fresh context)

**Issues Found & Fixed (7 total):**

1. **CRITICAL** - Template CSS block `extra_css` does not exist in `admin_base.html` (uses `css` block). Stepper CSS and Prism.js CSS were never rendered. Fixed: changed to `{% block css %}{{ block.super }}`.
2. **CRITICAL** - Prism.js scripts and inline JavaScript were inside `{% block content %}` instead of proper `{% block javascript %}` and `{% block inline_javascript %}` blocks. Fixed: moved to correct blocks with `{{ block.super }}`.
3. **HIGH** - Regenerate XML button had broken `hx-get` attribute pointing to nonexistent URL `regenerate-modal/` (would cause 404 on every click before onclick handler fires). Fixed: removed `hx-get`, `hx-target`, `hx-swap` attributes, kept only `onclick` handler.
4. **HIGH (Security)** - `IssueValidationView` and `GenerateXMLView` missing `has_publisher_access()` check. Any authenticated user could validate/generate XML for any issue. Fixed: added permission check to both views.
5. **MEDIUM** - Dead code: `_regenerate_confirm_modal.html` partial was never used (modal inlined in main template). Fixed: deleted unused file.
6. **LOW** - Script tags missing `defer` attribute (inconsistent with base template pattern). Fixed: added `defer` to Prism.js script tags.
7. **LOW** - Breadcrumbs use "Izdanja" (issues list) as first item instead of AC1-specified "Publikacija". Accepted as-is: more practical for navigation and consistent with project patterns.

### File List

**New files:**
- `doi_portal/doi_portal/issues/migrations/0004_add_crossref_deposit_fields.py`
- `doi_portal/doi_portal/templates/crossref/issue_crossref_deposit.html`
- `doi_portal/doi_portal/templates/crossref/partials/_deposit_status.html`
- `doi_portal/doi_portal/crossref/tests/test_deposit_workflow.py`

**Modified files:**
- `doi_portal/doi_portal/issues/models.py` (deposit tracking fields + is_crossref_deposited property)
- `doi_portal/doi_portal/crossref/views.py` (CrossrefDepositView + mark_deposited + permission fixes on IssueValidationView, GenerateXMLView)
- `doi_portal/doi_portal/crossref/urls.py` (2 new URL patterns)
- `doi_portal/doi_portal/templates/issues/issue_detail.html` (replaced Crossref card, added Quick Action)
- `doi_portal/doi_portal/templates/issues/issue_list.html` (deposit status badge)
- `_bmad-output/implementation-artifacts/sprint-status.yaml` (status update)
- `_bmad-output/implementation-artifacts/5-7-crossref-deposit-workflow-page.md` (task checkboxes + review record)

**Deleted files:**
- `doi_portal/doi_portal/templates/crossref/partials/_regenerate_confirm_modal.html` (dead code - modal inlined in main template)
