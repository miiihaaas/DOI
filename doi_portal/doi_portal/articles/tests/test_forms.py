"""
Tests for Article forms.

Story 3.1 - Task 7.5: Comprehensive form tests.
"""

import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group

from doi_portal.articles.forms import ArticleForm
from doi_portal.articles.models import ArticleStatus
from doi_portal.issues.tests.factories import IssueFactory
from doi_portal.publications.tests.factories import PublicationFactory, PublisherFactory

from .factories import ArticleFactory

User = get_user_model()


# =============================================================================
# Fixtures
# =============================================================================


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


# =============================================================================
# 7.5: Test ArticleForm validation
# =============================================================================


@pytest.mark.django_db
class TestArticleFormValidation:
    """Test ArticleForm validation."""

    def test_valid_form(self, admin_user, issue_a):
        """7.5: Form with valid data is valid."""
        form = ArticleForm(
            data={
                "issue": issue_a.pk,
                "title": "Valid Article",
                "doi_suffix": "valid.001",
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
            user=admin_user,
        )
        assert form.is_valid(), form.errors

    def test_missing_title_invalid(self, admin_user, issue_a):
        """7.5: Form without required title field is invalid."""
        form = ArticleForm(
            data={
                "issue": issue_a.pk,
                "doi_suffix": "notitle.001",
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
            user=admin_user,
        )
        assert not form.is_valid()
        assert "title" in form.errors

    def test_missing_doi_suffix_invalid(self, admin_user, issue_a):
        """7.5: Form without doi_suffix is invalid."""
        form = ArticleForm(
            data={
                "issue": issue_a.pk,
                "title": "No DOI suffix",
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
            user=admin_user,
        )
        assert not form.is_valid()
        assert "doi_suffix" in form.errors

    def test_missing_issue_invalid(self, admin_user):
        """7.5: Form without issue is invalid."""
        form = ArticleForm(
            data={
                "title": "No Issue",
                "doi_suffix": "noissue.001",
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
            user=admin_user,
        )
        assert not form.is_valid()
        assert "issue" in form.errors

    def test_duplicate_doi_suffix_same_issue_save_raises(self, admin_user, issue_a):
        """7.5: Duplicate (issue, doi_suffix) raises IntegrityError on save."""
        from django.db import IntegrityError

        ArticleFactory(issue=issue_a, doi_suffix="dup.001")
        form = ArticleForm(
            data={
                "issue": issue_a.pk,
                "title": "Duplicate DOI",
                "doi_suffix": "dup.001",
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
            user=admin_user,
        )
        # Conditional unique constraint is enforced at DB level
        if form.is_valid():
            with pytest.raises(IntegrityError):
                form.save()

    def test_edit_excludes_self_from_unique_check(self, admin_user, issue_a):
        """7.5: Editing existing article does not trigger duplicate error on itself."""
        article = ArticleFactory(issue=issue_a, doi_suffix="self.001")
        form = ArticleForm(
            data={
                "issue": issue_a.pk,
                "title": "Updated Title",
                "doi_suffix": "self.001",
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
            instance=article,
            user=admin_user,
        )
        assert form.is_valid(), form.errors

    def test_error_classes_added_on_invalid(self, admin_user, issue_a):
        """7.5: is-invalid class added to fields with errors."""
        form = ArticleForm(
            data={
                "issue": issue_a.pk,
                "title": "",  # Required field left empty
                "doi_suffix": "",  # Required field left empty
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
            user=admin_user,
        )
        assert not form.is_valid()
        # Check that is-invalid was added
        title_class = form.fields["title"].widget.attrs.get("class", "")
        assert "is-invalid" in title_class


# =============================================================================
# 7.5: Test ArticleForm issue queryset scoping
# =============================================================================


@pytest.mark.django_db
class TestArticleFormIssueScoping:
    """Test ArticleForm issue queryset scoping."""

    def test_admin_sees_all_issues(
        self, admin_user, issue_a, issue_b
    ):
        """7.5: Administrator sees all issues in dropdown."""
        form = ArticleForm(user=admin_user)
        queryset = form.fields["issue"].queryset
        assert issue_a in queryset
        assert issue_b in queryset

    def test_urednik_sees_only_own_publisher_issues(
        self, urednik_user, issue_a, issue_b
    ):
        """7.5: Urednik sees only issues from assigned publisher."""
        form = ArticleForm(user=urednik_user)
        queryset = form.fields["issue"].queryset
        assert issue_a in queryset
        assert issue_b not in queryset

    def test_bibliotekar_sees_only_own_publisher_issues(
        self, bibliotekar_user, issue_a, issue_b
    ):
        """7.5: Bibliotekar sees only issues from assigned publisher."""
        form = ArticleForm(user=bibliotekar_user)
        queryset = form.fields["issue"].queryset
        assert issue_a in queryset
        assert issue_b not in queryset

    def test_superuser_sees_all_issues(self, issue_a, issue_b):
        """7.5: Superuser sees all issues."""
        superuser = User.objects.create_superuser(
            email="super@test.com", password="testpass123"
        )
        form = ArticleForm(user=superuser)
        queryset = form.fields["issue"].queryset
        assert issue_a in queryset
        assert issue_b in queryset

    def test_user_without_publisher_sees_no_issues(self):
        """7.5: User without publisher sees no issues."""
        user = User.objects.create_user(
            email="nopub@test.com", password="testpass123"
        )
        form = ArticleForm(user=user)
        queryset = form.fields["issue"].queryset
        assert queryset.count() == 0


# =============================================================================
# 7.5: Test keywords JSON handling
# =============================================================================


@pytest.mark.django_db
class TestArticleFormKeywords:
    """Test keywords JSON field handling."""

    def test_keywords_parsed_from_json_string(self, admin_user, issue_a):
        """7.5: Keywords parsed from JSON string."""
        form = ArticleForm(
            data={
                "issue": issue_a.pk,
                "title": "Keywords test",
                "doi_suffix": "kw.001",
                "subtitle": "",
                "abstract": "",
                "keywords": '["python", "django", "test"]',
                "first_page": "",
                "last_page": "",
                "article_number": "",
                "language": "sr",
                "publication_type": "full_text",
                "license_url": "",
                "license_applies_to": "",
                "free_to_read_start_date": "",
            },
            user=admin_user,
        )
        assert form.is_valid(), form.errors
        assert form.cleaned_data["keywords"] == ["python", "django", "test"]

    def test_empty_keywords_parsed(self, admin_user, issue_a):
        """7.5: Empty keywords JSON string results in empty list."""
        form = ArticleForm(
            data={
                "issue": issue_a.pk,
                "title": "Empty kw",
                "doi_suffix": "ekw.001",
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
            user=admin_user,
        )
        assert form.is_valid(), form.errors
        assert form.cleaned_data["keywords"] == []

    def test_invalid_json_keywords_rejected(self, admin_user, issue_a):
        """7.5: Invalid JSON in keywords field is rejected by JSONField validator."""
        form = ArticleForm(
            data={
                "issue": issue_a.pk,
                "title": "Invalid JSON",
                "doi_suffix": "ijson.001",
                "subtitle": "",
                "abstract": "",
                "keywords": "not valid json",
                "first_page": "",
                "last_page": "",
                "article_number": "",
                "language": "sr",
                "publication_type": "full_text",
                "license_url": "",
                "license_applies_to": "",
                "free_to_read_start_date": "",
            },
            user=admin_user,
        )
        assert not form.is_valid()
        assert "keywords" in form.errors

    def test_keywords_strips_whitespace(self, admin_user, issue_a):
        """7.5: Keywords are stripped of whitespace."""
        form = ArticleForm(
            data={
                "issue": issue_a.pk,
                "title": "Strip kw",
                "doi_suffix": "strip.001",
                "subtitle": "",
                "abstract": "",
                "keywords": '["  python  ", "  django  "]',
                "first_page": "",
                "last_page": "",
                "article_number": "",
                "language": "sr",
                "publication_type": "full_text",
                "license_url": "",
                "license_applies_to": "",
                "free_to_read_start_date": "",
            },
            user=admin_user,
        )
        assert form.is_valid(), form.errors
        assert form.cleaned_data["keywords"] == ["python", "django"]

    def test_keywords_filters_empty_strings(self, admin_user, issue_a):
        """7.5: Empty strings are filtered from keywords."""
        form = ArticleForm(
            data={
                "issue": issue_a.pk,
                "title": "Filter empty",
                "doi_suffix": "empty.001",
                "subtitle": "",
                "abstract": "",
                "keywords": '["python", "", "  ", "django"]',
                "first_page": "",
                "last_page": "",
                "article_number": "",
                "language": "sr",
                "publication_type": "full_text",
                "license_url": "",
                "license_applies_to": "",
                "free_to_read_start_date": "",
            },
            user=admin_user,
        )
        assert form.is_valid(), form.errors
        assert form.cleaned_data["keywords"] == ["python", "django"]
