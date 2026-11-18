"""Signup step 1 (company check) and the sign-in handoff into a workspace."""

from datetime import UTC, datetime, timedelta

import pytest
from django.contrib.auth import get_user_model
from django.core.cache import cache
from freezegun import freeze_time

from apps.core.clock import FixedClock
from apps.core.events import EventBus
from apps.countrypacks.base import CompanyRecord
from apps.countrypacks.tests.fakes import FakeCompanyRegistry
from apps.tenants.repositories import TenantRepository
from apps.tenants.services import (
    CheckCompany,
    CompanyStatus,
    CreateTenant,
    IssueHandoff,
    LookupOutcome,
    NewWorkspace,
    RedeemHandoff,
)

SIRET = "73282932000074"
ACME = CompanyRecord(
    SIRET, "ACME", ("12 RUE DE LA PAIX",), "75002", "PARIS", True, True
)

pytestmark = pytest.mark.django_db


def check(registry=None, *, unique=True) -> CheckCompany:
    return CheckCompany(
        tenants=TenantRepository(),
        unique_tax_id=unique,
        registry_for=lambda country: registry,
    )


@pytest.fixture
def taken():
    """A real workspace already using SIRET."""
    owner = get_user_model().objects.create_user(email="first@acme.example")
    CreateTenant(
        tenants=TenantRepository(),
        root_domain="localhost",
        unique_tax_id=True,
        events=EventBus(),
        clock=FixedClock(datetime(2026, 11, 18, tzinfo=UTC)),
    )(owner, NewWorkspace("Acme", "fr", "siret", SIRET))


class TestCheckCompany:
    def test_found_company_is_ok_with_record(self):
        result = check(FakeCompanyRegistry({SIRET: ACME}))(
            "fr", "siret", "732 829 320 00074"
        )

        assert result.status is CompanyStatus.OK
        assert result.tax_id == SIRET
        assert result.lookup is LookupOutcome.FOUND
        assert result.record == ACME

    def test_invalid_identifier_explains_why(self):
        result = check()("fr", "siret", "123")

        assert result.status is CompanyStatus.INVALID
        assert "14" in result.error

    @pytest.mark.usefixtures("taken")
    def test_taken_identifier_points_to_an_invitation(self):
        result = check()("fr", "siret", SIRET)

        assert result.status is CompanyStatus.TAKEN
        assert "invite" in result.error

    @pytest.mark.usefixtures("taken")
    def test_taken_identifier_is_fine_when_uniqueness_is_off(self):
        assert check(unique=False)("fr", "siret", SIRET).ok

    def test_closed_establishment_is_refused(self):
        closed = CompanyRecord(SIRET, "ACME", (), "", "", active=False, public=True)

        result = check(FakeCompanyRegistry({SIRET: closed}))("fr", "siret", SIRET)

        assert result.status is CompanyStatus.CLOSED

    def test_not_public_company_is_ok_and_typed_by_hand(self):
        hidden = CompanyRecord(SIRET, "", (), "", "", active=True, public=False)

        result = check(FakeCompanyRegistry({SIRET: hidden}))("fr", "siret", SIRET)

        assert result.ok
        assert result.lookup is LookupOutcome.NOT_PUBLIC

    def test_registry_down_never_blocks_signup(self):
        result = check(FakeCompanyRegistry(down=True))("fr", "siret", SIRET)

        assert result.ok
        assert result.lookup is LookupOutcome.UNAVAILABLE

    def test_unknown_to_registry_is_ok_and_typed_by_hand(self):
        result = check(FakeCompanyRegistry())("fr", "siret", SIRET)

        assert result.ok
        assert result.lookup is LookupOutcome.NOT_FOUND

    def test_no_registry_configured_is_ok(self):
        result = check(None)("fr", "siret", SIRET)

        assert result.ok
        assert result.lookup is LookupOutcome.OFF


class TestHandoff:
    @pytest.fixture(autouse=True)
    def _clear(self):
        cache.clear()

    def test_handoff_token_signs_the_user_into_that_workspace_once(self):
        token = IssueHandoff(cache=cache)(user_id=7, tenant_id=3)
        redeem = RedeemHandoff(cache=cache)

        assert redeem(token, tenant_id=3) == 7
        assert redeem(token, tenant_id=3) is None  # single use

    def test_handoff_token_is_useless_for_another_workspace(self):
        token = IssueHandoff(cache=cache)(user_id=7, tenant_id=3)

        assert RedeemHandoff(cache=cache)(token, tenant_id=4) is None

    def test_handoff_token_expires_after_a_minute(self):
        with freeze_time("2026-11-18 10:00:00") as clock:
            token = IssueHandoff(cache=cache)(user_id=7, tenant_id=3)
            clock.tick(timedelta(seconds=61))

            assert RedeemHandoff(cache=cache)(token, tenant_id=3) is None

    @pytest.mark.parametrize("token", ["", "garbage", "a:b:c"])
    def test_handoff_tampered_token_is_rejected(self, token):
        assert RedeemHandoff(cache=cache)(token, tenant_id=3) is None
