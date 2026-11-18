from typing import Any

from allauth.account.forms import (
    ChangeEmailForm,
    ConfirmEmailVerificationCodeForm,
    ConfirmLoginCodeForm,
    LoginForm,
    RequestLoginCodeForm,
    ResetPasswordForm,
    ResetPasswordKeyForm,
)
from allauth.socialaccount.forms import SignupForm as SocialSignupForm
from django.conf import settings
from django.contrib.auth import forms as admin_forms
from django.forms import ChoiceField, EmailField, Form
from django.utils.translation import gettext_lazy as _

from apps.core.forms import PlainFieldsMixin, password_help_text

from .models import User


class UserAdminChangeForm(admin_forms.UserChangeForm):
    class Meta(admin_forms.UserChangeForm.Meta):
        model = User
        field_classes = {"email": EmailField}


class UserAdminCreationForm(admin_forms.AdminUserCreationForm):
    """
    Form for User Creation in the Admin Area.
    Signup itself lives in apps.tenants.forms.WorkspaceSignupForm.
    """

    class Meta(admin_forms.UserCreationForm.Meta):
        model = User
        fields = ("email",)
        field_classes = {"email": EmailField}
        error_messages = {
            "email": {"unique": _("This email has already been taken.")},
        }


class UserLoginForm(PlainFieldsMixin, LoginForm):
    pass


class UserResetPasswordForm(PlainFieldsMixin, ResetPasswordForm):
    pass


class UserResetPasswordKeyForm(PlainFieldsMixin, ResetPasswordKeyForm):
    """New password once; the show/hide toggle replaces typing it again."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        del self.fields["password2"]
        self.fields["password1"].help_text = password_help_text()


class UserRequestLoginCodeForm(PlainFieldsMixin, RequestLoginCodeForm):
    pass


class UserConfirmLoginCodeForm(PlainFieldsMixin, ConfirmLoginCodeForm):
    pass


class UserConfirmEmailVerificationCodeForm(
    PlainFieldsMixin, ConfirmEmailVerificationCodeForm
):
    pass


class UserChangeEmailForm(PlainFieldsMixin, ChangeEmailForm):
    pass


class UserSocialSignupForm(SocialSignupForm):
    """
    Renders the form when user has signed up using social accounts.
    Default fields will be added automatically.
    """


class LanguageForm(Form):
    language = ChoiceField(choices=settings.LANGUAGES)
