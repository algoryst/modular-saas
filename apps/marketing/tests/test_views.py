from unittest.mock import Mock

import pytest
from django.core.cache import cache
from django.urls import reverse

from apps.marketing import views

# transaction.on_commit in the service needs a connection.
pytestmark = pytest.mark.django_db

VALID = {"email": "Dev@Example.com", "product": "boilerplate", "privacy": "on"}


@pytest.fixture(autouse=True)
def _clear_rate_limit_counters():
    cache.clear()


@pytest.fixture
def enqueue(monkeypatch) -> Mock:
    task = Mock()
    monkeypatch.setattr(views, "subscribe_to_waitlist", task)
    return task.delay


@pytest.fixture
def waitlist_open(settings):
    settings.WAITLIST_ENABLED = True


def test_landing_get_when_closed_hides_form(client, settings):
    settings.WAITLIST_ENABLED = False

    response = client.get(reverse("home"))

    assert response.status_code == 200
    assert b'name="email"' not in response.content


@pytest.mark.usefixtures("waitlist_open")
def test_landing_get_when_open_shows_form(client):
    response = client.get(reverse("home"))

    assert response.status_code == 200
    assert b'name="email"' in response.content


@pytest.mark.usefixtures("waitlist_open")
def test_landing_post_valid_enqueues_and_redirects(
    client, enqueue, django_capture_on_commit_callbacks
):
    with django_capture_on_commit_callbacks(execute=True):
        response = client.post(reverse("home"), VALID)

    assert response.status_code == 302
    assert response.url == reverse("home") + "?joined=1"
    enqueue.assert_called_once_with("dev@example.com", "boilerplate")


def test_landing_joined_shows_confirmation_and_no_form(client, waitlist_open):
    response = client.get(reverse("home") + "?joined=1")

    assert b'name="email"' not in response.content
    assert b'data-testid="waitlist-joined"' in response.content


def test_landing_post_when_closed_enqueues_nothing(client, settings, enqueue):
    settings.WAITLIST_ENABLED = False

    response = client.post(reverse("home"), VALID)

    assert response.status_code == 200
    assert b'name="email"' not in response.content
    enqueue.assert_not_called()


@pytest.mark.usefixtures("waitlist_open")
def test_landing_post_invalid_rerenders_with_errors(client, enqueue):
    response = client.post(reverse("home"), {**VALID, "email": "not-an-email"})

    assert response.status_code == 200
    assert response.context["form"].errors["email"]
    enqueue.assert_not_called()


@pytest.mark.usefixtures("waitlist_open")
def test_landing_post_honeypot_pretends_success_without_enqueue(client, enqueue):
    response = client.post(reverse("home"), {**VALID, "website": "x"})

    assert response.status_code == 302
    enqueue.assert_not_called()


@pytest.mark.usefixtures("waitlist_open")
def test_landing_post_over_rate_limit_shows_friendly_wait_page(
    client, settings, enqueue, django_capture_on_commit_callbacks
):
    settings.WAITLIST_RATE_LIMIT = "2/h"

    with django_capture_on_commit_callbacks(execute=True):
        responses = [client.post(reverse("home"), VALID) for _ in range(3)]

    assert [r.status_code for r in responses] == [302, 302, 429]
    assert "429.html" in [t.name for t in responses[-1].templates]
    assert enqueue.call_count == 2


@pytest.mark.parametrize("name", ["marketing:legal_notice", "marketing:privacy"])
def test_legal_pages_render(client, name):
    response = client.get(reverse(name))

    assert response.status_code == 200
