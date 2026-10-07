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
from doi_portal.dashboard.services import get_bibliotekar_statistics
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

    # ------------------------------------------------------------------
    # Search (q) and list chrome - dashboard redesign
    # ------------------------------------------------------------------

    def test_search_by_title(self, client, admin_user, issue_a):
        """q matches the article title, case-insensitively."""
        ArticleFactory(issue=issue_a, title="Kvantna mehanika danas")
        ArticleFactory(issue=issue_a, title="Istorija Balkana")
        client.force_login(admin_user)
        response = client.get(reverse("articles:list"), {"q": "kvantna"})
        titles = [a.title for a in response.context["articles"]]
        assert titles == ["Kvantna mehanika danas"]

    def test_search_by_doi_suffix(self, client, admin_user, issue_a):
        """q matches the DOI suffix."""
        ArticleFactory(issue=issue_a, title="Prvi", doi_suffix="srch.2026.001")
        ArticleFactory(issue=issue_a, title="Drugi", doi_suffix="other.2026.002")
        client.force_login(admin_user)
        response = client.get(reverse("articles:list"), {"q": "srch.2026"})
        titles = [a.title for a in response.context["articles"]]
        assert titles == ["Prvi"]

    def test_search_by_full_doi(self, client, admin_user, issue_a, issue_b):
        """A pasted full DOI (prefix/suffix) finds the article."""
        ArticleFactory(issue=issue_a, title="Prvi", doi_suffix="full.001")
        ArticleFactory(issue=issue_b, title="Drugi", doi_suffix="full.001")
        prefix = issue_a.publication.publisher.doi_prefix
        assert prefix != issue_b.publication.publisher.doi_prefix
        client.force_login(admin_user)
        response = client.get(
            reverse("articles:list"), {"q": f"{prefix}/full.001"},
        )
        titles = [a.title for a in response.context["articles"]]
        assert titles == ["Prvi"]

    def test_search_by_author_surname(self, client, admin_user, issue_a):
        """q matches an author's surname, without duplicating the article."""
        from .factories import AuthorFactory  # noqa: PLC0415

        wanted = ArticleFactory(issue=issue_a, title="Sa autorom")
        AuthorFactory(article=wanted, given_name="Mira", surname="Petrović")
        AuthorFactory(article=wanted, given_name="Luka", surname="Petrović")
        other = ArticleFactory(issue=issue_a, title="Bez tog autora")
        AuthorFactory(article=other, given_name="Ana", surname="Jovanović")
        client.force_login(admin_user)
        response = client.get(reverse("articles:list"), {"q": "petrović"})
        titles = [a.title for a in response.context["articles"]]
        assert titles == ["Sa autorom"]
        assert response.context["result_count"] == 1

    def test_search_ignores_deleted_authors(self, client, admin_user, issue_a):
        """A soft-deleted author does not make the article match."""
        from .factories import AuthorFactory  # noqa: PLC0415

        article = ArticleFactory(issue=issue_a, title="Uklonjen autor")
        author = AuthorFactory(article=article, surname="Nestalović")
        author.soft_delete(user=admin_user)
        client.force_login(admin_user)
        response = client.get(reverse("articles:list"), {"q": "Nestalović"})
        assert list(response.context["articles"]) == []

    def test_search_keeps_publisher_scoping(
        self, client, urednik_user, issue_a, issue_b
    ):
        """Search never returns another publisher's articles."""
        ArticleFactory(issue=issue_a, title="Zajednički pojam moj")
        ArticleFactory(issue=issue_b, title="Zajednički pojam tuđi")
        client.force_login(urednik_user)
        response = client.get(reverse("articles:list"), {"q": "Zajednički"})
        titles = [a.title for a in response.context["articles"]]
        assert titles == ["Zajednički pojam moj"]

    def test_search_combines_with_status_and_issue(
        self, client, admin_user, issue_a, issue_b
    ):
        """q is ANDed with the existing status and issue params."""
        ArticleFactory(
            issue=issue_a, title="Tema nacrt", status=ArticleStatus.DRAFT,
        )
        ArticleFactory(
            issue=issue_a, title="Tema pregled", status=ArticleStatus.REVIEW,
        )
        ArticleFactory(
            issue=issue_b, title="Tema pregled drugo", status=ArticleStatus.REVIEW,
        )
        client.force_login(admin_user)
        response = client.get(
            reverse("articles:list"),
            {"q": "Tema", "status": "REVIEW", "issue": issue_a.pk},
        )
        titles = [a.title for a in response.context["articles"]]
        assert titles == ["Tema pregled"]

    def test_blank_search_returns_everything(self, client, admin_user, issue_a):
        """Whitespace-only q is ignored."""
        ArticleFactory(issue=issue_a, title="Jedan")
        ArticleFactory(issue=issue_a, title="Dva")
        client.force_login(admin_user)
        response = client.get(reverse("articles:list"), {"q": "   "})
        assert len(response.context["articles"]) == 2  # noqa: PLR2004
        assert response.context["has_filters"] is False

    def test_search_field_keeps_value_and_issue(self, client, admin_user, issue_a):
        """The filter bar echoes q and carries the issue as a hidden input."""
        ArticleFactory(issue=issue_a, title="Echo")
        client.force_login(admin_user)
        response = client.get(
            reverse("articles:list"), {"q": "Echo", "issue": issue_a.pk},
        )
        content = response.content.decode("utf-8")
        assert 'name="q" value="Echo"' in content
        assert f'<input type="hidden" name="issue" value="{issue_a.pk}">' in content
        assert "filter-bar__reset" in content

    def test_empty_list_without_filters(self, client, admin_user):
        """No articles at all: invite to create, no reset link."""
        client.force_login(admin_user)
        response = client.get(reverse("articles:list"))
        content = response.content.decode("utf-8")
        assert "Još nema unetih članaka." in content
        assert "Dodaj prvi članak" in content
        assert "Poništi filtere" not in content
        assert "filter-bar__reset" not in content

    def test_empty_list_with_filters(self, client, admin_user, issue_a):
        """Articles exist but none match: offer to reset the filters."""
        ArticleFactory(issue=issue_a, title="Postoji")
        client.force_login(admin_user)
        response = client.get(reverse("articles:list"), {"q": "nepostojeće"})
        content = response.content.decode("utf-8")
        assert "Nema rezultata za zadatu pretragu i filtere." in content
        assert "Poništi filtere" in content
        assert "Dodaj prvi članak" not in content

    def test_row_edit_action_only_for_draft(self, client, admin_user, issue_a):
        """The row edit link is rendered for DRAFT articles only."""
        draft = ArticleFactory(issue=issue_a, status=ArticleStatus.DRAFT)
        review = ArticleFactory(issue=issue_a, status=ArticleStatus.REVIEW)
        client.force_login(admin_user)
        response = client.get(reverse("articles:list"))
        content = response.content.decode("utf-8")
        assert reverse("articles:update", kwargs={"pk": draft.pk}) in content
        assert reverse("articles:update", kwargs={"pk": review.pk}) not in content
        assert 'aria-label="Izmeni: ' in content
        assert 'aria-label="Obriši: ' in content

    def test_sidebar_status_links_still_filter(self, client, admin_user, issue_a):
        """?status=DRAFT / ?status=REVIEW (sidebar links) keep working."""
        ArticleFactory(issue=issue_a, title="N", status=ArticleStatus.DRAFT)
        ArticleFactory(issue=issue_a, title="P", status=ArticleStatus.REVIEW)
        client.force_login(admin_user)
        for status, expected in (("DRAFT", ["N"]), ("REVIEW", ["P"])):
            response = client.get(reverse("articles:list"), {"status": status})
            assert [a.title for a in response.context["articles"]] == expected
            assert response.context["current_status"] == status

    def test_pagination_keeps_search_params(self, client, admin_user, issue_a):
        """Page links carry q and status."""
        for i in range(21):
            ArticleFactory(issue=issue_a, title=f"Serija {i}")
        client.force_login(admin_user)
        response = client.get(
            reverse("articles:list"), {"q": "Serija", "status": "DRAFT"},
        )
        content = response.content.decode("utf-8")
        assert response.context["result_count"] == 21  # noqa: PLR2004
        assert "q=Serija" in content
        assert "status=DRAFT" in content
        assert "page=2" in content

    # --- "Mine" filter (?mine=1): only articles created by the current user ---

    def test_mine_filter_shows_only_own_articles(
        self, client, bibliotekar_user, urednik_user, issue_a,
    ):
        ArticleFactory(issue=issue_a, title="Moj nacrt", created_by=bibliotekar_user)
        ArticleFactory(
            issue=issue_a,
            title="Moj na pregledu",
            created_by=bibliotekar_user,
            status=ArticleStatus.REVIEW,
        )
        ArticleFactory(issue=issue_a, title="Tuđi nacrt", created_by=urednik_user)
        client.force_login(bibliotekar_user)

        everything = client.get(reverse("articles:list"))
        assert len(everything.context["articles"]) == 3  # noqa: PLR2004
        assert everything.context["mine_filter"] is False
        assert "filter-bar__token" not in everything.content.decode("utf-8")

        mine = client.get(reverse("articles:list"), {"mine": "1"})
        titles = sorted(a.title for a in mine.context["articles"])
        assert titles == ["Moj na pregledu", "Moj nacrt"]
        assert mine.context["mine_filter"] is True
        assert mine.context["result_count"] == 2  # noqa: PLR2004

    def test_mine_filter_combines_with_status_and_search(
        self, client, bibliotekar_user, urednik_user, issue_a,
    ):
        ArticleFactory(issue=issue_a, title="Voda A", created_by=bibliotekar_user)
        ArticleFactory(issue=issue_a, title="Vazduh", created_by=bibliotekar_user)
        ArticleFactory(
            issue=issue_a,
            title="Voda B",
            created_by=bibliotekar_user,
            status=ArticleStatus.REVIEW,
        )
        ArticleFactory(issue=issue_a, title="Voda C", created_by=urednik_user)
        client.force_login(bibliotekar_user)
        response = client.get(
            reverse("articles:list"), {"mine": "1", "status": "DRAFT", "q": "voda"},
        )
        assert [a.title for a in response.context["articles"]] == ["Voda A"]

    def test_mine_filter_matches_dashboard_counts(
        self, client, bibliotekar_user, urednik_user, issue_a,
    ):
        """The list behind a dashboard tile shows exactly what the tile counts."""
        ArticleFactory(issue=issue_a, created_by=bibliotekar_user)
        ArticleFactory(issue=issue_a, created_by=bibliotekar_user)
        ArticleFactory(
            issue=issue_a, created_by=bibliotekar_user, status=ArticleStatus.REVIEW,
        )
        ArticleFactory(issue=issue_a, created_by=urednik_user)
        stats = get_bibliotekar_statistics(bibliotekar_user)
        client.force_login(bibliotekar_user)
        url = reverse("articles:list")

        drafts = client.get(url, {"mine": "1", "status": "DRAFT"})
        submitted = client.get(url, {"mine": "1", "status": "REVIEW"})
        total = client.get(url, {"mine": "1"})
        assert drafts.context["result_count"] == stats["my_drafts_count"] == 2  # noqa: PLR2004
        assert submitted.context["result_count"] == stats["my_submitted_count"] == 1
        assert total.context["result_count"] == stats["my_total_count"] == 3  # noqa: PLR2004

    def test_mine_filter_is_a_removable_active_filter(
        self, client, bibliotekar_user, issue_a
    ):
        ArticleFactory(issue=issue_a, created_by=bibliotekar_user)
        client.force_login(bibliotekar_user)
        response = client.get(
            reverse("articles:list"), {"mine": "1", "status": "DRAFT", "page": "1"},
        )
        content = response.content.decode("utf-8")
        list_url = reverse("articles:list")
        # kept through search / status changes
        assert '<input type="hidden" name="mine" value="1">' in content
        # removable on its own: the link drops mine (and page), keeps the rest
        assert response.context["mine_remove_url"] == f"{list_url}?status=DRAFT"
        assert f'href="{list_url}?status=DRAFT" class="filter-bar__token"' in content
        assert "Samo moji" in content
        # counts as an active filter, so "Poništi" is offered
        assert response.context["filters_active"] is True
        assert f'href="{list_url}" class="filter-bar__reset"' in content

    def test_mine_filter_alone_removes_to_plain_list(
        self, client, bibliotekar_user, issue_a
    ):
        client.force_login(bibliotekar_user)
        response = client.get(reverse("articles:list"), {"mine": "1"})
        assert response.context["mine_remove_url"] == reverse("articles:list")
        # empty + filtered: the "no results for filters" state, not "add first"
        assert "Poništi filtere" in response.content.decode("utf-8")

    def test_mine_filter_kept_in_pagination(self, client, bibliotekar_user, issue_a):
        for i in range(21):
            ArticleFactory(issue=issue_a, title=f"Moj {i}", created_by=bibliotekar_user)
        client.force_login(bibliotekar_user)
        content = client.get(reverse("articles:list"), {"mine": "1"}).content.decode(
            "utf-8",
        )
        assert 'href="?mine=1&amp;page=2"' in content

    def test_mine_filter_ignores_other_values(self, client, admin_user, issue_a):
        ArticleFactory(issue=issue_a)
        client.force_login(admin_user)
        response = client.get(reverse("articles:list"), {"mine": "yes"})
        assert response.context["mine_filter"] is False
        assert len(response.context["articles"]) == 1


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
        self, client, admin_user, issue_a, issue_b,
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
        self, client, urednik_user, issue_a, issue_b,
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
        self, client, bibliotekar_user, issue_a,
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
        # Kit status badge (components/_status_badge.html) replaced the
        # Bootstrap "badge bg-success" markup.
        assert "status-badge--success" in content
        assert "Objavljeno" in content

    def test_detail_header_shows_full_doi(self, client, admin_user, issue_a):
        """Page header shows the full DOI (publisher prefix + suffix)."""
        article = ArticleFactory(issue=issue_a, doi_suffix="hdr.001")
        client.force_login(admin_user)
        response = client.get(
            reverse("articles:detail", kwargs={"pk": article.pk})
        )
        content = response.content.decode("utf-8")
        prefix = issue_a.publication.publisher.doi_prefix
        assert f"DOI: {prefix}/hdr.001" in content

    def test_detail_has_single_workflow_bar_and_edit_link(
        self, client, admin_user, issue_a,
    ):
        """One workflow bar, one edit link, no "Brze akcije" card."""
        article = ArticleFactory(issue=issue_a, status=ArticleStatus.DRAFT)
        client.force_login(admin_user)
        response = client.get(
            reverse("articles:detail", kwargs={"pk": article.pk}),
        )
        content = response.content.decode("utf-8")
        update_url = reverse("articles:update", kwargs={"pk": article.pk})
        assert content.count('class="workflow-bar"') == 1
        assert content.count(f'href="{update_url}"') == 1
        assert "Brze akcije" not in content
        # The next step is the only primary button on the page
        assert content.count("btn btn-primary") == 1
        assert "submit-check" in content

    def test_detail_modal_shells_are_labelled(self, client, admin_user, issue_a):
        """Modal shells keep their ids/containers and point at a title id."""
        article = ArticleFactory(issue=issue_a)
        client.force_login(admin_user)
        response = client.get(
            reverse("articles:detail", kwargs={"pk": article.pk}),
        )
        content = response.content.decode("utf-8")
        for modal_id, container_id in [
            ("submitReviewModal", "submit-modal-container"),
            ("approveModal", "approve-modal-container"),
            ("returnRevisionModal", "return-modal-container"),
            ("publishModal", "publish-modal-container"),
            ("withdrawModal", "withdraw-modal-container"),
        ]:
            assert f'id="{modal_id}"' in content
            assert f'aria-labelledby="{modal_id}Label"' in content
            assert f'id="{container_id}"' in content

    def test_detail_licence_card_prints_free_access_once(
        self, client, admin_user, issue_a,
    ):
        """"Slobodan pristup" row is rendered once, with or without a licence."""
        plain = ArticleFactory(issue=issue_a, doi_suffix="lic.001")
        licensed = ArticleFactory(
            issue=issue_a,
            doi_suffix="lic.002",
            license_url="https://creativecommons.org/licenses/by/4.0/",
            free_to_read=True,
        )
        client.force_login(admin_user)
        for article in (plain, licensed):
            response = client.get(
                reverse("articles:detail", kwargs={"pk": article.pk}),
            )
            content = response.content.decode("utf-8")
            assert content.count("<dt>Slobodan pristup</dt>") == 1


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
        content = response.content.decode("utf-8")
        # Page title and confirm button name the action ("Obriši članak")
        assert content.count("Obriši članak") >= 2  # noqa: PLR2004
        assert "Da li ste sigurni" in content

    def test_urednik_cannot_delete(self, client, urednik_user, issue_a):
        """7.3: Urednik cannot delete articles."""
        article = ArticleFactory(issue=issue_a)
        client.force_login(urednik_user)
        response = client.get(
            reverse("articles:delete", kwargs={"pk": article.pk})
        )
        assert response.status_code == 403

    def test_bibliotekar_cannot_delete(
        self, client, bibliotekar_user, issue_a,
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
            reverse("articles:detail", kwargs={"pk": article.pk}),
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
