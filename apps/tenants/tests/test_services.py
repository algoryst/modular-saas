"""Creating a workspace: schema, domain, owner membership, event, all or nothing."""

from datetime import UTC, datetime

import pytest
from django.contrib.auth import get_user_model
from django.db import connection

from apps.core.clock import FixedClock
from apps.core.events import EventBus, WorkspaceCreated
from apps.tenants.models import Domain, Membership, Tenant
from apps.tenants.repositories import TenantRepository
from apps.tenants.services import (
    CreateTenant,
    InvalidTaxIdentityError,
    NewWorkspace,
    TaxIdentityTakenError,
)

NOON = datetime(2026, 11, 18, 12, 0, tzinfo=UTC)
ACME = NewWorkspace(
    name="Acme Conseil", country="fr", tax_id_type="siret", tax_id="732 829 320 00074"
)

pytestmark = pytest.mark.django_db


@pytest.fixture
def owner():
    # get_user_model, not the accounts factory: feature apps stay independent.
    return get_user_model().objects.create_user(email="owner@acme.example")


@pytest.fixture
def bus() -> EventBus:
    return EventBus()


def create_tenant(bus: EventBus, *, unique_tax_id: bool = True) -> CreateTenant:
    return CreateTenant(
        tenants=TenantRepository(),
        root_domain="localhost",
        unique_tax_id=unique_tax_id,
        events=bus,
        clock=FixedClock(NOON),
    )


def schema_exists(name: str) -> bool:
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT 1 FROM information_schema.schemata WHERE schema_name = %s", [name]
        )
        return cursor.fetchone() is not None


class TestCreateTenant:
    def test_creates_schema_domain_and_owner_membership(self, owner, bus):
        tenant = create_tenant(bus)(owner, ACME)

        assert tenant.schema_name == "ws_acme_conseil"
        assert schema_exists("ws_acme_conseil")
        assert Domain.objects.get(tenant=tenant).domain == "acme-conseil.localhost"
        assert Membership.objects.get(tenant=tenant, user=owner).role == "owner"

    def test_uses_country_pack_defaults_and_normalized_identifier(self, owner, bus):
        tenant = create_tenant(bus)(owner, ACME)

        assert (tenant.timezone, tenant.currency) == ("Europe/Paris", "EUR")
        assert tenant.tax_id == "73282932000074"

    def test_publishes_workspace_created_after_commit(
        self, owner, bus, django_capture_on_commit_callbacks
    ):
        received: list[WorkspaceCreated] = []
        bus.subscribe(WorkspaceCreated, received.append)

        with django_capture_on_commit_callbacks(execute=True):
            tenant = create_tenant(bus)(owner, ACME)

        assert received == [
            WorkspaceCreated(
                occurred_at=NOON, tenant_schema=tenant.schema_name, owner_id=owner.pk
            )
        ]

    def test_same_name_gets_a_distinct_address(self, owner, bus):
        first = create_tenant(bus, unique_tax_id=False)(owner, ACME)
        second = create_tenant(bus, unique_tax_id=False)(owner, ACME)

        assert first.schema_name != second.schema_name
        assert Domain.objects.get(tenant=second).domain == "acme-conseil-2.localhost"

    @pytest.mark.parametrize("name", ["Admin", "www", "API", "Public"])
    def test_reserved_names_never_become_addresses(self, owner, bus, name):
        workspace = NewWorkspace(name=name, **_identity())

        tenant = create_tenant(bus)(owner, workspace)

        domain = Domain.objects.get(tenant=tenant).domain
        assert domain.split(".")[0] not in {"admin", "www", "api", "public"}

    def test_name_without_letters_still_gets_an_address(self, owner, bus):
        tenant = create_tenant(bus)(owner, NewWorkspace(name="!!!", **_identity()))

        assert Domain.objects.get(tenant=tenant).domain == "workspace.localhost"

    def test_taken_tax_identity_is_refused_and_nothing_is_created(self, owner, bus):
        create_tenant(bus)(owner, ACME)
        before = Tenant.objects.count()

        with pytest.raises(TaxIdentityTakenError):
            create_tenant(bus)(owner, NewWorkspace(name="Other", **_identity()))

        assert Tenant.objects.count() == before
        assert not schema_exists("ws_other")

    def test_taken_tax_identity_allowed_when_uniqueness_is_off(self, owner, bus):
        create_tenant(bus, unique_tax_id=False)(owner, ACME)

        tenant = create_tenant(bus, unique_tax_id=False)(owner, ACME)

        assert tenant.pk

    def test_invalid_tax_identity_is_refused(self, owner, bus):
        bad = NewWorkspace(name="Bad", country="fr", tax_id_type="siret", tax_id="123")

        with pytest.raises(InvalidTaxIdentityError):
            create_tenant(bus)(owner, bad)

        assert not schema_exists("ws_bad")


def _identity() -> dict[str, str]:
    return {"country": "fr", "tax_id_type": "siret", "tax_id": "73282932000074"}
