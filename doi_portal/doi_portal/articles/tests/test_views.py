"""
Tests for Article views.

Story 3.1 - Task 7: Comprehensive view tests covering AC #1-#6.
"""

import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.test import Client
from django.urls import reverse

from doi_portal.articles.models import Article, ArticleStatus
from doi_portal.issues.tests.factories import IssueFactory
from doi_portal.publications.tests.factories import (
    PublicationFactory,
    PublisherFactory,
)

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
def publication_a(publisher_a):
    """Create publication for publisher A."""
    return PublicationFactory(publisher=publisher_a)


@pytest.fixture
def publication_b(publisher_b):
    """Create publication for publisher B."""
    return PublicationFactory(publisher=publisher_b)


@pytest.fixture
def issue_a(publication_a):
    """Create issue for publication A."""
    return IssueFactory(publication=publication_a, volume="1", issue_number="1")


@pytest.fixture
def issue_b(publication_b):
    """Create issue for publication B."""
    return IssueFactory(publication=publication_b, volume="1", issue_number="1")


@pytest.fixture
def admin_user():
    """Create an admin user."""
    user = User.objects.create_user(
        email="admin@test.com", password="testpass123"
    )
    group, _ = Group.objects.get_or_create(name="Administrator")
    user.groups.add(group)
    return user


@pytest.fixture
def superuser():
    """Create a Django superuser."""
    return User.objects.create_superuser(
        email="super@test.com", password="testpass123"
    )


@pytest.fixture
def urednik_user(publisher_a):
    """Create an Urednik user assigned to publisher A."""
    user = User.objects.create_user(
        email="urednik@test.com",
        password="testpass123",
        publisher=publisher_a,
    )
    group, _ = Group.objects.get_or_create(name="Urednik")
    user.groups.add(group)
    return user


@pytest.fixture
def bibliotekar_user(publisher_a):
    """Create a Bibliotekar user assigned to publisher A."""
    user = User.objects.create_user(
        email="bibliotekar@test.com",
        password="testpass123",
        publisher=publisher_a,
    )
    group, _ = Group.objects.get_or_create(name="Bibliotekar")
    user.groups.add(group)
    return user


@pytest.fixture
def regular_user():
    """Create a regular user without roles."""
    return User.objects.create_user(
        email="user@test.com", password="testpass123"
    )


# =============================================================================
# 7.3: Test ArticleListView
# =============================================================================


@pytest.mark.django_db
class TestArticleListView:
    """Test article list view."""

    def test_list_requires_login(self, client):
        """List view requires authentication."""
        response = client.get(reverse("articles:list"))
        assert response.status_code == 302
        assert "login" in response.url

    def test_list_requires_valid_role(self, client, regular_user):
        """List view requires a valid role."""
        client.force_login(regular_user)
        response = client.get(reverse("articles:list"))
        assert response.status_code == 403

    def test_list_accessible_to_admin(self, client, admin_user):
        """7.3: Admin can access list view."""
        client.force_login(admin_user)
        response = client.get(reverse("articles:list"))
        assert response.status_code == 200

    def test_list_accessible_to_bibliotekar(self, client, bibliotekar_user):
        """7.3: Bibliotekar can access list view."""
        client.force_login(bibliotekar_user)
        response = client.get(reverse("articles:list"))
        assert response.status_code == 200

    def test_list_shows_articles(self, client, admin_user, issue_a):
        """7.3: List view shows articles."""
        ArticleFactory(issue=issue_a, title="Test Article Alpha")
        client.force_login(admin_user)
        response = client.get(reverse("articles:list"))
        assert response.status_code == 200
        assert "Test Article Alpha" in response.content.decode("utf-8")

    def test_urednik_sees_only_own_publisher_articles(
        self, client, urednik_user, issue_a, issue_b
    ):
        """7.4: Urednik sees only articles from assigned publisher."""
        ArticleFactory(issue=issue_a, title="Moj članak")
        ArticleFactory(issue=issue_b, title="Tuđi članak")
        client.force_login(urednik_user)
        response = client.get(reverse("articles:list"))
        content = response.content.decode("utf-8")
        assert "Moj članak" in content
        assert "Tuđi članak" not in content

    def test_admin_sees_all_articles(
        self, client, admin_user, issue_a, issue_b
    ):
        """7.3: Administrator sees all articles (AC #5)."""
        ArticleFactory(issue=issue_a, title="Članak A")
        ArticleFactory(issue=issue_b, title="Članak B")
        client.force_login(admin_user)
        response = client.get(reverse("articles:list"))
        content = response.content.decode("utf-8")
        assert "Članak A" in content
        assert "Članak B" in content

    def test_filter_by_status(self, client, admin_user, issue_a):
        """7.3: Filter articles by status."""
        ArticleFactory(
            issue=issue_a,
            title="Draft Article",
            status=ArticleStatus.DRAFT,
            doi_suffix="flt.001",
        )
        ArticleFactory(
            issue=issue_a,
            title="Published Article",
            status=ArticleStatus.PUBLISHED,
            doi_suffix="flt.002",
        )
        client.force_login(admin_user)
        response = client.get(
            reverse("articles:list"), {"status": "PUBLISHED"}
        )
        content = response.content.decode("utf-8")
        assert "Published Article" in content
        assert "Draft Article" not in content

    def test_filter_by_issue(self, client, admin_user, issue_a, issue_b):
        """7.3: Filter articles by issue."""
        ArticleFactory(issue=issue_a, title="Issue A Article")
        ArticleFactory(issue=issue_b, title="Issue B Article")
        client.force_login(admin_user)
        response = client.get(
            reverse("articles:list"), {"issue": issue_a.pk}
        )
        content = response.content.decode("utf-8")
        assert "Issue A Article" in content
        assert "Issue B Article" not in content


# =============================================================================
# 7.3: Test ArticleCreateView
# =============================================================================


@pytest.mark.django_db
class TestArticleCreateView:
    """Test article create view."""

    def test_create_requires_login(self, client):
        """7.3: Create view requires authentication."""
        response = client.get(reverse("articles:create"))
        assert response.status_code == 302
        assert "login" in response.url

    def test_create_requires_valid_role(self, client, regular_user):
        """7.3: Create view requires a valid role."""
        client.force_login(regular_user)
        response = client.get(reverse("articles:create"))
        assert response.status_code == 403

    def test_create_form_displays(self, client, admin_user):
        """7.3: Create form is accessible."""
        client.force_login(admin_user)
        response = client.get(reverse("articles:create"))
        assert response.status_code == 200
        assert "Novi članak" in response.content.decode("utf-8")

    def test_bibliotekar_can_create_article(
        self, client, bibliotekar_user, issue_a
    ):
        """7.3: Bibliotekar can create articles (AC #2)."""
        client.force_login(bibliotekar_user)
        response = client.post(
            reverse("articles:create"),
            {
                "issue": issue_a.pk,
                "title": "Novi članak bibliotekar",
                "doi_suffix": "bib.001",
                "subtitle": "",
                "abstract": "",
                "keywords": "[]",
                "first_page": "",
                "last_page": "",
                "article_number": "",
                "language": "sr",
                "publication_type": "full_text",
                "license_url": "",
                "license_applies_to": "",
                "free_to_read_start_date": "",
            },
        )
        assert response.status_code == 302  # Redirect on success
        article = Article.objects.get(doi_suffix="bib.001")
        assert article.title == "Novi članak bibliotekar"
        assert article.created_by == bibliotekar_user
        assert article.status == ArticleStatus.DRAFT

    def test_admin_can_create_for_any_issue(
        self, client, admin_user, issue_a, issue_b
    ):
        """7.3: Administrator can create article for any issue."""
        client.force_login(admin_user)
        response = client.post(
            reverse("articles:create"),
            {
                "issue": issue_b.pk,
                "title": "Admin članak",
                "doi_suffix": "adm.001",
                "subtitle": "",
                "abstract": "",
                "keywords": "[]",
                "first_page": "",
                "last_page": "",
                "article_number": "",
                "language": "sr",
                "publication_type": "full_text",
                "license_url": "",
                "license_applies_to": "",
                "free_to_read_start_date": "",
            },
        )
        assert response.status_code == 302
        assert Article.objects.filter(doi_suffix="adm.001", issue=issue_b).exists()

    def test_bibliotekar_cannot_create_for_other_publisher_issue(
        self, client, bibliotekar_user, issue_b
    ):
        """7.4: Bibliotekar cannot create article for another publisher's issue."""
        client.force_login(bibliotekar_user)
        response = client.post(
            reverse("articles:create"),
            {
                "issue": issue_b.pk,
                "title": "Unauthorized article",
                "doi_suffix": "unauth.001",
                "subtitle": "",
                "abstract": "",
                "keywords": "[]",
                "first_page": "",
                "last_page": "",
                "article_number": "",
                "language": "sr",
                "publication_type": "full_text",
                "license_url": "",
                "license_applies_to": "",
                "free_to_read_start_date": "",
            },
        )
        # Form should be invalid because issue_b is not in user's queryset
        assert response.status_code == 200  # Form re-displayed
        assert not Article.objects.filter(doi_suffix="unauth.001").exists()

    def test_create_with_issue_preselect(
        self, client, admin_user, issue_a
    ):
        """7.3: Create form pre-selects issue from query param (AC #2)."""
        client.force_login(admin_user)
        response = client.get(
            reverse("articles:create"),
            {"issue": issue_a.pk},
        )
        assert response.status_code == 200

    def test_created_by_auto_set(self, client, admin_user, issue_a):
        """7.3: created_by is automatically set to current user (AC #4)."""
        client.force_login(admin_user)
        client.post(
            reverse("articles:create"),
            {
                "issue": issue_a.pk,
                "title": "Auto-set test",
                "doi_suffix": "auto.001",
                "subtitle": "",
                "abstract": "",
                "keywords": "[]",
                "first_page": "",
                "last_page": "",
                "article_number": "",
                "language": "sr",
                "publication_type": "full_text",
                "license_url": "",
                "license_applies_to": "",
                "free_to_read_start_date": "",
            },
        )
        article = Article.objects.get(doi_suffix="auto.001")
        assert article.created_by == admin_user

    def test_create_redirects_to_edit(self, client, admin_user, issue_a):
        """7.3: After creation, redirects to edit page (AC #4)."""
        client.force_login(admin_user)
        response = client.post(
            reverse("articles:create"),
            {
                "issue": issue_a.pk,
                "title": "Redirect test",
                "doi_suffix": "redir.001",
                "subtitle": "",
                "abstract": "",
                "keywords": "[]",
                "first_page": "",
                "last_page": "",
                "article_number": "",
                "language": "sr",
                "publication_type": "full_text",
                "license_url": "",
                "license_applies_to": "",
                "free_to_read_start_date": "",
            },
        )
        article = Article.objects.get(doi_suffix="redir.001")
        assert response.status_code == 302
        assert response.url == reverse("articles:update", kwargs={"pk": article.pk})


# =============================================================================
# 7.3: Test ArticleUpdateView
# =============================================================================


@pytest.mark.django_db
class TestArticleUpdateView:
    """Test article update view."""

    def test_update_requires_login(self, client, issue_a):
        """7.3: Update view requires authentication."""
        article = ArticleFactory(issue=issue_a, status=ArticleStatus.DRAFT)
        response = client.get(
            reverse("articles:update", kwargs={"pk": article.pk})
        )
        assert response.status_code == 302
        assert "login" in response.url

    def test_update_requires_valid_role(self, client, regular_user, issue_a):
        """7.3: Update view requires a valid role."""
        article = ArticleFactory(issue=issue_a, status=ArticleStatus.DRAFT)
        client.force_login(regular_user)
        response = client.get(
            reverse("articles:update", kwargs={"pk": article.pk})
        )
        assert response.status_code == 403

    def test_non_draft_article_cannot_be_edited(
        self, client, admin_user, issue_a
    ):
        """7.3: Non-DRAFT article returns 404 on edit (AC #4)."""
        article = ArticleFactory(
            issue=issue_a, status=ArticleStatus.PUBLISHED
        )
        client.force_login(admin_user)
        response = client.get(
            reverse("articles:update", kwargs={"pk": article.pk})
        )
        assert response.status_code == 404

    def test_review_status_article_cannot_be_edited(
        self, client, admin_user, issue_a
    ):
        """7.3: REVIEW status article returns 404 on edit (AC #4)."""
        article = ArticleFactory(
            issue=issue_a, status=ArticleStatus.REVIEW
        )
        client.force_login(admin_user)
        response = client.get(
            reverse("articles:update", kwargs={"pk": article.pk})
        )
        assert response.status_code == 404

    def test_urednik_can_edit_own_article(
        self, client, urednik_user, issue_a
    ):
        """7.3: Urednik can edit articles from assigned publisher."""
        article = ArticleFactory(issue=issue_a, status=ArticleStatus.DRAFT)
        client.force_login(urednik_user)
        response = client.get(
            reverse("articles:update", kwargs={"pk": article.pk})
        )
        assert response.status_code == 200

    def test_urednik_cannot_edit_other_publisher_article(
        self, client, urednik_user, issue_b
    ):
        """7.4: Urednik gets 404 for editing another publisher's article."""
        article = ArticleFactory(issue=issue_b, status=ArticleStatus.DRAFT)
        client.force_login(urednik_user)
        response = client.get(
            reverse("articles:update", kwargs={"pk": article.pk})
        )
        assert response.status_code == 404

    def test_update_changes_data(self, client, admin_user, issue_a):
        """7.3: Update view saves changes."""
        article = ArticleFactory(
            issue=issue_a,
            title="Original",
            status=ArticleStatus.DRAFT,
        )
        client.force_login(admin_user)
        response = client.post(
            reverse("articles:update", kwargs={"pk": article.pk}),
            {
                "issue": issue_a.pk,
                "title": "Updated Title",
                "doi_suffix": article.doi_suffix,
                "subtitle": "",
                "abstract": "Updated abstract",
                "keywords": '["updated"]',
                "first_page": "",
                "last_page": "",
                "article_number": "",
                "language": "sr",
                "publication_type": "full_text",
                "license_url": "",
                "license_applies_to": "",
                "free_to_read_start_date": "",
            },
        )
        assert response.status_code == 302
        article.refresh_from_db()
        assert article.title == "Updated Title"
        assert article.abstract == "Updated abstract"

    def test_bibliotekar_cannot_edit(
        self, client, bibliotekar_user, issue_a
    ):
        """7.4: Bibliotekar can edit DRAFT articles from their publisher."""
        article = ArticleFactory(issue=issue_a, status=ArticleStatus.DRAFT)
        client.force_login(bibliotekar_user)
        response = client.get(
            reverse("articles:update", kwargs={"pk": article.pk})
        )
        assert response.status_code == 200


# =============================================================================
# 7.3: Test ArticleDetailView
# =============================================================================


@pytest.mark.django_db
class TestArticleDetailView:
    """Test article detail view."""

    def test_detail_requires_login(self, client, issue_a):
        """7.3: Detail view requires authentication."""
        article = ArticleFactory(issue=issue_a)
        response = client.get(
            reverse("articles:detail", kwargs={"pk": article.pk})
        )
        assert response.status_code == 302
        assert "login" in response.url

    def test_detail_requires_valid_role(self, client, regular_user, issue_a):
        """7.3: Detail view requires a valid role."""
        article = ArticleFactory(issue=issue_a)
        client.force_login(regular_user)
        response = client.get(
            reverse("articles:detail", kwargs={"pk": article.pk})
        )
        assert response.status_code == 403

    def test_detail_displays_article(self, client, admin_user, issue_a):
        """7.3: Detail view displays article information."""
        article = ArticleFactory(
            issue=issue_a,
            title="Detalji članka",
            doi_suffix="det.001",
            status=ArticleStatus.DRAFT,
            abstract="Test apstrakt",
            keywords=["python", "django"],
        )
        client.force_login(admin_user)
        response = client.get(
            reverse("articles:detail", kwargs={"pk": article.pk})
        )
        assert response.status_code == 200
        content = response.content.decode("utf-8")
        assert "Detalji članka" in content
        assert "det.001" in content
        assert "Test apstrakt" in content
        assert "python" in content
        assert "django" in content

    def test_detail_scoped_for_urednik(
        self, client, urednik_user, issue_a, issue_b
    ):
        """7.4: Urednik can see own, gets 404 for other publisher's article."""
        article_own = ArticleFactory(issue=issue_a)
        article_other = ArticleFactory(issue=issue_b)
        client.force_login(urednik_user)
        response_own = client.get(
            reverse("articles:detail", kwargs={"pk": article_own.pk})
        )
        response_other = client.get(
            reverse("articles:detail", kwargs={"pk": article_other.pk})
        )
        assert response_own.status_code == 200
        assert response_other.status_code == 404

    def test_bibliotekar_can_view_detail(
        self, client, bibliotekar_user, issue_a
    ):
        """7.3: Bibliotekar can view article detail (read-only)."""
        article = ArticleFactory(issue=issue_a)
        client.force_login(bibliotekar_user)
        response = client.get(
            reverse("articles:detail", kwargs={"pk": article.pk})
        )
        assert response.status_code == 200

    def test_detail_shows_status_badge(self, client, admin_user, issue_a):
        """7.3: Detail view shows status badge."""
        article = ArticleFactory(
            issue=issue_a, status=ArticleStatus.PUBLISHED
        )
        client.force_login(admin_user)
        response = client.get(
            reverse("articles:detail", kwargs={"pk": article.pk})
        )
        content = response.content.decode("utf-8")
        assert "bg-success" in content
        assert "Objavljeno" in content


# =============================================================================
# 7.3: Test ArticleDeleteView
# =============================================================================


@pytest.mark.django_db
class TestArticleDeleteView:
    """Test article delete view."""

    def test_delete_requires_login(self, client, issue_a):
        """7.3: Delete view requires authentication."""
        article = ArticleFactory(issue=issue_a)
        response = client.get(
            reverse("articles:delete", kwargs={"pk": article.pk})
        )
        assert response.status_code == 302
        assert "login" in response.url

    def test_admin_can_access_delete(self, client, admin_user, issue_a):
        """7.3: Administrator can access delete confirmation."""
        article = ArticleFactory(issue=issue_a)
        client.force_login(admin_user)
        response = client.get(
            reverse("articles:delete", kwargs={"pk": article.pk})
        )
        assert response.status_code == 200
        assert "Potvrda brisanja" in response.content.decode("utf-8")

    def test_urednik_cannot_delete(self, client, urednik_user, issue_a):
        """7.3: Urednik cannot delete articles."""
        article = ArticleFactory(issue=issue_a)
        client.force_login(urednik_user)
        response = client.get(
            reverse("articles:delete", kwargs={"pk": article.pk})
        )
        assert response.status_code == 403

    def test_bibliotekar_cannot_delete(
        self, client, bibliotekar_user, issue_a
    ):
        """7.3: Bibliotekar cannot delete articles."""
        article = ArticleFactory(issue=issue_a)
        client.force_login(bibliotekar_user)
        response = client.get(
            reverse("articles:delete", kwargs={"pk": article.pk})
        )
        assert response.status_code == 403

    def test_soft_delete_via_view(self, client, admin_user, issue_a):
        """7.3: Delete view performs soft delete (not hard delete)."""
        article = ArticleFactory(issue=issue_a)
        client.force_login(admin_user)
        response = client.post(
            reverse("articles:delete", kwargs={"pk": article.pk})
        )
        assert response.status_code == 302

        # Should be soft deleted
        article.refresh_from_db()
        assert article.is_deleted is True
        assert not Article.objects.filter(pk=article.pk).exists()
        assert Article.all_objects.filter(pk=article.pk).exists()


# =============================================================================
# 7.3: Test breadcrumbs on all pages
# =============================================================================


@pytest.mark.django_db
class TestArticleBreadcrumbs:
    """Test breadcrumbs on all article pages."""

    def test_list_breadcrumbs(self, client, admin_user):
        """7.3: List page has correct breadcrumbs."""
        client.force_login(admin_user)
        response = client.get(reverse("articles:list"))
        assert response.status_code == 200
        content = response.content.decode("utf-8")
        assert "Kontrolna tabla" in content
        assert "Članci" in content

    def test_create_breadcrumbs(self, client, admin_user):
        """7.3: Create page has correct breadcrumbs."""
        client.force_login(admin_user)
        response = client.get(reverse("articles:create"))
        assert response.status_code == 200
        content = response.content.decode("utf-8")
        assert "Kontrolna tabla" in content
        assert "Članci" in content
        assert "Novi članak" in content

    def test_detail_breadcrumbs(self, client, admin_user, issue_a):
        """7.3: Detail page has correct breadcrumbs."""
        article = ArticleFactory(issue=issue_a)
        client.force_login(admin_user)
        response = client.get(
            reverse("articles:detail", kwargs={"pk": article.pk})
        )
        assert response.status_code == 200
        content = response.content.decode("utf-8")
        assert "Kontrolna tabla" in content
        assert "Članci" in content

    def test_delete_breadcrumbs(self, client, admin_user, issue_a):
        """7.3: Delete page has correct breadcrumbs."""
        article = ArticleFactory(issue=issue_a)
        client.force_login(admin_user)
        response = client.get(
            reverse("articles:delete", kwargs={"pk": article.pk})
        )
        assert response.status_code == 200
        content = response.content.decode("utf-8")
        assert "Kontrolna tabla" in content
        assert "Članci" in content


# =============================================================================
# 7.3: Test auditlog registration
# =============================================================================


@pytest.mark.django_db
class TestArticleAuditLog:
    """Test audit log registration for Article model."""

    def test_audit_log_records_create(self, client, admin_user, issue_a):
        """7.3: Audit log records article creation."""
        from auditlog.models import LogEntry

        client.force_login(admin_user)
        client.post(
            reverse("articles:create"),
            {
                "issue": issue_a.pk,
                "title": "Audit test create",
                "doi_suffix": "audit.001",
                "subtitle": "",
                "abstract": "",
                "keywords": "[]",
                "first_page": "",
                "last_page": "",
                "article_number": "",
                "language": "sr",
                "publication_type": "full_text",
                "license_url": "",
                "license_applies_to": "",
                "free_to_read_start_date": "",
            },
        )
        article = Article.objects.get(doi_suffix="audit.001")
        create_log = LogEntry.objects.filter(
            object_pk=str(article.pk),
            action=LogEntry.Action.CREATE,
        )
        assert create_log.exists()

    def test_audit_log_records_update(self, client, admin_user, issue_a):
        """7.3: Audit log records article update."""
        from auditlog.models import LogEntry

        article = ArticleFactory(issue=issue_a, status=ArticleStatus.DRAFT)
        client.force_login(admin_user)
        client.post(
            reverse("articles:update", kwargs={"pk": article.pk}),
            {
                "issue": issue_a.pk,
                "title": "Updated for audit",
                "doi_suffix": article.doi_suffix,
                "subtitle": "",
                "abstract": "",
                "keywords": "[]",
                "first_page": "",
                "last_page": "",
                "article_number": "",
                "language": "sr",
                "publication_type": "full_text",
                "license_url": "",
                "license_applies_to": "",
                "free_to_read_start_date": "",
            },
        )
        update_log = LogEntry.objects.filter(
            object_pk=str(article.pk),
            action=LogEntry.Action.UPDATE,
        )
        assert update_log.exists()
