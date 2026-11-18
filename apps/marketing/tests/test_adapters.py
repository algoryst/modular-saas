from unittest.mock import Mock

import pytest
import requests

from apps.marketing.adapters import BrevoWaitlistProvider, WaitlistProviderUnavailable


def _provider() -> BrevoWaitlistProvider:
    return BrevoWaitlistProvider(
        api_key="test-key",
        api_url="https://api.brevo.test/v3/",
        template_id=7,
        redirect_url="https://example.test/?confirmed=1",
    )


def _response(status: int) -> requests.Response:
    response = requests.Response()
    response.status_code = status
    return response


def test_brevo_subscribe_posts_double_opt_in_request(monkeypatch):
    post = Mock(return_value=_response(204))
    monkeypatch.setattr(requests, "post", post)

    _provider().subscribe("dev@example.com", 22)

    post.assert_called_once()
    url = post.call_args.args[0]
    kwargs = post.call_args.kwargs
    assert url == "https://api.brevo.test/v3/contacts/doubleOptinConfirmation"
    assert kwargs["headers"]["api-key"] == "test-key"
    assert kwargs["json"] == {
        "email": "dev@example.com",
        "includeListIds": [22],
        "templateId": 7,
        "redirectionUrl": "https://example.test/?confirmed=1",
    }
    assert kwargs["timeout"] > 0


def test_brevo_subscribe_server_error_raises_unavailable(monkeypatch):
    monkeypatch.setattr(requests, "post", Mock(return_value=_response(503)))

    with pytest.raises(WaitlistProviderUnavailable):
        _provider().subscribe("dev@example.com", 22)


def test_brevo_subscribe_connection_error_raises_unavailable(monkeypatch):
    monkeypatch.setattr(
        requests, "post", Mock(side_effect=requests.ConnectionError("down"))
    )

    with pytest.raises(WaitlistProviderUnavailable):
        _provider().subscribe("dev@example.com", 22)


def test_brevo_subscribe_client_error_raises_http_error(monkeypatch):
    monkeypatch.setattr(requests, "post", Mock(return_value=_response(400)))

    with pytest.raises(requests.HTTPError):
        _provider().subscribe("dev@example.com", 22)
