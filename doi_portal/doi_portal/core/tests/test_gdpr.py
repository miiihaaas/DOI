"""
Tests for GDPR Data Request Handling.

Story 6.4: GdprRequest model, GdprService, views, and Celery tasks.
"""

from datetime import timedelta
from unittest.mock import patch

import pytest
from django.contrib.auth.models import Group
from django.test import Client
from django.urls import reverse
from django.utils import timezone

from doi_portal.core.models import GdprRequest, GdprRequestStatus, GdprRequestType
from doi_portal.users.tests.factories import UserFactory


# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def superadmin_user(db):
    """Create a Superadmin user."""
    user = UserFactory()
    group, _ = Group.objects.get_or_create(name="Superadmin")
    user.groups.add(group)
    return user


@pytest.fixture
def regular_user(db):
    """Create a regular user with Bibliotekar role."""
    user = UserFactory()
    group, _ = Group.objects.get_or_create(name="Bibliotekar")
    user.groups.add(group)
    return user


@pytest.fixture
def superadmin_client(superadmin_user):
    """Client logged in as Superadmin."""
    client = Client()
    client.force_login(superadmin_user)
    return client


@pytest.fixture
def regular_client(regular_user):
    """Client logged in as regular user."""
    client = Client()
    client.force_login(regular_user)
    return client


@pytest.fixture
def gdpr_request(db, superadmin_user):
    """Create a sample GDPR request."""
    return GdprRequest.objects.create(
        requester_email="test@example.com",
        request_type=GdprRequestType.DELETION,
        status=GdprRequestStatus.PENDING,
        received_date=timezone.now().date(),
        created_by=superadmin_user,
    )


@pytest.fixture
def target_user(db):
    """Create a user that will be the target of GDPR request."""
    return UserFactory(email="target@example.com", name="Target User")


@pytest.fixture
def target_authors(db, target_user):
    """Create Author records matching the target user's email."""
    from doi_portal.articles.tests.factories import AuthorFactory

    author1 = AuthorFactory(email="target@example.com")
    author2 = AuthorFactory(email="target@example.com")
    return [author1, author2]


# ============================================================================
# Task 9: Tests for GdprRequest model (AC: #1, #2)
# ============================================================================


@pytest.mark.django_db
class TestGdprRequestModel:
    """Task 9.1-9.3: GdprRequest model tests."""

    def test_create_with_all_fields(self, superadmin_user):
        """Task 9.1: GdprRequest creation with all fields."""
        req = GdprRequest.objects.create(
            requester_email="user@example.com",
            request_type=GdprRequestType.DELETION,
            status=GdprRequestStatus.PENDING,
            notes="Test napomena",
            received_date=timezone.now().date(),
            created_by=superadmin_user,
        )
        assert req.pk is not None
        assert req.requester_email == "user@example.com"
        assert req.request_type == GdprRequestType.DELETION
        assert req.status == GdprRequestStatus.PENDING
        assert req.notes == "Test napomena"
        assert req.created_by == superadmin_user
        assert req.created_at is not None

    def test_status_choices(self):
        """Task 9.2: Status choices validation."""
        assert GdprRequestStatus.PENDING == "PENDING"
        assert GdprRequestStatus.PROCESSING == "PROCESSING"
        assert GdprRequestStatus.COMPLETED == "COMPLETED"
        assert GdprRequestStatus.CANCELLED == "CANCELLED"

    def test_default_status_is_pending(self, superadmin_user):
        """Task 9.3: Default status is PENDING."""
        req = GdprRequest.objects.create(
            requester_email="user@example.com",
            request_type=GdprRequestType.ACCESS,
            received_date=timezone.now().date(),
            created_by=superadmin_user,
        )
        assert req.status == GdprRequestStatus.PENDING

    def test_str_representation(self, gdpr_request):
        """String representation includes pk, email, and type."""
        result = str(gdpr_request)
        assert "GDPR-" in result
        assert "test@example.com" in result

    def test_ordering_reverse_chronological(self, superadmin_user):
        """Ordering is reverse chronological by created_at."""
        req1 = GdprRequest.objects.create(
            requester_email="a@example.com",
            request_type=GdprRequestType.ACCESS,
            received_date=timezone.now().date(),
            created_by=superadmin_user,
        )
        req2 = GdprRequest.objects.create(
            requester_email="b@example.com",
            request_type=GdprRequestType.DELETION,
            received_date=timezone.now().date(),
            created_by=superadmin_user,
        )
        requests = list(GdprRequest.objects.all())
        assert requests[0] == req2
        assert requests[1] == req1

    def test_request_type_choices(self):
        """Request type choices are ACCESS and DELETION."""
        assert GdprRequestType.ACCESS == "ACCESS"
        assert GdprRequestType.DELETION == "DELETION"


# ============================================================================
# Task 10: Tests for GdprService (AC: #3, #4, #5, #6)
# ============================================================================


@pytest.mark.django_db
class TestGdprServiceIdentifyAffectedData:
    """Task 10.1-10.3: identify_affected_data tests."""

    def test_identifies_user_by_email(self, target_user):
        """Task 10.1: Finds User by email."""
        from doi_portal.core.services import GdprService

        result = GdprService.identify_affected_data("target@example.com")
        assert result["user"] == target_user

    def test_identifies_author_records_by_email(self, target_user, target_authors):
        """Task 10.2: Finds Author records by email."""
        from doi_portal.core.services import GdprService

        result = GdprService.identify_affected_data("target@example.com")
        assert result["authors"].count() == 2

    def test_counts_audit_log_entries(self, target_user):
        """Task 10.3: Counts audit log entries for user."""
        from doi_portal.core.services import GdprService

        result = GdprService.identify_affected_data("target@example.com")
        assert "audit_entries_count" in result
        assert isinstance(result["audit_entries_count"], int)

    def test_returns_none_user_when_not_found(self, db):
        """Returns None for user when email not found."""
        from doi_portal.core.services import GdprService

        result = GdprService.identify_affected_data("nonexistent@example.com")
        assert result["user"] is None


@pytest.mark.django_db
class TestGdprServiceProcessDeletion:
    """Task 10.4-10.6: process_deletion_request tests."""

    def test_soft_deletes_user(self, gdpr_request, target_user, superadmin_user):
        """Task 10.4: Soft-deletes user (is_active=False)."""
        from doi_portal.core.services import GdprService

        gdpr_request.requester_email = "target@example.com"
        gdpr_request.save()

        GdprService.process_deletion_request(gdpr_request, superadmin_user)
        target_user.refresh_from_db()
        assert target_user.is_active is False

    def test_soft_deletes_author_records(
        self, gdpr_request, target_user, target_authors, superadmin_user
    ):
        """Task 10.5: Soft-deletes Author records."""
        from doi_portal.articles.models import Author
        from doi_portal.core.services import GdprService

        gdpr_request.requester_email = "target@example.com"
        gdpr_request.save()

        GdprService.process_deletion_request(gdpr_request, superadmin_user)
        for author in target_authors:
            author.refresh_from_db()
            assert author.is_deleted is True

    def test_sets_grace_period_end(self, gdpr_request, target_user, superadmin_user):
        """Task 10.6: Sets grace_period_end to 30 days from now."""
        from doi_portal.core.services import GdprService

        gdpr_request.requester_email = "target@example.com"
        gdpr_request.save()

        GdprService.process_deletion_request(gdpr_request, superadmin_user)
        gdpr_request.refresh_from_db()
        expected = timezone.now().date() + timedelta(days=30)
        assert gdpr_request.grace_period_end == expected
        assert gdpr_request.status == GdprRequestStatus.PROCESSING


@pytest.mark.django_db
class TestGdprServiceCancelRequest:
    """Task 10.7: cancel_request tests."""

    def test_cancel_restores_data_and_sets_cancelled(
        self, gdpr_request, target_user, target_authors, superadmin_user
    ):
        """Task 10.7: Cancelling restores soft-deleted data and sets CANCELLED."""
        from doi_portal.core.services import GdprService

        gdpr_request.requester_email = "target@example.com"
        gdpr_request.save()

        # First process the request
        GdprService.process_deletion_request(gdpr_request, superadmin_user)

        # Then cancel it
        GdprService.cancel_request(
            gdpr_request, "Korisnik se predomislio", superadmin_user
        )
        gdpr_request.refresh_from_db()
        assert gdpr_request.status == GdprRequestStatus.CANCELLED
        assert gdpr_request.cancellation_reason == "Korisnik se predomislio"

        # User should be re-activated
        target_user.refresh_from_db()
        assert target_user.is_active is True

        # Authors should be restored
        for author in target_authors:
            author.refresh_from_db()
            assert author.is_deleted is False


@pytest.mark.django_db
class TestGdprServiceCompleteRequest:
    """Task 10.8-10.9: complete_request tests."""

    def test_anonymizes_user_email_and_name(
        self, gdpr_request, target_user, superadmin_user
    ):
        """Task 10.8: Anonymizes user email and name."""
        from doi_portal.core.services import GdprService

        gdpr_request.requester_email = "target@example.com"
        gdpr_request.save()

        GdprService.process_deletion_request(gdpr_request, superadmin_user)
        GdprService.complete_request(gdpr_request)

        target_user.refresh_from_db()
        assert target_user.email == f"deleted_{target_user.pk}@anonymized.local"
        assert target_user.name == ""
        assert target_user.is_active is False
        assert not target_user.has_usable_password()

    def test_anonymizes_author_fields(
        self, gdpr_request, target_user, target_authors, superadmin_user
    ):
        """Task 10.9: Anonymizes Author personal data fields."""
        from doi_portal.articles.models import Author
        from doi_portal.core.services import GdprService

        gdpr_request.requester_email = "target@example.com"
        gdpr_request.save()

        GdprService.process_deletion_request(gdpr_request, superadmin_user)
        GdprService.complete_request(gdpr_request)

        for author in target_authors:
            author.refresh_from_db()
            assert author.given_name == "[Anonimizirano]"
            assert author.surname == "[Anonimizirano]"
            assert author.email == ""
            assert author.orcid == ""
            assert author.orcid_authenticated is False

    def test_sets_completed_status(
        self, gdpr_request, target_user, superadmin_user
    ):
        """complete_request sets status COMPLETED and completed_at."""
        from doi_portal.core.services import GdprService

        gdpr_request.requester_email = "target@example.com"
        gdpr_request.save()

        GdprService.process_deletion_request(gdpr_request, superadmin_user)
        GdprService.complete_request(gdpr_request)

        gdpr_request.refresh_from_db()
        assert gdpr_request.status == GdprRequestStatus.COMPLETED
        assert gdpr_request.completed_at is not None


@pytest.mark.django_db
class TestGdprServiceGenerateReport:
    """Task 10.10: generate_confirmation_report tests."""

    def test_generates_report_text(self, gdpr_request, superadmin_user):
        """Task 10.10: Generates report with all required data."""
        from doi_portal.core.services import GdprService

        gdpr_request.status = GdprRequestStatus.COMPLETED
        gdpr_request.completed_at = timezone.now()
        gdpr_request.save()

        report = GdprService.generate_confirmation_report(gdpr_request)
        assert isinstance(report, str)
        assert "GDPR" in report
        assert gdpr_request.requester_email in report
        assert "test@example.com" in report


# ============================================================================
# Task 11: Tests for views (AC: #1, #2, #7, #8)
# ============================================================================


@pytest.mark.django_db
class TestGdprRequestViews:
    """Task 11.1-11.7: View tests."""

    def test_superadmin_can_access_list(self, superadmin_client):
        """Task 11.1: Superadmin can access GDPR list (200)."""
        url = reverse("core:gdpr-request-list")
        response = superadmin_client.get(url)
        assert response.status_code == 200

    def test_non_superadmin_gets_403(self, regular_client):
        """Task 11.2: Non-Superadmin gets 403."""
        url = reverse("core:gdpr-request-list")
        response = regular_client.get(url)
        assert response.status_code == 403

    def test_create_request(self, superadmin_client):
        """Task 11.3: Creating a request works."""
        url = reverse("core:gdpr-request-create")
        data = {
            "requester_email": "requester@example.com",
            "request_type": GdprRequestType.DELETION,
            "received_date": timezone.now().date().isoformat(),
            "notes": "",
        }
        response = superadmin_client.post(url, data)
        assert response.status_code in (301, 302)
        assert GdprRequest.objects.filter(
            requester_email="requester@example.com"
        ).exists()

    def test_detail_view_shows_affected_data(
        self, superadmin_client, gdpr_request
    ):
        """Task 11.4: Detail view shows affected data section."""
        url = reverse("core:gdpr-request-detail", args=[gdpr_request.pk])
        response = superadmin_client.get(url)
        assert response.status_code == 200
        assert "affected_data" in response.context

    def test_process_endpoint(
        self, superadmin_client, gdpr_request, target_user
    ):
        """Task 11.5: Process endpoint triggers deletion processing."""
        gdpr_request.requester_email = "target@example.com"
        gdpr_request.save()

        url = reverse("core:gdpr-request-process", args=[gdpr_request.pk])
        response = superadmin_client.post(url)
        assert response.status_code in (301, 302)
        gdpr_request.refresh_from_db()
        assert gdpr_request.status == GdprRequestStatus.PROCESSING

    def test_cancel_endpoint(
        self, superadmin_client, gdpr_request, target_user, superadmin_user
    ):
        """Task 11.6: Cancel endpoint cancels the request."""
        from doi_portal.core.services import GdprService

        gdpr_request.requester_email = "target@example.com"
        gdpr_request.save()
        GdprService.process_deletion_request(gdpr_request, superadmin_user)

        url = reverse("core:gdpr-request-cancel", args=[gdpr_request.pk])
        response = superadmin_client.post(
            url, {"cancellation_reason": "Testni razlog"}
        )
        assert response.status_code in (301, 302)
        gdpr_request.refresh_from_db()
        assert gdpr_request.status == GdprRequestStatus.CANCELLED

    def test_download_report(self, superadmin_client, gdpr_request):
        """Task 11.7: Download report returns a file."""
        gdpr_request.status = GdprRequestStatus.COMPLETED
        gdpr_request.completed_at = timezone.now()
        gdpr_request.save()

        url = reverse("core:gdpr-request-report", args=[gdpr_request.pk])
        response = superadmin_client.get(url)
        assert response.status_code == 200
        assert response["Content-Type"] == "text/plain; charset=utf-8"
        assert "attachment" in response["Content-Disposition"]

    def test_non_superadmin_gets_403_on_process(self, regular_client, gdpr_request):
        """Non-Superadmin gets 403 on process endpoint."""
        url = reverse("core:gdpr-request-process", args=[gdpr_request.pk])
        response = regular_client.post(url)
        assert response.status_code == 403

    def test_non_superadmin_gets_403_on_cancel(self, regular_client, gdpr_request):
        """Non-Superadmin gets 403 on cancel endpoint."""
        url = reverse("core:gdpr-request-cancel", args=[gdpr_request.pk])
        response = regular_client.post(url)
        assert response.status_code == 403

    def test_non_superadmin_gets_403_on_report(self, regular_client, gdpr_request):
        """Non-Superadmin gets 403 on report download endpoint."""
        url = reverse("core:gdpr-request-report", args=[gdpr_request.pk])
        response = regular_client.get(url)
        assert response.status_code == 403

    def test_non_superadmin_gets_403_on_create(self, regular_client):
        """Non-Superadmin gets 403 on create endpoint."""
        url = reverse("core:gdpr-request-create")
        response = regular_client.get(url)
        assert response.status_code == 403

    def test_non_superadmin_gets_403_on_detail(self, regular_client, gdpr_request):
        """Non-Superadmin gets 403 on detail endpoint."""
        url = reverse("core:gdpr-request-detail", args=[gdpr_request.pk])
        response = regular_client.get(url)
        assert response.status_code == 403


# ============================================================================
# Task 12: Tests for Celery task (AC: #5, #6)
# ============================================================================


@pytest.mark.django_db
class TestGdprPermanentAnonymizeTask:
    """Task 12.1-12.4: Celery task tests."""

    def test_anonymizes_after_grace_period(
        self, gdpr_request, target_user, superadmin_user
    ):
        """Task 12.1: Task anonymizes user data after grace period."""
        from doi_portal.core.services import GdprService
        from doi_portal.core.tasks import gdpr_permanent_anonymize_task

        gdpr_request.requester_email = "target@example.com"
        gdpr_request.save()
        GdprService.process_deletion_request(gdpr_request, superadmin_user)

        # Set grace period to past
        gdpr_request.grace_period_end = timezone.now().date() - timedelta(days=1)
        gdpr_request.save()

        gdpr_permanent_anonymize_task(gdpr_request.id)
        gdpr_request.refresh_from_db()
        assert gdpr_request.status == GdprRequestStatus.COMPLETED

        target_user.refresh_from_db()
        assert target_user.email == f"deleted_{target_user.pk}@anonymized.local"

    def test_skips_if_grace_period_not_expired(
        self, gdpr_request, target_user, superadmin_user
    ):
        """Task 12.2: Task does not process if grace period not expired."""
        from doi_portal.core.services import GdprService
        from doi_portal.core.tasks import gdpr_permanent_anonymize_task

        gdpr_request.requester_email = "target@example.com"
        gdpr_request.save()
        GdprService.process_deletion_request(gdpr_request, superadmin_user)

        # Grace period is in the future (set by process_deletion_request)
        gdpr_permanent_anonymize_task(gdpr_request.id)
        gdpr_request.refresh_from_db()
        # Status should remain PROCESSING
        assert gdpr_request.status == GdprRequestStatus.PROCESSING

    def test_skips_if_status_not_processing(self, gdpr_request):
        """Task 12.3: Task does not process if status is not PROCESSING."""
        from doi_portal.core.tasks import gdpr_permanent_anonymize_task

        # Status is PENDING, not PROCESSING
        gdpr_permanent_anonymize_task(gdpr_request.id)
        gdpr_request.refresh_from_db()
        assert gdpr_request.status == GdprRequestStatus.PENDING

    def test_sets_completed_status(
        self, gdpr_request, target_user, superadmin_user
    ):
        """Task 12.4: Task sets status to COMPLETED."""
        from doi_portal.core.services import GdprService
        from doi_portal.core.tasks import gdpr_permanent_anonymize_task

        gdpr_request.requester_email = "target@example.com"
        gdpr_request.save()
        GdprService.process_deletion_request(gdpr_request, superadmin_user)

        gdpr_request.grace_period_end = timezone.now().date() - timedelta(days=1)
        gdpr_request.save()

        gdpr_permanent_anonymize_task(gdpr_request.id)
        gdpr_request.refresh_from_db()
        assert gdpr_request.status == GdprRequestStatus.COMPLETED
        assert gdpr_request.completed_at is not None


@pytest.mark.django_db
class TestGdprCheckGracePeriodsTask:
    """Tests for gdpr_check_grace_periods_task periodic task."""

    def test_completes_expired_grace_periods(
        self, gdpr_request, target_user, superadmin_user
    ):
        """Periodic task completes requests with expired grace periods."""
        from doi_portal.core.services import GdprService
        from doi_portal.core.tasks import gdpr_check_grace_periods_task

        gdpr_request.requester_email = "target@example.com"
        gdpr_request.save()
        GdprService.process_deletion_request(gdpr_request, superadmin_user)

        # Set grace period to past
        gdpr_request.grace_period_end = timezone.now().date() - timedelta(days=1)
        gdpr_request.save()

        result = gdpr_check_grace_periods_task()
        assert "1 requests completed" in result

        gdpr_request.refresh_from_db()
        assert gdpr_request.status == GdprRequestStatus.COMPLETED

    def test_skips_non_expired_grace_periods(
        self, gdpr_request, target_user, superadmin_user
    ):
        """Periodic task skips requests with future grace periods."""
        from doi_portal.core.services import GdprService
        from doi_portal.core.tasks import gdpr_check_grace_periods_task

        gdpr_request.requester_email = "target@example.com"
        gdpr_request.save()
        GdprService.process_deletion_request(gdpr_request, superadmin_user)

        # Grace period is in the future
        result = gdpr_check_grace_periods_task()
        assert "0 requests completed" in result

        gdpr_request.refresh_from_db()
        assert gdpr_request.status == GdprRequestStatus.PROCESSING


@pytest.mark.django_db
class TestGdprServiceCancelGracePeriodValidation:
    """Tests for cancel_request grace period expiration validation."""

    def test_cancel_raises_error_after_grace_period_expired(
        self, gdpr_request, target_user, superadmin_user
    ):
        """cancel_request raises ValueError when grace period has expired."""
        from doi_portal.core.services import GdprService

        gdpr_request.requester_email = "target@example.com"
        gdpr_request.save()
        GdprService.process_deletion_request(gdpr_request, superadmin_user)

        # Set grace period to past
        gdpr_request.grace_period_end = timezone.now().date() - timedelta(days=1)
        gdpr_request.save()

        with pytest.raises(ValueError, match="grace period"):
            GdprService.cancel_request(
                gdpr_request, "Kasno otkazivanje", superadmin_user
            )

    def test_cancel_works_during_grace_period(
        self, gdpr_request, target_user, superadmin_user
    ):
        """cancel_request succeeds when grace period is still active."""
        from doi_portal.core.services import GdprService

        gdpr_request.requester_email = "target@example.com"
        gdpr_request.save()
        GdprService.process_deletion_request(gdpr_request, superadmin_user)

        # Grace period is in the future (set by process_deletion_request)
        GdprService.cancel_request(
            gdpr_request, "Pravovremeno otkazivanje", superadmin_user
        )
        gdpr_request.refresh_from_db()
        assert gdpr_request.status == GdprRequestStatus.CANCELLED


# ============================================================================
# Task 13: Regression tests (AC: #8)
# ============================================================================


@pytest.mark.django_db
class TestGdprMenuVisibility:
    """Task 13.2: Sidebar menu shows GDPR only for Superadmin."""

    def test_menu_has_gdpr_for_superadmin(self):
        """GDPR zahtevi menu item exists with Superadmin role."""
        from doi_portal.core.menu import MENU_ITEMS

        assert "gdpr_requests" in MENU_ITEMS
        assert "Superadmin" in MENU_ITEMS["gdpr_requests"]["roles"]

    def test_menu_not_visible_for_non_superadmin(self):
        """GDPR zahtevi only visible to Superadmin."""
        from doi_portal.core.menu import MENU_ITEMS

        gdpr_roles = MENU_ITEMS["gdpr_requests"]["roles"]
        assert gdpr_roles == ["Superadmin"]
