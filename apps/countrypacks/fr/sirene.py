"""INSEE API Sirene 3.11 (open data): look a SIRET up in the official register.

Rate limit is 30 requests/minute per key, so answers are cached. Field names follow
the 3.11 documentation; re-check against a real response when the key is created.
Never log responses: for sole traders the record names a person.
"""

from __future__ import annotations

from typing import Any

import requests
from django.core.cache.backends.base import BaseCache

from apps.countrypacks.base import CompanyRecord, RegistryUnavailable
from apps.countrypacks.fr.identifiers import validate_siret

_NOT_FOUND = "not-found"


class SireneRegistry:
    TIMEOUT_SECONDS = 3
    CACHE_SECONDS = 24 * 60 * 60
    KEY_HEADER = "X-INSEE-Api-Key-Integration"

    def __init__(self, *, api_key: str, api_url: str, cache: BaseCache) -> None:
        self._api_key = api_key
        self._api_url = api_url.rstrip("/")
        self._cache = cache

    def lookup(self, type_code: str, value: str) -> CompanyRecord | None:
        checked = validate_siret(value)
        if type_code != "siret" or not checked.valid:
            return None
        cache_key = f"sirene:siret:{checked.normalized}"
        cached = self._cache.get(cache_key)
        if isinstance(cached, CompanyRecord):
            return cached
        if cached == _NOT_FOUND:
            return None
        record = self._fetch(checked.normalized)
        self._cache.set(cache_key, record or _NOT_FOUND, self.CACHE_SECONDS)
        return record

    def _fetch(self, siret: str) -> CompanyRecord | None:
        try:
            response = requests.get(
                f"{self._api_url}/siret/{siret}",
                headers={self.KEY_HEADER: self._api_key, "Accept": "application/json"},
                timeout=self.TIMEOUT_SECONDS,
            )
        except (requests.ConnectionError, requests.Timeout) as exc:
            raise RegistryUnavailable("Sirene unreachable") from exc
        if response.status_code == 404:
            return None
        if response.status_code != 200:
            # 401/403: bad or missing key; 429: rate limit; 5xx: outage.
            raise RegistryUnavailable(f"Sirene answered {response.status_code}")
        return _to_record(siret, response.json()["etablissement"])


def _to_record(siret: str, etablissement: dict[str, Any]) -> CompanyRecord:
    periods = etablissement.get("periodesEtablissement") or [{}]
    active = periods[0].get("etatAdministratifEtablissement") != "F"
    if etablissement.get("statutDiffusionEtablissement") == "P":
        # Partial disclosure: name and address are withheld; the user types them.
        return CompanyRecord(siret, "", (), "", "", active=active, public=False)
    address = etablissement.get("adresseEtablissement") or {}
    return CompanyRecord(
        identifier=siret,
        legal_name=_legal_name(etablissement.get("uniteLegale") or {}),
        address_lines=_address_lines(address),
        postcode=address.get("codePostalEtablissement") or "",
        city=address.get("libelleCommuneEtablissement") or "",
        active=active,
        public=True,
    )


def _legal_name(unite: dict[str, Any]) -> str:
    if denomination := unite.get("denominationUniteLegale"):
        return str(denomination)
    # Sole traders have no company name: the register gives the person's name.
    parts = (unite.get("prenomUsuelUniteLegale"), unite.get("nomUniteLegale"))
    return " ".join(str(p) for p in parts if p)


def _address_lines(address: dict[str, Any]) -> tuple[str, ...]:
    street = " ".join(
        str(address[key])
        for key in (
            "numeroVoieEtablissement",
            "indiceRepetitionEtablissement",
            "typeVoieEtablissement",
            "libelleVoieEtablissement",
        )
        if address.get(key)
    )
    complement = address.get("complementAdresseEtablissement")
    return tuple(line for line in (str(complement or ""), street) if line)
