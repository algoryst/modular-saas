"""The language a signed-in user picks is kept on their account."""

from __future__ import annotations

import pytest
from django.conf import settings
from django.core.cache import cache
from django.urls import reverse

from apps.accounts.models import User
from apps.accounts.repositories import UserRepository
from apps.accounts.services import SetPreferredLanguage
from apps.accounts.tests.factories import UserFactory

EN_HEADING = "Run your small business from one simple workspace"
FR_HEADING = "Pilotez votre petite entreprise depuis un seul espace simple"

pytestmark = pytest.mark.django_db


@pytest.fixture(autouse=True)
def _clear_rate_limits():
    cache.clear()


class TestSetPreferredLanguage:
    def test_set_preferred_language_saves_supported_code(self):
        user = UserFactory.create()

        SetPreferredLanguage(users=UserRepository())(user, "fr")

        user.refresh_from_db()
        assert user.language == "fr"

    @pytest.mark.parametrize("code", ["de", "", "fr-xx-bad", "FR"])
    def test_set_preferred_language_ignores_unsupported_code(self, code):
        user = UserFactory.create(language="en")

        SetPreferredLanguage(users=UserRepository())(user, code)

        user.refresh_from_db()
        assert user.language == "en"


class TestSwitcherForSignedInUsers:
    def test_switcher_saves_choice_on_account(self, client):
        user = UserFactory.create()
        client.force_login(user)

        response = client.post(
            reverse("set_language"), {"language": "fr", "next": "/about/"}
        )

        user.refresh_from_db()
        assert user.language == "fr"
        assert response.status_code == 302
        assert response.url == "/about/"
        assert response.cookies[settings.LANGUAGE_COOKIE_NAME].value == "fr"

    def test_switcher_for_anonymous_visitor_sets_cookie_only(self, client):
        response = client.post(reverse("set_language"), {"language": "fr", "next": "/"})

        assert response.cookies[settings.LANGUAGE_COOKIE_NAME].value == "fr"
        assert not User.objects.filter(language="fr").exists()


class TestAccountLanguageWins:
    def test_account_language_beats_cookie_and_browser(self, client):
        client.force_login(UserFactory.create(language="fr"))
        client.cookies[settings.LANGUAGE_COOKIE_NAME] = "en"

        response = client.get(reverse("home"), HTTP_ACCEPT_LANGUAGE="en")

        assert FR_HEADING in response.content.decode()
        assert response["Content-Language"] == "fr"

    def test_account_without_language_falls_back_to_browser(self, client):
        client.force_login(UserFactory.create(language=""))

        response = client.get(reverse("home"), HTTP_ACCEPT_LANGUAGE="fr")

        assert FR_HEADING in response.content.decode()

    def test_anonymous_visitor_unaffected(self, client):
        response = client.get(reverse("home"))

        assert EN_HEADING in response.content.decode()


class TestSignupRemembersLanguage:
    def test_signup_stores_the_language_being_viewed(self, client, settings):
        settings.ACCOUNT_ALLOW_REGISTRATION = True
        client.post(
            reverse("tenants:signup"), {"country": "fr", "tax_id": "73282932000074"}
        )

        client.post(
            reverse("account_signup"),
            {
                "company_name": "Acme",
                "email": "nouveau@example.fr",
                "password1": "correct-horse-battery-42",
            },
            HTTP_ACCEPT_LANGUAGE="fr",
        )

        assert User.objects.get(email="nouveau@example.fr").language == "fr"
