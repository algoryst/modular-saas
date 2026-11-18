from django.db import connection

from apps.tenants.models import Domain, Membership, Tenant


class TenantRepository:
    def lock_tax_identity(self, country: str, type_code: str, value: str) -> None:
        """Serialise signups for one identifier until the transaction ends."""
        key = f"tax-identity:{country}:{type_code}:{value}"
        with connection.cursor() as cursor:
            cursor.execute("SELECT pg_advisory_xact_lock(hashtext(%s))", [key])

    def tax_identity_taken(self, country: str, type_code: str, value: str) -> bool:
        return Tenant.objects.filter(
            tax_country=country, tax_id_type=type_code, tax_id=value
        ).exists()

    def address_taken(self, schema_name: str, domain: str) -> bool:
        return (
            Tenant.objects.filter(schema_name=schema_name).exists()
            or Domain.objects.filter(domain=domain).exists()
        )

    def create(self, tenant: Tenant) -> Tenant:
        # TenantMixin.save() creates the schema and runs tenant migrations.
        tenant.save()
        return tenant

    def add_domain(self, tenant: Tenant, domain: str) -> Domain:
        return Domain.objects.create(tenant=tenant, domain=domain, is_primary=True)

    def add_membership(self, user_id: int, tenant: Tenant, role: str) -> Membership:
        return Membership.objects.create(user_id=user_id, tenant=tenant, role=role)

    def is_member(self, user_id: int, tenant_id: int) -> bool:
        return Membership.objects.filter(user_id=user_id, tenant_id=tenant_id).exists()
