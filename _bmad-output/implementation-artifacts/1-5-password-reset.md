# Story 1.5: Password Reset

Status: done

## Story

As a **user who forgot their password**,
I want **to reset my password via email**,
So that **I can regain access to my account**.

## Acceptance Criteria

1. **Given** a registered user
   **When** clicking "Forgot Password" on login page
   **Then** a password reset form is displayed requesting email

2. **Given** valid email is submitted
   **When** the form is processed
   **Then** a password reset email is sent with secure token
   **And** user sees confirmation message (regardless of email existence for security)

3. **Given** user clicks the reset link in email
   **When** the link is valid and not expired
   **Then** a new password form is displayed

4. **Given** new password meets policy requirements
   **When** the password reset form is submitted
   **Then** password is updated with argon2 hashing
   **And** user is redirected to login page with success message
   **And** all existing sessions are invalidated

## Tasks / Subtasks

- [x] Task 1: Configure django-allauth Password Reset Settings (AC: #1, #2)
  - [x] 1.1 Verify password reset URLs are configured (allauth default)
  - [x] 1.2 Configure ACCOUNT_PASSWORD_RESET_TIMEOUT to 3600 (1 hour)
  - [x] 1.3 Configure email backend for password reset emails
  - [x] 1.4 Verify SITE_ID is configured for email links

- [x] Task 2: Create Bootstrap 5 Password Reset Request Template (AC: #1, #2)
  - [x] 2.1 Create templates/account/password_reset.html extending base.html
  - [x] 2.2 Style form with Bootstrap 5 (form-control, btn-primary)
  - [x] 2.3 Add email input field with proper label
  - [x] 2.4 Add "Back to Login" link
  - [x] 2.5 Display validation errors with Bootstrap alert styling
  - [x] 2.6 Center form on page with responsive container

- [x] Task 3: Create Password Reset Sent Confirmation Template (AC: #2)
  - [x] 3.1 Create templates/account/password_reset_done.html
  - [x] 3.2 Display security-conscious confirmation message
  - [x] 3.3 Style with Bootstrap 5 (card, alert-info)
  - [x] 3.4 Add link to return to login page

- [x] Task 4: Configure Password Reset Email Template (AC: #2)
  - [x] 4.1 Create templates/account/email/password_reset_key_message.txt
  - [x] 4.2 Include secure reset link with token
  - [x] 4.3 Add expiration time notice (1 hour)
  - [x] 4.4 Add security notice (ignore if not requested)
  - [x] 4.5 Use Serbian language for email content

- [x] Task 5: Create New Password Form Template (AC: #3, #4)
  - [x] 5.1 Create templates/account/password_reset_from_key.html
  - [x] 5.2 Style form with Bootstrap 5
  - [x] 5.3 Add password and password confirmation fields
  - [x] 5.4 Display password policy requirements (min 8 chars, letters+numbers)
  - [x] 5.5 Add client-side password match validation (Alpine.js)
  - [x] 5.6 Display validation errors with Bootstrap alert styling

- [x] Task 6: Create Password Reset Success Template (AC: #4)
  - [x] 6.1 Create templates/account/password_reset_from_key_done.html
  - [x] 6.2 Display success message
  - [x] 6.3 Style with Bootstrap 5 (card, alert-success)
  - [x] 6.4 Add "Go to Login" button

- [x] Task 7: Implement Session Invalidation on Password Reset (AC: #4)
  - [x] 7.1 Create signal handler for password_changed signal
  - [x] 7.2 Clear all user sessions on password reset
  - [x] 7.3 Register signal in users app ready() method

- [x] Task 8: Configure Password Policy Validation (AC: #4)
  - [x] 8.1 Verify AUTH_PASSWORD_VALIDATORS in settings (Cookiecutter default)
  - [x] 8.2 Ensure MinimumLengthValidator is set to 8 characters
  - [x] 8.3 Verify CommonPasswordValidator is enabled
  - [x] 8.4 Verify NumericPasswordValidator is disabled (allow numeric+letters combo)

- [x] Task 9: Create Invalid/Expired Token Template (AC: #3)
  - [x] 9.1 Create or override templates/account/password_reset_from_key.html for invalid token state
  - [x] 9.2 Display user-friendly error message for expired/invalid links
  - [x] 9.3 Add "Request New Reset Link" button
  - [x] 9.4 Style with Bootstrap 5 (card, alert-warning)

- [x] Task 10: Write Unit Tests (AC: #1, #2, #3, #4)
  - [x] 10.1 Test password reset page renders with form
  - [x] 10.2 Test valid email submission shows confirmation
  - [x] 10.3 Test invalid email format shows error
  - [x] 10.4 Test confirmation shown even for non-existent email (security)
  - [x] 10.5 Test password reset email is sent for valid user
  - [x] 10.6 Test reset link with valid token shows password form
  - [x] 10.7 Test reset link with expired token shows error
  - [x] 10.8 Test reset link with invalid token shows error
  - [x] 10.9 Test password update succeeds with valid password
  - [x] 10.10 Test password policy enforced (min length, etc.)
  - [x] 10.11 Test sessions invalidated after password reset
  - [x] 10.12 Test redirect to login after successful reset

## Dev Notes

### CRITICAL: django-allauth Password Reset is Pre-configured

**IMPORTANT:** Cookiecutter Django with django-allauth already has password reset functionality. Do NOT:
- Create custom password reset views (use allauth views)
- Override allauth URLs for password reset (already configured)
- Implement custom token generation (use allauth's secure tokens)

**DO:**
- Override templates in templates/account/
- Configure settings in config/settings/base.py
- Use allauth's password_changed signal for session invalidation

### django-allauth Password Reset URLs (Already Configured)

From allauth, these URLs are already available:
- `/accounts/password/reset/` - Request password reset
- `/accounts/password/reset/done/` - Confirmation page after request
- `/accounts/password/reset/key/<uidb36>-<key>/` - Reset form with token
- `/accounts/password/reset/key/done/` - Success page after reset

### Password Reset Configuration

```python
# config/settings/base.py

# Password reset timeout (1 hour = 3600 seconds)
# This is the Django default, but explicitly set for clarity
PASSWORD_RESET_TIMEOUT = 3600  # seconds

# Allauth settings (some may already exist)
ACCOUNT_PASSWORD_MIN_LENGTH = 8  # Minimum password length
```

### Password Policy (AUTH_PASSWORD_VALIDATORS)

Cookiecutter Django includes validators in base.py. Verify these exist:

```python
AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
        "OPTIONS": {"min_length": 8},
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
]
```

### Session Invalidation on Password Reset

Create a signal handler to invalidate all sessions when password is changed:

```python
# doi_portal/users/signals.py

from django.contrib.auth import user_logged_out
from django.contrib.sessions.models import Session
from django.db.models import Q
from django.utils import timezone
from allauth.account.signals import password_changed


def invalidate_user_sessions(sender, request, user, **kwargs):
    """Invalidate all sessions for user when password is changed."""
    # Get all sessions
    sessions = Session.objects.filter(expire_date__gte=timezone.now())

    for session in sessions:
        session_data = session.get_decoded()
        # Check if this session belongs to the user
        if str(session_data.get('_auth_user_id')) == str(user.pk):
            session.delete()


password_changed.connect(invalidate_user_sessions)
```

Register in users app:

```python
# doi_portal/users/apps.py

class UsersConfig(AppConfig):
    name = "doi_portal.users"
    verbose_name = "Users"

    def ready(self):
        try:
            import doi_portal.users.signals  # noqa: F401
        except ImportError:
            pass
```

### Template Structure

```
templates/
├── account/
│   ├── login.html                           # EXISTS (Story 1.3)
│   ├── logout.html                          # EXISTS (Story 1.3)
│   ├── password_reset.html                  # CREATE - Reset request form
│   ├── password_reset_done.html             # CREATE - Confirmation message
│   ├── password_reset_from_key.html         # CREATE - New password form
│   ├── password_reset_from_key_done.html    # CREATE - Success message
│   └── email/
│       └── password_reset_key_message.txt   # CREATE - Email template
```

### Bootstrap 5 Password Reset Request Template Pattern

```html
{% extends "base.html" %}
{% load crispy_forms_tags %}

{% block content %}
<div class="container">
  <div class="row justify-content-center mt-5">
    <div class="col-md-6 col-lg-4">
      <div class="card shadow">
        <div class="card-body p-4">
          <h2 class="card-title text-center mb-4">Resetovanje lozinke</h2>

          <p class="text-muted text-center mb-4">
            Unesite vasu email adresu i posalcemo vam link za resetovanje lozinke.
          </p>

          {% if form.errors %}
          <div class="alert alert-danger">
            {{ form.errors }}
          </div>
          {% endif %}

          <form method="post">
            {% csrf_token %}
            {{ form|crispy }}
            <button type="submit" class="btn btn-primary w-100 mt-3">
              Posalji link za reset
            </button>
          </form>

          <div class="text-center mt-3">
            <a href="{% url 'account_login' %}">Nazad na prijavu</a>
          </div>
        </div>
      </div>
    </div>
  </div>
</div>
{% endblock %}
```

### Password Reset Email Template Pattern

```
{% load i18n %}
{% autoescape off %}
{% blocktrans %}Postovani,

Primili smo zahtev za resetovanje lozinke za vas nalog na DOI Portalu.

Kliknite na sledeci link da resetujete lozinku:
{% endblocktrans %}

{{ password_reset_url }}

{% blocktrans %}Ovaj link istice za 1 sat.

Ako niste zahtevali reset lozinke, mozete ignorisati ovu poruku.

Srdacno,
DOI Portal tim{% endblocktrans %}
{% endautoescape %}
```

### New Password Form with Alpine.js Validation

```html
{% extends "base.html" %}
{% load crispy_forms_tags %}

{% block content %}
<div class="container">
  <div class="row justify-content-center mt-5">
    <div class="col-md-6 col-lg-4">
      <div class="card shadow">
        <div class="card-body p-4">
          <h2 class="card-title text-center mb-4">Nova lozinka</h2>

          {% if token_fail %}
          <div class="alert alert-warning">
            <strong>Link je istekao ili nije validan.</strong>
            <p class="mb-0 mt-2">Molimo zatrazite novi link za resetovanje lozinke.</p>
          </div>
          <a href="{% url 'account_reset_password' %}" class="btn btn-primary w-100 mt-3">
            Zatrazi novi link
          </a>
          {% else %}

          <div class="alert alert-info mb-4">
            <small>
              Lozinka mora imati najmanje 8 karaktera i kombinaciju slova i brojeva.
            </small>
          </div>

          {% if form.errors %}
          <div class="alert alert-danger">
            {{ form.errors }}
          </div>
          {% endif %}

          <form method="post" x-data="passwordForm()">
            {% csrf_token %}
            {{ form|crispy }}

            <div x-show="!passwordsMatch && password2.length > 0" class="text-danger small mt-1">
              Lozinke se ne poklapaju.
            </div>

            <button type="submit" class="btn btn-primary w-100 mt-3" :disabled="!passwordsMatch">
              Sacuvaj novu lozinku
            </button>
          </form>
          {% endif %}
        </div>
      </div>
    </div>
  </div>
</div>

<script>
function passwordForm() {
  return {
    password1: '',
    password2: '',
    get passwordsMatch() {
      if (this.password2.length === 0) return true;
      return this.password1 === this.password2;
    }
  }
}
</script>
{% endblock %}
```

### Email Backend Configuration

For local development, Cookiecutter Django uses Mailpit. For production:

```python
# config/settings/base.py (verify these exist)
DEFAULT_FROM_EMAIL = env("DJANGO_DEFAULT_FROM_EMAIL", default="DOI Portal <noreply@doi.rs>")

# config/settings/local.py (Cookiecutter default)
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
# OR Mailpit if configured
```

### Testing Strategy

**Test File:** `doi_portal/users/tests/test_password_reset.py`

```python
import pytest
from django.urls import reverse
from django.core import mail
from django.contrib.auth import get_user_model
from django.contrib.sessions.models import Session
from allauth.account.models import EmailAddress

User = get_user_model()


@pytest.fixture
def verified_user(db):
    """Create a user with verified email."""
    user = User.objects.create_user(
        email='test@example.com',
        password='oldpassword123'  # noqa: S106
    )
    EmailAddress.objects.create(
        user=user,
        email=user.email,
        verified=True,
        primary=True
    )
    return user


@pytest.mark.django_db
class TestPasswordResetRequest:
    def test_password_reset_page_renders(self, client):
        """Password reset request page should render."""
        response = client.get(reverse('account_reset_password'))
        assert response.status_code == 200
        assert 'form' in response.context

    def test_valid_email_shows_confirmation(self, client, verified_user):
        """Valid email submission shows confirmation."""
        response = client.post(
            reverse('account_reset_password'),
            {'email': verified_user.email}
        )
        assert response.status_code == 302
        assert response.url == reverse('account_reset_password_done')

    def test_nonexistent_email_still_shows_confirmation(self, client):
        """Non-existent email still shows confirmation (security)."""
        response = client.post(
            reverse('account_reset_password'),
            {'email': 'nonexistent@example.com'}
        )
        assert response.status_code == 302
        assert response.url == reverse('account_reset_password_done')

    def test_password_reset_email_sent(self, client, verified_user):
        """Password reset email is sent for valid user."""
        client.post(
            reverse('account_reset_password'),
            {'email': verified_user.email}
        )
        assert len(mail.outbox) == 1
        assert verified_user.email in mail.outbox[0].to


@pytest.mark.django_db
class TestPasswordResetConfirm:
    def test_valid_token_shows_form(self, client, verified_user):
        """Valid reset token shows password form."""
        # Request password reset
        client.post(
            reverse('account_reset_password'),
            {'email': verified_user.email}
        )
        # Extract token from email
        email_body = mail.outbox[0].body
        # Parse the reset URL from email (implementation specific)
        # This test may need adjustment based on actual URL format
        pass  # TODO: Implement with actual token extraction

    def test_password_update_succeeds(self, client, verified_user):
        """Password update with valid password succeeds."""
        # This requires a valid token, typically tested with integration tests
        pass  # TODO: Implement with token extraction


@pytest.mark.django_db
class TestSessionInvalidation:
    def test_sessions_invalidated_on_password_reset(self, client, verified_user):
        """All sessions should be invalidated when password is reset."""
        # Login to create session
        client.login(email=verified_user.email, password='oldpassword123')

        # Verify session exists
        initial_sessions = Session.objects.count()
        assert initial_sessions >= 1

        # Change password (simulating reset)
        verified_user.set_password('newpassword123')
        verified_user.save()

        # Trigger signal manually for test (in real scenario, allauth triggers it)
        from allauth.account.signals import password_changed
        password_changed.send(
            sender=verified_user.__class__,
            request=None,
            user=verified_user
        )

        # Verify sessions are cleared
        # Note: This test may need adjustment based on session storage
```

### Previous Story Learnings (Story 1.3)

From Story 1.3 implementation:
1. **Use existing allauth views:** Don't create custom authentication views
2. **Bootstrap 5 styling:** Follow established card + form-control pattern
3. **Crispy forms:** Use `{{ form|crispy }}` for consistent form rendering
4. **Test patterns:** Follow established test structure in `tests/` folder
5. **Session config exists:** SESSION_COOKIE_AGE = 1800 already configured
6. **LastActivityMiddleware exists:** Can leverage for session tracking

### Git Commit Patterns from Project

Recent commits follow pattern:
- `feat(module): description` for new features
- `fix(module): description` for bug fixes

Expected commit for this story:
```
feat(auth): implement Password Reset functionality (Story 1.5)
```

### NFR Requirements Addressed

From PRD:
- **NFR8:** Password policy - Min 8 characters, combination of letters/numbers
- **NFR9:** Session management - Invalidate sessions on password change
- **NFR10:** Passwords hashed with argon2 (Cookiecutter default)

### Alignment with Architecture

From architecture.md:
- **Authentication:** django-allauth (use existing password reset)
- **Password Hashing:** argon2 (Cookiecutter default, no changes needed)
- **Session Backend:** Redis (sessions stored in Redis)
- **Frontend:** Bootstrap 5 styled templates
- **Email:** django-anymail + Mailgun (production), console/Mailpit (local)

### Files to Create

- `templates/account/password_reset.html` - Reset request form
- `templates/account/password_reset_done.html` - Confirmation page
- `templates/account/password_reset_from_key.html` - New password form
- `templates/account/password_reset_from_key_done.html` - Success page
- `templates/account/email/password_reset_key_message.txt` - Email template
- `doi_portal/users/signals.py` - Session invalidation signal
- `doi_portal/users/tests/test_password_reset.py` - Unit tests

### Files to Modify

- `config/settings/base.py` - Verify password validators, add timeout if needed
- `doi_portal/users/apps.py` - Import signals in ready()

### Existing Files (DO NOT recreate)

- `templates/account/login.html` - Has "Forgot Password?" link (Story 1.3)
- `templates/base.html` - Base template
- `requirements/base.txt` - django-allauth already included

### Anti-Patterns to Avoid

```python
# WRONG - Creating custom password reset views
class CustomPasswordResetView(View):  # NO! Use allauth
    pass

# WRONG - Hardcoded URLs
return redirect('/accounts/password/reset/done/')  # NO! Use named URLs

# WRONG - Not clearing sessions on password change
user.set_password(new_password)
user.save()  # MISSING: session invalidation

# WRONG - Revealing email existence
if User.objects.filter(email=email).exists():
    send_reset_email()
else:
    return "Email not found"  # NO! Security vulnerability
```

### References

- [Source: architecture.md#Authentication & Security]
- [Source: project-context.md#NFR8 - Password policy]
- [Source: project-context.md#NFR9 - Session management]
- [Source: epics.md#Story 1.5]
- [Source: 1-3-user-login-logout.md#Dev Notes - Session configuration]

## Dev Agent Record

### Agent Model Used

Claude Opus 4.5 (claude-opus-4-5-20251101)

### Debug Log References

- TDD RED phase: 5 tests initially failed (back to login link, bootstrap styling, no email for nonexistent, session invalidation, timeout config)
- TDD GREEN phase: All 25 tests passing after implementation
- Full test suite: 101 passed, 3 skipped (existing skips), 38 warnings (mostly staticfiles)

### Completion Notes List

1. **Task 1**: Configured PASSWORD_RESET_TIMEOUT=3600 and ACCOUNT_PASSWORD_MIN_LENGTH=8 in base.py. Updated AUTH_PASSWORD_VALIDATORS to explicitly set min_length=8 and removed NumericPasswordValidator per story requirements.

2. **Task 2-6**: Created 4 Bootstrap 5 styled templates for password reset flow (request, done, from_key, from_key_done) plus email template with Serbian language. All templates follow established card pattern from Story 1.3.

3. **Task 7**: Implemented session invalidation via signal handlers for password_changed, password_reset, and password_set signals. Signal module registered in apps.py ready() method.

4. **Task 8**: Verified and updated AUTH_PASSWORD_VALIDATORS. Explicitly configured min_length=8 for MinimumLengthValidator. CommonPasswordValidator enabled. NumericPasswordValidator removed to allow alphanumeric combinations.

5. **Task 9**: Invalid/expired token handling integrated into password_reset_from_key.html template using allauth's token_fail context variable.

6. **Task 10**: Created comprehensive test suite with 25 tests covering all acceptance criteria. Tests verify: page rendering, email submission flow, email sending, token handling, password policy enforcement, session invalidation, and settings configuration.

### File List

**Created:**
- `doi_portal/doi_portal/templates/account/password_reset.html` - Password reset request form
- `doi_portal/doi_portal/templates/account/password_reset_done.html` - Confirmation page
- `doi_portal/doi_portal/templates/account/password_reset_from_key.html` - New password form + invalid token handling
- `doi_portal/doi_portal/templates/account/password_reset_from_key_done.html` - Success page
- `doi_portal/doi_portal/templates/account/email/password_reset_key_message.txt` - Email content
- `doi_portal/doi_portal/templates/account/email/password_reset_key_subject.txt` - Email subject
- `doi_portal/doi_portal/users/signals.py` - Session invalidation signal handlers
- `doi_portal/doi_portal/users/tests/test_password_reset.py` - Unit tests (26 tests)

**Modified:**
- `doi_portal/config/settings/base.py` - Added PASSWORD_RESET_TIMEOUT, ACCOUNT_PASSWORD_MIN_LENGTH, updated AUTH_PASSWORD_VALIDATORS
- `doi_portal/doi_portal/users/apps.py` - Import signals module in ready()

## Code Review Record

### Review Date
2026-01-26

### Reviewer
Amelia (Dev Agent) - Claude Opus 4.5 (claude-opus-4-5-20251101)

### Review Type
ADVERSARIAL Code Review (fresh context)

### Issues Found: 7

| # | Severity | Category | File | Issue Description | Fix Applied |
|---|----------|----------|------|-------------------|-------------|
| 1 | HIGH | Security/Performance | signals.py | N+1 query problem - iterating all sessions and decoding each is inefficient and potential DoS vector | Refactored to use `.iterator()` and bulk delete with `session_key__in` filter |
| 2 | MEDIUM | Code Quality | signals.py | Missing type hints - not mypy compatible per project-context.md | Added full type annotations with TYPE_CHECKING imports |
| 3 | MEDIUM | Accessibility | password_reset_from_key.html | Alpine.js validation missing aria-live for screen readers | Added `role="alert"` and `aria-live="polite"` attributes |
| 4 | MEDIUM | Test Coverage | test_password_reset.py | Missing test for password mismatch validation (AC#4) | Added `test_password_mismatch_rejected()` test |
| 5 | LOW | Code Quality | test_password_reset.py | Duplicated `_get_reset_url_from_email()` helper in 2 classes | Refactored to module-level function `get_reset_url_from_email()` |
| 6 | LOW | i18n | password_reset_key_subject.txt | Email subject hardcoded without `{% trans %}` tag despite loading i18n | Wrapped in `{% trans %}` block |
| 7 | LOW | Linting | signals.py | Ruff S112 warning for try-except-continue | Added noqa comment with security justification |

### Issues Fixed: 7/7 (100%)

### Tests After Fix
- Password reset tests: 26 passed (was 25, +1 new test)
- Full test suite: 102 passed, 3 skipped, 39 warnings
- Ruff: All checks passed
- All ACs verified

### Definition of Done (DoD) Checklist

- [x] All acceptance criteria implemented and verified
- [x] All tasks/subtasks marked complete
- [x] Unit tests written and passing (26 tests)
- [x] Full test suite passing (102 passed)
- [x] Code follows project-context.md standards
- [x] Ruff linter passing (0 errors)
- [x] Type hints added where applicable
- [x] Accessibility attributes added
- [x] i18n properly configured
- [x] No security vulnerabilities
- [x] Story status updated to `done`
- [x] sprint-status.yaml updated

### Recommendation
**APPROVED** - Story 1.5 Password Reset is complete and ready for production.
