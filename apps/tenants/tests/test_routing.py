"""The host decides the schema and the URLconf: root domain vs workspace."""

import pytest
from django.contrib.auth import get_user_model
from django_tenants.test.cases import TenantTestCase
from django_tenants.test.client import TenantClient

ACME_DOMAIN = "acme.localhost"


class AcmeTenantTestCase(TenantTestCase):
    """A real "acme" workspace schema, created per class and dropped afterwards."""

    @classmethod
    def get_test_schema_name(cls) -> str:
        return "ws_acme"

    @classmethod
    def get_test_tenant_domain(cls) -> str:
        return ACME_DOMAIN

    @classmethod
    def setup_tenant(cls, tenant) -> None:
        tenant.name = "Acme"
        tenant.timezone = "Europe/Paris"
        tenant.currency = "EUR"
        tenant.tax_country = "fr"
        tenant.tax_id_type = "siret"
        tenant.tax_id = "73282932000074"


class TestWorkspaceHost(AcmeTenantTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.client = TenantClient(self.tenant)

    def test_workspace_home_asks_anonymous_visitors_to_sign_in(self):
        response = self.client.get("/")

        assert response.status_code == 302
        assert "/accounts/login/" in response.url

    def test_workspace_home_greets_signed_in_user_with_workspace_name(self):
        # get_user_model, not the accounts factory: feature apps stay independent.
        self.client.force_login(
            get_user_model().objects.create_user(email="owner@acme.example")
        )

        response = self.client.get("/")

        assert response.status_code == 200
        assert "Welcome to Acme" in response.content.decode()

    def test_workspace_host_does_not_serve_the_admin(self):
        response = self.client.get("/admin/")

        assert response.status_code == 404


@pytest.mark.django_db
def test_root_domain_serves_the_marketing_site(client):
    response = client.get("/")

    assert response.status_code == 200
    assert "marketing/landing.html" in [t.name for t in response.templates]
