from unittest.mock import Mock

import pytest
import requests

from apps.marketing import tasks
from apps.marketing.adapters import WaitlistProviderUnavailable
from apps.marketing.tests.fakes import InMemoryWaitlistProvider


@pytest.fixture
def waitlist_settings(settings):
    settings.BREVO_WAITLIST_LIST_SAAS = 11
    settings.BREVO_WAITLIST_LIST_BOILERPLATE = 22
    settings.BREVO_API_KEY = "test-key"
    settings.BREVO_DOI_TEMPLATE_ID = 7
    settings.WAITLIST_CONFIRMED_URL = "https://example.test/?confirmed=1"
    settings.CELERY_TASK_ALWAYS_EAGER = True


@pytest.mark.usefixtures("waitlist_settings")
def test_subscribe_task_subscribes_to_product_list(monkeypatch):
    provider = InMemoryWaitlistProvider()
    monkeypatch.setattr(tasks, "_provider", lambda: provider)

    tasks.subscribe_to_waitlist.delay("dev@example.com", "boilerplate")

    assert provider.subscriptions == [("dev@example.com", 22)]


@pytest.mark.usefixtures("waitlist_settings")
def test_subscribe_task_provider_built_from_settings(monkeypatch):
    response = requests.Response()
    response.status_code = 204
    post = Mock(return_value=response)
    monkeypatch.setattr(requests, "post", post)

    tasks.subscribe_to_waitlist.delay("dev@example.com", "saas")

    assert post.call_args.kwargs["json"]["includeListIds"] == [11]
    assert post.call_args.kwargs["headers"]["api-key"] == "test-key"


def test_subscribe_task_retries_when_provider_unavailable():
    assert WaitlistProviderUnavailable in tasks.subscribe_to_waitlist.autoretry_for
    assert requests.HTTPError not in tasks.subscribe_to_waitlist.autoretry_for
