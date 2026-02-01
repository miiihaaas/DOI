"""
Tests for PDF Upload with Virus Scanning.

Story 3.3 - Tasks 1-11: Comprehensive tests for PDF upload, validation,
virus scanning (Celery task), HTMX views, and publisher scoping.
"""

from unittest.mock import MagicMock
from unittest.mock import patch

import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client
from django.urls import reverse

from doi_portal.articles.models import Article
from doi_portal.articles.models import PdfStatus
from doi_portal.articles.validators import MAX_PDF_SIZE
from doi_portal.articles.validators import validate_pdf_file
from doi_portal.issues.tests.factories import IssueFactory
from doi_portal.publications.tests.factories import PublicationFactory
from doi_portal.publications.tests.factories import PublisherFactory

from .factories import ArticleFactory

User = get_user_model()


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def client():
    """Create a test client."""
    return Client()


@pytest.fixture
def publisher_a():
    """Create publisher A."""
    return PublisherFactory(name="Izdavač A")


@pytest.fixture
def publisher_b():
    """Create publisher B."""
    return PublisherFactory(name="Izdavač B")


@pytest.fixture
def bibliotekar_a(publisher_a):
    """Create a Bibliotekar user for publisher A."""
    group, _ = Group.objects.get_or_create(name="Bibliotekar")
    user = User.objects.create_user(
        email="biblio_a@example.com",
        password="testpass123",
    )
    user.groups.add(group)
    user.publisher = publisher_a
    user.save()
    return user


@pytest.fixture
def bibliotekar_b(publisher_b):
    """Create a Bibliotekar user for publisher B."""
    group, _ = Group.objects.get_or_create(name="Bibliotekar")
    user = User.objects.create_user(
        email="biblio_b@example.com",
        password="testpass123",
    )
    user.groups.add(group)
    user.publisher = publisher_b
    user.save()
    return user


@pytest.fixture
def admin_user():
    """Create an Administrator user."""
    group, _ = Group.objects.get_or_create(name="Administrator")
    user = User.objects.create_user(
        email="admin@example.com",
        password="testpass123",
    )
    user.groups.add(group)
    user.save()
    return user


@pytest.fixture
def article_a(publisher_a):
    """Create an article under publisher A."""
    publication = PublicationFactory(publisher=publisher_a)
    issue = IssueFactory(publication=publication)
    return ArticleFactory(issue=issue)


@pytest.fixture
def article_b(publisher_b):
    """Create an article under publisher B."""
    publication = PublicationFactory(publisher=publisher_b)
    issue = IssueFactory(publication=publication)
    return ArticleFactory(issue=issue)


@pytest.fixture
def pdf_file():
    """Create a simple PDF file for testing."""
    content = (
        b"%PDF-1.4\n1 0 obj\n<<\n>>\nendobj\nxref\n0 1\n"
        b"0000000000 65535 f \ntrailer\n<<\n>>\nstartxref\n9\n%%EOF"
    )
    return SimpleUploadedFile("test.pdf", content, content_type="application/pdf")


@pytest.fixture
def non_pdf_file():
    """Create a non-PDF file."""
    return SimpleUploadedFile("test.txt", b"not a pdf", content_type="text/plain")


@pytest.fixture
def wrong_extension_file():
    """Create a file with wrong extension but PDF content type."""
    return SimpleUploadedFile("test.docx", b"some content", content_type="application/pdf")


@pytest.fixture
def wrong_content_type_file():
    """Create a file with PDF extension but wrong content type."""
    return SimpleUploadedFile("test.pdf", b"some content", content_type="text/plain")


# =============================================================================
# Task 1: Model Tests - PdfStatus choices, pdf_status field, pdf_original_filename
# =============================================================================


@pytest.mark.django_db
class TestPdfStatusModel:
    """Tests for PdfStatus enum and Article model fields."""

    def test_pdf_status_choices_exist(self):
        """PdfStatus has all required choices."""
        values = [c[0] for c in PdfStatus.choices]
        assert "none" in values
        assert "uploading" in values
        assert "scanning" in values
        assert "clean" in values
        assert "infected" in values
        assert "scan_failed" in values

    def test_pdf_status_labels_serbian(self):
        """PdfStatus labels are in Serbian with proper diacritics."""
        labels = dict(PdfStatus.choices)
        assert str(labels["none"]) == "Nema PDF-a"
        assert str(labels["clean"]) == "Čist"
        assert str(labels["infected"]) == "Inficiran"
        assert str(labels["scanning"]) == "Skeniranje"
        assert str(labels["scan_failed"]) == "Skeniranje neuspešno"

    def test_article_pdf_status_default_none(self):
        """New article has pdf_status=NONE by default."""
        article = ArticleFactory()
        assert article.pdf_status == PdfStatus.NONE

    def test_article_pdf_original_filename_blank(self):
        """New article has empty pdf_original_filename."""
        article = ArticleFactory()
        assert article.pdf_original_filename == ""

    def test_article_pdf_status_can_be_set(self):
        """Article pdf_status can be changed to any valid value."""
        article = ArticleFactory()
        article.pdf_status = PdfStatus.SCANNING
        article.save(update_fields=["pdf_status"])
        article.refresh_from_db()
        assert article.pdf_status == PdfStatus.SCANNING

    def test_article_pdf_original_filename_can_be_set(self):
        """Article pdf_original_filename can be set."""
        article = ArticleFactory()
        article.pdf_original_filename = "document.pdf"
        article.save(update_fields=["pdf_original_filename"])
        article.refresh_from_db()
        assert article.pdf_original_filename == "document.pdf"


# =============================================================================
# Task 2: Validator Tests - validate_pdf_file
# =============================================================================


class TestPdfValidator:
    """Tests for validate_pdf_file function."""

    def test_valid_pdf_no_errors(self, pdf_file):
        """Valid PDF file returns no errors."""
        errors = validate_pdf_file(pdf_file)
        assert errors == []

    def test_wrong_extension_rejected(self, wrong_extension_file):
        """File with non-.pdf extension is rejected."""
        errors = validate_pdf_file(wrong_extension_file)
        assert len(errors) == 1
        assert "Dozvoljeni su samo PDF fajlovi." in errors[0]

    def test_wrong_content_type_rejected(self, wrong_content_type_file):
        """File with non-PDF content type is rejected."""
        errors = validate_pdf_file(wrong_content_type_file)
        assert len(errors) == 1
        assert "Dozvoljeni su samo PDF fajlovi." in errors[0]

    def test_non_pdf_file_rejected(self, non_pdf_file):
        """Non-PDF file is rejected by extension check."""
        errors = validate_pdf_file(non_pdf_file)
        assert len(errors) == 1
        assert "Dozvoljeni su samo PDF fajlovi." in errors[0]

    def test_oversized_file_rejected(self):
        """File exceeding 100MB is rejected."""
        # Create a mock file object with size > 100MB
        large_file = SimpleUploadedFile(
            "large.pdf", b"x", content_type="application/pdf",
        )
        large_file.size = MAX_PDF_SIZE + 1
        errors = validate_pdf_file(large_file)
        assert len(errors) == 1
        assert "Maksimalna veličina fajla je 100 MB." in errors[0]

    def test_exact_max_size_accepted(self):
        """File exactly at 100MB limit is accepted."""
        file = SimpleUploadedFile(
            "exact.pdf", b"x", content_type="application/pdf",
        )
        file.size = MAX_PDF_SIZE
        errors = validate_pdf_file(file)
        assert errors == []

    def test_case_insensitive_extension(self):
        """PDF extension check is case-insensitive."""
        file = SimpleUploadedFile(
            "test.PDF", b"%PDF", content_type="application/pdf",
        )
        file.size = 100
        errors = validate_pdf_file(file)
        assert errors == []


# =============================================================================
# Task 3: Celery Task Tests - virus_scan_pdf_task
# =============================================================================


@pytest.mark.django_db
class TestVirusScanTask:
    """Tests for virus_scan_pdf_task Celery task."""

    @patch("doi_portal.articles.tasks.pyclamd")
    def test_clean_pdf_sets_status_clean(self, mock_pyclamd):
        """Clean PDF passes virus scan and sets status to clean."""
        mock_cd = MagicMock()
        mock_cd.ping.return_value = True
        mock_cd.scan_stream.return_value = None  # None = clean
        mock_pyclamd.ClamdNetworkSocket.return_value = mock_cd

        article = ArticleFactory(pdf_status=PdfStatus.SCANNING)
        # Create a file so pdf_file.read() works
        article.pdf_file.save("test.pdf", SimpleUploadedFile("test.pdf", b"%PDF-1.4"))

        from doi_portal.articles.tasks import virus_scan_pdf_task

        virus_scan_pdf_task(article.id)

        article.refresh_from_db()
        assert article.pdf_status == PdfStatus.CLEAN

    @patch("doi_portal.articles.tasks.pyclamd")
    def test_infected_pdf_sets_status_infected(self, mock_pyclamd):
        """Infected PDF is detected, file deleted, status set to infected."""
        mock_cd = MagicMock()
        mock_cd.ping.return_value = True
        mock_cd.scan_stream.return_value = {"stream": ("FOUND", "Eicar-Test-Signature")}
        mock_pyclamd.ClamdNetworkSocket.return_value = mock_cd

        article = ArticleFactory(
            pdf_status=PdfStatus.SCANNING,
            pdf_original_filename="test.pdf",
        )
        article.pdf_file.save("test.pdf", SimpleUploadedFile("test.pdf", b"%PDF-1.4"))

        from doi_portal.articles.tasks import virus_scan_pdf_task

        virus_scan_pdf_task(article.id)

        article.refresh_from_db()
        assert article.pdf_status == PdfStatus.INFECTED
        assert not article.pdf_file
        assert article.pdf_original_filename == ""

    @patch("doi_portal.articles.tasks.pyclamd")
    def test_connection_failure_sets_scan_failed(self, mock_pyclamd):
        """ClamAV connection failure after max retries sets scan_failed."""
        mock_pyclamd.ClamdNetworkSocket.side_effect = ConnectionError("ClamAV down")

        article = ArticleFactory(pdf_status=PdfStatus.SCANNING)
        article.pdf_file.save("test.pdf", SimpleUploadedFile("test.pdf", b"%PDF-1.4"))

        from doi_portal.articles.tasks import virus_scan_pdf_task

        # Simulate max retries exceeded by directly patching self.retry
        # to raise MaxRetriesExceededError immediately
        with patch.object(
            virus_scan_pdf_task, "retry",
            side_effect=virus_scan_pdf_task.MaxRetriesExceededError(),
        ):
            virus_scan_pdf_task(article.id)

        article.refresh_from_db()
        assert article.pdf_status == PdfStatus.SCAN_FAILED

    @patch("doi_portal.articles.tasks.pyclamd")
    def test_nonexistent_article_logs_error(self, mock_pyclamd):
        """Task handles nonexistent article gracefully."""
        from doi_portal.articles.tasks import virus_scan_pdf_task

        # Should not raise - just logs and returns
        virus_scan_pdf_task(99999)

    @patch("doi_portal.articles.tasks._delete_old_pdf")
    @patch("doi_portal.articles.tasks.pyclamd")
    def test_clean_scan_deletes_old_pdf(self, mock_pyclamd, mock_delete_old):
        """Clean scan of replacement PDF deletes old file."""
        mock_cd = MagicMock()
        mock_cd.ping.return_value = True
        mock_cd.scan_stream.return_value = None
        mock_pyclamd.ClamdNetworkSocket.return_value = mock_cd

        article = ArticleFactory(pdf_status=PdfStatus.SCANNING)
        article.pdf_file.save("new.pdf", SimpleUploadedFile("new.pdf", b"%PDF-1.4"))

        from doi_portal.articles.tasks import virus_scan_pdf_task

        virus_scan_pdf_task(article.id, old_pdf_path="articles/pdfs/old.pdf")

        article.refresh_from_db()
        assert article.pdf_status == PdfStatus.CLEAN
        mock_delete_old.assert_called_once_with("articles/pdfs/old.pdf")

    @patch("doi_portal.articles.tasks.pyclamd")
    def test_infected_scan_does_not_delete_old_pdf(self, mock_pyclamd):
        """Infected scan of replacement PDF does NOT delete old file."""
        mock_cd = MagicMock()
        mock_cd.ping.return_value = True
        mock_cd.scan_stream.return_value = {"stream": ("FOUND", "Malware")}
        mock_pyclamd.ClamdNetworkSocket.return_value = mock_cd

        article = ArticleFactory(
            pdf_status=PdfStatus.SCANNING,
            pdf_original_filename="new.pdf",
        )
        article.pdf_file.save("new.pdf", SimpleUploadedFile("new.pdf", b"%PDF-1.4"))

        from doi_portal.articles.tasks import virus_scan_pdf_task

        with patch("doi_portal.articles.tasks._delete_old_pdf") as mock_delete:
            virus_scan_pdf_task(article.id, old_pdf_path="articles/pdfs/old.pdf")
            mock_delete.assert_not_called()

        article.refresh_from_db()
        assert article.pdf_status == PdfStatus.INFECTED

    @patch("doi_portal.articles.tasks.pyclamd")
    def test_scan_error_sets_scan_failed(self, mock_pyclamd):
        """Scan error after max retries sets scan_failed."""
        mock_cd = MagicMock()
        mock_cd.ping.return_value = True
        mock_cd.scan_stream.side_effect = Exception("Read error")
        mock_pyclamd.ClamdNetworkSocket.return_value = mock_cd

        article = ArticleFactory(pdf_status=PdfStatus.SCANNING)
        article.pdf_file.save("test.pdf", SimpleUploadedFile("test.pdf", b"%PDF-1.4"))

        from doi_portal.articles.tasks import virus_scan_pdf_task

        # Simulate max retries exceeded by directly patching self.retry
        with patch.object(
            virus_scan_pdf_task, "retry",
            side_effect=virus_scan_pdf_task.MaxRetriesExceededError(),
        ):
            virus_scan_pdf_task(article.id)

        article.refresh_from_db()
        assert article.pdf_status == PdfStatus.SCAN_FAILED


# =============================================================================
# Tasks 4, 5, 6: View Tests - pdf_upload, pdf_status, pdf_delete
# =============================================================================


@pytest.mark.django_db
class TestPdfUploadView:
    """Tests for pdf_upload HTMX view."""

    @patch("doi_portal.articles.tasks.virus_scan_pdf_task")
    def test_upload_valid_pdf(self, mock_task, client, bibliotekar_a, article_a, pdf_file):
        """Valid PDF upload sets status to scanning and triggers task."""
        client.login(email=bibliotekar_a.email, password="testpass123")
        url = reverse("articles:pdf-upload", kwargs={"article_pk": article_a.pk})

        response = client.post(url, {"pdf_file": pdf_file}, HTTP_HX_REQUEST="true")

        assert response.status_code == 200
        article_a.refresh_from_db()
        assert article_a.pdf_status == PdfStatus.SCANNING
        assert article_a.pdf_original_filename == "test.pdf"
        mock_task.delay.assert_called_once()

    def test_upload_no_file(self, client, bibliotekar_a, article_a):
        """Upload without file returns error message."""
        client.login(email=bibliotekar_a.email, password="testpass123")
        url = reverse("articles:pdf-upload", kwargs={"article_pk": article_a.pk})

        response = client.post(url, {}, HTTP_HX_REQUEST="true")

        assert response.status_code == 200
        assert "Izaberite PDF fajl za otpremanje." in response.content.decode()

    def test_upload_non_pdf_file(self, client, bibliotekar_a, article_a, non_pdf_file):
        """Non-PDF file upload returns validation error."""
        client.login(email=bibliotekar_a.email, password="testpass123")
        url = reverse("articles:pdf-upload", kwargs={"article_pk": article_a.pk})

        response = client.post(url, {"pdf_file": non_pdf_file}, HTTP_HX_REQUEST="true")

        assert response.status_code == 200
        assert "Dozvoljeni su samo PDF fajlovi." in response.content.decode()
        article_a.refresh_from_db()
        assert article_a.pdf_status == PdfStatus.NONE

    def test_upload_requires_login(self, client, article_a, pdf_file):
        """Upload endpoint requires authentication."""
        url = reverse("articles:pdf-upload", kwargs={"article_pk": article_a.pk})
        response = client.post(url, {"pdf_file": pdf_file})
        assert response.status_code == 302  # Redirect to login

    def test_upload_requires_post(self, client, bibliotekar_a, article_a):
        """Upload endpoint only accepts POST requests."""
        client.login(email=bibliotekar_a.email, password="testpass123")
        url = reverse("articles:pdf-upload", kwargs={"article_pk": article_a.pk})
        response = client.get(url)
        assert response.status_code == 405  # Method Not Allowed

    @patch("doi_portal.articles.tasks.virus_scan_pdf_task")
    def test_upload_replacement_passes_old_path(
        self, mock_task, client, bibliotekar_a, article_a, pdf_file,
    ):
        """Replacing existing PDF passes old_pdf_path to task."""
        # Set up article with existing PDF
        article_a.pdf_file.save(
            "old.pdf",
            SimpleUploadedFile("old.pdf", b"%PDF-1.4"),
        )
        article_a.pdf_status = PdfStatus.CLEAN
        article_a.save()
        old_path = article_a.pdf_file.name

        client.login(email=bibliotekar_a.email, password="testpass123")
        url = reverse("articles:pdf-upload", kwargs={"article_pk": article_a.pk})

        response = client.post(url, {"pdf_file": pdf_file}, HTTP_HX_REQUEST="true")

        assert response.status_code == 200
        mock_task.delay.assert_called_once()
        call_kwargs = mock_task.delay.call_args
        assert call_kwargs[1].get("old_pdf_path") == old_path or call_kwargs[0][1] == old_path


@pytest.mark.django_db
class TestPdfStatusView:
    """Tests for pdf_status HTMX polling view."""

    def test_status_returns_html(self, client, bibliotekar_a, article_a):
        """Status endpoint returns HTML fragment."""
        client.login(email=bibliotekar_a.email, password="testpass123")
        url = reverse("articles:pdf-status", kwargs={"article_pk": article_a.pk})

        response = client.get(url, HTTP_HX_REQUEST="true")

        assert response.status_code == 200
        assert b"pdf-section" in response.content

    def test_status_scanning_includes_polling(self, client, bibliotekar_a, article_a):
        """Scanning status includes HTMX polling trigger."""
        article_a.pdf_status = PdfStatus.SCANNING
        article_a.save(update_fields=["pdf_status"])

        client.login(email=bibliotekar_a.email, password="testpass123")
        url = reverse("articles:pdf-status", kwargs={"article_pk": article_a.pk})

        response = client.get(url, HTTP_HX_REQUEST="true")

        content = response.content.decode()
        assert "every 3s" in content
        assert "Skeniranje u toku..." in content

    def test_status_clean_shows_filename(self, client, bibliotekar_a, article_a):
        """Clean status shows filename and checkmark."""
        article_a.pdf_status = PdfStatus.CLEAN
        article_a.pdf_original_filename = "document.pdf"
        article_a.save(update_fields=["pdf_status", "pdf_original_filename"])

        client.login(email=bibliotekar_a.email, password="testpass123")
        url = reverse("articles:pdf-status", kwargs={"article_pk": article_a.pk})

        response = client.get(url, HTTP_HX_REQUEST="true")

        content = response.content.decode()
        assert "document.pdf" in content
        assert "Čist" in content

    def test_status_infected_shows_warning(self, client, bibliotekar_a, article_a):
        """Infected status shows warning message."""
        article_a.pdf_status = PdfStatus.INFECTED
        article_a.save(update_fields=["pdf_status"])

        client.login(email=bibliotekar_a.email, password="testpass123")
        url = reverse("articles:pdf-status", kwargs={"article_pk": article_a.pk})

        response = client.get(url, HTTP_HX_REQUEST="true")

        content = response.content.decode()
        assert "detektovana bezbednosna pretnja" in content

    def test_status_scan_failed_shows_retry(self, client, bibliotekar_a, article_a):
        """Scan failed status shows retry message."""
        article_a.pdf_status = PdfStatus.SCAN_FAILED
        article_a.save(update_fields=["pdf_status"])

        client.login(email=bibliotekar_a.email, password="testpass123")
        url = reverse("articles:pdf-status", kwargs={"article_pk": article_a.pk})

        response = client.get(url, HTTP_HX_REQUEST="true")

        content = response.content.decode()
        assert "Skeniranje neuspešno" in content

    def test_status_none_shows_upload_form(self, client, bibliotekar_a, article_a):
        """None status shows upload form."""
        client.login(email=bibliotekar_a.email, password="testpass123")
        url = reverse("articles:pdf-status", kwargs={"article_pk": article_a.pk})

        response = client.get(url, HTTP_HX_REQUEST="true")

        content = response.content.decode()
        assert "Prevucite PDF fajl ovde" in content

    def test_status_requires_login(self, client, article_a):
        """Status endpoint requires authentication."""
        url = reverse("articles:pdf-status", kwargs={"article_pk": article_a.pk})
        response = client.get(url)
        assert response.status_code == 302

    def test_status_requires_get(self, client, bibliotekar_a, article_a):
        """Status endpoint only accepts GET requests."""
        client.login(email=bibliotekar_a.email, password="testpass123")
        url = reverse("articles:pdf-status", kwargs={"article_pk": article_a.pk})
        response = client.post(url)
        assert response.status_code == 405


@pytest.mark.django_db
class TestPdfDeleteView:
    """Tests for pdf_delete HTMX view."""

    def test_delete_resets_fields(self, client, bibliotekar_a, article_a):
        """Delete removes file and resets status to NONE."""
        article_a.pdf_file.save(
            "to_delete.pdf",
            SimpleUploadedFile("to_delete.pdf", b"%PDF-1.4"),
        )
        article_a.pdf_status = PdfStatus.CLEAN
        article_a.pdf_original_filename = "to_delete.pdf"
        article_a.save()

        client.login(email=bibliotekar_a.email, password="testpass123")
        url = reverse("articles:pdf-delete", kwargs={"article_pk": article_a.pk})

        response = client.post(url, HTTP_HX_REQUEST="true")

        assert response.status_code == 200
        article_a.refresh_from_db()
        assert article_a.pdf_status == PdfStatus.NONE
        assert article_a.pdf_original_filename == ""
        assert not article_a.pdf_file

    def test_delete_requires_login(self, client, article_a):
        """Delete endpoint requires authentication."""
        url = reverse("articles:pdf-delete", kwargs={"article_pk": article_a.pk})
        response = client.post(url)
        assert response.status_code == 302

    def test_delete_requires_post(self, client, bibliotekar_a, article_a):
        """Delete endpoint only accepts POST requests."""
        client.login(email=bibliotekar_a.email, password="testpass123")
        url = reverse("articles:pdf-delete", kwargs={"article_pk": article_a.pk})
        response = client.get(url)
        assert response.status_code == 405

    def test_delete_without_file(self, client, bibliotekar_a, article_a):
        """Delete without existing file still resets status."""
        client.login(email=bibliotekar_a.email, password="testpass123")
        url = reverse("articles:pdf-delete", kwargs={"article_pk": article_a.pk})

        response = client.post(url, HTTP_HX_REQUEST="true")

        assert response.status_code == 200
        article_a.refresh_from_db()
        assert article_a.pdf_status == PdfStatus.NONE

    def test_delete_blocked_during_scanning(self, client, bibliotekar_a, article_a):
        """Delete is blocked while virus scan is in progress."""
        article_a.pdf_file.save(
            "scanning.pdf",
            SimpleUploadedFile("scanning.pdf", b"%PDF-1.4"),
        )
        article_a.pdf_status = PdfStatus.SCANNING
        article_a.pdf_original_filename = "scanning.pdf"
        article_a.save()

        client.login(email=bibliotekar_a.email, password="testpass123")
        url = reverse("articles:pdf-delete", kwargs={"article_pk": article_a.pk})

        response = client.post(url, HTTP_HX_REQUEST="true")

        assert response.status_code == 200
        content = response.content.decode()
        assert "skeniranje u toku" in content.lower()
        # Status should remain SCANNING - not reset
        article_a.refresh_from_db()
        assert article_a.pdf_status == PdfStatus.SCANNING


# =============================================================================
# Task 11.6: Permission Tests - publisher scoping for PDF endpoints
# =============================================================================


@pytest.mark.django_db
class TestPdfPermissions:
    """Tests for publisher-scoped permissions on PDF endpoints."""

    @patch("doi_portal.articles.tasks.virus_scan_pdf_task")
    def test_bibliotekar_can_upload_own_publisher(
        self, mock_task, client, bibliotekar_a, article_a, pdf_file,
    ):
        """Bibliotekar can upload PDF to own publisher's article."""
        client.login(email=bibliotekar_a.email, password="testpass123")
        url = reverse("articles:pdf-upload", kwargs={"article_pk": article_a.pk})

        response = client.post(url, {"pdf_file": pdf_file}, HTTP_HX_REQUEST="true")

        assert response.status_code == 200

    def test_bibliotekar_cannot_upload_other_publisher(
        self, client, bibliotekar_b, article_a, pdf_file,
    ):
        """Bibliotekar cannot upload PDF to other publisher's article."""
        client.login(email=bibliotekar_b.email, password="testpass123")
        url = reverse("articles:pdf-upload", kwargs={"article_pk": article_a.pk})

        response = client.post(url, {"pdf_file": pdf_file}, HTTP_HX_REQUEST="true")

        assert response.status_code == 403

    def test_bibliotekar_cannot_get_status_other_publisher(
        self, client, bibliotekar_b, article_a,
    ):
        """Bibliotekar cannot poll status of other publisher's article."""
        client.login(email=bibliotekar_b.email, password="testpass123")
        url = reverse("articles:pdf-status", kwargs={"article_pk": article_a.pk})

        response = client.get(url, HTTP_HX_REQUEST="true")

        assert response.status_code == 403

    def test_bibliotekar_cannot_delete_other_publisher(
        self, client, bibliotekar_b, article_a,
    ):
        """Bibliotekar cannot delete PDF from other publisher's article."""
        client.login(email=bibliotekar_b.email, password="testpass123")
        url = reverse("articles:pdf-delete", kwargs={"article_pk": article_a.pk})

        response = client.post(url, HTTP_HX_REQUEST="true")

        assert response.status_code == 403

    @patch("doi_portal.articles.tasks.virus_scan_pdf_task")
    def test_admin_can_access_any_publisher(
        self, mock_task, client, admin_user, article_a, pdf_file,
    ):
        """Administrator can upload PDF to any article."""
        client.login(email=admin_user.email, password="testpass123")
        url = reverse("articles:pdf-upload", kwargs={"article_pk": article_a.pk})

        response = client.post(url, {"pdf_file": pdf_file}, HTTP_HX_REQUEST="true")

        assert response.status_code == 200


# =============================================================================
# URL routing tests
# =============================================================================


@pytest.mark.django_db
class TestPdfUrls:
    """Tests for PDF URL routing."""

    def test_pdf_upload_url_resolves(self):
        """PDF upload URL resolves correctly."""
        url = reverse("articles:pdf-upload", kwargs={"article_pk": 1})
        assert "/pdf/upload/" in url

    def test_pdf_status_url_resolves(self):
        """PDF status URL resolves correctly."""
        url = reverse("articles:pdf-status", kwargs={"article_pk": 1})
        assert "/pdf/status/" in url

    def test_pdf_delete_url_resolves(self):
        """PDF delete URL resolves correctly."""
        url = reverse("articles:pdf-delete", kwargs={"article_pk": 1})
        assert "/pdf/delete/" in url
