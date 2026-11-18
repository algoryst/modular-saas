import pytest
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import IntegrityError

from apps.tenants.models import Domain, Membership, Tenant

pytestmark = pytest.mark.django_db


def test_public_tenant_exists_with_the_site_domain(settings):
    public = Tenant.objects.get(schema_name="public")

    assert Domain.objects.filter(
        tenant=public, domain=settings.SITE_DOMAIN.split(":")[0], is_primary=True
    ).exists()


def test_tenant_clean_validates_the_tax_identity():
    tenant = Tenant(
        schema_name="ws_acme",
        name="Acme",
        timezone="Europe/Paris",
        currency="EUR",
        tax_country="FR",
        tax_id_type="siret",
        tax_id="73282932000075",  # bad checksum
    )

    with pytest.raises(ValidationError) as excinfo:
        tenant.clean()

    assert "tax_id" in excinfo.value.message_dict


def test_membership_is_unique_per_user_and_workspace(user):
    public = Tenant.objects.get(schema_name="public")
    Membership.objects.create(user=user, tenant=public, role=Membership.Role.OWNER)

    with pytest.raises(IntegrityError):
        Membership.objects.create(user=user, tenant=public, role=Membership.Role.MEMBER)


def test_tenant_and_membership_read_well():
    public = Tenant.objects.get(schema_name="public")
    membership = Membership(
        user=get_user_model()(email="a@example.fr"),
        tenant=public,
        role=Membership.Role.ADMIN,
    )

    assert str(public) == public.name
    assert str(membership) == f"a@example.fr @ {public.name} (admin)"
