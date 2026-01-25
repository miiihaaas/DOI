# Story 1.3: User Login & Logout

Status: done

## Story

As a **team member**,
I want **to log in and out of the system securely**,
So that **I can access the admin panel according to my role**.

## Acceptance Criteria

1. **Given** a registered user with valid credentials
   **When** the user navigates to the login page
   **Then** a Bootstrap 5 styled login form is displayed
   **And** the user can enter email and password

2. **Given** valid credentials are submitted
   **When** the login form is processed
   **Then** the user is authenticated and redirected to dashboard
   **And** a session is created with 30-minute inactivity timeout
   **And** last_activity timestamp is updated

3. **Given** an authenticated user
   **When** the user clicks logout
   **Then** the session is terminated
   **And** the user is redirected to login page

4. **Given** invalid credentials are submitted
   **When** the login form is processed
   **Then** an error message is displayed
   **And** the user remains on the login page

## Tasks / Subtasks

- [x] Task 1: Configure django-allauth Login Settings (AC: #1, #2)
  - [x] 1.1 Verify django-allauth is installed (Cookiecutter default)
  - [x] 1.2 Configure ACCOUNT_AUTHENTICATION_METHOD = 'email'
  - [x] 1.3 Configure ACCOUNT_EMAIL_REQUIRED = True
  - [x] 1.4 Configure ACCOUNT_USERNAME_REQUIRED = False
  - [x] 1.5 Configure LOGIN_REDIRECT_URL to dashboard
  - [x] 1.6 Configure LOGOUT_REDIRECT_URL to login page

- [x] Task 2: Configure Session Management (AC: #2, #3)
  - [x] 2.1 Configure SESSION_COOKIE_AGE = 1800 (30 minutes)
  - [x] 2.2 Configure SESSION_SAVE_EVERY_REQUEST = True (extend on activity)
  - [x] 2.3 Create LastActivityMiddleware to update User.last_activity
  - [x] 2.4 Add middleware to MIDDLEWARE setting after AuthenticationMiddleware

- [x] Task 3: Create Bootstrap 5 Login Template (AC: #1, #4)
  - [x] 3.1 Create templates/account/login.html extending base template
  - [x] 3.2 Style form with Bootstrap 5 classes (form-control, btn-primary)
  - [x] 3.3 Add email and password input fields
  - [x] 3.4 Display django-allauth form errors with Bootstrap alert styling
  - [x] 3.5 Add "Forgot Password?" link to password reset
  - [x] 3.6 Center form on page with responsive container

- [x] Task 4: Create Logout Functionality (AC: #3)
  - [x] 4.1 Configure ACCOUNT_LOGOUT_ON_GET = False (require POST for security)
  - [x] 4.2 Create templates/account/logout.html with confirmation
  - [x] 4.3 Style logout page with Bootstrap 5
  - [x] 4.4 Verify redirect to login after logout

- [x] Task 5: Create Base Admin Template Shell (AC: #2)
  - [x] 5.1 Create templates/base.html if not exists (public base)
  - [x] 5.2 Create templates/admin_base.html for admin panel layout
  - [x] 5.3 Add placeholder header with user info and logout button
  - [x] 5.4 Add basic page structure for future dashboard content
  - [x] 5.5 Include Bootstrap 5 CSS and JS from CDN

- [x] Task 6: Create Dashboard Placeholder View (AC: #2)
  - [x] 6.1 Create doi_portal/core/views.py with DashboardView
  - [x] 6.2 Require login using LoginRequiredMixin
  - [x] 6.3 Create templates/dashboard/dashboard.html extending admin_base.html
  - [x] 6.4 Display "Welcome, {user.name}" message
  - [x] 6.5 Add route in config/urls.py: path('dashboard/', ...)

- [x] Task 7: Write Unit Tests (AC: #1, #2, #3, #4)
  - [x] 7.1 Test login page renders with Bootstrap form
  - [x] 7.2 Test successful login redirects to dashboard
  - [x] 7.3 Test login updates last_activity timestamp
  - [x] 7.4 Test invalid credentials show error message
  - [x] 7.5 Test logout terminates session
  - [x] 7.6 Test logout redirects to login page
  - [x] 7.7 Test unauthenticated user cannot access dashboard

## Dev Notes

### CRITICAL: django-allauth is Pre-installed

**IMPORTANT:** Cookiecutter Django already includes django-allauth. Do NOT:
- Install django-allauth separately (already in requirements)
- Override allauth URLs (already configured)
- Create custom authentication views (use allauth views)

**DO:**
- Override templates in templates/account/
- Configure settings in config/settings/base.py
- Use allauth forms and views as-is

### django-allauth Configuration Reference

From Cookiecutter Django, these settings exist in base.py. Modify as needed:

```python
# config/settings/base.py

# django-allauth settings
ACCOUNT_AUTHENTICATION_METHOD = "email"  # Use email, not username
ACCOUNT_EMAIL_REQUIRED = True
ACCOUNT_USERNAME_REQUIRED = False  # We use email for login
ACCOUNT_EMAIL_VERIFICATION = "mandatory"  # Email verification required
ACCOUNT_ALLOW_REGISTRATION = env.bool("DJANGO_ACCOUNT_ALLOW_REGISTRATION", True)

# Redirect URLs
LOGIN_REDIRECT_URL = "dashboard"  # After successful login
LOGOUT_REDIRECT_URL = "account_login"  # After logout
```

### Session Configuration for 30-Minute Timeout

```python
# config/settings/base.py

# Session configuration
SESSION_COOKIE_AGE = 1800  # 30 minutes in seconds
SESSION_SAVE_EVERY_REQUEST = True  # Extend session on each request
SESSION_EXPIRE_AT_BROWSER_CLOSE = False  # Use cookie age instead
```

### LastActivityMiddleware Implementation

```python
# doi_portal/core/middleware.py

from django.utils import timezone

class LastActivityMiddleware:
    """Update last_activity on each authenticated request."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        if request.user.is_authenticated:
            # Update without triggering model save signals
            request.user.__class__.objects.filter(pk=request.user.pk).update(
                last_activity=timezone.now()
            )

        return response
```

Add to settings:
```python
MIDDLEWARE = [
    ...
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'doi_portal.core.middleware.LastActivityMiddleware',  # ADD AFTER AUTH
    ...
]
```

### Template Structure (Already Partially Exists)

From Cookiecutter Django, templates/account/ has basic allauth templates. Override with Bootstrap 5:

```
templates/
├── base.html                    # EXISTS - public base
├── admin_base.html              # CREATE - admin layout
├── account/
│   ├── login.html               # OVERRIDE - Bootstrap 5 styled
│   └── logout.html              # OVERRIDE - Bootstrap 5 styled
├── dashboard/
│   └── dashboard.html           # CREATE - simple placeholder
└── components/
    └── _toast.html              # CREATE (optional for future)
```

### Bootstrap 5 Login Form Template Pattern

```html
{% extends "base.html" %}
{% load crispy_forms_tags %}

{% block content %}
<div class="container">
  <div class="row justify-content-center mt-5">
    <div class="col-md-6 col-lg-4">
      <div class="card shadow">
        <div class="card-body p-4">
          <h2 class="card-title text-center mb-4">Prijava</h2>

          {% if form.errors %}
          <div class="alert alert-danger">
            Neispravni podaci za prijavu.
          </div>
          {% endif %}

          <form method="post">
            {% csrf_token %}
            {{ form|crispy }}
            <button type="submit" class="btn btn-primary w-100 mt-3">
              Prijavi se
            </button>
          </form>

          <div class="text-center mt-3">
            <a href="{% url 'account_reset_password' %}">Zaboravili ste lozinku?</a>
          </div>
        </div>
      </div>
    </div>
  </div>
</div>
{% endblock %}
```

### Dashboard Placeholder View Pattern

```python
# doi_portal/core/views.py

from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView

class DashboardView(LoginRequiredMixin, TemplateView):
    """Admin dashboard placeholder - full implementation in Story 1.7."""
    template_name = "dashboard/dashboard.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['user'] = self.request.user
        return context
```

### URL Configuration

```python
# config/urls.py

from doi_portal.core.views import DashboardView

urlpatterns = [
    ...
    path("dashboard/", DashboardView.as_view(), name="dashboard"),
    ...
]
```

### RBAC Integration from Story 1.2

From previous story, these exist and should be used:
- User model with `last_activity` field at `doi_portal/users/models.py`
- 4 RBAC Groups: Superadmin, Administrator, Urednik, Bibliotekar
- PublisherPermissionMixin at `doi_portal/core/permissions.py`
- role_required decorator at `doi_portal/core/permissions.py`

**Note:** This story does NOT implement role-based dashboard differences. That is Story 1.7.

### Project Structure Notes

**Files to Create:**
- `doi_portal/core/middleware.py` - LastActivityMiddleware
- `templates/account/login.html` - Bootstrap 5 login form
- `templates/account/logout.html` - Bootstrap 5 logout confirmation
- `templates/admin_base.html` - Admin panel base template
- `templates/dashboard/dashboard.html` - Dashboard placeholder
- `doi_portal/core/views.py` - DashboardView
- `doi_portal/core/tests/test_authentication.py` - Auth tests

**Files to Modify:**
- `config/settings/base.py` - Session and allauth settings
- `config/urls.py` - Dashboard URL route

**Existing Files (DO NOT recreate):**
- `templates/base.html` - Cookiecutter base template
- `requirements/base.txt` - django-allauth already included
- `doi_portal/users/models.py` - User model with last_activity

### Testing Strategy

**Test File:** `doi_portal/core/tests/test_authentication.py`

```python
import pytest
from django.urls import reverse
from django.contrib.auth import get_user_model

User = get_user_model()

@pytest.mark.django_db
class TestLogin:
    def test_login_page_renders(self, client):
        """Login page should render with form."""
        response = client.get(reverse('account_login'))
        assert response.status_code == 200
        assert 'form' in response.context

    def test_successful_login_redirects(self, client):
        """Valid credentials redirect to dashboard."""
        user = User.objects.create_user(
            email='test@test.com',
            password='testpass123'
        )
        response = client.post(reverse('account_login'), {
            'login': 'test@test.com',
            'password': 'testpass123'
        })
        assert response.status_code == 302
        assert response.url == reverse('dashboard')

    def test_login_updates_last_activity(self, client):
        """Login should update user's last_activity."""
        user = User.objects.create_user(
            email='test@test.com',
            password='testpass123'
        )
        client.login(email='test@test.com', password='testpass123')
        user.refresh_from_db()
        assert user.last_activity is not None

    def test_invalid_login_shows_error(self, client):
        """Invalid credentials show error message."""
        response = client.post(reverse('account_login'), {
            'login': 'wrong@test.com',
            'password': 'wrongpass'
        })
        assert response.status_code == 200
        assert 'form' in response.context
        assert response.context['form'].errors

@pytest.mark.django_db
class TestLogout:
    def test_logout_terminates_session(self, client):
        """Logout should end user session."""
        user = User.objects.create_user(
            email='test@test.com',
            password='testpass123'
        )
        client.login(email='test@test.com', password='testpass123')
        response = client.post(reverse('account_logout'))
        assert response.status_code == 302

    def test_logout_redirects_to_login(self, client):
        """After logout, redirect to login page."""
        user = User.objects.create_user(
            email='test@test.com',
            password='testpass123'
        )
        client.login(email='test@test.com', password='testpass123')
        response = client.post(reverse('account_logout'))
        assert reverse('account_login') in response.url

@pytest.mark.django_db
class TestDashboard:
    def test_dashboard_requires_login(self, client):
        """Dashboard should require authentication."""
        response = client.get(reverse('dashboard'))
        assert response.status_code == 302
        assert 'login' in response.url

    def test_authenticated_user_sees_dashboard(self, client):
        """Authenticated user can access dashboard."""
        user = User.objects.create_user(
            email='test@test.com',
            password='testpass123'
        )
        client.login(email='test@test.com', password='testpass123')
        response = client.get(reverse('dashboard'))
        assert response.status_code == 200
```

### Previous Story Learnings (Story 1.2)

From Story 1.2 implementation:
1. **SQLite for tests:** Use `config/settings/test.py` with SQLite in-memory for faster tests
2. **Factory Boy:** Use UserFactory from existing tests for consistent test data
3. **Skip problematic tests:** Some OpenAPI tests may need to be skipped
4. **Core app exists:** `doi_portal/core/` was created in Story 1.2

### Git Commit Patterns from Project

Recent commits follow pattern:
- `feat(module): description` for new features
- `fix(module): description` for bug fixes

Expected commit for this story:
```
feat(auth): implement User Login & Logout (Story 1.3)
```

### Anti-Patterns to Avoid

```python
# WRONG - Creating custom auth views
class CustomLoginView(View):  # NO! Use allauth
    pass

# WRONG - Hardcoded redirect URLs
return redirect('/dashboard/')  # NO! Use named URLs

# WRONG - Manual session handling
request.session['user_id'] = user.id  # NO! Use Django auth

# WRONG - Plain text in templates
<p>Invalid credentials</p>  # NO! Use translation strings
```

### Alignment with Architecture

From architecture.md:
- **Authentication:** django-allauth (Cookiecutter default)
- **Password Hashing:** argon2 (Cookiecutter default, no changes needed)
- **Session Backend:** Redis (already configured by Cookiecutter)
- **Frontend:** Bootstrap 5 styled templates
- **HTMX:** Not needed for this story (login/logout are full page)

### Dependencies (Already Installed)

All dependencies are already installed via Cookiecutter Django:
- django-allauth (authentication)
- django-crispy-forms + crispy-bootstrap5 (form rendering)
- argon2-cffi (password hashing)

### References

- [Source: architecture.md#Authentication & Security]
- [Source: ux-design-specification.md#Desired Emotional Response - Sigurnost]
- [Source: project-context.md#NFR9 - Session timeout 30 min]
- [Source: epics.md#Story 1.3]
- [Source: 1-2-custom-user-model-rbac-setup.md#Dev Notes - last_activity field]

## Dev Agent Record

### Agent Model Used

Claude Opus 4.5 (claude-opus-4-5-20251101)

### Debug Log References

- All 21 authentication tests pass
- Full test suite: 76 passed, 3 skipped (OpenAPI tests)

### Completion Notes List

1. **Task 1**: Configured django-allauth settings in `config/settings/base.py`:
   - LOGIN_REDIRECT_URL = "dashboard"
   - LOGOUT_REDIRECT_URL = "account_login"
   - Verified existing ACCOUNT_LOGIN_METHODS = {"email"}

2. **Task 2**: Configured session management:
   - SESSION_COOKIE_AGE = 1800 (30 min)
   - SESSION_SAVE_EVERY_REQUEST = True
   - Created LastActivityMiddleware in `doi_portal/core/middleware.py`
   - Added middleware after AuthenticationMiddleware

3. **Task 3**: Created Bootstrap 5 login template:
   - `templates/account/login.html` with form-control classes
   - Error display with alert-danger
   - "Forgot Password?" link
   - Responsive centered layout

4. **Task 4**: Created logout functionality:
   - ACCOUNT_LOGOUT_ON_GET = False (POST required)
   - `templates/account/logout.html` with confirmation
   - Verified redirect to login after logout

5. **Task 5**: Created admin base template:
   - `templates/admin_base.html` with Bootstrap 5
   - Header with user dropdown and logout
   - Footer and message display

6. **Task 6**: Created dashboard placeholder:
   - `doi_portal/core/views.py` with DashboardView
   - LoginRequiredMixin enforced
   - `templates/dashboard/dashboard.html`
   - Route at `/dashboard/`

7. **Task 7**: All tests written and passing (21 tests):
   - 6 configuration tests
   - 5 login page tests
   - 2 successful login tests
   - 1 middleware test
   - 2 invalid login tests
   - 2 logout tests
   - 3 dashboard tests

### File List

**Files Created:**
- `doi_portal/doi_portal/core/middleware.py` - LastActivityMiddleware
- `doi_portal/doi_portal/core/views.py` - DashboardView
- `doi_portal/doi_portal/core/tests/test_authentication.py` - 21 tests
- `doi_portal/doi_portal/templates/account/login.html` - Bootstrap 5 login
- `doi_portal/doi_portal/templates/account/logout.html` - Bootstrap 5 logout
- `doi_portal/doi_portal/templates/admin_base.html` - Admin base template
- `doi_portal/doi_portal/templates/dashboard/dashboard.html` - Dashboard page

**Files Modified:**
- `doi_portal/config/settings/base.py` - Session, redirect, allauth settings
- `doi_portal/config/urls.py` - Dashboard URL route

## Code Review Record

### Reviewer
Dev Agent (Amelia) - Claude Opus 4.5 (claude-opus-4-5-20251101)
Date: 2026-01-25

### Issues Found: 10

| # | Severity | Category | Issue | Resolution |
|---|----------|----------|-------|------------|
| 1 | HIGH | Code Quality | PLC0415 - Import statements inside test methods instead of top-level (8 occurrences) | Moved `EmailAddress` import to top-level, created helper function `_create_verified_user()` |
| 2 | HIGH | Code Quality | COM812 - Missing trailing comma in middleware.py | Added trailing comma |
| 3 | HIGH | Code Quality | E501 - Lines too long (>88 characters) in test file (3 lines) | Split long lines per PEP8 |
| 4 | MEDIUM | Code Quality | PT018 - Complex assertion should be broken into multiple parts | Refactored compound assertions into separate assert statements |
| 5 | MEDIUM | Code Quality | PLR2004 - Magic numbers (200, 302, 1800) | Replaced with `HTTPStatus.OK`, `HTTPStatus.FOUND`, `SESSION_TIMEOUT_SECONDS` constant |
| 6 | MEDIUM | Code Quality | S106 - Hardcoded password warnings | Added `# noqa: S105` comments for test constants |
| 7 | MEDIUM | Code Quality | Code formatting not compliant | Ran `ruff format` on all core files |
| 8 | MEDIUM | Consistency | Bootstrap version mismatch (base.html: 5.2.3, admin_base.html: 5.3.3) | Updated base.html to Bootstrap 5.3.3 |
| 9 | LOW | Code Quality | UP035 - Import Callable from collections.abc instead of typing | Fixed import |
| 10 | LOW | Documentation | Missing type hints in views.py and middleware.py | Added proper type annotations |

### All Issues Fixed: YES

### Test Results After Fixes
- Authentication tests: 21 passed
- Full test suite: 76 passed, 3 skipped (OpenAPI tests)
- Ruff lint: All checks passed
- Ruff format: All files formatted

### Definition of Done (DoD) Checklist

- [x] All Acceptance Criteria met (AC#1, AC#2, AC#3, AC#4)
- [x] All tasks/subtasks completed (Task 1-7)
- [x] Unit tests written and passing (21 tests)
- [x] Full test suite passing (76 passed, 3 skipped)
- [x] Code quality checks pass (ruff lint + format)
- [x] No critical security issues
- [x] Documentation updated (Dev Agent Record)
- [x] Story status updated to "done"
- [x] sprint-status.yaml updated
