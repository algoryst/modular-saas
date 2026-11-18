"""URLs served on both the root domain and every workspace host.

config.urls (root domain) and config.urls_tenant (workspaces) each add their own
"home" and include these.
"""

from django.conf import settings
from django.conf.urls.static import static
from django.urls import include, path
from django.views import defaults as default_views
from django.views.generic import TemplateView
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from rest_framework.authtoken.views import obtain_auth_token

from apps.accounts.views import set_language_view
from apps.tenants.views import WorkspaceSignupView

urlpatterns = [
    path(
        "about/",
        TemplateView.as_view(template_name="pages/about.html"),
        name="about",
    ),
    # User management
    path("users/", include("apps.accounts.urls", namespace="accounts")),
    # Signup step 2 replaces allauth's view (same URL name), before allauth's URLs.
    path("accounts/signup/", WorkspaceSignupView.as_view(), name="account_signup"),
    path("accounts/", include("allauth.urls")),
    path("", include("apps.tenants.urls", namespace="tenants")),
    # Your stuff: custom urls includes go here
    path("", include("apps.marketing.urls", namespace="marketing")),
    # Stores the language choice in a cookie, and on the account when signed in.
    path("i18n/setlang/", set_language_view, name="set_language"),
    # Media files
    *static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT),
]

# API URLS
urlpatterns += [
    # API base url
    path("api/", include("config.api_router")),
    # DRF auth token
    path("api/auth-token/", obtain_auth_token, name="obtain_auth_token"),
    path("api/schema/", SpectacularAPIView.as_view(), name="api-schema"),
    path(
        "api/docs/",
        SpectacularSwaggerView.as_view(url_name="api-schema"),
        name="api-docs",
    ),
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
