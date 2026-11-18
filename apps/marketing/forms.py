from django import forms
from django.utils.translation import gettext_lazy as _

from .services import WaitlistProduct


class WaitlistForm(forms.Form):
    email = forms.EmailField(label=_("Work email"))
    product = forms.ChoiceField(
        label=_("I am interested in"), choices=WaitlistProduct.choices
    )
    privacy = forms.BooleanField(
        label=_(
            "I agree to receive launch news by email. I can unsubscribe at any time."
        )
    )
    # Honeypot: hidden from people with CSS, left empty by them, filled by bots.
    website = forms.CharField(
        label=_("Leave this field empty"),
        required=False,
        widget=forms.TextInput(attrs={"autocomplete": "off", "tabindex": "-1"}),
    )

    @property
    def is_spam(self) -> bool:
        return bool(self.cleaned_data.get("website"))
