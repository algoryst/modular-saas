import pytest

from apps.marketing.services import (
    JoinWaitlist,
    SubscribeToWaitlist,
    WaitlistClosedError,
    WaitlistProduct,
)
from apps.marketing.tests.fakes import InMemoryWaitlistProvider

LIST_IDS = {WaitlistProduct.SAAS: 11, WaitlistProduct.BOILERPLATE: 22}


class TestJoinWaitlist:
    @pytest.mark.django_db
    def test_join_waitlist_when_open_enqueues_normalised_email(
        self, django_capture_on_commit_callbacks
    ):
        enqueued: list[tuple[str, str]] = []
        join = JoinWaitlist(enabled=True, enqueue=lambda e, p: enqueued.append((e, p)))

        with django_capture_on_commit_callbacks(execute=True):
            join("  Founder@Example.FR ", WaitlistProduct.SAAS)

        assert enqueued == [("founder@example.fr", "saas")]

    def test_join_waitlist_when_closed_raises_and_enqueues_nothing(self):
        enqueued: list[tuple[str, str]] = []
        join = JoinWaitlist(enabled=False, enqueue=lambda e, p: enqueued.append((e, p)))

        with pytest.raises(WaitlistClosedError):
            join("founder@example.fr", WaitlistProduct.SAAS)

        assert enqueued == []


class TestSubscribeToWaitlist:
    @pytest.mark.parametrize(
        ("product", "list_id"),
        [(WaitlistProduct.SAAS, 11), (WaitlistProduct.BOILERPLATE, 22)],
    )
    def test_subscribe_to_waitlist_uses_the_product_list(self, product, list_id):
        provider = InMemoryWaitlistProvider()

        SubscribeToWaitlist(provider=provider, list_ids=LIST_IDS)(
            "dev@example.com", product
        )

        assert provider.subscriptions == [("dev@example.com", list_id)]

    def test_subscribe_to_waitlist_without_configured_list_raises(self):
        provider = InMemoryWaitlistProvider()
        subscribe = SubscribeToWaitlist(
            provider=provider, list_ids={WaitlistProduct.SAAS: 11}
        )

        with pytest.raises(WaitlistClosedError):
            subscribe("dev@example.com", WaitlistProduct.BOILERPLATE)

        assert provider.subscriptions == []
