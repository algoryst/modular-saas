import pytest
from django import forms
from django.template.loader import render_to_string
from django.urls import reverse


class _Form(forms.Form):
    email = forms.EmailField()
    password = forms.CharField(widget=forms.PasswordInput)


def _render(field_name: str) -> str:
    return render_to_string(
        "components/form_field.html", {"field": _Form()[field_name]}
    )


def test_form_field_password_renders_visibility_toggle():
    html = _render("password")

    assert 'x-data="passwordToggle"' in html
    assert 'aria-controls="id_password"' in html
    assert 'type="button"' in html


def test_form_field_non_password_has_no_toggle():
    assert "passwordToggle" not in _render("email")


@pytest.mark.django_db
def test_login_page_loads_alpine_and_toggle(client):
    response = client.get(reverse("account_login"))

    content = response.content.decode()
    assert 'x-data="passwordToggle"' in content
    # components.js registers the component, so it must load before Alpine.
    assert content.index("js/components.js") < content.index("alpine-csp-")
