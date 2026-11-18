"""Fixtures for every test, under apps/ and tests/ alike."""

import importlib
from typing import Any, cast

import pytest
from django.db import connection
from django.utils import translation


@pytest.fixture(autouse=True)
def _reset_schema():
    # Like the language: a test that enters a workspace schema must not leave the
    # next test in it. TenantTestCase classes re-enter their schema in setUp.
    # set_schema_to_public() only resets connection attributes; no query runs.
    yield
    # cast: django-tenants' connection wrapper ships no type hints.
    cast(Any, connection).set_schema_to_public()


@pytest.fixture(autouse=True)
def _reset_language():
    # A request in one test (e.g. a French user) leaves its language active on the
    # thread; later tests calling gettext directly must not inherit it.
    yield
    translation.deactivate()


@pytest.fixture
def public_urls(settings):
    """reverse() for root-domain-only pages (admin, signup).

    Outside a request, reverse() uses ROOT_URLCONF, which serves workspace hosts.
    """
    settings.ROOT_URLCONF = settings.PUBLIC_SCHEMA_URLCONF


@pytest.fixture(scope="session")
def django_db_setup(django_db_setup, django_db_blocker):
    """Recreate the rows data migrations seed (public tenant, Site), once per run.

    Transactional tests flush every table when they finish; with --reuse-db the next
    run would start without them, since migrations do not run again.
    """
    from django.apps import apps
    from django.conf import settings
    from django.contrib.sites.models import Site

    seed = importlib.import_module("apps.tenants.migrations.0002_create_public_tenant")
    with django_db_blocker.unblock():
        seed.create_public_tenant(apps, None)
        Site.objects.update_or_create(
            id=settings.SITE_ID,
            defaults={"domain": settings.SITE_DOMAIN, "name": "Modular SaaS"},
        )
