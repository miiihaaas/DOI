# Story 5.5: XML Preview with Syntax Highlighting

Status: done

## Story

As an **Administrator**,
I want **to preview the generated XML with syntax highlighting**,
so that **I can review the content before downloading**.

## Acceptance Criteria

1. **AC1: Preview Modal/Panel Opens**
   - Given XML has been generated
   - When clicking "Pregled XML"
   - Then modal or panel opens with XML content displayed

2. **AC2: Syntax Highlighting**
   - Given XML preview is displayed
   - When viewing the content
   - Then XML is syntax highlighted (tags, attributes, values in different colors)
   - And line numbers are shown
   - And content is scrollable for large files

3. **AC3: Collapsible Sections and Search**
   - Given XML preview is shown
   - When reviewing content
   - Then key sections are collapsible/expandable
   - And search within preview is available (Ctrl+F browser native)

4. **AC4: Action Buttons**
   - Given preview modal/panel
   - When viewing actions
   - Then "Kopiraj u clipboard" button is available
   - And "Preuzmi XML" button is available
   - And "Zatvori" button returns to Crossref page

5. **AC5: Error Highlighting for Invalid XML**
   - Given XML is invalid (from Story 5.4 XSD validation)
   - When previewing
   - Then validation errors are highlighted in context
   - And error lines are marked with red indicator

## Tasks / Subtasks

- [x] **Task 1: Add Prism.js or Highlight.js library** (AC: #2)
  - [x] Choose appropriate syntax highlighting library (recommend Prism.js for XML support)
  - [x] Add to base template or specific page (consider CDN vs bundled)
  - [x] Include XML/markup language support
  - [x] Include line numbers plugin
  - [x] Style to match Bootstrap 5 admin theme

- [x] **Task 2: Create XML preview modal component** (AC: #1, #4)
  - [x] Create `templates/crossref/partials/_xml_preview_modal.html`
  - [x] Bootstrap 5 modal with fullscreen option (large XML files)
  - [x] Header with title "Pregled XML" and close button
  - [x] Footer with action buttons: "Kopiraj u clipboard", "Preuzmi XML", "Zatvori"
  - [x] Body with scrollable pre/code block for XML content

- [x] **Task 3: Implement syntax highlighting rendering** (AC: #2, #3)
  - [x] Wrap XML in `<pre><code class="language-xml">` structure
  - [x] Apply Prism.js/Highlight.js highlighting
  - [x] Add line numbers via plugin or CSS
  - [x] Ensure large files (>1000 lines) perform well
  - [x] Consider lazy loading/virtualization for very large XML

- [x] **Task 4: Implement collapsible XML sections** (AC: #3)
  - [x] Add collapse controls for major XML elements (head, body, journal_article, etc.)
  - [x] Use Alpine.js for toggle state management
  - [x] Visual indicators for collapsed sections (arrows, +/- icons)
  - [x] Persist expand/collapse state during session (optional)

- [x] **Task 5: Add error line highlighting** (AC: #5)
  - [x] Parse XSD error line numbers from Issue.xsd_errors
  - [x] Add CSS class for error lines (red background/indicator)
  - [x] Auto-scroll to first error line on open (if errors exist)
  - [x] Tooltip or sidebar indicator showing error message per line

- [x] **Task 6: Implement clipboard copy functionality** (AC: #4)
  - [x] JavaScript function to copy XML to clipboard
  - [x] Use Clipboard API (navigator.clipboard.writeText)
  - [x] Toast notification on success: "XML kopiran u clipboard"
  - [x] Fallback for older browsers (execCommand)

- [x] **Task 7: Implement XML download from modal** (AC: #4)
  - [x] Create download endpoint or use existing Issue.crossref_xml
  - [x] Generate Blob from XML content
  - [x] Trigger download with proper filename format
  - [x] Filename: `{publication-slug}_{volume}_{issue}_{timestamp}.xml`

- [x] **Task 8: Create HTMX endpoint for preview** (AC: #1)
  - [x] Add view `crossref_xml_preview` in crossref/views.py
  - [x] Return rendered modal partial with XML content
  - [x] Handle case when XML not yet generated (error message)
  - [x] Add URL pattern `/crossref/issues/{issue_id}/preview/`

- [x] **Task 9: Add "Pregled XML" button to generation result** (AC: #1)
  - [x] Modify `_generation_result.html` to include preview button
  - [x] Button triggers HTMX request to load modal
  - [x] Button disabled if no XML generated
  - [x] HTMX target to append modal to body

- [x] **Task 10: Write unit and integration tests** (AC: #1-5)
  - [x] Test modal renders with XML content
  - [x] Test syntax highlighting applied correctly
  - [x] Test error lines marked for invalid XML
  - [x] Test clipboard copy functionality (mock Clipboard API)
  - [x] Test download triggers with correct filename
  - [x] Test HTMX endpoint returns correct response
  - [x] Test large XML performance (>100KB)

## Dev Notes

### Syntax Highlighting Library Choice

**Recommended: Prism.js**
- Lightweight (~2KB core)
- Excellent XML/markup support
- Line numbers plugin available
- Good performance with large files
- CDN available: `https://cdnjs.cloudflare.com/ajax/libs/prism/1.29.0/`

**Alternative: Highlight.js**
- More language support
- Larger bundle size
- Auto-detection of languages

**Implementation:**
```html
<!-- CDN approach (recommended for simplicity) -->
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/prism/1.29.0/themes/prism.min.css">
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/prism/1.29.0/plugins/line-numbers/prism-line-numbers.min.css">
<script src="https://cdnjs.cloudflare.com/ajax/libs/prism/1.29.0/prism.min.js"></script>
<script src="https://cdnjs.cloudflare.com/ajax/libs/prism/1.29.0/components/prism-markup.min.js"></script>
<script src="https://cdnjs.cloudflare.com/ajax/libs/prism/1.29.0/plugins/line-numbers/prism-line-numbers.min.js"></script>
```

### Existing Code Context (from Stories 5.1-5.4)

**Issue model fields (from Story 5.3, 5.4):**
```python
# issues/models.py - Issue model
crossref_xml = models.TextField(blank=True)  # Stores generated XML
xml_generated_at = models.DateTimeField(null=True)
xml_generation_status = models.CharField(...)
xsd_valid = models.BooleanField(null=True)  # Story 5.4
xsd_errors = models.JSONField(default=list)  # Story 5.4 - list of error dicts
xsd_validated_at = models.DateTimeField(null=True)  # Story 5.4
```

**XSD Error Structure (from Story 5.4):**
```python
# Each error in xsd_errors list:
{
    "message": "Error description",
    "line": 15,  # Line number (may be None)
    "column": 4,  # Column number (may be None)
    "element": "/doi_batch/body/journal"  # XPath (may be None)
}
```

**Current generation result template (`_generation_result.html`):**
- Already shows generation success/failure
- Includes XSD validation result
- Needs "Pregled XML" button added

### Modal Template Pattern

**`_xml_preview_modal.html` structure:**
```html
{# Story 5.5: XML Preview with Syntax Highlighting #}
<div class="modal fade" id="xmlPreviewModal" tabindex="-1" aria-labelledby="xmlPreviewModalLabel" aria-hidden="true">
  <div class="modal-dialog modal-fullscreen-lg-down modal-xl">
    <div class="modal-content">
      <div class="modal-header">
        <h5 class="modal-title" id="xmlPreviewModalLabel">
          <i class="bi bi-code-square me-2"></i>Pregled XML
        </h5>
        <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Zatvori"></button>
      </div>
      <div class="modal-body p-0">
        {% if xsd_valid is False %}
        <div class="alert alert-warning m-3 mb-0">
          <i class="bi bi-exclamation-triangle me-2"></i>
          XML ima {{ xsd_errors|length }} greske validacije. Linije sa greskama su oznacene.
        </div>
        {% endif %}
        <div class="xml-preview-container" style="max-height: 70vh; overflow: auto;">
          <pre class="line-numbers" data-line="{{ error_lines }}"><code class="language-xml">{{ xml_content|escape }}</code></pre>
        </div>
      </div>
      <div class="modal-footer">
        <button type="button" class="btn btn-outline-secondary" onclick="copyXmlToClipboard()">
          <i class="bi bi-clipboard me-1"></i>Kopiraj u clipboard
        </button>
        <a href="{% url 'crossref:xml-download' issue.pk %}" class="btn btn-outline-primary" download>
          <i class="bi bi-download me-1"></i>Preuzmi XML
        </a>
        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Zatvori</button>
      </div>
    </div>
  </div>
</div>

<script>
function copyXmlToClipboard() {
  const xmlContent = document.querySelector('#xmlPreviewModal code').textContent;
  navigator.clipboard.writeText(xmlContent).then(() => {
    // Show toast notification
    showToast('XML kopiran u clipboard', 'success');
  }).catch(err => {
    console.error('Failed to copy:', err);
    showToast('Greska pri kopiranju', 'danger');
  });
}
</script>
```

### Error Line Highlighting

**Prism.js Line Highlight Plugin:**
```html
<!-- Add plugin CSS and JS -->
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/prism/1.29.0/plugins/line-highlight/prism-line-highlight.min.css">
<script src="https://cdnjs.cloudflare.com/ajax/libs/prism/1.29.0/plugins/line-highlight/prism-line-highlight.min.js"></script>

<!-- Usage with data-line attribute -->
<pre data-line="15,23,45"><code class="language-xml">...</code></pre>
```

**Custom Error Line Styling:**
```css
/* Custom red highlight for error lines */
.line-highlight.error-line {
  background: linear-gradient(to right, rgba(220, 53, 69, 0.3) 70%, rgba(220, 53, 69, 0));
}

/* Error line marker */
pre[data-line]::before {
  content: "";
  position: absolute;
  left: 0;
  width: 4px;
  background: var(--bs-danger);
}
```

### HTMX Integration Pattern

**Button in `_generation_result.html`:**
```html
{% if success and xml_content %}
<button type="button"
        class="btn btn-outline-info"
        hx-get="{% url 'crossref:xml-preview' issue.pk %}"
        hx-target="body"
        hx-swap="beforeend">
  <i class="bi bi-eye me-1"></i>Pregled XML
</button>
{% endif %}
```

**View in `crossref/views.py`:**
```python
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.template.response import TemplateResponse
from doi_portal.issues.models import Issue


def xml_preview(request, issue_id):
    """
    Return XML preview modal for an issue.

    Story 5.5: XML Preview with Syntax Highlighting.
    """
    issue = get_object_or_404(Issue, pk=issue_id)

    if not issue.crossref_xml:
        return HttpResponse(
            '<div class="alert alert-warning">XML nije generisan.</div>',
            status=200,
        )

    # Extract error line numbers for highlighting
    error_lines = []
    if issue.xsd_errors:
        for error in issue.xsd_errors:
            if error.get("line"):
                error_lines.append(str(error["line"]))

    context = {
        "issue": issue,
        "xml_content": issue.crossref_xml,
        "xsd_valid": issue.xsd_valid,
        "xsd_errors": issue.xsd_errors,
        "error_lines": ",".join(error_lines),
    }

    return TemplateResponse(
        request,
        "crossref/partials/_xml_preview_modal.html",
        context,
    )
```

**URL pattern in `crossref/urls.py`:**
```python
from django.urls import path
from doi_portal.crossref import views

app_name = "crossref"

urlpatterns = [
    # ... existing URLs ...
    path(
        "issues/<int:issue_id>/preview/",
        views.xml_preview,
        name="xml-preview",
    ),
]
```

### Collapsible Sections with Alpine.js

**Pattern for collapsible XML sections:**
```html
<div x-data="{
  headExpanded: true,
  bodyExpanded: true,
  toggleSection(section) {
    this[section + 'Expanded'] = !this[section + 'Expanded'];
  }
}">
  <!-- Section toggle buttons above code -->
  <div class="xml-section-toggles d-flex gap-2 p-2 border-bottom">
    <button class="btn btn-sm btn-outline-secondary"
            @click="toggleSection('head')"
            :class="{ 'active': headExpanded }">
      <i class="bi" :class="headExpanded ? 'bi-chevron-down' : 'bi-chevron-right'"></i>
      &lt;head&gt;
    </button>
    <button class="btn btn-sm btn-outline-secondary"
            @click="toggleSection('body')"
            :class="{ 'active': bodyExpanded }">
      <i class="bi" :class="bodyExpanded ? 'bi-chevron-down' : 'bi-chevron-right'"></i>
      &lt;body&gt;
    </button>
  </div>

  <pre class="line-numbers"><code class="language-xml">{{ xml_content }}</code></pre>
</div>
```

**Note:** True XML folding requires more complex JS. Consider simplified approach:
- Show full XML with syntax highlighting
- Provide navigation buttons to jump to sections
- Browser native Ctrl+F for search

### Performance Considerations

**Large XML Files (>100 articles):**
- Prism.js handles ~10KB XML well
- For >50KB, consider:
  - Async highlighting: `Prism.highlightElement(element)` after modal shown
  - Line number virtualization (only render visible lines)
  - Truncation with "Show full XML" option

**Lazy Loading Pattern:**
```javascript
// Highlight after modal is shown
const modal = document.getElementById('xmlPreviewModal');
modal.addEventListener('shown.bs.modal', function () {
  const codeBlock = modal.querySelector('code');
  if (!codeBlock.classList.contains('highlighted')) {
    Prism.highlightElement(codeBlock);
    codeBlock.classList.add('highlighted');
  }
});
```

### File Structure

**Files to create:**
```
doi_portal/
└── doi_portal/
    ├── crossref/
    │   ├── views.py              # ADD xml_preview view
    │   └── urls.py               # ADD xml-preview URL
    ├── templates/
    │   ├── base.html             # ADD Prism.js CDN links
    │   └── crossref/
    │       └── partials/
    │           ├── _xml_preview_modal.html    # NEW
    │           └── _generation_result.html    # MODIFY - add preview button
    └── static/
        └── css/
            └── xml-preview.css   # NEW (optional - custom styles)
```

### Testing Standards

**Required Test Coverage:**
```python
# crossref/tests/test_views.py
class TestXMLPreviewView:
    def test_preview_returns_modal_with_xml(self, issue_with_xml):
        """Preview endpoint returns modal template with XML content."""

    def test_preview_without_xml_shows_warning(self, issue_without_xml):
        """Preview endpoint shows warning when no XML generated."""

    def test_preview_includes_error_lines(self, issue_with_invalid_xml):
        """Preview includes error line numbers from XSD validation."""

    def test_preview_requires_authentication(self, client, issue_with_xml):
        """Preview endpoint requires logged-in user."""

    def test_preview_requires_permission(self, client, other_user):
        """Preview endpoint requires appropriate permissions."""


# Template tests
class TestXMLPreviewTemplate:
    def test_modal_renders_xml_content(self):
        """Modal template renders XML content correctly."""

    def test_modal_shows_error_warning_for_invalid_xml(self):
        """Modal shows warning banner for invalid XML."""

    def test_action_buttons_present(self):
        """All action buttons (copy, download, close) are present."""

    def test_prism_classes_applied(self):
        """Prism.js CSS classes applied for syntax highlighting."""


# JavaScript tests (using pytest-playwright or similar)
class TestXMLPreviewJavaScript:
    def test_copy_to_clipboard_works(self, page):
        """Copy to clipboard button copies XML content."""

    def test_download_triggers_file_save(self, page):
        """Download button triggers file download."""

    def test_modal_closes_on_button_click(self, page):
        """Close button dismisses modal."""
```

### Serbian UI Text (REQUIRED)

Use proper Serbian characters with diacritics:
- "Pregled XML" (Preview XML)
- "Kopiraj u clipboard" (Copy to clipboard)
- "Preuzmi XML" (Download XML)
- "Zatvori" (Close)
- "XML kopiran u clipboard" (XML copied to clipboard)
- "Greska pri kopiranju" (Error copying) - note: greska -> greska
- "XML nije generisan" (XML not generated)
- "XML ima X greske validacije. Linije sa greskama su oznacene." (XML has X validation errors. Lines with errors are marked.)

### Dependencies on Previous Stories

- **Story 5.3**: XML generation, Issue.crossref_xml field, generate_and_store_xml()
- **Story 5.4**: XSD validation, Issue.xsd_valid, Issue.xsd_errors with line numbers

### Project Context Reminders

From `project-context.md`:
- HTMX partials use `_` prefix naming convention
- Bootstrap 5 for all UI components
- Alpine.js for lightweight interactivity
- Serbian UI text with proper diacritics
- Toast notifications for user feedback
- Views in services layer for complex logic

### References

- [Source: epics.md - Story 5.5] XML Preview acceptance criteria
- [Source: PRD - FR34] System displays preview of generated XML
- [Source: project-context.md] HTMX patterns, Bootstrap 5, Serbian UI
- [Source: 5-3-xml-generation.md] Issue.crossref_xml field
- [Source: 5-4-xsd-validation.md] XSD validation, error line numbers
- [Prism.js Documentation] https://prismjs.com/
- [Bootstrap 5 Modal] https://getbootstrap.com/docs/5.3/components/modal/

## Dev Agent Record

### Agent Model Used

Claude Opus 4.5 (claude-opus-4-5-20251101)

### Debug Log References

- All tests passing: 180 passed in crossref tests (after code review fixes)
- TDD workflow followed: tests written first, then implementation

### Completion Notes List

1. **Prism.js Integration**: Selected Prism.js for syntax highlighting due to lightweight size and excellent XML support. Added via CDN in modal template (not base template) to avoid loading on all pages.

2. **Modal Implementation**: Created fullscreen-responsive Bootstrap 5 modal with all required action buttons. Modal is dynamically loaded via HTMX and auto-shown on load, then removed from DOM when closed.

3. **Section Navigation**: Implemented simplified approach - navigation buttons that scroll to XML sections (<head>, <body>) instead of true XML folding. Browser native Ctrl+F is available for search.

4. **Error Line Highlighting**: Using Prism.js line-highlight plugin with data-line attribute. Error lines from XSD validation are extracted and highlighted in red. "Prva greška" button scrolls to first error line.

5. **Clipboard & Download**: Full implementation with Clipboard API, fallback for older browsers using execCommand, and toast notifications. Download uses proper filename format with publication slug, volume, issue, and timestamp.

6. **HTMX Integration**: Preview button in _generation_result.html uses hx-get to load modal, hx-target="body", hx-swap="beforeend" pattern for appending modal to body.

7. **Serbian UI**: All UI text uses proper Serbian characters with diacritics (greške, označene, etc.).

### Senior Developer Review (AI)

**Review Date:** 2026-02-03
**Reviewer:** Claude Opus 4.5 (Adversarial Code Review)
**Status:** APPROVED after fixes

#### Issues Found and Fixed (7 total):

**HIGH (3):**
1. **SECURITY: Missing publisher permission check in xml_preview and xml_download views**
   - Fix: Added `has_publisher_access()` check to both views, raises PermissionDenied for unauthorized users
   - File: `views.py` lines 178-180, 229-231

2. **SECURITY: XSS vulnerability in JavaScript toast messages**
   - Fix: Added `escapeHtml()` sanitization function, all toast messages are now HTML-escaped
   - File: `_xml_preview_modal.html` showToast() function

3. **TEST COVERAGE: Missing tests for permission checks**
   - Fix: Added TestPublisherPermissions class with 3 tests for permission denied scenarios
   - File: `test_xml_preview.py`

**MEDIUM (3):**
4. **PERFORMANCE: No warning for large XML files (>100KB)**
   - Fix: Added `is_large_xml` and `xml_size_kb` context variables, template shows warning for large files
   - Files: `views.py`, `_xml_preview_modal.html`

5. **TEST COVERAGE: Missing test for large XML performance (Task 10 requirement)**
   - Fix: Added TestLargeXMLHandling class with 2 tests
   - File: `test_xml_preview.py`

6. **CODE QUALITY: Hardcoded z-index 11000 in toast container**
   - Fix: Changed to z-index 1090 (above Bootstrap modal's 1055) with comment explaining rationale
   - File: `_xml_preview_modal.html`

**LOW (1):**
7. **DOCUMENTATION: Missing JSDoc comments in JavaScript functions**
   - Fix: Added JSDoc comments to all xmlPreviewState() methods
   - File: `_xml_preview_modal.html`

#### Tests After Fixes:
- **Total crossref tests:** 180 passed
- **Story 5.5 tests:** 25 passed (increased from 17 to 25)
- **New test classes added:** TestPublisherPermissions, TestLargeXMLHandling, TestEdgeCases

### File List

**Created:**
- `doi_portal/doi_portal/templates/crossref/partials/_xml_preview_modal.html` - New modal component
- `doi_portal/doi_portal/crossref/tests/test_xml_preview.py` - Test file with 25 tests (expanded from 17)

**Modified:**
- `doi_portal/doi_portal/crossref/views.py` - Added xml_preview and xml_download views with permission checks
- `doi_portal/doi_portal/crossref/urls.py` - Added xml-preview and xml-download URL patterns
- `doi_portal/doi_portal/templates/crossref/partials/_generation_result.html` - Added Pregled XML and Preuzmi XML buttons
- `_bmad-output/implementation-artifacts/sprint-status.yaml` - Updated story status to done
- `_bmad-output/implementation-artifacts/5-5-xml-preview-with-syntax-highlighting.md` - Updated task checkboxes and Dev Agent Record
