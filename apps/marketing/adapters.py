from typing import Protocol

import requests


class WaitlistProviderUnavailable(Exception):
    """Transient failure: worth retrying later."""


class WaitlistProvider(Protocol):
    def subscribe(self, email: str, list_id: int) -> None: ...


class BrevoWaitlistProvider:
    """Brevo double opt-in: the contact joins the list only after clicking the email link."""

    TIMEOUT_SECONDS = 10

    def __init__(
        self, *, api_key: str, api_url: str, template_id: int, redirect_url: str
    ) -> None:
        self._api_key = api_key
        self._api_url = api_url
        self._template_id = template_id
        self._redirect_url = redirect_url

    def subscribe(self, email: str, list_id: int) -> None:
        try:
            response = requests.post(
                f"{self._api_url}contacts/doubleOptinConfirmation",
                json={
                    "email": email,
                    "includeListIds": [list_id],
                    "templateId": self._template_id,
                    "redirectionUrl": self._redirect_url,
                },
                headers={"api-key": self._api_key, "accept": "application/json"},
                timeout=self.TIMEOUT_SECONDS,
            )
        except (requests.ConnectionError, requests.Timeout) as exc:
            raise WaitlistProviderUnavailable from exc
        if response.status_code >= 500:
            raise WaitlistProviderUnavailable(response.status_code)
        response.raise_for_status()
