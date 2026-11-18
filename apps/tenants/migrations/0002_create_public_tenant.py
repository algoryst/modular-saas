"""The public tenant: the root domain (marketing site, signup, admin).

TenantMainMiddleware falls back to it for unknown hosts, so it must exist.
"""

from django.conf import settings
from django.db import migrations

PUBLIC_SCHEMA = "public"


def create_public_tenant(apps, schema_editor):
    Tenant = apps.get_model("tenants", "Tenant")
    Domain = apps.get_model("tenants", "Domain")
    # Historical models skip TenantMixin.save(): no schema is created (public exists).
    tenant, _ = Tenant.objects.get_or_create(
        schema_name=PUBLIC_SCHEMA,
        defaults={
            "name": "Modular SaaS",
            "timezone": settings.TIME_ZONE,
            "currency": "EUR",
        },
    )
    host = settings.SITE_DOMAIN.split(":")[0]
    Domain.objects.get_or_create(
        domain=host, defaults={"tenant": tenant, "is_primary": True}
    )


def delete_public_tenant(apps, schema_editor):
    Tenant = apps.get_model("tenants", "Tenant")
    Tenant.objects.filter(schema_name=PUBLIC_SCHEMA).delete()


class Migration(migrations.Migration):
    dependencies = [("tenants", "0001_initial")]

    operations = [migrations.RunPython(create_public_tenant, delete_public_tenant)]
