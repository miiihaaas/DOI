from django.urls import path

from .views import UserCreateAdminView
from .views import UserListAdminView
from .views import UserUpdateAdminView
from .views import user_detail_view
from .views import user_redirect_view
from .views import user_toggle_active
from .views import user_update_view

app_name = "users"
urlpatterns = [
    path("~redirect/", view=user_redirect_view, name="redirect"),
    path("~update/", view=user_update_view, name="update"),
    path("<int:pk>/", view=user_detail_view, name="detail"),
    # Story 1.6: User Management by Superadmin
    path("manage/", view=UserListAdminView.as_view(), name="manage-list"),
    path("manage/create/", view=UserCreateAdminView.as_view(), name="create"),
    path("manage/<int:pk>/edit/", view=UserUpdateAdminView.as_view(), name="edit"),
    path(
        "manage/<int:pk>/toggle-active/", view=user_toggle_active, name="toggle-active",
    ),
]
