from collections.abc import Callable, Mapping

from django.db import models, transaction
from django.utils.translation import gettext_lazy as _

from .adapters import WaitlistProvider


class WaitlistProduct(models.TextChoices):
    SAAS = "saas", _("The platform for French SMEs")
    BOILERPLATE = "boilerplate", _("The Django boilerplate")


class WaitlistClosedError(Exception):
    pass


class JoinWaitlist:
    def __init__(self, *, enabled: bool, enqueue: Callable[[str, str], None]) -> None:
        self._enabled = enabled
        self._enqueue = enqueue

    def __call__(self, email: str, product: WaitlistProduct) -> None:
        if not self._enabled:
            raise WaitlistClosedError
        normalised = email.strip().lower()
        transaction.on_commit(lambda: self._enqueue(normalised, product.value))


class SubscribeToWaitlist:
    def __init__(
        self,
        *,
        provider: WaitlistProvider,
        list_ids: Mapping[WaitlistProduct, int],
    ) -> None:
        self._provider = provider
        self._list_ids = list_ids

    def __call__(self, email: str, product: WaitlistProduct) -> None:
        list_id = self._list_ids.get(product)
        if not list_id:
            raise WaitlistClosedError(product)
        self._provider.subscribe(email, list_id)
