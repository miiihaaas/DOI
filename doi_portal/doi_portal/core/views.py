"""
Core views for DOI Portal.

DashboardView - Admin dashboard with role-based content (Story 1.7, 3.8).
AuditLogListView, AuditLogDetailView - Audit log viewer (Story 6.2).
DeletedItemsView, deleted_item_restore, deleted_item_permanent_delete - Deleted items management (Story 6.3).
GdprRequest views - GDPR data request handling (Story 6.4).
"""

import json
from typing import Any

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.mixins import UserPassesTestMixin
from django.contrib.contenttypes.models import ContentType
from django.db.models import Q
from django.http import Http404, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.views.decorators.http import require_GET, require_POST
from django.views import View
from django.views.generic import CreateView, DetailView
from django.views.generic import ListView
from django.views.generic import TemplateView

from auditlog.models import LogEntry
from auditlog.registry import auditlog

from doi_portal.core.menu import get_user_role
from doi_portal.core.permissions import role_required
from doi_portal.users.models import User
from doi_portal.dashboard.services import (
    get_dashboard_statistics,
    get_my_draft_articles,
    get_pending_review_articles,
    get_ready_to_publish_articles,
)


class DashboardView(LoginRequiredMixin, TemplateView):
    """
    Admin dashboard with role-based content.

    Story 1.7: Base dashboard shell.
    Story 3.8: Full statistics, pending items, quick actions.

    Displays a Bootstrap 5 admin layout with:
    - Role-based statistic cards (AC#1, #4, #5)
    - Pending review articles (AC#2)
    - Ready to publish articles (AC#3)
    - My drafts section for Bibliotekar (AC#5)
    - Quick actions (AC#8)
    - Empty state messages (AC#7)
    """

    template_name = "dashboard/dashboard.html"

    def _get_role_flags(self) -> dict[str, bool]:
        """
        Get cached role flags for current user.

        Returns:
            Dict with is_admin, is_urednik, is_bibliotekar, has_publisher keys.
        """
        if hasattr(self, "_role_flags"):
            return self._role_flags

        user = self.request.user
        flags = {
            "is_admin": False,
            "is_urednik": False,
            "is_bibliotekar": False,
            "has_publisher": hasattr(user, "publisher") and user.publisher is not None,
        }

        if user.is_superuser:
            flags["is_admin"] = True
        else:
            user_groups = set(user.groups.values_list("name", flat=True))
            if "Administrator" in user_groups or "Superadmin" in user_groups:
                flags["is_admin"] = True
            if "Urednik" in user_groups:
                flags["is_urednik"] = True
            if "Bibliotekar" in user_groups:
                flags["is_bibliotekar"] = True

        self._role_flags = flags
        return flags

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        user = self.request.user
        flags = self._get_role_flags()

        # Basic user info
        context["user"] = user
        context["user_role"] = get_user_role(user)
        context["role_flags"] = flags

        # Breadcrumbs - Dashboard is the root
        context["breadcrumbs"] = [
            {"label": "Kontrolna tabla", "url": None},
        ]

        # Statistics
        context["stats"] = get_dashboard_statistics(user, flags)

        # Pending items based on role
        if flags["is_admin"] or flags["is_urednik"]:
            context["pending_review_articles"] = get_pending_review_articles(
                user, flags
            )
        if flags["is_admin"]:
            context["ready_to_publish_articles"] = get_ready_to_publish_articles(
                user, flags
            )
        if flags["is_bibliotekar"]:
            context["my_draft_articles"] = get_my_draft_articles(user)

        # Quick actions
        context["quick_actions"] = self._get_quick_actions(flags)

        return context

    def _get_quick_actions(self, flags: dict[str, bool]) -> list[dict[str, str]]:
        """
        Return role-appropriate quick action links.

        Args:
            flags: Role flags dict.

        Returns:
            List of action dicts with label, url_name, icon keys.
        """
        actions = []
        if flags["is_admin"]:
            actions = [
                {
                    "label": "Svi članci",
                    "url_name": "articles:list",
                    "icon": "bi-file-earmark-text",
                },
                {
                    "label": "Publikacije",
                    "url_name": "publications:list",
                    "icon": "bi-journal-text",
                },
                {
                    "label": "Izdavači",
                    "url_name": "publishers:list",
                    "icon": "bi-building",
                },
            ]
        elif flags["is_urednik"]:
            actions = [
                {
                    "label": "Članci na pregledu",
                    "url_name": "articles:list",
                    "icon": "bi-hourglass-split",
                },
                {
                    "label": "Izdanja",
                    "url_name": "issues:list",
                    "icon": "bi-collection",
                },
            ]
        elif flags["is_bibliotekar"]:
            actions = [
                {
                    "label": "Novi članak",
                    "url_name": "articles:create",
                    "icon": "bi-plus-circle",
                },
                {
                    "label": "Moji nacrti",
                    "url_name": "articles:list",
                    "icon": "bi-pencil-square",
                },
            ]
        return actions


# ============================================================================
# Story 6.2: Audit Log Viewer
# ============================================================================

# Action labels in Serbian for display
ACTION_CHOICES = [
    (LogEntry.Action.CREATE, "Kreiranje"),
    (LogEntry.Action.UPDATE, "Izmena"),
    (LogEntry.Action.DELETE, "Brisanje"),
]


class SuperadminRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    """Mixin that restricts access to Superadmin users only."""

    def test_func(self) -> bool:
        """Check if user is Superadmin."""
        return (
            self.request.user.is_superuser
            or self.request.user.groups.filter(name="Superadmin").exists()
        )


class AuditLogListView(SuperadminRequiredMixin, ListView):
    """
    List view for audit log entries with filtering and search.

    AC#1: Accessible at dashboard/audit-log/
    AC#2: Paginated, reverse chronological
    AC#3: Filtering by date, actor, action, model, object_id
    AC#5: HTMX search by object_repr and actor email
    AC#6: Superadmin only
    """

    model = LogEntry
    paginate_by = 50
    ordering = ["-timestamp"]
    template_name = "core/audit_log_list.html"
    context_object_name = "entries"

    def get_queryset(self):
        """Apply filters and search to queryset."""
        qs = super().get_queryset().select_related("content_type", "actor")

        # Date range filters
        date_from = self.request.GET.get("date_from")
        if date_from:
            qs = qs.filter(timestamp__date__gte=date_from)

        date_to = self.request.GET.get("date_to")
        if date_to:
            qs = qs.filter(timestamp__date__lte=date_to)

        # Actor filter
        actor = self.request.GET.get("actor")
        if actor:
            qs = qs.filter(actor_id=actor)

        # Action filter
        action = self.request.GET.get("action")
        if action is not None and action != "":
            try:
                qs = qs.filter(action=int(action))
            except (ValueError, TypeError):
                pass  # Ignore invalid action values

        # Content type (model) filter
        model_ct = self.request.GET.get("model")
        if model_ct:
            qs = qs.filter(content_type_id=model_ct)

        # Object ID filter
        object_id = self.request.GET.get("object_id")
        if object_id:
            qs = qs.filter(object_pk=object_id)

        # Search (q) - by object_repr or actor email
        q = self.request.GET.get("q")
        if q:
            qs = qs.filter(
                Q(object_repr__icontains=q) | Q(actor__email__icontains=q)
            )

        return qs

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        """Add filter options and form persistence to context."""
        context = super().get_context_data(**kwargs)

        # Breadcrumbs
        context["breadcrumbs"] = [
            {"label": "Kontrolna tabla", "url": "dashboard"},
            {"label": "Revizioni log", "url": None},
        ]

        # Filter persistence
        context["filter_date_from"] = self.request.GET.get("date_from", "")
        context["filter_date_to"] = self.request.GET.get("date_to", "")
        context["filter_actor"] = self.request.GET.get("actor", "")
        context["filter_action"] = self.request.GET.get("action", "")
        context["filter_model"] = self.request.GET.get("model", "")
        context["filter_object_id"] = self.request.GET.get("object_id", "")
        context["search_query"] = self.request.GET.get("q", "")

        # Dropdown options - only load for full page renders (not HTMX partials)
        if not self.request.headers.get("HX-Request"):
            context["users"] = User.objects.all().order_by("email")
            context["action_choices"] = ACTION_CHOICES

            # Registered content types for model dropdown
            registered_models = list(auditlog._registry.keys())
            if registered_models:
                ct_map = ContentType.objects.get_for_models(*registered_models)
                context["content_types"] = sorted(
                    ct_map.values(), key=lambda ct: ct.model
                )
            else:
                context["content_types"] = []

        return context

    def get(self, request, *args, **kwargs):
        """Override get to support HTMX partial rendering."""
        self.object_list = self.get_queryset()
        context = self.get_context_data()
        if request.headers.get("HX-Request"):
            return render(
                request, "core/partials/_audit_log_table.html", context
            )
        return render(request, self.template_name, context)


class AuditLogDetailView(SuperadminRequiredMixin, DetailView):
    """
    Detail view for a single audit log entry.

    AC#4: Shows metadata and changes (old vs new for UPDATE).
    AC#6: Superadmin only.
    """

    model = LogEntry
    template_name = "core/audit_log_detail.html"
    context_object_name = "entry"

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        """Parse changes JSON for display."""
        context = super().get_context_data(**kwargs)
        entry = self.object

        # Breadcrumbs
        context["breadcrumbs"] = [
            {"label": "Kontrolna tabla", "url": "dashboard"},
            {"label": "Revizioni log", "url": "core:audit-log-list"},
            {"label": f"Detalj #{entry.pk}", "url": None},
        ]

        # Action labels
        context["action_choices"] = ACTION_CHOICES

        # Parse changes
        changes_data = {}
        try:
            raw = entry.changes
            if raw:
                parsed = json.loads(raw) if isinstance(raw, str) else raw
                for field_name, values in parsed.items():
                    if isinstance(values, list) and len(values) == 2:
                        changes_data[field_name] = {
                            "old": values[0],
                            "new": values[1],
                        }
                    else:
                        changes_data[field_name] = {
                            "old": "",
                            "new": str(values),
                        }
        except (json.JSONDecodeError, TypeError):
            changes_data = {}

        context["changes_data"] = changes_data

        return context


# ============================================================================
# Story 6.3: Deleted Items Management
# ============================================================================

# Lazy imports to avoid circular dependencies
MODEL_TYPE_MAP = None


def _get_model_type_map():
    """Lazy-load model type mapping to avoid circular imports."""
    global MODEL_TYPE_MAP
    if MODEL_TYPE_MAP is None:
        from doi_portal.articles.models import Article, Author
        from doi_portal.issues.models import Issue
        from doi_portal.publications.models import Publication
        from doi_portal.publishers.models import Publisher

        MODEL_TYPE_MAP = {
            "publisher": Publisher,
            "publication": Publication,
            "issue": Issue,
            "article": Article,
            "author": Author,
        }
    return MODEL_TYPE_MAP


# Section config: (key, label, icon)
MODEL_TYPE_SECTIONS = [
    ("publisher", "Izdavači", "bi-building"),
    ("publication", "Publikacije", "bi-journal-text"),
    ("issue", "Izdanja", "bi-collection"),
    ("article", "Članci", "bi-file-earmark-text"),
    ("author", "Autori", "bi-person"),
]


class DeletedItemsView(SuperadminRequiredMixin, TemplateView):
    """
    View for managing soft-deleted items across all models.

    AC#5: Superadmin can access "Obrisane stavke" page.
    AC#8: Superadmin only access.
    """

    template_name = "core/deleted_items.html"

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)

        model_map = _get_model_type_map()
        type_filter = self.request.GET.get("type", "")

        # Build sections with pre-computed counts to avoid N+1 in template
        sections = []
        total_deleted_count = 0
        for key, label, icon in MODEL_TYPE_SECTIONS:
            model_class = model_map[key]
            if type_filter and type_filter != key:
                items = model_class.all_objects.none()
            else:
                items = (
                    model_class.all_objects.filter(is_deleted=True)
                    .select_related("deleted_by")
                    .order_by("-deleted_at")
                )
            count = items.count()
            total_deleted_count += count
            sections.append({
                "key": key,
                "type": key,
                "label": label,
                "icon": icon,
                "items": items,
                "count": count,
            })

        context["deleted_sections"] = sections
        context["total_deleted_count"] = total_deleted_count
        context["type_filter"] = type_filter

        # Breadcrumbs
        context["breadcrumbs"] = [
            {"label": "Kontrolna tabla", "url": "dashboard"},
            {"label": "Obrisane stavke", "url": None},
        ]

        return context


@require_POST
@role_required("Superadmin")
def deleted_item_restore(request, model_type, pk):
    """
    Restore a soft-deleted item.

    AC#6: Superadmin can restore deleted records via HTMX POST.
    """
    model_map = _get_model_type_map()
    model_class = model_map.get(model_type)
    if not model_class:
        raise Http404

    instance = get_object_or_404(
        model_class.all_objects, pk=pk, is_deleted=True
    )
    instance.restore()
    messages.success(request, f"Stavka '{instance}' je uspešno vraćena.")
    return HttpResponse("")


@require_POST
@role_required("Superadmin")
def deleted_item_permanent_delete(request, model_type, pk):
    """
    Permanently delete a soft-deleted item.

    AC#7: Superadmin can permanently delete records via HTMX POST.
    """
    model_map = _get_model_type_map()
    model_class = model_map.get(model_type)
    if not model_class:
        raise Http404

    instance = get_object_or_404(
        model_class.all_objects, pk=pk, is_deleted=True
    )
    label = str(instance)
    instance.delete()
    messages.success(request, f"Stavka '{label}' je trajno obrisana.")
    return HttpResponse("")


# ============================================================================
# Story 6.4: GDPR Data Request Handling
# ============================================================================


class GdprRequestListView(SuperadminRequiredMixin, ListView):
    """
    List view for GDPR data requests.

    AC#1: Paginated list of all requests, reverse chronological.
    AC#8: Superadmin only.
    """

    model = None  # Set dynamically to avoid circular import
    paginate_by = 25
    template_name = "core/gdpr_request_list.html"
    context_object_name = "requests"

    def get_queryset(self):
        from doi_portal.core.models import GdprRequest

        return GdprRequest.objects.all()

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context["breadcrumbs"] = [
            {"label": "Kontrolna tabla", "url": "dashboard"},
            {"label": "GDPR zahtevi", "url": None},
        ]
        return context


class GdprRequestCreateView(SuperadminRequiredMixin, CreateView):
    """
    Create view for new GDPR data request.

    AC#2: Form for creating new GDPR request with auto-set created_by.
    AC#8: Superadmin only.
    """

    template_name = "core/gdpr_request_form.html"
    success_url = reverse_lazy("core:gdpr-request-list")

    def get_form_class(self):
        from doi_portal.core.forms import GdprRequestForm

        return GdprRequestForm

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        return super().form_valid(form)

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context["breadcrumbs"] = [
            {"label": "Kontrolna tabla", "url": "dashboard"},
            {"label": "GDPR zahtevi", "url": "core:gdpr-request-list"},
            {"label": "Novi zahtev", "url": None},
        ]
        return context


class GdprRequestDetailView(SuperadminRequiredMixin, DetailView):
    """
    Detail view for a GDPR data request.

    AC#3: Shows affected data section.
    AC#8: Superadmin only.
    """

    template_name = "core/gdpr_request_detail.html"
    context_object_name = "gdpr_request"

    def get_queryset(self):
        from doi_portal.core.models import GdprRequest

        return GdprRequest.objects.all()

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        from doi_portal.core.models import GdprRequestStatus
        from doi_portal.core.services import GdprService

        affected_data = GdprService.identify_affected_data(
            self.object.requester_email
        )
        # Pre-compute count to avoid extra query in template
        affected_data["authors_count"] = affected_data["authors"].count()
        context["affected_data"] = affected_data
        context["GdprRequestStatus"] = GdprRequestStatus
        context["breadcrumbs"] = [
            {"label": "Kontrolna tabla", "url": "dashboard"},
            {"label": "GDPR zahtevi", "url": "core:gdpr-request-list"},
            {"label": f"GDPR-{self.object.pk}", "url": None},
        ]
        return context


@require_POST
@role_required("Superadmin")
def gdpr_request_process(request, pk):
    """
    Process a GDPR deletion request.

    AC#4, AC#5: Triggers soft delete + schedules anonymization.
    """
    from doi_portal.core.models import GdprRequest, GdprRequestStatus
    from doi_portal.core.services import GdprService

    gdpr_request = get_object_or_404(GdprRequest, pk=pk)

    if gdpr_request.status != GdprRequestStatus.PENDING:
        messages.error(request, "Zahtev nije u statusu 'Na čekanju'.")
        return redirect("core:gdpr-request-detail", pk=pk)

    if gdpr_request.request_type != "DELETION":
        messages.error(request, "Samo zahtevi za brisanje mogu biti obrađeni.")
        return redirect("core:gdpr-request-detail", pk=pk)

    GdprService.process_deletion_request(gdpr_request, request.user)
    messages.success(request, "Zahtev je uspešno obrađen. Grace period: 30 dana.")
    return redirect("core:gdpr-request-detail", pk=pk)


@require_POST
@role_required("Superadmin")
def gdpr_request_cancel(request, pk):
    """
    Cancel a GDPR request during grace period.

    AC#5: Restores soft-deleted data, sets CANCELLED.
    """
    from doi_portal.core.models import GdprRequest, GdprRequestStatus
    from doi_portal.core.services import GdprService

    gdpr_request = get_object_or_404(GdprRequest, pk=pk)

    if gdpr_request.status != GdprRequestStatus.PROCESSING:
        messages.error(request, "Samo zahtevi u obradi mogu biti otkazani.")
        return redirect("core:gdpr-request-detail", pk=pk)

    reason = request.POST.get("cancellation_reason", "")
    try:
        GdprService.cancel_request(gdpr_request, reason, request.user)
    except ValueError as e:
        messages.error(request, str(e))
        return redirect("core:gdpr-request-detail", pk=pk)
    messages.success(request, "Zahtev je otkazan. Podaci su vraćeni.")
    return redirect("core:gdpr-request-detail", pk=pk)


# ============================================================================
# Story 6.5: Sentry Test Endpoint
# ============================================================================


class SentryTestView(SuperadminRequiredMixin, View):
    """
    Sentry test endpoint for verifying Sentry integration.

    AC#7: Superadmin-only endpoint that generates a test error
    and sends it to Sentry for verification.
    """

    def get(self, request):
        sentry_active = False
        sentry_dsn_configured = False
        event_id = None
        sentry_environment = None

        try:
            import sentry_sdk

            client = sentry_sdk.get_client()
            sentry_dsn_configured = bool(client.dsn)
            sentry_active = client.is_active()
            if sentry_active:
                from django.conf import settings

                sentry_environment = getattr(settings, "SENTRY_ENVIRONMENT", None)
                if sentry_environment is None:
                    import os

                    sentry_environment = os.environ.get(
                        "SENTRY_ENVIRONMENT", "production"
                    )
        except ImportError:
            pass

        if sentry_active and request.GET.get("send_test"):
            try:
                raise Exception("DOI Portal - Sentry test event")  # noqa: TRY002, TRY301
            except Exception:
                import sentry_sdk

                event_id = sentry_sdk.capture_exception()

        context = {
            "sentry_active": sentry_active,
            "sentry_dsn_configured": sentry_dsn_configured,
            "sentry_environment": sentry_environment,
            "event_id": event_id,
            "breadcrumbs": [
                {"label": "Kontrolna tabla", "url": "dashboard"},
                {"label": "Sentry test", "url": None},
            ],
        }
        return render(request, "core/sentry_test.html", context)


@require_GET
@role_required("Superadmin")
def gdpr_request_download_report(request, pk):
    """
    Download confirmation report for a GDPR request.

    AC#7: Generates and returns TXT report.
    """
    from doi_portal.core.models import GdprRequest
    from doi_portal.core.services import GdprService

    gdpr_request = get_object_or_404(GdprRequest, pk=pk)
    report = GdprService.generate_confirmation_report(gdpr_request)

    response = HttpResponse(report, content_type="text/plain; charset=utf-8")
    response["Content-Disposition"] = (
        f'attachment; filename="gdpr_report_{gdpr_request.pk}.txt"'
    )
    return response
