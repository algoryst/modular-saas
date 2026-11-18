"""Root domain: marketing site, signup, admin. Workspaces use config.urls_tenant."""

from django.conf import settings
from django.contrib import admin
from django.urls import include, path

from apps.marketing.views import LandingView

urlpatterns = [
    path("", LandingView.as_view(), name="home"),
    # Platform admin only on the root domain (django-tenants 4.0.6 advice).
    path(settings.ADMIN_URL, admin.site.urls),
    path("", include("config.urls_shared")),
]
