"""Fixtures for every test, under apps/ and tests/ alike."""

import pytest
from django.utils import translation


@pytest.fixture(autouse=True)
def _reset_language():
    # A request in one test (e.g. a French user) leaves its language active on the
    # thread; later tests calling gettext directly must not inherit it.
    yield
    translation.deactivate()
