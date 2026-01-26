"""
Public portal views for DOI Portal.

Story 2.2: Public Publisher Page

These are PUBLIC views - no authentication required.
CSRF protection is handled by Django middleware for GET requests (safe methods).
"""

from django.urls import reverse
from django.views.generic import DetailView
from django.views.generic import ListView

from doi_portal.publishers.models import Publisher


class PublisherPublicListView(ListView):
    """
    Public listing of all active publishers.

    AC: #2 - Lists all active publishers with logos and names.
    Each publisher links to their detail page.
    """

    model = Publisher
    template_name = "portal/publishers/publisher_list.html"
    context_object_name = "publishers"

    def get_queryset(self):
        """
        Return all active (non-deleted) publishers.

        SoftDeleteManager already excludes is_deleted=True records.
        """
        return Publisher.objects.all().order_by("name")

    def get_context_data(self, **kwargs):
        """Add breadcrumbs to context."""
        context = super().get_context_data(**kwargs)
        context["breadcrumbs"] = [
            {"label": "Početna", "url": reverse("home")},
            {"label": "Izdavači", "url": None},
        ]
        return context


class PublisherPublicDetailView(DetailView):
    """
    Public view of a single publisher with their publications.

    AC: #1, #3, #4 - Shows publisher details and publications.
    Returns 404 for deleted or non-existent publishers.
    """

    model = Publisher
    template_name = "portal/publishers/publisher_detail.html"
    context_object_name = "publisher"
    slug_url_kwarg = "slug"

    def get_queryset(self):
        """
        Return queryset of active publishers.

        SoftDeleteManager excludes deleted publishers - will raise 404.
        """
        return Publisher.objects.all()

    def get_context_data(self, **kwargs):
        """Add breadcrumbs and publications placeholder to context."""
        context = super().get_context_data(**kwargs)
        context["breadcrumbs"] = [
            {"label": "Početna", "url": reverse("home")},
            {"label": "Izdavači", "url": reverse("portal:publisher-list")},
            {"label": self.object.name, "url": None},
        ]
        # Publications placeholder - empty for now, Story 2.3 will populate
        context["publications"] = []
        return context
