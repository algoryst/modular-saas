"""In-process event bus: the only way feature apps affect each other.

Event classes live here, in core, because a subscriber in one app cannot import
another app's modules. Handlers run after the publishing transaction commits, so a
rolled-back change emits nothing; they must stay quick and hand slow work to Celery.
Each app subscribes in its handlers.py, imported from AppConfig.ready().
"""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from django.db import transaction


@dataclass(frozen=True, kw_only=True)
class Event:
    occurred_at: datetime
    # The workspace concerned. Handlers pass it on to any Celery task they enqueue
    # (TenantTask), which re-enters that schema itself.
    tenant_schema: str


@dataclass(frozen=True, kw_only=True)
class WorkspaceCreated(Event):
    owner_id: int


type Handler[E: Event] = Callable[[E], None]


class EventBus:
    def __init__(self) -> None:
        self._handlers: defaultdict[type[Event], list[Handler[Any]]] = defaultdict(list)

    def subscribe[E: Event](self, event_type: type[E], handler: Handler[E]) -> None:
        # ready() can run more than once (tests, reloads); never double-register.
        if handler not in self._handlers[event_type]:
            self._handlers[event_type].append(handler)

    def subscriber[E: Event](
        self, event_type: type[E]
    ) -> Callable[[Handler[E]], Handler[E]]:
        def register(handler: Handler[E]) -> Handler[E]:
            self.subscribe(event_type, handler)
            return handler

        return register

    def publish(self, event: Event) -> None:
        for handler in self._handlers[type(event)]:
            # robust: a failing handler is logged and the others still run.
            transaction.on_commit(_bind(handler, event), robust=True)


def _bind[E: Event](handler: Handler[E], event: E) -> Callable[[], None]:
    def deliver() -> None:
        handler(event)

    # Django's robust on_commit logs the callback's __qualname__ when it fails.
    deliver.__qualname__ = getattr(handler, "__qualname__", repr(handler))
    return deliver


bus = EventBus()
subscriber = bus.subscriber
