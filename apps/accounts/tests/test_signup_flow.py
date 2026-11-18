"""Sign-up, email verification by code and sign-in by code, end to end."""

from __future__ import annotations

import re
from datetime import timedelta
from typing import TYPE_CHECKING

import pytest
from allauth.account.models import EmailAddress
from django.core import mail
from django.core.cache import cache
from django.urls import reverse
from freezegun import freeze_time

from apps.accounts.tests.factories import UserFactory

if TYPE_CHECKING:
    from django.test import Client

pytestmark = pytest.mark.django_db

PASSWORD = "correct-horse-battery-staple-42"


@pytest.fixture(autouse=True)
def _clear_rate_limits():
    cache.clear()


@pytest.fixture
def signup_open(settings):
    settings.ACCOUNT_ALLOW_REGISTRATION = True


def _code_from_last_email() -> str:
    body = str(mail.outbox[-1].body)
    match = re.search(r"^\s*([A-Z0-9]{4}-[A-Z0-9]{4})\s*$", body, re.MULTILINE)
    assert match, body
    return match.group(1)


def _signed_in(client: Client) -> bool:
    return "_auth_user_id" in client.session


def _start_signup(client: Client) -> None:
    """Step 1 (company). No Sirene key in tests, so the name is typed in step 2."""
    client.post(
        reverse("tenants:signup"), {"country": "fr", "tax_id": "73282932000074"}
    )


def _sign_up(client: Client, email: str = "founder@example.fr"):
    _start_signup(client)
    return client.post(
        reverse("account_signup"),
        {"company_name": "Acme", "email": email, "password1": PASSWORD},
    )


class TestSignupClosed:
    def test_signup_closed_by_default_points_to_waitlist(self, client):
        response = client.get(reverse("account_signup"), follow=True)

        content = response.content.decode()
        assert 'name="password1"' not in content
        assert f'href="{reverse("home")}#waitlist"' in content

    def test_signup_closed_nav_has_no_signup_link(self, client):
        response = client.get(reverse("home"))

        assert 'id="sign-up-link"' not in response.content.decode()


@pytest.mark.usefixtures("signup_open")
class TestSignupByCode:
    def test_signup_form_asks_password_once_with_short_help(self, client):
        _start_signup(client)
        response = client.get(reverse("account_signup"))

        form = response.context["form"]
        assert "password2" not in form.fields
        assert "8" in str(form.fields["password1"].help_text)
        assert "<li>" not in str(form.fields["password1"].help_text)

    def test_signup_sends_code_and_shows_code_page(self, client):
        response = _sign_up(client)

        assert response.status_code == 302
        assert response.url == reverse("account_email_verification_sent")
        assert len(mail.outbox) == 1
        page = client.get(response.url).content.decode()
        assert 'name="code"' in page
        assert 'value="resend"' in page
        assert 'value="change"' in page

    def test_signup_correct_code_verifies_and_signs_in(self, client):
        _sign_up(client)

        response = client.post(
            reverse("account_email_verification_sent"),
            {"code": _code_from_last_email()},
        )

        assert response.status_code == 302
        assert _signed_in(client)
        assert EmailAddress.objects.get(email="founder@example.fr").verified

    def test_signup_flow_keeps_only_the_useful_message(self, client):
        _sign_up(client)

        response = client.post(
            reverse("account_email_verification_sent"),
            {"code": _code_from_last_email()},
            follow=True,
        )

        texts = [str(m) for m in response.context["messages"]]
        # "Code sent" and "signed in" repeat what the screen shows; "confirmed" does not.
        assert len(texts) == 1
        assert "founder@example.fr" in texts[0]

    def test_signup_wrong_code_is_rejected(self, client):
        _sign_up(client)

        response = client.post(
            reverse("account_email_verification_sent"), {"code": "WRONG1"}
        )

        assert response.status_code == 200
        assert response.context["verify_form"].errors["code"]
        assert not _signed_in(client)

    def test_signup_resend_after_cooldown_sends_a_new_code(self, client):
        with freeze_time("2026-11-18 10:00:00") as clock:
            _sign_up(client)
            clock.tick(timedelta(seconds=11))

            client.post(
                reverse("account_email_verification_sent"), {"action": "resend"}
            )

        assert len(mail.outbox) == 2

    def test_signup_resend_too_soon_shows_friendly_wait_page(self, client):
        _sign_up(client)
        code_page = reverse("account_email_verification_sent")

        response = client.post(code_page, {"action": "resend"})

        assert response.status_code == 429
        assert len(mail.outbox) == 1
        assert "429.html" in [t.name for t in response.templates]
        assert f'href="{code_page}"' in response.content.decode()

    def test_signup_nav_link_is_not_a_primary_button(self, client):
        response = client.get(reverse("home"))

        link = re.search(r'<a id="sign-up-link"[^>]*>', response.content.decode())
        assert link
        assert "bg-blue-600" not in link.group(0)


class TestLoginPage:
    def test_login_page_has_no_remember_me_and_no_placeholders(self, client):
        response = client.get(reverse("account_login"))

        content = response.content.decode()
        assert 'name="remember"' not in content
        assert "placeholder=" not in content

    def test_login_page_offers_sign_in_code(self, client):
        response = client.get(reverse("account_login"))

        assert reverse("account_request_login_code") in response.content.decode()

    @pytest.mark.parametrize(
        "url_name", ["account_reset_password", "account_request_login_code"]
    )
    def test_auth_pages_have_no_placeholders(self, client, url_name):
        response = client.get(reverse(url_name))

        assert "placeholder=" not in response.content.decode()


class TestLoginByCode:
    @pytest.fixture
    def verified_user(self):
        user = UserFactory(email="client@example.fr")
        EmailAddress.objects.create(
            user=user, email=user.email, primary=True, verified=True
        )
        return user

    def test_login_by_code_signs_in(self, client, verified_user):
        response = client.post(
            reverse("account_request_login_code"), {"email": verified_user.email}
        )
        assert response.status_code == 302

        response = client.post(
            reverse("account_confirm_login_code"), {"code": _code_from_last_email()}
        )

        assert response.status_code == 302
        assert _signed_in(client)

    def test_login_by_code_wrong_code_is_rejected(self, client, verified_user):
        client.post(
            reverse("account_request_login_code"), {"email": verified_user.email}
        )

        response = client.post(
            reverse("account_confirm_login_code"), {"code": "WRONG1"}
        )

        assert not _signed_in(client)
        assert response.status_code == 200
