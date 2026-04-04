"""
Tests for ArticleRelation model, form, and views.

Crossref Relations metadata support.
"""

import json

import pytest
from django.test import RequestFactory
from django.urls import reverse

from doi_portal.articles.forms import ArticleRelationForm
from doi_portal.articles.models import ArticleRelation, RelationScope
from doi_portal.articles.tests.factories import (
    ArticleFactory,
    ArticleRelationFactory,
    AuthorFactory,
)
from doi_portal.users.tests.factories import UserFactory


# =============================================================================
# Model tests
# =============================================================================


@pytest.mark.django_db
class TestArticleRelationModel:
    """Tests for ArticleRelation model."""

    def test_auto_scope_intra_work(self):
        """Given relationship_type='isPreprintOf', relation_scope auto-set to 'intra_work'."""
        relation = ArticleRelationFactory(relationship_type="isPreprintOf")
        assert relation.relation_scope == RelationScope.INTRA_WORK

    def test_auto_scope_inter_work(self):
        """Given relationship_type='isSupplementTo', relation_scope auto-set to 'inter_work'."""
        relation = ArticleRelationFactory(relationship_type="isSupplementTo")
        assert relation.relation_scope == RelationScope.INTER_WORK

    def test_str_representation(self):
        """__str__() returns '{relationship_type} -> {target_identifier}'."""
        relation = ArticleRelationFactory(
            relationship_type="isPreprintOf",
            target_identifier="10.1234/test",
        )
        assert str(relation) == "isPreprintOf \u2192 10.1234/test"

    def test_ordering(self):
        """Relations are ordered by 'order' field."""
        article = ArticleFactory()
        r2 = ArticleRelationFactory(article=article, order=2)
        r0 = ArticleRelationFactory(article=article, order=0)
        r1 = ArticleRelationFactory(article=article, order=1)

        relations = list(article.relations.all())
        assert relations == [r0, r1, r2]

    def test_cascade_delete(self):
        """Deleting article cascades to relations."""
        relation = ArticleRelationFactory()
        article = relation.article
        article_pk = article.pk
        article.delete()
        assert not ArticleRelation.objects.filter(article_id=article_pk).exists()

    def test_all_intra_types_set_intra_scope(self):
        """All intra-work relationship types set scope to intra_work."""
        from doi_portal.articles.models import INTRA_WORK_TYPES

        article = ArticleFactory()
        for rt, _ in INTRA_WORK_TYPES:
            relation = ArticleRelation(
                article=article,
                relationship_type=rt,
                identifier_type="doi",
                target_identifier="10.1234/test",
            )
            relation.save()
            assert relation.relation_scope == RelationScope.INTRA_WORK

    def test_all_inter_types_set_inter_scope(self):
        """All inter-work relationship types set scope to inter_work."""
        from doi_portal.articles.models import INTER_WORK_TYPES

        article = ArticleFactory()
        for rt, _ in INTER_WORK_TYPES:
            relation = ArticleRelation(
                article=article,
                relationship_type=rt,
                identifier_type="doi",
                target_identifier="10.1234/test",
            )
            relation.save()
            assert relation.relation_scope == RelationScope.INTER_WORK


# =============================================================================
# Form tests
# =============================================================================


@pytest.mark.django_db
class TestArticleRelationForm:
    """Tests for ArticleRelationForm."""

    def test_valid_form(self):
        """Form is valid with all required fields."""
        form = ArticleRelationForm(data={
            "relationship_type": "isPreprintOf",
            "identifier_type": "doi",
            "target_identifier": "10.1234/test",
            "description": "",
        })
        assert form.is_valid()

    def test_required_fields(self):
        """Form requires relationship_type and target_identifier."""
        form = ArticleRelationForm(data={})
        assert not form.is_valid()
        assert "relationship_type" in form.errors
        assert "target_identifier" in form.errors

    def test_grouped_choices(self):
        """relationship_type field uses grouped choices (optgroup)."""
        form = ArticleRelationForm()
        choices = form.fields["relationship_type"].choices
        # Grouped choices: first item should be a tuple of (group_label, list_of_choices)
        # The empty choice is added automatically by Django
        found_group = False
        for item in choices:
            if isinstance(item, (list, tuple)) and len(item) == 2:
                label, sub_choices = item
                if isinstance(sub_choices, (list, tuple)) and len(sub_choices) > 0:
                    found_group = True
                    break
        assert found_group, "Expected grouped choices (optgroup) for relationship_type"

    def test_description_optional(self):
        """description field is optional."""
        form = ArticleRelationForm(data={
            "relationship_type": "isSupplementTo",
            "identifier_type": "doi",
            "target_identifier": "10.1234/test",
        })
        assert form.is_valid()


# =============================================================================
# View tests
# =============================================================================


@pytest.mark.django_db
class TestRelationViews:
    """Tests for relation HTMX views."""

    def setup_method(self):
        """Set up test data."""
        self.user = UserFactory(is_superuser=True)
        self.article = ArticleFactory()

    def test_relation_add_success(self, client):
        """POST to relation-add creates relation and returns list partial."""
        client.force_login(self.user)
        url = reverse("articles:relation-add", kwargs={"article_pk": self.article.pk})
        response = client.post(url, {
            "relationship_type": "isPreprintOf",
            "identifier_type": "doi",
            "target_identifier": "10.1234/test",
            "description": "Test description",
        })
        assert response.status_code == 200
        assert self.article.relations.count() == 1
        relation = self.article.relations.first()
        assert relation.relationship_type == "isPreprintOf"
        assert relation.relation_scope == RelationScope.INTRA_WORK

    def test_relation_add_invalid(self, client):
        """POST with invalid data returns form with errors and HX-Retarget."""
        client.force_login(self.user)
        url = reverse("articles:relation-add", kwargs={"article_pk": self.article.pk})
        response = client.post(url, {
            "relationship_type": "",
            "target_identifier": "",
        })
        assert response.status_code == 200
        assert response["HX-Retarget"] == "#relation-form-container"
        assert response["HX-Reswap"] == "innerHTML"

    def test_relation_delete(self, client):
        """POST to relation-delete removes relation."""
        client.force_login(self.user)
        relation = ArticleRelationFactory(article=self.article)
        url = reverse("articles:relation-delete", kwargs={"pk": relation.pk})
        response = client.post(url)
        assert response.status_code == 200
        assert self.article.relations.count() == 0

    def test_relation_reorder(self, client):
        """POST to relation-reorder updates order (0-indexed)."""
        client.force_login(self.user)
        r1 = ArticleRelationFactory(article=self.article, order=0)
        r2 = ArticleRelationFactory(article=self.article, order=1)
        url = reverse("articles:relation-reorder", kwargs={"article_pk": self.article.pk})
        response = client.post(
            url,
            json.dumps({"order": [r2.pk, r1.pk]}),
            content_type="application/json",
        )
        assert response.status_code == 200
        r1.refresh_from_db()
        r2.refresh_from_db()
        assert r2.order == 0
        assert r1.order == 1

    def test_relation_form_view(self, client):
        """GET to relation-form returns empty form."""
        client.force_login(self.user)
        url = reverse("articles:relation-form", kwargs={"article_pk": self.article.pk})
        response = client.get(url)
        assert response.status_code == 200

    def test_relation_add_permission_denied(self, client):
        """Non-privileged user cannot add relations."""
        regular_user = UserFactory()
        client.force_login(regular_user)
        url = reverse("articles:relation-add", kwargs={"article_pk": self.article.pk})
        response = client.post(url, {
            "relationship_type": "isPreprintOf",
            "identifier_type": "doi",
            "target_identifier": "10.1234/test",
        })
        assert response.status_code == 403
