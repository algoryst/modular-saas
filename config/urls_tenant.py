"""Workspace hosts (acme.app.example.fr)."""

from django.urls import include, path

from apps.tenants.views import WorkspaceHomeView

urlpatterns = [
    path("", WorkspaceHomeView.as_view(), name="home"),
    path("", include("config.urls_shared")),
]
