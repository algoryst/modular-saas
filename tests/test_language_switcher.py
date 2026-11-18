import re

import pytest
from django.conf import settings
from django.urls import reverse

# The landing page heading, in each language.
EN_HEADING = "Run your small business from one simple workspace"
FR_HEADING = "Pilotez votre petite entreprise depuis un seul espace simple"

pytestmark = pytest.mark.django_db


def test_language_default_without_preference_is_english(client):
    response = client.get(reverse("home"))

    assert EN_HEADING in response.content.decode()


def test_language_french_browser_gets_french_without_choosing(client):
    response = client.get(reverse("home"), HTTP_ACCEPT_LANGUAGE="fr-FR,fr;q=0.9")

    assert FR_HEADING in response.content.decode()


def test_language_unsupported_browser_language_falls_back_to_english(client):
    response = client.get(reverse("home"), HTTP_ACCEPT_LANGUAGE="de-DE,de;q=0.9")

    assert EN_HEADING in response.content.decode()


def test_set_language_french_sets_cookie_and_redirects_back(client):
    response = client.post(
        reverse("set_language"), {"language": "fr", "next": "/about/"}
    )

    assert response.status_code == 302
    assert response.url == "/about/"
    assert response.cookies[settings.LANGUAGE_COOKIE_NAME].value == "fr"


def test_set_language_choice_overrides_browser_language(client):
    client.post(reverse("set_language"), {"language": "en", "next": "/"})

    response = client.get(reverse("home"), HTTP_ACCEPT_LANGUAGE="fr-FR")

    assert EN_HEADING in response.content.decode()


def test_set_language_unsupported_code_still_renders_english(client):
    # set_language accepts any code Django has a catalogue for; LocaleMiddleware
    # then ignores codes outside LANGUAGES.
    client.post(reverse("set_language"), {"language": "de", "next": "/"})

    response = client.get(reverse("home"))

    assert EN_HEADING in response.content.decode()


def test_set_language_external_next_is_not_followed(client):
    response = client.post(
        reverse("set_language"),
        {"language": "fr", "next": "https://evil.example/"},
    )

    assert "evil.example" not in response.url


def test_language_switcher_in_nav_marks_current_language(client):
    response = client.get(reverse("home"), HTTP_ACCEPT_LANGUAGE="fr")

    content = response.content.decode()
    current = re.findall(r'<button[^>]*aria-current="true"[^>]*>', content)
    assert f'action="{reverse("set_language")}"' in content
    assert len(current) == 1
    assert 'value="fr"' in current[0]
    assert "Français" in content and "English" in content
