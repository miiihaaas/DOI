from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include
from django.urls import path
from django.views import defaults as default_views
from django.views.generic import TemplateView

from doi_portal.core.views import DashboardView

urlpatterns = [
    path("", TemplateView.as_view(template_name="pages/home.html"), name="home"),
    path(
        "about/",
        TemplateView.as_view(template_name="pages/about.html"),
        name="about",
    ),
    # Django Admin, use {% url 'admin:index' %}
    path(settings.ADMIN_URL, admin.site.urls),
    # User management
    path("users/", include("doi_portal.users.urls", namespace="users")),
    path("accounts/", include("allauth.urls")),
    # API
    path("api/", include("config.api_router")),
    # Your stuff: custom urls includes go here
    # Story 1.3: Dashboard route
    path("dashboard/", DashboardView.as_view(), name="dashboard"),
    # Story 2.1: Publisher admin routes (under dashboard, not Django admin)
    path("dashboard/publishers/", include("doi_portal.publishers.urls", namespace="publishers")),
    # Story 2.3: Publication admin routes (under dashboard)
    path("dashboard/publications/", include("doi_portal.publications.urls", namespace="publications")),
    # Story 2.6: Issue admin routes (under dashboard)
    path("dashboard/issues/", include("doi_portal.issues.urls", namespace="issues")),
    # Story 2.2: Public portal routes (no authentication required)
    path("publishers/", include("doi_portal.portal.urls", namespace="portal")),
    # Story 2.5: Public publications portal routes (no authentication required)
    path("publications/", include("doi_portal.portal.urls_publications", namespace="portal-publications")),
    # Media files
    *static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT),
]


if settings.DEBUG:
    # This allows the error pages to be debugged during development, just visit
    # these url in browser to see how these error pages look like.
    urlpatterns += [
        path(
            "400/",
            default_views.bad_request,
            kwargs={"exception": Exception("Bad Request!")},
        ),
        path(
            "403/",
            default_views.permission_denied,
            kwargs={"exception": Exception("Permission Denied")},
        ),
        path(
            "404/",
            default_views.page_not_found,
            kwargs={"exception": Exception("Page not Found")},
        ),
        path("500/", default_views.server_error),
    ]
    if "debug_toolbar" in settings.INSTALLED_APPS:
        import debug_toolbar

        urlpatterns = [
            path("__debug__/", include(debug_toolbar.urls)),
            *urlpatterns,
        ]
