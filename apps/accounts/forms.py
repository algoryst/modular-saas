from typing import Any

from allauth.account.forms import (
    ChangeEmailForm,
    ConfirmEmailVerificationCodeForm,
    ConfirmLoginCodeForm,
    LoginForm,
    RequestLoginCodeForm,
    ResetPasswordForm,
    ResetPasswordKeyForm,
    SignupForm,
)
from allauth.socialaccount.forms import SignupForm as SocialSignupForm
from django.conf import settings
from django.contrib.auth import forms as admin_forms
from django.contrib.auth.password_validation import (
    MinimumLengthValidator,
    get_default_password_validators,
)
from django.forms import ChoiceField, EmailField, Field, Form
from django.utils.translation import gettext_lazy as _

from .models import User


class UserAdminChangeForm(admin_forms.UserChangeForm):
    class Meta(admin_forms.UserChangeForm.Meta):
        model = User
        field_classes = {"email": EmailField}


class UserAdminCreationForm(admin_forms.AdminUserCreationForm):
    """
    Form for User Creation in the Admin Area.
    To change user signup, see UserSignupForm and UserSocialSignupForm.
    """

    class Meta(admin_forms.UserCreationForm.Meta):
        model = User
        fields = ("email",)
        field_classes = {"email": EmailField}
        error_messages = {
            "email": {"unique": _("This email has already been taken.")},
        }


class PlainFieldsMixin:
    """Labels only: allauth's placeholders repeat the label and vanish on typing."""

    EMAIL_FIELDS = ("email", "login")
    fields: dict[str, Field]  # provided by the forms.Form this is mixed into

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            field.widget.attrs.pop("placeholder", None)
            if name in self.EMAIL_FIELDS:
                field.label = _("Email address")


def password_help_text() -> str:
    """One sentence built from the configured validators, so it cannot drift."""
    min_length = next(
        (
            v.min_length
            for v in get_default_password_validators()
            if isinstance(v, MinimumLengthValidator)
        ),
        None,
    )
    if min_length is None:
        return str(_("Avoid common or all-number passwords."))
    return str(
        _("At least %(min_length)d characters. Avoid common or all-number passwords.")
        % {"min_length": min_length}
    )


class UserLoginForm(PlainFieldsMixin, LoginForm):
    pass


class UserSignupForm(PlainFieldsMixin, SignupForm):
    """
    Form that will be rendered on a user sign up section/screen.
    Default fields will be added automatically.
    Check UserSocialSignupForm for accounts created from social.
    """

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.fields["password1"].help_text = password_help_text()


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
    See UserSignupForm otherwise.
    """


class LanguageForm(Form):
    language = ChoiceField(choices=settings.LANGUAGES)
