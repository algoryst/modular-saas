"""Reset by email link: one new-password field, and a clear way out of a dead link."""

from __future__ import annotations

import re

import pytest
from django.core import mail
from django.core.cache import cache
from django.urls import reverse

from apps.accounts.tests.factories import UserFactory

NEW_PASSWORD = "a-brand-new-passphrase-2026"

pytestmark = pytest.mark.django_db


@pytest.fixture(autouse=True)
def _clear_rate_limits():
    cache.clear()


def _open_reset_link(client, email: str):
    client.post(reverse("account_reset_password"), {"email": email})
    link = re.search(r"https?://\S+/password/reset/key/\S+", str(mail.outbox[-1].body))
    assert link, mail.outbox[-1].body
    # allauth swaps the key for a session token and redirects to the form.
    return client.get(link.group(0), follow=True)


def test_reset_form_asks_new_password_once(client):
    user = UserFactory.create()

    response = _open_reset_link(client, user.email)

    form = response.context["form"]
    assert list(form.fields) == ["password1"]
    assert "8" in str(form.fields["password1"].help_text)
    assert "placeholder=" not in response.content.decode()


def test_reset_with_single_password_changes_it(client):
    user = UserFactory.create()
    response = _open_reset_link(client, user.email)
    form_url = response.redirect_chain[-1][0]

    response = client.post(form_url, {"password1": NEW_PASSWORD})

    assert response.status_code == 302
    user.refresh_from_db()
    assert user.check_password(NEW_PASSWORD)


def test_reset_rejects_weak_password(client):
    user = UserFactory.create()
    response = _open_reset_link(client, user.email)
    form_url = response.redirect_chain[-1][0]

    response = client.post(form_url, {"password1": "12345678"})

    assert response.status_code == 200
    assert response.context["form"].errors["password1"]


def test_reset_dead_link_explains_and_offers_new_link(client):
    response = client.get(
        reverse(
            "account_reset_password_from_key", kwargs={"uidb36": "0", "key": "dead-key"}
        )
    )

    content = response.content.decode()
    assert "Bad Token" not in content
    assert f'href="{reverse("account_reset_password")}"' in content
    assert 'name="password1"' not in content
