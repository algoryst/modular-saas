"""Celery base task for workspace work: the caller names the schema, the task enters it.

Workers have no request, so nothing else sets the tenant. Use it for every task that
touches tenant data:

    @shared_task(base=TenantTask)
    def send_quote(quote_id: int) -> None: ...

    send_quote.delay(quote_id, tenant_schema=event.tenant_schema)
"""

from typing import Any

from celery import Task
from django_tenants.utils import schema_context


class TenantTask(Task):  # type: ignore[misc]  # celery ships no type hints
    # Celery checks call arguments against run()'s signature; tenant_schema is ours.
    typing = False

    def __call__(self, *args: Any, **kwargs: Any) -> Any:
        if "tenant_schema" not in kwargs:
            raise TypeError(f"{self.name} needs tenant_schema=<schema name>")
        tenant_schema = kwargs.pop("tenant_schema")
        with schema_context(tenant_schema):
            return super().__call__(*args, **kwargs)
