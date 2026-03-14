"""
Tests for auditlog model registration (Story 6.1).

Tests cover:
- AC#2: All required models are registered with auditlog
"""

import pytest
from auditlog.registry import auditlog
from django.contrib.auth import get_user_model

from doi_portal.articles.models import Affiliation, Article, Author
from doi_portal.crossref.models import CrossrefExport
from doi_portal.issues.models import Issue
from doi_portal.publications.models import Publication
from doi_portal.publishers.models import Publisher

User = get_user_model()


@pytest.mark.django_db
class TestAllModelsRegistered:
    """AC2: Verify all required models are registered with auditlog."""

    REQUIRED_MODELS = [
        (Publisher, "Publisher"),
        (Publication, "Publication"),
        (Issue, "Issue"),
        (Article, "Article"),
        (Author, "Author"),
        (Affiliation, "Affiliation"),
        (User, "User"),
        (CrossrefExport, "CrossrefExport"),
    ]

    @pytest.mark.parametrize(
        "model,model_name",
        REQUIRED_MODELS,
        ids=[name for _, name in REQUIRED_MODELS],
    )
    def test_model_registered_with_auditlog(self, model, model_name):
        """AC2: {model_name} is registered with auditlog."""
        assert auditlog.contains(model), (
            f"{model_name} must be registered with auditlog"
        )

    def test_all_required_models_registered_at_once(self):
        """AC2: Unified check that ALL required models are registered."""
        unregistered = []
        for model, model_name in self.REQUIRED_MODELS:
            if not auditlog.contains(model):
                unregistered.append(model_name)
        assert not unregistered, (
            f"Models not registered with auditlog: {', '.join(unregistered)}"
        )
