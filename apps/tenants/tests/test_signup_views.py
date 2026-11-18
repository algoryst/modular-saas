"""Signup end to end: company, account, email code, workspace, handoff."""

from __future__ import annotations

import re
from datetime import UTC, datetime
from typing import Any
from unittest.mock import Mock
from urllib.parse import urlparse

import pytest
import requests
from django.contrib.auth import get_user_model
from django.core import mail
from django.core.cache import cache
from django.db import connection
from django.test.utils import CaptureQueriesContext
from django.urls import reverse

from apps.core.clock import FixedClock
from apps.core.events import EventBus
from apps.tenants.models import Membership, Tenant
from apps.tenants.repositories import TenantRepository
from apps.tenants.services import CreateTenant, NewWorkspace

SIRET = "73282932000074"
PASSWORD = "correct-horse-battery-staple-42"

pytestmark = pytest.mark.django_db


@pytest.fixture(autouse=True)
def _open_signup(settings):
    settings.ACCOUNT_ALLOW_REGISTRATION = True
    cache.clear()


def company_step(client, tax_id: str = SIRET):
    return client.post(reverse("tenants:signup"), {"country": "fr", "tax_id": tax_id})


def account_step(client, email: str = "founder@acme.example"):
    return client.post(
        reverse("account_signup"),
        {"company_name": "Acme", "email": email, "password1": PASSWORD},
    )


def verify_email(client):
    code = re.search(
        r"^\s*([A-Z0-9]{4}-[A-Z0-9]{4})\s*$", str(mail.outbox[-1].body), re.M
    )
    assert code
    return client.post(reverse("account_email_verification_sent"), {"code": code[1]})


def follow_handoff(client, response):
    """Follow a handoff redirect onto the workspace host, as a browser would."""
    url = urlparse(response.url)
    return client.get(f"{url.path}?{url.query}", HTTP_HOST=url.hostname)


def workspace_for(email: str, name: str, siret: str) -> Tenant:
    owner = get_user_model().objects.create_user(email=email, password=PASSWORD)
    return CreateTenant(
        tenants=TenantRepository(),
        root_domain="localhost",
        unique_tax_id=True,
        events=EventBus(),
        clock=FixedClock(datetime(2026, 11, 18, tzinfo=UTC)),
    )(owner, NewWorkspace(name, "fr", "siret", siret))


def sirene_answers(monkeypatch, settings, payload: dict[str, Any] | None, status=200):
    settings.SIRENE_API_KEY = "test-key"
    response = Mock(spec=requests.Response, status_code=status)
    response.json.return_value = payload or {}
    monkeypatch.setattr(requests, "get", Mock(return_value=response))


ACME_SIRENE = {
    "etablissement": {
        "statutDiffusionEtablissement": "O",
        "uniteLegale": {"denominationUniteLegale": "ACME CONSEIL"},
        "adresseEtablissement": {
            "numeroVoieEtablissement": "12",
            "typeVoieEtablissement": "RUE",
            "libelleVoieEtablissement": "DE LA PAIX",
            "codePostalEtablissement": "75002",
            "libelleCommuneEtablissement": "PARIS",
        },
        "periodesEtablissement": [{"etatAdministratifEtablissement": "A"}],
    }
}


class TestCompanyStep:
    def test_invalid_number_explains_why_on_the_field(self, client):
        response = company_step(client, "1234")

        assert response.status_code == 200
        assert "14" in str(response.context["form"].errors["tax_id"])

    def test_taken_company_points_to_an_invitation(self, client):
        workspace_for("first@acme.example", "Acme", SIRET)

        response = company_step(client)

        assert "invite" in str(response.context["form"].errors["tax_id"])

    def test_found_company_prefills_step_two(self, client, monkeypatch, settings):
        sirene_answers(monkeypatch, settings, ACME_SIRENE)

        company_step(client)
        response = client.get(reverse("account_signup"))

        content = response.content.decode()
        assert "ACME CONSEIL" in content
        assert "12 RUE DE LA PAIX" in content
        assert response.context["form"].initial["company_name"] == "ACME CONSEIL"

    def test_closed_establishment_is_refused(self, client, monkeypatch, settings):
        closed = {"etablissement": {**ACME_SIRENE["etablissement"]}}
        closed["etablissement"]["periodesEtablissement"] = [
            {"etatAdministratifEtablissement": "F"}
        ]
        sirene_answers(monkeypatch, settings, closed)

        response = company_step(client)

        assert "closed" in str(response.context["form"].errors["tax_id"])

    def test_register_down_still_lets_people_sign_up(
        self, client, monkeypatch, settings
    ):
        sirene_answers(monkeypatch, settings, None, status=503)

        response = company_step(client)
        step_two = client.get(reverse("account_signup"))

        assert response.status_code == 302
        assert "could not reach" in step_two.content.decode()

    def test_skipping_step_one_sends_people_back(self, client):
        response = client.get(reverse("account_signup"))

        assert response.url == reverse("tenants:signup")

    def test_company_step_is_rate_limited(self, client, settings):
        settings.SIGNUP_LOOKUP_RATE_LIMIT = "2/m"

        statuses = [company_step(client, "1234").status_code for _ in range(3)]

        assert statuses == [200, 200, 429]


class TestFullSignup:
    def test_no_workspace_exists_before_the_email_is_verified(self, client):
        company_step(client)
        account_step(client)

        assert not Tenant.objects.exclude(schema_name="public").exists()

    def test_verified_signup_creates_workspace_and_lands_inside_it(self, client):
        company_step(client)
        account_step(client)

        response = client.get(verify_email(client).url)

        tenant = Tenant.objects.get(tax_id=SIRET)
        owner = get_user_model().objects.get(email="founder@acme.example")
        assert (tenant.name, tenant.timezone) == ("Acme", "Europe/Paris")
        assert Membership.objects.get(tenant=tenant).user == owner
        assert response.url.startswith("http://acme.localhost:8000/auth/handoff/")
        landing = follow_handoff(client, response)
        assert landing.status_code == 302
        home = client.get(landing.url, HTTP_HOST="acme.localhost")
        assert "Welcome to Acme" in home.content.decode()


class TestGoToWorkspace:
    def test_user_without_workspace_is_offered_to_create_one(self, client):
        client.force_login(get_user_model().objects.create_user(email="x@y.example"))

        response = client.get(reverse("tenants:go"))

        assert "tenants/no_workspace.html" in [t.name for t in response.templates]

    def test_user_with_one_workspace_goes_straight_in(self, client):
        tenant = workspace_for("solo@acme.example", "Acme", SIRET)
        client.force_login(tenant.memberships.get().user)

        response = client.get(reverse("tenants:go"))

        assert urlparse(response.url).hostname == "acme.localhost"

    def test_user_with_several_workspaces_picks_one(self, client):
        first = workspace_for("multi@acme.example", "Acme", SIRET)
        second = workspace_for("other@globex.example", "Globex", "55203253400646")
        user = first.memberships.get().user
        Membership.objects.create(user=user, tenant=second, role="member")
        client.force_login(user)

        with CaptureQueriesContext(connection) as queries:
            response = client.get(reverse("tenants:go"))

        # django-tenants adds a SET search_path before queries; count real ones:
        # domain lookup, session, user, memberships, domains (one for all rows).
        real = [q for q in queries if not q["sql"].startswith("SET search_path")]
        assert len(real) == 5

        content = response.content.decode()
        assert "Acme" in content and "Globex" in content

    def test_cannot_open_someone_elses_workspace(self, client):
        tenant = workspace_for("owner@acme.example", "Acme", SIRET)
        client.force_login(get_user_model().objects.create_user(email="x@y.example"))

        response = client.get(reverse("tenants:open", args=[tenant.pk]))

        assert response.status_code == 404


class TestSignedInUserAddsWorkspace:
    def test_company_step_then_name_creates_workspace(self, client):
        client.force_login(get_user_model().objects.create_user(email="x@y.example"))
        company_step(client)

        response = client.post(reverse("tenants:create"), {"company_name": "Acme"})

        assert urlparse(response.url).hostname == "acme.localhost"
        assert Tenant.objects.filter(tax_id=SIRET).exists()


class TestHandoff:
    def test_expired_or_forged_link_explains_and_offers_sign_in(self, client):
        tenant = workspace_for("owner@acme.example", "Acme", SIRET)

        response = client.get(
            reverse("tenants:handoff") + "?token=forged", HTTP_HOST="acme.localhost"
        )

        assert response.status_code == 400
        assert "/accounts/login/" in response.content.decode()
        assert tenant.pk

    def test_root_only_pages_on_a_workspace_host_go_to_the_root_domain(self, client):
        workspace_for("owner@acme.example", "Acme", SIRET)

        response = client.get(reverse("tenants:signup"), HTTP_HOST="acme.localhost")

        assert response.url == "http://localhost:8000/signup/"
