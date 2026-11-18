from typing import Any, cast

import pytest
from celery import shared_task
from django.db import connection
from django_tenants.utils import schema_context

from apps.core.tasks import TenantTask


@shared_task(base=TenantTask)
def current_schema() -> str:
    return str(cast(Any, connection).schema_name)  # untyped django-tenants wrapper


@pytest.fixture(autouse=True)
def _eager(settings):
    settings.CELERY_TASK_ALWAYS_EAGER = True
    settings.CELERY_TASK_EAGER_PROPAGATES = True


@pytest.mark.django_db
def test_tenant_task_runs_inside_the_given_schema():
    result = current_schema.delay(tenant_schema="public")

    assert result.get() == "public"


@pytest.mark.django_db
def test_tenant_task_restores_the_previous_schema_afterwards():
    with schema_context("public"):
        current_schema.delay(tenant_schema="public")

        assert cast(Any, connection).schema_name == "public"


def test_tenant_task_without_tenant_schema_is_refused():
    with pytest.raises(TypeError, match="tenant_schema"):
        current_schema.delay()
