"""Workspace A can never read or write workspace B: access, data, cache."""

from datetime import UTC, datetime
from typing import ClassVar

import pytest
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.db import connection, models
from django_tenants.utils import schema_context

from apps.core.clock import FixedClock
from apps.core.events import EventBus
from apps.tenants.repositories import TenantRepository
from apps.tenants.services import CreateTenant, NewWorkspace

pytestmark = pytest.mark.django_db


class Note(models.Model):
    """Stands in for business data until the first tenant app exists."""

    text = models.CharField(max_length=50)

    # Explicit manager: the stubs plugin only knows models from INSTALLED_APPS.
    objects: ClassVar[models.Manager["Note"]] = models.Manager()

    class Meta:
        app_label = "tenants"
        managed = False


def make_workspace(name: str, siret: str, owner):
    return CreateTenant(
        tenants=TenantRepository(),
        root_domain="localhost",
        unique_tax_id=True,
        events=EventBus(),
        clock=FixedClock(datetime(2026, 11, 18, tzinfo=UTC)),
    )(owner, NewWorkspace(name=name, country="fr", tax_id_type="siret", tax_id=siret))


@pytest.fixture
def alice():
    # get_user_model, not the accounts factory: feature apps stay independent.
    return get_user_model().objects.create_user(email="alice@acme.example")


@pytest.fixture
def bob():
    return get_user_model().objects.create_user(email="bob@globex.example")


@pytest.fixture
def acme(alice):
    return make_workspace("Acme", "73282932000074", alice)


@pytest.fixture
def globex(bob):
    return make_workspace("Globex", "55203253400646", bob)


class TestAccess:
    def test_member_can_open_their_workspace(self, client, alice, acme):
        client.force_login(alice)

        response = client.get("/", HTTP_HOST="acme.localhost")

        assert response.status_code == 200

    def test_signed_in_non_member_is_refused_with_a_way_out(
        self, client, bob, acme, globex
    ):
        client.force_login(bob)

        response = client.get("/", HTTP_HOST="acme.localhost")

        assert response.status_code == 403
        assert "tenants/no_access.html" in [t.name for t in response.templates]

    def test_non_member_is_refused_on_every_workspace_page(self, client, bob, acme):
        client.force_login(bob)

        response = client.get("/users/~update/", HTTP_HOST="acme.localhost")

        assert response.status_code == 403

    def test_anonymous_visitor_is_sent_to_sign_in(self, client, acme):
        response = client.get("/", HTTP_HOST="acme.localhost")

        assert response.status_code == 302
        assert "/accounts/login/" in response.url

    def test_root_domain_needs_no_membership(self, client, bob):
        client.force_login(bob)

        response = client.get("/")

        assert response.status_code == 200


class TestData:
    def test_rows_written_in_one_workspace_are_invisible_in_another(self, acme, globex):
        for tenant in (acme, globex):
            with schema_context(tenant.schema_name), connection.schema_editor() as e:
                e.create_model(Note)
        with schema_context(acme.schema_name):
            Note.objects.create(text="acme secret")

        with schema_context(globex.schema_name):
            assert not Note.objects.exists()
        with schema_context(acme.schema_name):
            assert Note.objects.get().text == "acme secret"


class TestCache:
    def test_cache_entries_do_not_cross_workspaces(self, acme, globex):
        with schema_context(acme.schema_name):
            cache.set("dashboard", "acme numbers")

        with schema_context(globex.schema_name):
            assert cache.get("dashboard") is None
        with schema_context(acme.schema_name):
            assert cache.get("dashboard") == "acme numbers"
