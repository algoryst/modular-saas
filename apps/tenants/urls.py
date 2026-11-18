from django.urls import path

from apps.tenants.views import (
    CompanySignupView,
    CreateWorkspaceView,
    GoToWorkspaceView,
    HandoffView,
    OpenWorkspaceView,
)

# Included on every host; root-domain views redirect there from a workspace host.
app_name = "tenants"
urlpatterns = [
    path("signup/", CompanySignupView.as_view(), name="signup"),
    path("workspaces/", GoToWorkspaceView.as_view(), name="go"),
    path("workspaces/new/", CreateWorkspaceView.as_view(), name="create"),
    path("workspaces/<int:pk>/open/", OpenWorkspaceView.as_view(), name="open"),
    path("auth/handoff/", HandoffView.as_view(), name="handoff"),
]
