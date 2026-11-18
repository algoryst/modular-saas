from datetime import UTC, datetime, timedelta

import pytest
from freezegun import freeze_time

from apps.core.clock import FixedClock, SystemClock

NOON = datetime(2026, 11, 18, 12, 0, tzinfo=UTC)


def test_system_clock_returns_aware_current_time():
    with freeze_time(NOON):
        now = SystemClock().now()

    assert now == NOON
    assert now.tzinfo is not None


def test_fixed_clock_returns_its_time_until_advanced():
    clock = FixedClock(NOON)

    assert clock.now() == NOON
    clock.advance(timedelta(minutes=5))
    assert clock.now() == NOON + timedelta(minutes=5)


def test_fixed_clock_naive_datetime_raises():
    with pytest.raises(ValueError):
        FixedClock(datetime(2026, 11, 18, 12, 0))  # naive on purpose
