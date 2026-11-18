from dataclasses import dataclass
from datetime import UTC, datetime

import pytest

from apps.core.events import Event, EventBus

NOON = datetime(2026, 11, 18, 12, 0, tzinfo=UTC)

pytestmark = pytest.mark.django_db


@dataclass(frozen=True, kw_only=True)
class ThingHappened(Event):
    name: str


@dataclass(frozen=True, kw_only=True)
class OtherThingHappened(Event):
    pass


@pytest.fixture
def bus() -> EventBus:
    return EventBus()


def test_publish_runs_handlers_after_commit(bus, django_capture_on_commit_callbacks):
    received: list[Event] = []
    bus.subscribe(ThingHappened, received.append)
    event = ThingHappened(occurred_at=NOON, name="a")

    with django_capture_on_commit_callbacks() as callbacks:
        bus.publish(event)
        assert received == []  # nothing runs before the transaction commits

    for callback in callbacks:
        callback()
    assert received == [event]


def test_publish_rolled_back_runs_no_handlers(bus):
    from django.db import transaction

    received: list[Event] = []
    bus.subscribe(ThingHappened, received.append)

    with pytest.raises(RuntimeError), transaction.atomic():
        bus.publish(ThingHappened(occurred_at=NOON, name="a"))
        raise RuntimeError

    assert received == []


def test_publish_only_reaches_handlers_of_that_event_type(
    bus, django_capture_on_commit_callbacks
):
    received: list[Event] = []
    bus.subscribe(OtherThingHappened, received.append)

    with django_capture_on_commit_callbacks(execute=True):
        bus.publish(ThingHappened(occurred_at=NOON, name="a"))

    assert received == []


def test_failing_handler_does_not_stop_the_others(
    bus, django_capture_on_commit_callbacks, caplog
):
    received: list[Event] = []

    def broken(event: ThingHappened) -> None:
        raise ValueError("boom")

    bus.subscribe(ThingHappened, broken)
    bus.subscribe(ThingHappened, received.append)
    event = ThingHappened(occurred_at=NOON, name="a")

    with django_capture_on_commit_callbacks(execute=True):
        bus.publish(event)

    assert received == [event]
    assert "broken" in caplog.text  # the log names the failing handler


def test_subscribe_same_handler_twice_registers_once(
    bus, django_capture_on_commit_callbacks
):
    received: list[Event] = []
    bus.subscribe(ThingHappened, received.append)
    bus.subscribe(ThingHappened, received.append)

    with django_capture_on_commit_callbacks(execute=True):
        bus.publish(ThingHappened(occurred_at=NOON, name="a"))

    assert len(received) == 1


def test_subscriber_decorator_registers_and_returns_handler(
    bus, django_capture_on_commit_callbacks
):
    received: list[str] = []

    @bus.subscriber(ThingHappened)
    def on_thing(event: ThingHappened) -> None:
        received.append(event.name)

    with django_capture_on_commit_callbacks(execute=True):
        bus.publish(ThingHappened(occurred_at=NOON, name="decorated"))

    assert received == ["decorated"]
    assert callable(on_thing)


def test_events_are_immutable():
    event = ThingHappened(occurred_at=NOON, name="a")

    with pytest.raises(AttributeError):
        event.name = "b"  # type: ignore[misc]  # the point of the test
