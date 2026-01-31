"""
Tests for Author and Affiliation models, views, forms, and ORCID validation.

Story 3.2 - Tasks 1-8: Comprehensive tests for Author Management.
"""

import json

import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.exceptions import ValidationError
from django.test import Client
from django.urls import reverse

from doi_portal.articles.forms import AffiliationForm, AuthorForm
from doi_portal.articles.models import (
    Affiliation,
    Author,
    AuthorSequence,
    ContributorRole,
)
from doi_portal.articles.validators import validate_orcid
from doi_portal.issues.tests.factories import IssueFactory
from doi_portal.publications.tests.factories import (
    PublicationFactory,
    PublisherFactory,
)

from .factories import AffiliationFactory, ArticleFactory, AuthorFactory

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
def bibliotekar_user_b(publisher_b):
    """Create a Bibliotekar user assigned to publisher B."""
    user = User.objects.create_user(
        email="bibliotekar_b@test.com",
        password="testpass123",
        publisher=publisher_b,
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


@pytest.fixture
def article_a(issue_a):
    """Create article in publisher A's issue."""
    return ArticleFactory(issue=issue_a)


@pytest.fixture
def article_b(issue_b):
    """Create article in publisher B's issue."""
    return ArticleFactory(issue=issue_b)


# =============================================================================
# Task 1: Author Model Tests (AC #1)
# =============================================================================


@pytest.mark.django_db
class TestAuthorModelCreation:
    """Test Author model creation with all fields."""

    def test_create_author_with_required_fields(self, article_a):
        """1.3: Author can be created with required fields (surname, article)."""
        author = Author.objects.create(
            article=article_a,
            surname="Petrović",
            order=1,
        )
        assert author.pk is not None
        assert author.surname == "Petrović"

    def test_create_author_with_all_fields(self, article_a):
        """1.3: Author can be created with all fields (AC #1)."""
        author = Author.objects.create(
            article=article_a,
            given_name="Marko",
            surname="Petrović",
            suffix="Jr.",
            email="marko@test.com",
            orcid="0000-0001-2345-6789",
            orcid_authenticated=True,
            sequence=AuthorSequence.FIRST,
            contributor_role=ContributorRole.AUTHOR,
            is_corresponding=True,
            order=1,
        )
        assert author.pk is not None
        assert author.given_name == "Marko"
        assert author.surname == "Petrović"
        assert author.suffix == "Jr."
        assert author.email == "marko@test.com"
        assert author.orcid == "0000-0001-2345-6789"
        assert author.orcid_authenticated is True
        assert author.sequence == AuthorSequence.FIRST
        assert author.contributor_role == ContributorRole.AUTHOR
        assert author.is_corresponding is True
        assert author.order == 1

    def test_default_contributor_role_is_author(self, article_a):
        """1.3: Default contributor_role is AUTHOR (AC #1)."""
        author = Author.objects.create(
            article=article_a, surname="Test", order=1
        )
        assert author.contributor_role == ContributorRole.AUTHOR

    def test_default_sequence_is_additional(self, article_a):
        """1.3: Default sequence is ADDITIONAL (AC #1)."""
        author = Author.objects.create(
            article=article_a, surname="Test", order=1
        )
        assert author.sequence == AuthorSequence.ADDITIONAL

    def test_default_is_corresponding_is_false(self, article_a):
        """1.3: Default is_corresponding is False."""
        author = Author.objects.create(
            article=article_a, surname="Test", order=1
        )
        assert author.is_corresponding is False

    def test_default_orcid_authenticated_is_false(self, article_a):
        """1.3: Default orcid_authenticated is False."""
        author = Author.objects.create(
            article=article_a, surname="Test", order=1
        )
        assert author.orcid_authenticated is False

    def test_str_with_given_name(self):
        """1.5: __str__ returns 'given_name surname' when given_name exists."""
        author = AuthorFactory(given_name="Ana", surname="Jovanović")
        assert str(author) == "Ana Jovanović"

    def test_str_without_given_name(self):
        """1.5: __str__ returns 'surname' when no given_name."""
        author = AuthorFactory(given_name="", surname="Jovanović")
        assert str(author) == "Jovanović"

    def test_verbose_names(self):
        """1.4: verbose_name and verbose_name_plural are correct."""
        assert Author._meta.verbose_name == "Autor"
        assert Author._meta.verbose_name_plural == "Autori"

    def test_ordering_by_order(self, article_a):
        """1.4: Default ordering is ['order']."""
        author3 = AuthorFactory(article=article_a, order=3)
        author1 = AuthorFactory(article=article_a, order=1)
        author2 = AuthorFactory(article=article_a, order=2)
        authors = list(article_a.authors.all())
        assert authors == [author1, author2, author3]

    def test_article_cascade_delete(self, article_a):
        """1.3: Authors are cascade deleted when article is deleted."""
        AuthorFactory(article=article_a, order=1)
        AuthorFactory(article=article_a, order=2)
        assert article_a.authors.count() == 2
        article_a.delete()
        assert Author.objects.count() == 0

    def test_article_related_name(self, article_a):
        """1.3: article FK related_name='authors' works."""
        a1 = AuthorFactory(article=article_a, order=1)
        a2 = AuthorFactory(article=article_a, order=2)
        assert article_a.authors.count() == 2
        assert a1 in article_a.authors.all()
        assert a2 in article_a.authors.all()

    def test_author_count_property(self, article_a):
        """1.9: Article.author_count property returns correct count."""
        assert article_a.author_count == 0
        AuthorFactory(article=article_a, order=1)
        assert article_a.author_count == 1
        AuthorFactory(article=article_a, order=2)
        assert article_a.author_count == 2


# =============================================================================
# Task 1: AuthorSequence and ContributorRole Enums (AC #1)
# =============================================================================


@pytest.mark.django_db
class TestAuthorSequenceEnum:
    """Test AuthorSequence TextChoices."""

    def test_sequence_choices(self):
        """1.1: AuthorSequence has FIRST and ADDITIONAL."""
        assert AuthorSequence.FIRST == "first"
        assert AuthorSequence.ADDITIONAL == "additional"

    def test_sequence_labels(self):
        """1.1: AuthorSequence labels are in Serbian."""
        assert AuthorSequence.FIRST.label == "Glavni (first)"
        assert AuthorSequence.ADDITIONAL.label == "Ostali (additional)"


@pytest.mark.django_db
class TestContributorRoleEnum:
    """Test ContributorRole TextChoices."""

    def test_role_choices(self):
        """1.2: ContributorRole has all 5 roles."""
        assert ContributorRole.AUTHOR == "author"
        assert ContributorRole.EDITOR == "editor"
        assert ContributorRole.CHAIR == "chair"
        assert ContributorRole.TRANSLATOR == "translator"
        assert ContributorRole.REVIEWER == "reviewer"

    def test_role_labels(self):
        """1.2: ContributorRole labels are in Serbian with diacritics."""
        assert ContributorRole.AUTHOR.label == "Autor"
        assert ContributorRole.EDITOR.label == "Urednik"
        assert ContributorRole.CHAIR.label == "Predsedavajući"
        assert ContributorRole.TRANSLATOR.label == "Prevodilac"
        assert ContributorRole.REVIEWER.label == "Recenzent"

    def test_all_roles_valid(self):
        """1.2: All roles can be assigned to Author."""
        for role_value, _ in ContributorRole.choices:
            author = AuthorFactory(contributor_role=role_value)
            assert author.contributor_role == role_value


# =============================================================================
# Task 1: Affiliation Model Tests (AC #2)
# =============================================================================


@pytest.mark.django_db
class TestAffiliationModel:
    """Test Affiliation model creation and structure (AC #2)."""

    def test_create_affiliation(self):
        """1.6: Affiliation can be created with required fields."""
        author = AuthorFactory()
        aff = Affiliation.objects.create(
            author=author,
            institution_name="Univerzitet u Beogradu",
            order=1,
        )
        assert aff.pk is not None
        assert aff.institution_name == "Univerzitet u Beogradu"

    def test_create_affiliation_with_all_fields(self):
        """1.6: Affiliation with all fields (AC #2)."""
        author = AuthorFactory()
        aff = Affiliation.objects.create(
            author=author,
            institution_name="Univerzitet u Beogradu",
            institution_ror_id="https://ror.org/02qsmb048",
            department="Matematički fakultet",
            order=1,
        )
        assert aff.institution_ror_id == "https://ror.org/02qsmb048"
        assert aff.department == "Matematički fakultet"

    def test_multiple_affiliations_per_author(self):
        """1.6: Author can have multiple affiliations (1:N, AC #2)."""
        author = AuthorFactory()
        AffiliationFactory(author=author, order=1)
        AffiliationFactory(author=author, order=2)
        assert author.affiliations.count() == 2

    def test_str_without_department(self):
        """1.7: __str__ returns institution_name when no department."""
        aff = AffiliationFactory(
            institution_name="MIT",
            department="",
        )
        assert str(aff) == "MIT"

    def test_str_with_department(self):
        """1.7: __str__ returns 'department, institution_name' with department."""
        aff = AffiliationFactory(
            institution_name="MIT",
            department="CSAIL",
        )
        assert str(aff) == "CSAIL, MIT"

    def test_verbose_names(self):
        """1.7: verbose_name and verbose_name_plural are correct."""
        assert Affiliation._meta.verbose_name == "Afilijacija"
        assert Affiliation._meta.verbose_name_plural == "Afilijacije"

    def test_ordering_by_order(self):
        """1.7: Default ordering is ['order']."""
        author = AuthorFactory()
        a3 = AffiliationFactory(author=author, order=3)
        a1 = AffiliationFactory(author=author, order=1)
        a2 = AffiliationFactory(author=author, order=2)
        affs = list(author.affiliations.all())
        assert affs == [a1, a2, a3]

    def test_cascade_delete_on_author(self):
        """1.6: Affiliations cascade deleted when author is deleted."""
        author = AuthorFactory()
        AffiliationFactory(author=author, order=1)
        AffiliationFactory(author=author, order=2)
        assert Affiliation.objects.filter(author=author).count() == 2
        author.delete()
        assert Affiliation.objects.count() == 0


# =============================================================================
# Task 2: ORCID Validator Tests (AC #5, #9)
# =============================================================================


@pytest.mark.django_db
class TestOrcidValidator:
    """Test ORCID format validation (AC #5, #9)."""

    def test_valid_orcid_all_digits(self):
        """2.1-2.2: Valid ORCID with all digits passes."""
        validate_orcid("0000-0001-2345-6789")  # Should not raise

    def test_valid_orcid_with_x(self):
        """2.1-2.2: Valid ORCID ending with X passes."""
        validate_orcid("0000-0002-1825-009X")  # Should not raise

    def test_empty_value_passes(self):
        """2.1: Empty string passes (field is optional)."""
        validate_orcid("")  # Should not raise

    def test_invalid_format_too_short(self):
        """2.2: Too short ORCID raises ValidationError."""
        with pytest.raises(ValidationError) as exc:
            validate_orcid("0000-0001-2345")
        assert exc.value.code == "invalid_orcid"

    def test_invalid_format_no_dashes(self):
        """2.2: ORCID without dashes raises ValidationError."""
        with pytest.raises(ValidationError):
            validate_orcid("0000000123456789")

    def test_invalid_format_lowercase_x(self):
        """2.2: Lowercase x is invalid."""
        with pytest.raises(ValidationError):
            validate_orcid("0000-0002-1825-009x")

    def test_invalid_format_letters(self):
        """2.2: Letters in ORCID are invalid."""
        with pytest.raises(ValidationError):
            validate_orcid("000A-0001-2345-6789")

    def test_invalid_format_extra_chars(self):
        """2.2: Extra characters are invalid."""
        with pytest.raises(ValidationError):
            validate_orcid("0000-0001-2345-67890")

    def test_error_message_in_serbian(self):
        """2.3: Error message is in Serbian."""
        with pytest.raises(ValidationError) as exc:
            validate_orcid("invalid")
        assert "Neispravan ORCID format" in str(exc.value.message)

    def test_model_validation_with_invalid_orcid(self, article_a):
        """2.4: Author model validates ORCID field."""
        author = Author(
            article=article_a,
            surname="Test",
            orcid="invalid-orcid",
            order=1,
        )
        with pytest.raises(ValidationError):
            author.full_clean()

    def test_model_validation_with_valid_orcid(self, article_a):
        """2.4: Author model accepts valid ORCID."""
        author = Author(
            article=article_a,
            surname="Test",
            orcid="0000-0001-2345-6789",
            order=1,
        )
        author.full_clean()  # Should not raise

    def test_model_validation_empty_orcid_ok(self, article_a):
        """2.4: Author model accepts empty ORCID (optional)."""
        author = Author(
            article=article_a,
            surname="Test",
            orcid="",
            order=1,
        )
        author.full_clean()  # Should not raise


# =============================================================================
# Task 3: AuthorForm Tests (AC #4)
# =============================================================================


@pytest.mark.django_db
class TestAuthorForm:
    """Test AuthorForm validation and fields (AC #4)."""

    def test_valid_author_form(self):
        """3.1: Form with valid data is valid."""
        form = AuthorForm(data={
            "given_name": "Marko",
            "surname": "Petrović",
            "suffix": "",
            "email": "marko@test.com",
            "orcid": "0000-0001-2345-6789",
            "contributor_role": "author",
            "is_corresponding": True,
        })
        assert form.is_valid(), form.errors

    def test_surname_required(self):
        """3.1: Surname is required."""
        form = AuthorForm(data={
            "given_name": "Marko",
            "surname": "",
            "contributor_role": "author",
        })
        assert not form.is_valid()
        assert "surname" in form.errors

    def test_given_name_optional(self):
        """3.1: given_name is optional."""
        form = AuthorForm(data={
            "given_name": "",
            "surname": "Petrović",
            "contributor_role": "author",
        })
        assert form.is_valid(), form.errors

    def test_form_has_bootstrap_classes(self):
        """3.2: Form fields have Bootstrap 5 CSS classes."""
        form = AuthorForm()
        assert "form-control" in form.fields["surname"].widget.attrs["class"]
        assert "form-select" in form.fields["contributor_role"].widget.attrs["class"]
        assert "form-check-input" in form.fields["is_corresponding"].widget.attrs["class"]

    def test_form_labels_in_serbian(self):
        """3.3: Form labels are in Serbian with correct diacritics."""
        form = AuthorForm()
        assert str(form.fields["given_name"].label) == "Ime"
        assert str(form.fields["surname"].label) == "Prezime"
        assert str(form.fields["contributor_role"].label) == "Uloga kontributora"
        assert str(form.fields["is_corresponding"].label) == "Korespondentan autor"

    def test_invalid_orcid_rejected(self):
        """3.1: Invalid ORCID is rejected by form."""
        form = AuthorForm(data={
            "given_name": "Marko",
            "surname": "Petrović",
            "orcid": "invalid",
            "contributor_role": "author",
        })
        assert not form.is_valid()
        assert "orcid" in form.errors


# =============================================================================
# Task 3: AffiliationForm Tests (AC #8)
# =============================================================================


@pytest.mark.django_db
class TestAffiliationForm:
    """Test AffiliationForm validation and fields (AC #8)."""

    def test_valid_affiliation_form(self):
        """3.4: Form with valid data is valid."""
        form = AffiliationForm(data={
            "institution_name": "Univerzitet u Beogradu",
            "institution_ror_id": "https://ror.org/02qsmb048",
            "department": "Matematički fakultet",
        })
        assert form.is_valid(), form.errors

    def test_institution_name_required(self):
        """3.4: institution_name is required."""
        form = AffiliationForm(data={
            "institution_name": "",
            "institution_ror_id": "",
            "department": "",
        })
        assert not form.is_valid()
        assert "institution_name" in form.errors

    def test_form_has_bootstrap_classes(self):
        """3.5: Form fields have Bootstrap 5 CSS classes."""
        form = AffiliationForm()
        assert "form-control" in form.fields["institution_name"].widget.attrs["class"]
        assert "form-control" in form.fields["institution_ror_id"].widget.attrs["class"]

    def test_form_labels_in_serbian(self):
        """3.5: Form labels are in Serbian."""
        form = AffiliationForm()
        assert str(form.fields["institution_name"].label) == "Naziv institucije"
        assert str(form.fields["institution_ror_id"].label) == "ROR ID"
        assert str(form.fields["department"].label) == "Departman"


# =============================================================================
# Task 4: Author Add View Tests (AC #4)
# =============================================================================


@pytest.mark.django_db
class TestAuthorAddView:
    """Test author_add HTMX view (AC #4)."""

    def test_add_author_requires_login(self, client, article_a):
        """4.1: author_add requires authentication."""
        url = reverse("articles:author-add", kwargs={"article_pk": article_a.pk})
        response = client.post(url, {"surname": "Test", "contributor_role": "author"})
        assert response.status_code == 302
        assert "login" in response.url

    def test_add_author_as_bibliotekar(self, client, bibliotekar_user, article_a):
        """4.1: Bibliotekar can add author to own publisher's article."""
        client.force_login(bibliotekar_user)
        url = reverse("articles:author-add", kwargs={"article_pk": article_a.pk})
        response = client.post(url, {
            "given_name": "Marko",
            "surname": "Petrović",
            "contributor_role": "author",
        })
        assert response.status_code == 200
        assert article_a.authors.count() == 1
        author = article_a.authors.first()
        assert author.surname == "Petrović"
        assert author.order == 1
        assert author.sequence == AuthorSequence.FIRST

    def test_add_second_author_gets_additional_sequence(
        self, client, bibliotekar_user, article_a
    ):
        """4.1: Second author gets ADDITIONAL sequence."""
        AuthorFactory(article=article_a, order=1, sequence=AuthorSequence.FIRST)
        client.force_login(bibliotekar_user)
        url = reverse("articles:author-add", kwargs={"article_pk": article_a.pk})
        response = client.post(url, {
            "given_name": "Ana",
            "surname": "Jovanović",
            "contributor_role": "author",
        })
        assert response.status_code == 200
        second_author = article_a.authors.order_by("-order").first()
        assert second_author.sequence == AuthorSequence.ADDITIONAL
        assert second_author.order == 2

    def test_add_author_blocked_for_other_publisher(
        self, client, bibliotekar_user, article_b
    ):
        """4.8: Bibliotekar cannot add author to another publisher's article."""
        client.force_login(bibliotekar_user)
        url = reverse("articles:author-add", kwargs={"article_pk": article_b.pk})
        response = client.post(url, {
            "surname": "Test",
            "contributor_role": "author",
        })
        assert response.status_code == 403

    def test_add_author_returns_html(self, client, bibliotekar_user, article_a):
        """4.1: Returns HTML fragment (not JSON)."""
        client.force_login(bibliotekar_user)
        url = reverse("articles:author-add", kwargs={"article_pk": article_a.pk})
        response = client.post(url, {
            "surname": "Petrović",
            "contributor_role": "author",
        })
        assert response.status_code == 200
        assert "text/html" in response["Content-Type"]

    def test_admin_can_add_author(self, client, admin_user, article_a):
        """4.1: Administrator can add author."""
        client.force_login(admin_user)
        url = reverse("articles:author-add", kwargs={"article_pk": article_a.pk})
        response = client.post(url, {
            "surname": "Admin Autor",
            "contributor_role": "author",
        })
        assert response.status_code == 200
        assert article_a.authors.count() == 1

    def test_superuser_can_add_author(self, client, superuser, article_a):
        """4.1: Superuser can add author."""
        client.force_login(superuser)
        url = reverse("articles:author-add", kwargs={"article_pk": article_a.pk})
        response = client.post(url, {
            "surname": "Super Autor",
            "contributor_role": "author",
        })
        assert response.status_code == 200
        assert article_a.authors.count() == 1


# =============================================================================
# Task 4: Author Update View Tests
# =============================================================================


@pytest.mark.django_db
class TestAuthorUpdateView:
    """Test author_update HTMX view."""

    def test_update_author(self, client, bibliotekar_user, article_a):
        """4.2: Bibliotekar can update author."""
        author = AuthorFactory(article=article_a, surname="Old", order=1)
        client.force_login(bibliotekar_user)
        url = reverse("articles:author-update", kwargs={"pk": author.pk})
        response = client.post(url, {
            "given_name": "Novi",
            "surname": "Novi Prezime",
            "contributor_role": "editor",
        })
        assert response.status_code == 200
        author.refresh_from_db()
        assert author.surname == "Novi Prezime"
        assert author.contributor_role == ContributorRole.EDITOR

    def test_update_author_blocked_for_other_publisher(
        self, client, bibliotekar_user, article_b
    ):
        """4.8: Cannot update another publisher's author."""
        author = AuthorFactory(article=article_b, order=1)
        client.force_login(bibliotekar_user)
        url = reverse("articles:author-update", kwargs={"pk": author.pk})
        response = client.post(url, {
            "surname": "Hacked",
            "contributor_role": "author",
        })
        assert response.status_code == 403


# =============================================================================
# Task 4: Author Delete View Tests (AC #7)
# =============================================================================


@pytest.mark.django_db
class TestAuthorDeleteView:
    """Test author_delete HTMX view (AC #7)."""

    def test_delete_author(self, client, bibliotekar_user, article_a):
        """4.3: Bibliotekar can delete author from own article."""
        author = AuthorFactory(article=article_a, order=1)
        client.force_login(bibliotekar_user)
        url = reverse("articles:author-delete", kwargs={"pk": author.pk})
        response = client.post(url)
        assert response.status_code == 200
        assert article_a.authors.count() == 0

    def test_delete_reorders_remaining(self, client, bibliotekar_user, article_a):
        """4.3: After delete, remaining authors are re-ordered (AC #7)."""
        a1 = AuthorFactory(article=article_a, order=1, sequence=AuthorSequence.FIRST)
        a2 = AuthorFactory(article=article_a, order=2, sequence=AuthorSequence.ADDITIONAL)
        a3 = AuthorFactory(article=article_a, order=3, sequence=AuthorSequence.ADDITIONAL)

        client.force_login(bibliotekar_user)
        url = reverse("articles:author-delete", kwargs={"pk": a1.pk})
        response = client.post(url)
        assert response.status_code == 200

        a2.refresh_from_db()
        a3.refresh_from_db()
        assert a2.order == 1
        assert a2.sequence == AuthorSequence.FIRST  # First becomes FIRST
        assert a3.order == 2
        assert a3.sequence == AuthorSequence.ADDITIONAL

    def test_delete_blocked_for_other_publisher(
        self, client, bibliotekar_user, article_b
    ):
        """4.8: Cannot delete another publisher's author."""
        author = AuthorFactory(article=article_b, order=1)
        client.force_login(bibliotekar_user)
        url = reverse("articles:author-delete", kwargs={"pk": author.pk})
        response = client.post(url)
        assert response.status_code == 403


# =============================================================================
# Task 4: Author Reorder View Tests (AC #6)
# =============================================================================


@pytest.mark.django_db
class TestAuthorReorderView:
    """Test author_reorder HTMX view (AC #6)."""

    def test_reorder_authors(self, client, bibliotekar_user, article_a):
        """4.4: Reorder updates order and auto-calculates sequence (AC #6)."""
        a1 = AuthorFactory(article=article_a, order=1, sequence=AuthorSequence.FIRST)
        a2 = AuthorFactory(article=article_a, order=2, sequence=AuthorSequence.ADDITIONAL)
        a3 = AuthorFactory(article=article_a, order=3, sequence=AuthorSequence.ADDITIONAL)

        client.force_login(bibliotekar_user)
        url = reverse("articles:author-reorder", kwargs={"article_pk": article_a.pk})
        # Reverse order: a3, a1, a2
        response = client.post(
            url,
            json.dumps({"order": [a3.pk, a1.pk, a2.pk]}),
            content_type="application/json",
        )
        assert response.status_code == 200

        a1.refresh_from_db()
        a2.refresh_from_db()
        a3.refresh_from_db()

        assert a3.order == 1
        assert a3.sequence == AuthorSequence.FIRST  # First gets FIRST
        assert a1.order == 2
        assert a1.sequence == AuthorSequence.ADDITIONAL
        assert a2.order == 3
        assert a2.sequence == AuthorSequence.ADDITIONAL

    def test_reorder_blocked_for_other_publisher(
        self, client, bibliotekar_user, article_b
    ):
        """4.8: Cannot reorder another publisher's authors."""
        a1 = AuthorFactory(article=article_b, order=1)
        a2 = AuthorFactory(article=article_b, order=2)
        client.force_login(bibliotekar_user)
        url = reverse("articles:author-reorder", kwargs={"article_pk": article_b.pk})
        response = client.post(
            url,
            json.dumps({"order": [a2.pk, a1.pk]}),
            content_type="application/json",
        )
        assert response.status_code == 403

    def test_reorder_requires_post(self, client, bibliotekar_user, article_a):
        """4.9: Reorder only accepts POST."""
        client.force_login(bibliotekar_user)
        url = reverse("articles:author-reorder", kwargs={"article_pk": article_a.pk})
        response = client.get(url)
        assert response.status_code == 405  # Method Not Allowed


# =============================================================================
# Task 4: ORCID Validation View Tests (AC #5, #9)
# =============================================================================


@pytest.mark.django_db
class TestValidateOrcidView:
    """Test validate_orcid_view HTMX endpoint (AC #5, #9)."""

    def test_valid_orcid_returns_valid(self, client, bibliotekar_user):
        """4.5: Valid ORCID returns valid HTML fragment (AC #9)."""
        client.force_login(bibliotekar_user)
        url = reverse("articles:validate-orcid")
        response = client.get(url, {"orcid": "0000-0001-2345-6789"})
        assert response.status_code == 200
        content = response.content.decode("utf-8")
        assert "check-circle-fill" in content  # Valid icon

    def test_invalid_orcid_returns_invalid(self, client, bibliotekar_user):
        """4.5: Invalid ORCID returns invalid HTML fragment (AC #9)."""
        client.force_login(bibliotekar_user)
        url = reverse("articles:validate-orcid")
        response = client.get(url, {"orcid": "invalid"})
        assert response.status_code == 200
        content = response.content.decode("utf-8")
        assert "x-circle-fill" in content  # Invalid icon

    def test_empty_orcid_returns_empty(self, client, bibliotekar_user):
        """4.5: Empty ORCID returns no feedback."""
        client.force_login(bibliotekar_user)
        url = reverse("articles:validate-orcid")
        response = client.get(url, {"orcid": ""})
        assert response.status_code == 200
        content = response.content.decode("utf-8").strip()
        assert "circle-fill" not in content

    def test_orcid_with_x_valid(self, client, bibliotekar_user):
        """4.5: ORCID ending with X is valid (AC #9)."""
        client.force_login(bibliotekar_user)
        url = reverse("articles:validate-orcid")
        response = client.get(url, {"orcid": "0000-0002-1825-009X"})
        content = response.content.decode("utf-8")
        assert "check-circle-fill" in content

    def test_validate_orcid_requires_login(self, client):
        """4.5: ORCID validation requires authentication."""
        url = reverse("articles:validate-orcid")
        response = client.get(url, {"orcid": "0000-0001-2345-6789"})
        assert response.status_code == 302
        assert "login" in response.url

    def test_validate_orcid_only_get(self, client, bibliotekar_user):
        """4.9: ORCID validation only accepts GET."""
        client.force_login(bibliotekar_user)
        url = reverse("articles:validate-orcid")
        response = client.post(url, {"orcid": "0000-0001-2345-6789"})
        assert response.status_code == 405


# =============================================================================
# Task 4: Affiliation Add/Delete View Tests (AC #8)
# =============================================================================


@pytest.mark.django_db
class TestAffiliationViews:
    """Test affiliation HTMX views (AC #8)."""

    def test_add_affiliation(self, client, bibliotekar_user, article_a):
        """4.6: Bibliotekar can add affiliation to author."""
        author = AuthorFactory(article=article_a, order=1)
        client.force_login(bibliotekar_user)
        url = reverse("articles:affiliation-add", kwargs={"author_pk": author.pk})
        response = client.post(url, {
            "institution_name": "Univerzitet u Beogradu",
            "institution_ror_id": "",
            "department": "Matematički fakultet",
        })
        assert response.status_code == 200
        assert author.affiliations.count() == 1
        aff = author.affiliations.first()
        assert aff.institution_name == "Univerzitet u Beogradu"
        assert aff.department == "Matematički fakultet"

    def test_add_multiple_affiliations(self, client, bibliotekar_user, article_a):
        """4.6: Can add multiple affiliations per author (AC #8)."""
        author = AuthorFactory(article=article_a, order=1)
        client.force_login(bibliotekar_user)
        url = reverse("articles:affiliation-add", kwargs={"author_pk": author.pk})
        client.post(url, {"institution_name": "Aff 1"})
        client.post(url, {"institution_name": "Aff 2"})
        assert author.affiliations.count() == 2

    def test_delete_affiliation(self, client, bibliotekar_user, article_a):
        """4.7: Bibliotekar can delete affiliation."""
        author = AuthorFactory(article=article_a, order=1)
        aff = AffiliationFactory(author=author, order=1)
        client.force_login(bibliotekar_user)
        url = reverse("articles:affiliation-delete", kwargs={"pk": aff.pk})
        response = client.post(url)
        assert response.status_code == 200
        assert author.affiliations.count() == 0

    def test_affiliation_add_blocked_for_other_publisher(
        self, client, bibliotekar_user, article_b
    ):
        """4.8: Cannot add affiliation to another publisher's author."""
        author = AuthorFactory(article=article_b, order=1)
        client.force_login(bibliotekar_user)
        url = reverse("articles:affiliation-add", kwargs={"author_pk": author.pk})
        response = client.post(url, {"institution_name": "Hacked"})
        assert response.status_code == 403

    def test_affiliation_delete_blocked_for_other_publisher(
        self, client, bibliotekar_user, article_b
    ):
        """4.8: Cannot delete another publisher's affiliation."""
        author = AuthorFactory(article=article_b, order=1)
        aff = AffiliationFactory(author=author, order=1)
        client.force_login(bibliotekar_user)
        url = reverse("articles:affiliation-delete", kwargs={"pk": aff.pk})
        response = client.post(url)
        assert response.status_code == 403


# =============================================================================
# Task 8: Auditlog Tests (AC #10)
# =============================================================================


@pytest.mark.django_db
class TestAuthorAuditLog:
    """Test auditlog registration for Author and Affiliation models (AC #10)."""

    def test_author_auditlog_registered(self):
        """1.8: Author is registered with auditlog."""
        from auditlog.registry import auditlog
        assert Author in auditlog.get_models()

    def test_affiliation_auditlog_registered(self):
        """1.8: Affiliation is registered with auditlog."""
        from auditlog.registry import auditlog
        assert Affiliation in auditlog.get_models()

    def test_author_create_logged(self):
        """1.8: Author creation is logged by auditlog."""
        from auditlog.models import LogEntry

        author = AuthorFactory()
        log = LogEntry.objects.filter(
            object_pk=str(author.pk),
            action=LogEntry.Action.CREATE,
        )
        assert log.exists()

    def test_affiliation_create_logged(self):
        """1.8: Affiliation creation is logged by auditlog."""
        from auditlog.models import LogEntry

        aff = AffiliationFactory()
        log = LogEntry.objects.filter(
            object_pk=str(aff.pk),
            action=LogEntry.Action.CREATE,
        )
        assert log.exists()


# =============================================================================
# Task 8: Permission Scoping Tests
# =============================================================================


@pytest.mark.django_db
class TestPublisherScoping:
    """Test publisher scoping for author operations."""

    def test_bibliotekar_a_cannot_access_publisher_b_article(
        self, client, bibliotekar_user, article_b
    ):
        """Bibliotekar scoped to publisher A gets 403 on publisher B's article."""
        client.force_login(bibliotekar_user)
        url = reverse("articles:author-add", kwargs={"article_pk": article_b.pk})
        response = client.post(url, {
            "surname": "Test",
            "contributor_role": "author",
        })
        assert response.status_code == 403

    def test_regular_user_gets_403(self, client, regular_user, article_a):
        """Regular user (no role) gets 403."""
        client.force_login(regular_user)
        url = reverse("articles:author-add", kwargs={"article_pk": article_a.pk})
        response = client.post(url, {
            "surname": "Test",
            "contributor_role": "author",
        })
        assert response.status_code == 403

    def test_urednik_can_access_own_publisher(
        self, client, urednik_user, article_a
    ):
        """Urednik can add author to own publisher's article."""
        client.force_login(urednik_user)
        url = reverse("articles:author-add", kwargs={"article_pk": article_a.pk})
        response = client.post(url, {
            "surname": "Urednik Autor",
            "contributor_role": "author",
        })
        assert response.status_code == 200
        assert article_a.authors.count() == 1


# =============================================================================
# Code Review Fixes: Additional Tests
# =============================================================================


@pytest.mark.django_db
class TestReorderJsonErrorHandling:
    """Test author_reorder view handles malformed JSON gracefully."""

    def test_reorder_with_invalid_json(self, client, bibliotekar_user, article_a):
        """Reorder with invalid JSON body returns 200 without crash."""
        client.force_login(bibliotekar_user)
        url = reverse("articles:author-reorder", kwargs={"article_pk": article_a.pk})
        response = client.post(
            url,
            "not valid json",
            content_type="application/json",
        )
        assert response.status_code == 200

    def test_reorder_with_empty_body(self, client, bibliotekar_user, article_a):
        """Reorder with empty body returns 200 without crash."""
        client.force_login(bibliotekar_user)
        url = reverse("articles:author-reorder", kwargs={"article_pk": article_a.pk})
        response = client.post(
            url,
            "",
            content_type="application/json",
        )
        assert response.status_code == 200

    def test_reorder_with_non_integer_pks(self, client, bibliotekar_user, article_a):
        """Reorder with non-integer PKs skips them gracefully."""
        a1 = AuthorFactory(article=article_a, order=1, sequence=AuthorSequence.FIRST)
        client.force_login(bibliotekar_user)
        url = reverse("articles:author-reorder", kwargs={"article_pk": article_a.pk})
        response = client.post(
            url,
            json.dumps({"order": ["abc", a1.pk]}),
            content_type="application/json",
        )
        assert response.status_code == 200
        a1.refresh_from_db()
        # a1 should be index 2 (since "abc" was skipped, a1 is the only valid one at index 2)
        assert a1.order == 2

    def test_reorder_with_non_list_order(self, client, bibliotekar_user, article_a):
        """Reorder with non-list 'order' value handles gracefully."""
        client.force_login(bibliotekar_user)
        url = reverse("articles:author-reorder", kwargs={"article_pk": article_a.pk})
        response = client.post(
            url,
            json.dumps({"order": "not-a-list"}),
            content_type="application/json",
        )
        assert response.status_code == 200


@pytest.mark.django_db
class TestFormValidationErrorFeedback:
    """Test that form validation errors are returned to the user."""

    def test_add_author_invalid_returns_form_with_errors(
        self, client, bibliotekar_user, article_a
    ):
        """Adding author with empty required field returns form with errors."""
        client.force_login(bibliotekar_user)
        url = reverse("articles:author-add", kwargs={"article_pk": article_a.pk})
        response = client.post(url, {
            "given_name": "Marko",
            "surname": "",  # Required field empty
            "contributor_role": "author",
        })
        assert response.status_code == 200
        # Should return the form template with errors, retargeted to form container
        assert response.get("HX-Retarget") == "#author-form-container"
        assert article_a.authors.count() == 0  # Author was NOT created

    def test_add_author_invalid_orcid_returns_form_with_errors(
        self, client, bibliotekar_user, article_a
    ):
        """Adding author with invalid ORCID returns form with errors."""
        client.force_login(bibliotekar_user)
        url = reverse("articles:author-add", kwargs={"article_pk": article_a.pk})
        response = client.post(url, {
            "given_name": "Marko",
            "surname": "Petrovic",
            "orcid": "invalid-orcid",
            "contributor_role": "author",
        })
        assert response.status_code == 200
        assert response.get("HX-Retarget") == "#author-form-container"
        assert article_a.authors.count() == 0

    def test_update_author_invalid_returns_form_with_errors(
        self, client, bibliotekar_user, article_a
    ):
        """Updating author with invalid data returns form with errors."""
        author = AuthorFactory(article=article_a, surname="Original", order=1)
        client.force_login(bibliotekar_user)
        url = reverse("articles:author-update", kwargs={"pk": author.pk})
        response = client.post(url, {
            "given_name": "Test",
            "surname": "",  # Required field empty
            "contributor_role": "author",
        })
        assert response.status_code == 200
        assert response.get("HX-Retarget") == "#author-form-container"
        author.refresh_from_db()
        assert author.surname == "Original"  # Not changed

    def test_add_affiliation_invalid_returns_form_with_errors(
        self, client, bibliotekar_user, article_a
    ):
        """Adding affiliation with empty required field returns form with errors."""
        author = AuthorFactory(article=article_a, order=1)
        client.force_login(bibliotekar_user)
        url = reverse("articles:affiliation-add", kwargs={"author_pk": author.pk})
        response = client.post(url, {
            "institution_name": "",  # Required field empty
            "institution_ror_id": "",
            "department": "",
        })
        assert response.status_code == 200
        assert response.get("HX-Retarget") == "#author-form-container"
        assert author.affiliations.count() == 0
