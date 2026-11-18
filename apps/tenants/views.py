from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView


class WorkspaceHomeView(LoginRequiredMixin, TemplateView):
    """Landing page inside a workspace until the W7 dashboard replaces it."""

    template_name = "tenants/home.html"
