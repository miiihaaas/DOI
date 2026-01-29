# Story 2.3a: Crossref Depositor Fields Migration

Status: ready-for-dev

## Story

As an **Administrator**,
I want **Publisher and Publication models to have Crossref-compliant depositor and conference fields**,
So that **XML generation in Epic 5 can produce valid Crossref deposits with proper head metadata**.

## Background

After reviewing Crossref XML schema 5.4.0 documentation, we identified missing required fields that were not captured in the initial PRD:

1. **Publisher Depositor Fields** - Required for Crossref XML `<head>` element:
   - `depositor_name` - Name of the organization depositing DOIs
   - `depositor_email` - Email for deposit notifications
   - `registrant` - Name of the DOI registrant organization

2. **Publication Conference Fields** - Required for complete `<event_metadata>`:
   - `conference_date_end` - End date for multi-day conferences
   - `conference_number` - Conference occurrence number (e.g., "15th annual")

These fields are optional now (blank=True) because existing publishers don't have this data yet. They will become required for XML generation in Epic 5.

## Acceptance Criteria

1. **Given** the Publisher model exists
   **When** reviewing the model fields
   **Then** it includes new Crossref depositor fields:
   - `depositor_name` (CharField, max_length=255, blank=True)
   - `depositor_email` (EmailField, blank=True)
   - `registrant` (CharField, max_length=255, blank=True)

2. **Given** the Publication model exists
   **When** reviewing the model fields (CONFERENCE type)
   **Then** it includes new conference fields:
   - `conference_date_end` (DateField, null=True, blank=True)
   - `conference_number` (PositiveIntegerField, null=True, blank=True)

3. **Given** the Django migrations are created
   **When** migrations are applied to the database
   **Then** migrations complete successfully without data loss

4. **Given** the Publisher admin form
   **When** editing a publisher
   **Then** depositor fields appear in a new "Crossref Depositor" fieldset

5. **Given** the Publication admin form for CONFERENCE type
   **When** editing a conference publication
   **Then** new fields appear in the conference fieldset alongside existing fields

6. **Given** the existing test suite
   **When** running all tests
   **Then** all existing tests pass without modification

## Tasks / Subtasks

- [ ] Task 1: Add Publisher Model Fields (AC: #1)
  - [ ] 1.1 Add `depositor_name` field (CharField, max_length=255, blank=True)
  - [ ] 1.2 Add `depositor_email` field (EmailField, blank=True)
  - [ ] 1.3 Add `registrant` field (CharField, max_length=255, blank=True)
  - [ ] 1.4 Add Serbian verbose_name labels with proper diacritics

- [ ] Task 2: Add Publication Model Fields (AC: #2)
  - [ ] 2.1 Add `conference_date_end` field (DateField, null=True, blank=True)
  - [ ] 2.2 Add `conference_number` field (PositiveIntegerField, null=True, blank=True)
  - [ ] 2.3 Add Serbian verbose_name labels with proper diacritics
  - [ ] 2.4 Add help_text explaining field purpose

- [ ] Task 3: Create and Apply Migrations (AC: #3)
  - [ ] 3.1 Run `makemigrations publishers` for depositor fields
  - [ ] 3.2 Run `makemigrations publications` for conference fields
  - [ ] 3.3 Run `migrate` to apply both migrations
  - [ ] 3.4 Verify migrations are reversible

- [ ] Task 4: Update Publisher Admin Form (AC: #4)
  - [ ] 4.1 Add "Crossref Depositor" fieldset to PublisherForm
  - [ ] 4.2 Group fields: depositor_name, depositor_email, registrant
  - [ ] 4.3 Add fieldset heading in Serbian

- [ ] Task 5: Update Publication Admin Form (AC: #5)
  - [ ] 5.1 Add conference_date_end to conference partial template
  - [ ] 5.2 Add conference_number to conference partial template
  - [ ] 5.3 Update form field ordering for logical grouping

- [ ] Task 6: Write Unit Tests (AC: #1-#6)
  - [ ] 6.1 Test Publisher model has new depositor fields
  - [ ] 6.2 Test depositor_email validates as EmailField
  - [ ] 6.3 Test Publication model has new conference fields
  - [ ] 6.4 Test conference_number accepts positive integers only
  - [ ] 6.5 Test all existing tests still pass
  - [ ] 6.6 Test admin forms render new fieldsets

## Dev Notes

### CRITICAL: This is a Patch Story

This story adds missing Crossref compliance fields identified after PRD review. It is intentionally minimal - only adding fields, not changing existing functionality.

### Publisher Model Changes

```python
# publishers/models.py - Add after website field, before doi_prefix

# Crossref Depositor fields (for XML Head)
depositor_name = models.CharField(
    _("Naziv deponenta"),
    max_length=255,
    blank=True,
    help_text=_("Naziv organizacije koja deponuje DOI (za Crossref XML)"),
)
depositor_email = models.EmailField(
    _("Email deponenta"),
    blank=True,
    help_text=_("Email za notifikacije o depozitu"),
)
registrant = models.CharField(
    _("Registrant"),
    max_length=255,
    blank=True,
    help_text=_("Naziv organizacije registranta DOI"),
)
```

### Publication Model Changes

```python
# publications/models.py - Add after conference_date field

conference_date_end = models.DateField(
    _("Datum završetka konferencije"),
    blank=True,
    null=True,
    help_text=_("Završni datum za višednevne konferencije"),
)
conference_number = models.PositiveIntegerField(
    _("Broj konferencije"),
    blank=True,
    null=True,
    help_text=_("Redni broj konferencije (npr. 15 za '15. godišnja')"),
)
```

### Admin Form Fieldset Pattern

```python
# publishers/forms.py - Update fieldsets

fieldsets = {
    'basic': ['name', 'description', 'logo'],
    'contact': ['contact_email', 'contact_phone', 'website'],
    'crossref_depositor': ['depositor_name', 'depositor_email', 'registrant'],  # NEW
    'doi': ['doi_prefix'],
}
```

### Template Update Pattern

```html
<!-- publications/partials/_type_fields_conference.html -->
<!-- Add after conference_date field -->
<div class="col-md-6">
    <div class="mb-3">
        <label for="id_conference_date_end" class="form-label">Datum završetka</label>
        <input type="date" name="conference_date_end" id="id_conference_date_end"
               class="form-control"
               value="{{ form.conference_date_end.value|default:'' }}">
        <div class="form-text">Za višednevne konferencije</div>
    </div>
</div>
<div class="col-md-6">
    <div class="mb-3">
        <label for="id_conference_number" class="form-label">Broj konferencije</label>
        <input type="number" name="conference_number" id="id_conference_number"
               class="form-control" min="1"
               value="{{ form.conference_number.value|default:'' }}">
        <div class="form-text">npr. 15 za "15. godišnja konferencija"</div>
    </div>
</div>
```

### Crossref XML Context

These fields map to Crossref XML 5.4.0 schema:

**Publisher depositor fields -> XML `<head>` element:**
```xml
<head>
    <doi_batch_id>...</doi_batch_id>
    <timestamp>...</timestamp>
    <depositor>
        <depositor_name>{{ publisher.depositor_name }}</depositor_name>
        <email_address>{{ publisher.depositor_email }}</email_address>
    </depositor>
    <registrant>{{ publisher.registrant }}</registrant>
</head>
```

**Publication conference fields -> XML `<event_metadata>` element:**
```xml
<event_metadata>
    <conference_name>{{ publication.conference_name }}</conference_name>
    <conference_acronym>{{ publication.conference_acronym }}</conference_acronym>
    <conference_number>{{ publication.conference_number }}</conference_number>
    <conference_location>{{ publication.conference_location }}</conference_location>
    <conference_date start_day="..." start_month="..." start_year="..."
                     end_day="..." end_month="..." end_year="..."/>
</event_metadata>
```

### Files to Modify

- `doi_portal/doi_portal/publishers/models.py` - Add 3 depositor fields
- `doi_portal/doi_portal/publications/models.py` - Add 2 conference fields
- `doi_portal/doi_portal/publishers/forms.py` - Add Crossref Depositor fieldset
- `doi_portal/doi_portal/templates/publications/partials/_type_fields_conference.html` - Add new fields
- `doi_portal/doi_portal/publishers/tests/test_models.py` - Add field tests
- `doi_portal/doi_portal/publications/tests/test_models.py` - Add field tests

### Files Created by Migrations

- `doi_portal/doi_portal/publishers/migrations/0002_publisher_depositor_fields.py`
- `doi_portal/doi_portal/publications/migrations/0002_publication_conference_fields.py`

### Anti-Patterns to Avoid

```python
# WRONG - Making fields required immediately
depositor_name = models.CharField(max_length=255)  # No blank=True

# CORRECT - Optional for now, Epic 5 will handle validation
depositor_name = models.CharField(max_length=255, blank=True)

# WRONG - Missing null=True for date/integer fields
conference_date_end = models.DateField(blank=True)

# CORRECT - Date and integer fields need null=True for blank
conference_date_end = models.DateField(blank=True, null=True)

# WRONG - Using ASCII Serbian
verbose_name=_("Naziv deponenta")  # Good

# WRONG - Missing help_text for new fields
depositor_email = models.EmailField(blank=True)

# CORRECT - Help text explains purpose
depositor_email = models.EmailField(blank=True, help_text=_("..."))
```

### Testing Strategy

```python
# publishers/tests/test_models.py

@pytest.mark.django_db
class TestPublisherDepositorFields:
    """Test new Crossref depositor fields."""

    def test_depositor_fields_exist(self):
        """Verify depositor fields are on Publisher model."""
        publisher = PublisherFactory()
        assert hasattr(publisher, 'depositor_name')
        assert hasattr(publisher, 'depositor_email')
        assert hasattr(publisher, 'registrant')

    def test_depositor_fields_optional(self):
        """Verify depositor fields can be blank."""
        publisher = PublisherFactory(
            depositor_name='',
            depositor_email='',
            registrant='',
        )
        publisher.full_clean()  # Should not raise

    def test_depositor_email_validates(self):
        """Verify depositor_email validates as email."""
        publisher = PublisherFactory.build(depositor_email='invalid')
        with pytest.raises(ValidationError):
            publisher.full_clean()


# publications/tests/test_models.py

@pytest.mark.django_db
class TestPublicationConferenceFields:
    """Test new conference fields."""

    def test_conference_fields_exist(self):
        """Verify new conference fields are on Publication model."""
        publication = PublicationFactory(
            publication_type=PublicationType.CONFERENCE
        )
        assert hasattr(publication, 'conference_date_end')
        assert hasattr(publication, 'conference_number')

    def test_conference_number_positive(self):
        """Verify conference_number only accepts positive integers."""
        publication = PublicationFactory.build(
            publication_type=PublicationType.CONFERENCE,
            conference_number=-1,
        )
        with pytest.raises(ValidationError):
            publication.full_clean()
```

### Git Commit Pattern

Expected commit message:
```
story-2-3a: feat(models): add Crossref depositor and conference fields (Story 2.3a)

- Add depositor_name, depositor_email, registrant to Publisher
- Add conference_date_end, conference_number to Publication
- Update admin forms with new fieldsets
- All fields optional (blank=True) for backward compatibility
```

### References

- [Source: Crossref XML Schema 5.4.0 - head element]
- [Source: Crossref XML Schema 5.4.0 - event_metadata element]
- [Source: publishers/models.py - Existing Publisher model]
- [Source: publications/models.py - Existing Publication model]
- [Source: architecture.md - Data Architecture]

## Dependencies

**Depends On:** None (standalone patch)

**Blocks:** Epic 5 - Crossref Integration (XML generation will use these fields)

## Definition of Done

- [ ] All 6 Acceptance Criteria verified
- [ ] All Tasks/Subtasks completed
- [ ] Django migrations created and applied
- [ ] Unit tests added for new fields
- [ ] Full test suite passes (no regressions)
- [ ] Admin forms display new fieldsets correctly
- [ ] Code review approved
