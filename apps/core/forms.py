"""Form helpers shared by every app (accounts, tenants, ...)."""

from typing import Any

from django.contrib.auth.password_validation import (
    MinimumLengthValidator,
    get_default_password_validators,
)
from django.forms import Field
from django.utils.translation import gettext_lazy as _


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
