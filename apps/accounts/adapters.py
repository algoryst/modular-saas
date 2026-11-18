from __future__ import annotations

import typing

from allauth.account.adapter import DefaultAccountAdapter
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from django.conf import settings
from django.urls import reverse
from django.utils import translation
from django_tenants.utils import get_public_schema_name

if typing.TYPE_CHECKING:
    from allauth.socialaccount.models import SocialLogin
    from django.forms import Form
    from django.http import HttpRequest

    from apps.accounts.models import User


class AccountAdapter(DefaultAccountAdapter):
    def is_open_for_signup(self, request: HttpRequest) -> bool:
        return getattr(settings, "ACCOUNT_ALLOW_REGISTRATION", True)

    def get_login_redirect_url(self, request: HttpRequest) -> str:
        # On a workspace host, stay there; on the root domain, go to (or create)
        # the user's workspace, which hands the session over to its host.
        tenant = getattr(request, "tenant", None)
        if tenant is not None and tenant.schema_name != get_public_schema_name():
            return reverse("home")
        return reverse("tenants:go")

    def get_signup_redirect_url(self, request: HttpRequest) -> str:
        # allauth reads ACCOUNT_SIGNUP_REDIRECT_URL here, not the login logic above.
        return self.get_login_redirect_url(request)

    def save_user(
        self, request: HttpRequest, user: User, form: Form, commit: bool = True
    ) -> User:
        # Remember the language the person signed up in; they never have to choose.
        user.language = translation.get_language() or ""
        return super().save_user(request, user, form, commit=commit)


class SocialAccountAdapter(DefaultSocialAccountAdapter):
    def is_open_for_signup(
        self,
        request: HttpRequest,
        sociallogin: SocialLogin,
    ) -> bool:
        return getattr(settings, "ACCOUNT_ALLOW_REGISTRATION", True)

    def populate_user(
        self,
        request: HttpRequest,
        sociallogin: SocialLogin,
        data: dict[str, typing.Any],
    ) -> User:
        """
        Populates user information from social provider info.

        See "Creating and Populating User Instances" in
        https://docs.allauth.org/en/latest/socialaccount/advanced.html
        """
        user = super().populate_user(request, sociallogin, data)
        if not user.name:
            if name := data.get("name"):
                user.name = name
            elif first_name := data.get("first_name"):
                user.name = first_name
                if last_name := data.get("last_name"):
                    user.name += f" {last_name}"
        return user
