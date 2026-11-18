"""CompanyRegistry contract (fake and Sirene), plus Sirene-specific parsing.

Sirene is exercised with requests.get mocked at the boundary. The response shapes
follow API Sirene 3.11; re-check them against a real response once a key exists.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any
from unittest.mock import Mock

import pytest
import requests
from django.core.cache import cache

from apps.countrypacks.base import CompanyRecord, CompanyRegistry, RegistryUnavailable
from apps.countrypacks.fr.pack import FrancePack
from apps.countrypacks.fr.sirene import SireneRegistry
from apps.countrypacks.generic.pack import GenericPack
from apps.countrypacks.tests.fakes import FakeCompanyRegistry

SIRET = "73282932000074"
ACME = CompanyRecord(
    identifier=SIRET,
    legal_name="ACME",
    address_lines=("12 RUE DE LA PAIX",),
    postcode="75002",
    city="PARIS",
    active=True,
    public=True,
)


def sirene_payload(
    *,
    diffusion: str = "O",
    state: str = "A",
    denomination: str | None = "ACME",
    first_name: str | None = None,
    last_name: str | None = None,
) -> dict[str, Any]:
    return {
        "etablissement": {
            "siret": SIRET,
            "statutDiffusionEtablissement": diffusion,
            "uniteLegale": {
                "denominationUniteLegale": denomination,
                "prenomUsuelUniteLegale": first_name,
                "nomUniteLegale": last_name,
            },
            "adresseEtablissement": {
                "complementAdresseEtablissement": None,
                "numeroVoieEtablissement": "12",
                "indiceRepetitionEtablissement": None,
                "typeVoieEtablissement": "RUE",
                "libelleVoieEtablissement": "DE LA PAIX",
                "codePostalEtablissement": "75002",
                "libelleCommuneEtablissement": "PARIS",
            },
            "periodesEtablissement": [
                {"dateFin": None, "etatAdministratifEtablissement": state}
            ],
        }
    }


def response(status: int, payload: dict[str, Any] | None = None) -> Mock:
    mock = Mock(spec=requests.Response)
    mock.status_code = status
    mock.json.return_value = payload or {}
    return mock


@pytest.fixture(autouse=True)
def _clear_cache():
    cache.clear()


def sirene(monkeypatch, get: Mock) -> SireneRegistry:
    monkeypatch.setattr(requests, "get", get)
    return SireneRegistry(api_key="k", api_url="https://sirene.test/3.11", cache=cache)


@dataclass
class World:
    """One registry plus ways to make it find, miss or fail."""

    registry: CompanyRegistry
    found: Callable[[], None]
    missing: Callable[[], None]
    down: Callable[[], None]


@pytest.fixture(params=["fake", "sirene"])
def world(request, monkeypatch) -> World:
    if request.param == "fake":
        fake = FakeCompanyRegistry()
        return World(
            registry=fake,
            found=lambda: fake.records.__setitem__(SIRET, ACME),
            missing=lambda: None,
            down=lambda: setattr(fake, "down", True),
        )
    get = Mock(return_value=response(404))
    registry = sirene(monkeypatch, get)

    def answer(value: Mock) -> None:
        get.return_value, get.side_effect = value, None

    return World(
        registry=registry,
        found=lambda: answer(response(200, sirene_payload())),
        missing=lambda: answer(response(404)),
        down=lambda: setattr(get, "side_effect", requests.Timeout()),
    )


class TestRegistryContract:
    def test_found_returns_the_record(self, world):
        world.found()

        assert world.registry.lookup("siret", SIRET) == ACME

    def test_missing_returns_none(self, world):
        world.missing()

        assert world.registry.lookup("siret", SIRET) is None

    def test_outage_raises_unavailable(self, world):
        world.down()

        with pytest.raises(RegistryUnavailable):
            world.registry.lookup("siret", SIRET)

    def test_unsupported_identifier_type_returns_none(self, world):
        world.found()

        assert world.registry.lookup("vat", "FR83404833048") is None


class TestSirene:
    def test_sirene_sends_key_and_normalized_siret(self, monkeypatch):
        get = Mock(return_value=response(200, sirene_payload()))

        sirene(monkeypatch, get).lookup("siret", "732 829 320 00074")

        assert get.call_args.args[0] == f"https://sirene.test/3.11/siret/{SIRET}"
        assert get.call_args.kwargs["headers"]["X-INSEE-Api-Key-Integration"] == "k"
        assert get.call_args.kwargs["timeout"] <= 5

    def test_sirene_closed_establishment_is_inactive(self, monkeypatch):
        get = Mock(return_value=response(200, sirene_payload(state="F")))

        record = sirene(monkeypatch, get).lookup("siret", SIRET)

        assert record is not None and not record.active

    def test_sirene_sole_trader_name_is_first_and_last_name(self, monkeypatch):
        payload = sirene_payload(
            denomination=None, first_name="MARIE", last_name="CURIE"
        )
        get = Mock(return_value=response(200, payload))

        record = sirene(monkeypatch, get).lookup("siret", SIRET)

        assert record is not None and record.legal_name == "MARIE CURIE"

    def test_sirene_partial_disclosure_hides_name_and_address(self, monkeypatch):
        get = Mock(return_value=response(200, sirene_payload(diffusion="P")))

        record = sirene(monkeypatch, get).lookup("siret", SIRET)

        assert record is not None
        assert not record.public
        assert (record.legal_name, record.address_lines, record.city) == ("", (), "")

    @pytest.mark.parametrize("status", [401, 403, 429, 500, 503])
    def test_sirene_error_statuses_mean_unavailable(self, monkeypatch, status):
        registry = sirene(monkeypatch, Mock(return_value=response(status)))

        with pytest.raises(RegistryUnavailable):
            registry.lookup("siret", SIRET)

    def test_sirene_invalid_siret_is_not_sent(self, monkeypatch):
        get = Mock()

        assert sirene(monkeypatch, get).lookup("siret", "123") is None
        get.assert_not_called()

    def test_sirene_caches_found_and_missing_answers(self, monkeypatch):
        get = Mock(return_value=response(200, sirene_payload()))
        registry = sirene(monkeypatch, get)

        registry.lookup("siret", SIRET)
        registry.lookup("siret", SIRET)

        assert get.call_count == 1

    def test_sirene_caches_not_found(self, monkeypatch):
        get = Mock(return_value=response(404))
        registry = sirene(monkeypatch, get)

        assert registry.lookup("siret", SIRET) is None
        assert registry.lookup("siret", SIRET) is None
        assert get.call_count == 1

    def test_sirene_does_not_cache_outages(self, monkeypatch):
        get = Mock(side_effect=[requests.ConnectionError(), response(404)])
        registry = sirene(monkeypatch, get)

        with pytest.raises(RegistryUnavailable):
            registry.lookup("siret", SIRET)
        assert registry.lookup("siret", SIRET) is None


class TestPackRegistries:
    def test_france_without_key_has_no_registry(self, settings):
        settings.SIRENE_API_KEY = ""

        assert FrancePack().company_registry() is None

    def test_france_with_key_uses_sirene(self, settings):
        settings.SIRENE_API_KEY = "k"

        assert isinstance(FrancePack().company_registry(), SireneRegistry)

    def test_generic_has_no_registry(self):
        assert GenericPack().company_registry() is None
