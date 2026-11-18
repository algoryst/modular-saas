from typing import Any

from allauth.account.forms import SignupForm
from django import forms
from django.conf import settings
from django.http import HttpRequest
from django.utils.translation import gettext_lazy as _

from apps.core.forms import PlainFieldsMixin, password_help_text
from apps.countrypacks.registry import get_pack

# Session keys for the two signup steps. The workspace itself is created only after
# the email address is verified (no schema for unverified sign-ups).
SIGNUP_COMPANY = "signup_company"
PENDING_WORKSPACE = "pending_workspace"


def country_choices() -> list[tuple[str, str]]:
    codes = sorted(settings.COUNTRY_PACKS, key=lambda code: (code == "generic", code))
    return [(code, str(get_pack(code).name)) for code in codes]


class CompanyForm(forms.Form):
    country = forms.ChoiceField(
        label=_("Country"), choices=country_choices, initial="fr"
    )
    tax_id = forms.CharField(
        label=_("Company number"),
        max_length=40,
        help_text=_("In France, your 14-digit SIRET."),
    )


class CompanyNameField(forms.CharField):
    def __init__(self, **kwargs: Any) -> None:
        super().__init__(label=_("Company name"), max_length=200, **kwargs)


class WorkspaceSignupForm(PlainFieldsMixin, SignupForm):
    """Signup step 2: company name (confirmed or typed), email, password."""

    company_name = CompanyNameField()

    field_order = ["company_name", "email", "password1"]

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.fields["password1"].help_text = password_help_text()
        self.order_fields(self.field_order)

    def signup(self, request: HttpRequest, user: Any) -> None:
        # Called by allauth once the user exists; the workspace waits for the code.
        company = request.session[SIGNUP_COMPANY]
        request.session[PENDING_WORKSPACE] = {
            **company,
            "name": self.cleaned_data["company_name"],
        }


class WorkspaceNameForm(forms.Form):
    """For a signed-in user creating another workspace: just confirm the name."""

    company_name = CompanyNameField()
