from typing import Any

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.core.exceptions import PermissionDenied
from django.db.models import Q
from django.db.models import QuerySet
from django.http import HttpRequest
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.shortcuts import redirect
from django.shortcuts import render
from django.urls import reverse
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _
from django.views.generic import CreateView
from django.views.generic import DetailView
from django.views.generic import ListView
from django.views.generic import RedirectView
from django.views.generic import UpdateView

from doi_portal.users.forms import UserCreateForm
from doi_portal.users.forms import UserUpdateForm
from doi_portal.users.mixins import SuperadminRequiredMixin
from doi_portal.users.models import User
from doi_portal.users.services import invalidate_user_sessions

# Permission denied messages (ruff EM101 fix)
MSG_SUPERADMIN_ONLY = "Samo Superadmin ima pristup ovoj funkciji."
MSG_CANNOT_DEACTIVATE_SELF = "Ne možete deaktivirati sopstveni nalog."


class UserDetailView(LoginRequiredMixin, DetailView):
    model = User
    slug_field = "id"
    slug_url_kwarg = "id"


user_detail_view = UserDetailView.as_view()


class UserUpdateView(LoginRequiredMixin, SuccessMessageMixin, UpdateView):
    model = User
    fields = ["name"]
    success_message = _("Information successfully updated")

    def get_success_url(self) -> str:
        assert self.request.user.is_authenticated  # type guard
        return self.request.user.get_absolute_url()

    def get_object(self, queryset: QuerySet | None=None) -> User:
        assert self.request.user.is_authenticated  # type guard
        return self.request.user


user_update_view = UserUpdateView.as_view()


class UserRedirectView(LoginRequiredMixin, RedirectView):
    permanent = False

    def get_redirect_url(self) -> str:
        return reverse("users:detail", kwargs={"pk": self.request.user.pk})


user_redirect_view = UserRedirectView.as_view()


# ============================================================================
# Story 1.6: User Management Views for Superadmin
# ============================================================================


class UserListAdminView(SuperadminRequiredMixin, ListView):
    """
    List all users for Superadmin (Story 1.6, AC#1).

    Displays users with columns: email, name, role, publisher, status, last_activity.
    Supports filtering by role and status, and search by email/name.
    """

    model = User
    template_name = "users/user_list_admin.html"
    context_object_name = "users"
    paginate_by = 25

    def get_queryset(self) -> QuerySet[User]:
        """
        Get filtered and searched user queryset.

        Query params:
        - role: Filter by Group name
        - status: Filter by active/inactive
        - search: Search by email or name
        """
        queryset = User.objects.prefetch_related("groups").select_related("publisher")

        # Filter by role (Group)
        role = self.request.GET.get("role")
        if role:
            queryset = queryset.filter(groups__name=role)

        # Filter by status
        status = self.request.GET.get("status")
        if status == "active":
            queryset = queryset.filter(is_active=True)
        elif status == "inactive":
            queryset = queryset.filter(is_active=False)

        # Search by email or name
        search = self.request.GET.get("search")
        if search:
            queryset = queryset.filter(
                Q(email__icontains=search) | Q(name__icontains=search),
            )

        return queryset.order_by("-date_joined")

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        """Add filter values to context for form persistence."""
        context = super().get_context_data(**kwargs)
        context["current_role"] = self.request.GET.get("role", "")
        context["current_status"] = self.request.GET.get("status", "")
        context["current_search"] = self.request.GET.get("search", "")
        return context


class UserCreateAdminView(SuperadminRequiredMixin, SuccessMessageMixin, CreateView):
    """
    Create new user by Superadmin (Story 1.6, AC#2, AC#3).

    Creates user with role (Group) assignment and optional publisher.
    Supports password entry or email invitation (set_unusable_password).
    """

    model = User
    form_class = UserCreateForm
    template_name = "users/user_create.html"
    success_url = reverse_lazy("users:manage-list")
    success_message = _("Korisnik uspesno kreiran.")


class UserUpdateAdminView(SuperadminRequiredMixin, SuccessMessageMixin, UpdateView):
    """
    Update existing user by Superadmin (Story 1.6, AC#4).

    Updates user data, role (Group), and publisher assignment.
    Role changes update Group membership (old groups removed).
    """

    model = User
    form_class = UserUpdateForm
    template_name = "users/user_edit.html"
    success_url = reverse_lazy("users:manage-list")
    success_message = _("Korisnik uspesno azuriran.")


@login_required
def user_toggle_active(request: HttpRequest, pk: int) -> HttpResponse:
    """
    Toggle user activation status (Story 1.6, AC#5).

    HTMX endpoint for activating/deactivating users.
    Deactivation also invalidates all user sessions.

    Args:
        request: HTTP request
        pk: User primary key

    Returns:
        HTMX: Partial template with updated user row
        Non-HTMX: Redirect to user list
    """
    # Check Superadmin permission
    if not (
        request.user.groups.filter(name="Superadmin").exists()
        or request.user.is_superuser
    ):
        raise PermissionDenied(MSG_SUPERADMIN_ONLY)

    user = get_object_or_404(User, pk=pk)

    # Prevent self-deactivation
    if user.pk == request.user.pk:
        messages.error(request, _(MSG_CANNOT_DEACTIVATE_SELF))
        if request.headers.get("HX-Request"):
            return render(
                request,
                "users/partials/_user_row.html",
                {"user": user, "current_user_pk": request.user.pk},
            )
        return redirect("users:manage-list")

    # Toggle active status
    user.is_active = not user.is_active
    user.save()

    # Invalidate sessions if deactivating
    if not user.is_active:
        sessions_deleted = invalidate_user_sessions(user)
        messages.success(
            request,
            _("Korisnik deaktiviran. %(count)d sesija terminisano.")
            % {"count": sessions_deleted},
        )
    else:
        messages.success(request, _("Korisnik aktiviran."))

    # Return HTMX partial or redirect
    if request.headers.get("HX-Request"):
        return render(
            request,
            "users/partials/_user_row.html",
            {"user": user, "current_user_pk": request.user.pk},
        )

    return redirect("users:manage-list")
