from __future__ import annotations

from typing import TYPE_CHECKING

from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.views import View
from django.views.generic import DetailView, RedirectView, UpdateView
from django.views.i18n import set_language

from apps.accounts.forms import LanguageForm
from apps.accounts.models import User
from apps.accounts.repositories import UserRepository
from apps.accounts.services import SetPreferredLanguage

if TYPE_CHECKING:
    from django.db.models import QuerySet
    from django.http import HttpRequest, HttpResponse


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
        # mypy type guard; LoginRequiredMixin already rejects anonymous users.
        assert self.request.user.is_authenticated  # nosec B101
        return self.request.user.get_absolute_url()

    def get_object(self, queryset: QuerySet | None = None) -> User:
        # mypy type guard; LoginRequiredMixin already rejects anonymous users.
        assert self.request.user.is_authenticated  # nosec B101
        return self.request.user


user_update_view = UserUpdateView.as_view()


class UserRedirectView(LoginRequiredMixin, RedirectView):
    permanent = False

    def get_redirect_url(self) -> str:
        return reverse("accounts:detail", kwargs={"pk": self.request.user.pk})


user_redirect_view = UserRedirectView.as_view()


class SetLanguageView(View):
    """Django's set_language, plus saving the choice on a signed-in user's account."""

    http_method_names = ["post"]

    def post(self, request: HttpRequest) -> HttpResponse:
        form = LanguageForm(request.POST)
        if request.user.is_authenticated and form.is_valid():
            SetPreferredLanguage(users=UserRepository())(
                request.user, form.cleaned_data["language"]
            )
        return set_language(request)


set_language_view = SetLanguageView.as_view()
