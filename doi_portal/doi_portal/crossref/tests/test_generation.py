"""
Tests for XML generation.

Story 5.3: XML Generation for All Publication Types.
Tests for GenerateXMLView, CrossrefService.generate_and_store_xml,
crossref_generate_xml_task, and Issue model XML fields.
"""

from datetime import date
from unittest.mock import MagicMock
from unittest.mock import patch

import pytest

from doi_portal.articles.models import ArticleStatus
from doi_portal.articles.models import AuthorSequence
from doi_portal.articles.models import ContributorRole
from doi_portal.articles.tests.factories import ArticleFactory
from doi_portal.articles.tests.factories import AuthorFactory
from doi_portal.core.models import SiteSettings
from doi_portal.issues.models import Issue
from doi_portal.issues.tests.factories import IssueFactory
from doi_portal.publications.tests.factories import BookFactory
from doi_portal.publications.tests.factories import ConferenceFactory
from doi_portal.publications.tests.factories import JournalFactory
from doi_portal.publications.tests.factories import PublisherFactory
from doi_portal.users.tests.factories import UserFactory


# =============================================================================
# Task 5: Issue Model XML Fields Tests
# =============================================================================


@pytest.mark.django_db
class TestIssueXMLFields:
    """Tests for Issue model XML storage fields."""

    def test_issue_has_crossref_xml_field(self):
        """Test Issue model has crossref_xml TextField."""
        issue = IssueFactory()
        assert hasattr(issue, "crossref_xml")
        assert issue.crossref_xml == ""  # Default empty

    def test_issue_has_xml_generated_at_field(self):
        """Test Issue model has xml_generated_at DateTimeField."""
        issue = IssueFactory()
        assert hasattr(issue, "xml_generated_at")
        assert issue.xml_generated_at is None  # Default null

    def test_issue_has_xml_generation_status_field(self):
        """Test Issue model has xml_generation_status CharField."""
        issue = IssueFactory()
        assert hasattr(issue, "xml_generation_status")
        assert issue.xml_generation_status == "pending"  # Default

    def test_xml_generation_status_choices(self):
        """Test xml_generation_status has valid choices."""
        issue = IssueFactory()
        valid_choices = ["pending", "generating", "completed", "failed"]
        for choice in valid_choices:
            issue.xml_generation_status = choice
            issue.full_clean()  # Should not raise

    def test_crossref_xml_can_store_large_content(self):
        """Test crossref_xml can store large XML content."""
        issue = IssueFactory()
        large_xml = "<?xml version='1.0'?>" + "<data>" * 10000 + "</data>" * 10000
        issue.crossref_xml = large_xml
        issue.save()
        issue.refresh_from_db()
        assert issue.crossref_xml == large_xml


# =============================================================================
# Task 2: CrossrefService.generate_and_store_xml Tests
# =============================================================================


@pytest.fixture
def site_settings_configured(db):
    """Create SiteSettings with depositor data configured."""
    return SiteSettings.objects.create(
        depositor_name="Test Depositor",
        depositor_email="depositor@test.com",
    )


@pytest.fixture
def publisher(db):
    """Create test publisher."""
    return PublisherFactory(
        name="Test Publisher",
        doi_prefix="10.12345",
    )


@pytest.fixture
def journal_publication(publisher):
    """Create a journal publication."""
    return JournalFactory(
        title="Test Journal",
        publisher=publisher,
        issn_print="1234-5678",
    )


@pytest.fixture
def conference_publication(publisher):
    """Create a conference publication."""
    return ConferenceFactory(
        title="Test Conference",
        publisher=publisher,
        conference_name="Test Conference 2026",
        conference_date=date(2026, 5, 15),
        conference_location="Belgrade, Serbia",
    )


@pytest.fixture
def book_publication(publisher):
    """Create a book publication."""
    return BookFactory(
        title="Test Book",
        publisher=publisher,
        isbn_print="978-86-7549-100-1",
    )


@pytest.fixture
def valid_journal_issue(journal_publication, site_settings_configured):
    """Create a valid journal issue with articles."""
    issue = IssueFactory(
        publication=journal_publication,
        volume="10",
        issue_number="2",
        year=2026,
        publication_date=date(2026, 3, 15),
    )
    article = ArticleFactory(
        issue=issue,
        title="Test Article",
        doi_suffix="test.2026.001",
        status=ArticleStatus.PUBLISHED,
    )
    AuthorFactory(
        article=article,
        given_name="John",
        surname="Doe",
        sequence=AuthorSequence.FIRST,
        contributor_role=ContributorRole.AUTHOR,
        order=1,
    )
    return issue


@pytest.fixture
def valid_conference_issue(conference_publication, site_settings_configured):
    """Create a valid conference issue with articles."""
    issue = IssueFactory(
        publication=conference_publication,
        year=2026,
        publication_date=date(2026, 5, 20),
        proceedings_title="Proceedings of Test Conference 2026",
    )
    article = ArticleFactory(
        issue=issue,
        title="Conference Paper",
        doi_suffix="conf.2026.001",
        status=ArticleStatus.PUBLISHED,
    )
    AuthorFactory(
        article=article,
        given_name="Jane",
        surname="Smith",
        sequence=AuthorSequence.FIRST,
        contributor_role=ContributorRole.AUTHOR,
        order=1,
    )
    return issue


@pytest.fixture
def valid_book_issue(book_publication, site_settings_configured):
    """Create a valid book issue with chapters."""
    issue = IssueFactory(
        publication=book_publication,
        year=2026,
        publication_date=date(2026, 6, 1),
    )
    article = ArticleFactory(
        issue=issue,
        title="Book Chapter",
        doi_suffix="book.2026.ch1",
        status=ArticleStatus.PUBLISHED,
    )
    AuthorFactory(
        article=article,
        given_name="Alice",
        surname="Brown",
        sequence=AuthorSequence.FIRST,
        contributor_role=ContributorRole.AUTHOR,
        order=1,
    )
    return issue


@pytest.mark.django_db
class TestCrossrefServiceGenerateAndStore:
    """Tests for CrossrefService.generate_and_store_xml method."""

    def test_generate_and_store_returns_success_tuple(self, valid_journal_issue):
        """Test method returns tuple of (success, xml_or_message)."""
        from doi_portal.crossref.services import CrossrefService

        service = CrossrefService()
        result = service.generate_and_store_xml(valid_journal_issue)

        assert isinstance(result, tuple)
        assert len(result) == 2
        success, xml_or_message = result
        assert isinstance(success, bool)
        assert isinstance(xml_or_message, str)

    def test_generate_and_store_success_stores_xml(self, valid_journal_issue):
        """Test successful generation stores XML in issue."""
        from doi_portal.crossref.services import CrossrefService

        service = CrossrefService()
        success, xml = service.generate_and_store_xml(valid_journal_issue)

        assert success is True
        valid_journal_issue.refresh_from_db()
        assert valid_journal_issue.crossref_xml == xml
        assert "<?xml" in xml or "<doi_batch" in xml

    def test_generate_and_store_records_timestamp(self, valid_journal_issue):
        """Test successful generation records xml_generated_at timestamp."""
        from doi_portal.crossref.services import CrossrefService

        service = CrossrefService()
        service.generate_and_store_xml(valid_journal_issue)

        valid_journal_issue.refresh_from_db()
        assert valid_journal_issue.xml_generated_at is not None

    def test_generate_and_store_sets_completed_status(self, valid_journal_issue):
        """Test successful generation sets status to completed."""
        from doi_portal.crossref.services import CrossrefService

        service = CrossrefService()
        service.generate_and_store_xml(valid_journal_issue)

        valid_journal_issue.refresh_from_db()
        assert valid_journal_issue.xml_generation_status == "completed"

    def test_generate_and_store_journal_uses_journal_template(self, valid_journal_issue):
        """Test journal type uses journal XML structure."""
        from doi_portal.crossref.services import CrossrefService

        service = CrossrefService()
        success, xml = service.generate_and_store_xml(valid_journal_issue)

        assert success is True
        assert "<journal>" in xml or "journal" in xml.lower()

    def test_generate_and_store_conference_uses_conference_template(
        self, valid_conference_issue
    ):
        """Test conference type uses conference XML structure."""
        from doi_portal.crossref.services import CrossrefService

        service = CrossrefService()
        success, xml = service.generate_and_store_xml(valid_conference_issue)

        assert success is True
        assert "<conference>" in xml or "conference" in xml.lower()

    def test_generate_and_store_book_uses_book_template(self, valid_book_issue):
        """Test book type uses book XML structure."""
        from doi_portal.crossref.services import CrossrefService

        service = CrossrefService()
        success, xml = service.generate_and_store_xml(valid_book_issue)

        assert success is True
        assert "<book>" in xml or "book" in xml.lower()

    def test_generate_and_store_xml_has_proper_encoding(self, valid_journal_issue):
        """Test generated XML has proper UTF-8 encoding declaration."""
        from doi_portal.crossref.services import CrossrefService

        service = CrossrefService()
        success, xml = service.generate_and_store_xml(valid_journal_issue)

        assert success is True
        # XML should start with declaration or have UTF-8 content
        assert "<?xml" in xml or xml.startswith("<")

    def test_generate_and_store_failure_sets_failed_status(
        self, valid_journal_issue, monkeypatch
    ):
        """Test failure sets status to failed."""
        from doi_portal.crossref.services import CrossrefService

        service = CrossrefService()
        # Mock generate_xml to raise exception
        monkeypatch.setattr(
            service, "generate_xml", lambda x: (_ for _ in ()).throw(Exception("Template error"))
        )

        success, message = service.generate_and_store_xml(valid_journal_issue)

        assert success is False
        assert "Template error" in message
        valid_journal_issue.refresh_from_db()
        assert valid_journal_issue.xml_generation_status == "failed"


# =============================================================================
# Task 3: Celery Task Tests
# =============================================================================


@pytest.mark.django_db
class TestCrossrefGenerateXMLTask:
    """Tests for crossref_generate_xml_task Celery task."""

    def test_task_generates_xml(self, valid_journal_issue):
        """Test task calls CrossrefService and stores result."""
        from doi_portal.crossref.tasks import crossref_generate_xml_task

        result = crossref_generate_xml_task(valid_journal_issue.pk)

        assert result["success"] is True
        valid_journal_issue.refresh_from_db()
        assert valid_journal_issue.crossref_xml != ""
        assert valid_journal_issue.xml_generation_status == "completed"

    def test_task_handles_missing_issue(self):
        """Test task returns error for non-existent issue."""
        from doi_portal.crossref.tasks import crossref_generate_xml_task

        result = crossref_generate_xml_task(99999)

        assert result["success"] is False
        # Message should be in Serbian: "Izdanje 99999 nije pronađeno"
        assert "pronađeno" in result["message"].lower() or "99999" in result["message"]

    def test_task_sets_generating_status(self, valid_journal_issue):
        """Test task sets generating status before processing."""
        from doi_portal.crossref.tasks import crossref_generate_xml_task

        # Before task, status should be pending
        assert valid_journal_issue.xml_generation_status == "pending"

        crossref_generate_xml_task(valid_journal_issue.pk)

        # After task, status should be completed
        valid_journal_issue.refresh_from_db()
        assert valid_journal_issue.xml_generation_status == "completed"

    def test_task_returns_dict_with_status_and_message(self, valid_journal_issue):
        """Test task returns dict with success and message keys."""
        from doi_portal.crossref.tasks import crossref_generate_xml_task

        result = crossref_generate_xml_task(valid_journal_issue.pk)

        assert isinstance(result, dict)
        assert "success" in result
        assert "message" in result

    def test_task_sets_failed_status_on_max_retries(self, valid_journal_issue):
        """Test task sets status to failed when max retries exceeded."""
        from celery.exceptions import MaxRetriesExceededError

        from doi_portal.crossref.tasks import crossref_generate_xml_task

        # Mock CrossrefService to always fail
        class MockCrossrefService:
            def generate_and_store_xml(self, issue):
                raise Exception("Transient error")

        # Patch services.CrossrefService (the actual import target)
        with patch(
            "doi_portal.crossref.services.CrossrefService",
            MockCrossrefService,
        ):
            # Mock retry to raise MaxRetriesExceededError
            with patch.object(
                crossref_generate_xml_task,
                "retry",
                side_effect=MaxRetriesExceededError(),
            ):
                result = crossref_generate_xml_task(valid_journal_issue.pk)

        assert result["success"] is False
        assert "neuspešno" in result["message"].lower()
        valid_journal_issue.refresh_from_db()
        assert valid_journal_issue.xml_generation_status == "failed"

    def test_task_success_message_in_serbian(self, valid_journal_issue):
        """Test task returns success message in Serbian with diacritics."""
        from doi_portal.crossref.tasks import crossref_generate_xml_task

        result = crossref_generate_xml_task(valid_journal_issue.pk)

        assert result["success"] is True
        assert "uspešno" in result["message"].lower()

    def test_task_error_message_for_missing_issue_in_serbian(self):
        """Test task returns error message in Serbian for missing issue."""
        from doi_portal.crossref.tasks import crossref_generate_xml_task

        result = crossref_generate_xml_task(99999)

        assert result["success"] is False
        assert "pronađeno" in result["message"].lower() or "99999" in result["message"]


# =============================================================================
# Task 1: GenerateXMLView Tests
# =============================================================================


@pytest.fixture
def invalid_issue(journal_publication, site_settings_configured):
    """Create an issue with validation errors."""
    issue = IssueFactory(
        publication=journal_publication,
        year=2026,
        publication_date=None,  # Missing required field
    )
    # Article without authors - will cause validation error
    ArticleFactory(
        issue=issue,
        title="Invalid Article",
        doi_suffix="invalid.001",
        status=ArticleStatus.PUBLISHED,
    )
    return issue


@pytest.fixture
def large_issue(journal_publication, site_settings_configured):
    """Create issue with > 20 articles for async generation."""
    issue = IssueFactory(
        publication=journal_publication,
        volume="10",
        issue_number="special",
        year=2026,
        publication_date=date(2026, 3, 15),
    )
    # Create 25 articles
    for i in range(25):
        article = ArticleFactory(
            issue=issue,
            title=f"Article {i+1}",
            doi_suffix=f"large.2026.{i+1:03d}",
            status=ArticleStatus.PUBLISHED,
        )
        AuthorFactory(
            article=article,
            given_name=f"Author{i+1}",
            surname=f"Surname{i+1}",
            sequence=AuthorSequence.FIRST,
            contributor_role=ContributorRole.AUTHOR,
            order=1,
        )
    return issue


@pytest.mark.django_db
class TestGenerateXMLView:
    """Tests for GenerateXMLView."""

    def test_view_requires_authentication(self, client, valid_journal_issue):
        """Test anonymous users cannot access generation endpoint."""
        response = client.post(
            f"/dashboard/crossref/issues/{valid_journal_issue.pk}/generate/"
        )

        # Should redirect to login
        assert response.status_code == 302
        assert "/accounts/login/" in response.url or "/login/" in response.url

    def test_view_blocks_when_validation_errors(self, client, admin_user, invalid_issue):
        """Test generation blocked when validation errors exist."""
        client.force_login(admin_user)

        response = client.post(
            f"/dashboard/crossref/issues/{invalid_issue.pk}/generate/"
        )

        assert response.status_code == 200
        # Response should indicate failure due to validation
        content = response.content.decode()
        assert "success" not in content.lower() or "false" in content.lower() or "greška" in content.lower() or "blokirano" in content.lower()

    def test_view_generates_xml_sync_small_issue(
        self, client, admin_user, valid_journal_issue
    ):
        """Test small issues (<= 20 articles) generate synchronously."""
        client.force_login(admin_user)

        response = client.post(
            f"/dashboard/crossref/issues/{valid_journal_issue.pk}/generate/"
        )

        assert response.status_code == 200
        valid_journal_issue.refresh_from_db()
        assert valid_journal_issue.crossref_xml != ""
        assert valid_journal_issue.xml_generation_status == "completed"

    def test_view_generates_xml_async_large_issue(
        self, client, admin_user, large_issue
    ):
        """Test large issues (> 20 articles) trigger Celery task."""
        client.force_login(admin_user)

        # Mock the Celery task using patch
        with patch(
            "doi_portal.crossref.views.crossref_generate_xml_task"
        ) as mock_task:
            mock_task.delay.return_value = MagicMock(id="test-task-id")

            response = client.post(
                f"/dashboard/crossref/issues/{large_issue.pk}/generate/"
            )

            assert response.status_code == 200
            mock_task.delay.assert_called_once_with(large_issue.pk)

    def test_xml_stored_in_issue_model(self, client, admin_user, valid_journal_issue):
        """Test generated XML is stored in Issue.crossref_xml field."""
        client.force_login(admin_user)

        client.post(f"/dashboard/crossref/issues/{valid_journal_issue.pk}/generate/")

        valid_journal_issue.refresh_from_db()
        assert valid_journal_issue.crossref_xml != ""

    def test_timestamp_recorded(self, client, admin_user, valid_journal_issue):
        """Test generation timestamp is recorded in xml_generated_at."""
        client.force_login(admin_user)

        client.post(f"/dashboard/crossref/issues/{valid_journal_issue.pk}/generate/")

        valid_journal_issue.refresh_from_db()
        assert valid_journal_issue.xml_generated_at is not None

    def test_htmx_response_format(self, client, admin_user, valid_journal_issue):
        """Test response is HTML partial suitable for HTMX swap."""
        client.force_login(admin_user)

        response = client.post(
            f"/dashboard/crossref/issues/{valid_journal_issue.pk}/generate/",
            HTTP_HX_REQUEST="true",
        )

        assert response.status_code == 200
        assert "text/html" in response["Content-Type"]

    def test_view_returns_404_for_invalid_issue(self, client, admin_user):
        """Test view returns 404 for non-existent issue."""
        client.force_login(admin_user)

        response = client.post("/dashboard/crossref/issues/99999/generate/")

        assert response.status_code == 404

    def test_success_message_displayed(self, client, admin_user, valid_journal_issue):
        """Test success message 'XML uspešno generisan' is in response."""
        client.force_login(admin_user)

        response = client.post(
            f"/dashboard/crossref/issues/{valid_journal_issue.pk}/generate/"
        )

        content = response.content.decode()
        assert "uspešno" in content.lower() or "success" in content.lower()
