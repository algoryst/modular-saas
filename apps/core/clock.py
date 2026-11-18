"""Time source for services: inject a Clock instead of calling datetime.now()."""

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Protocol

from django.utils import timezone


class Clock(Protocol):
    def now(self) -> datetime: ...


class SystemClock:
    def now(self) -> datetime:
        return timezone.now()


@dataclass
class FixedClock:
    """Deterministic clock for tests."""

    at: datetime

    def __post_init__(self) -> None:
        if timezone.is_naive(self.at):
            raise ValueError("FixedClock needs a timezone-aware datetime")

    def now(self) -> datetime:
        return self.at

    def advance(self, delta: timedelta) -> None:
        self.at += delta
