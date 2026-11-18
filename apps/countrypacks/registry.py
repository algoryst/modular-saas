"""Find the pack for a country. Packs are listed in settings.COUNTRY_PACKS."""

from functools import cache

from django.conf import settings
from django.utils.module_loading import import_string

from apps.countrypacks.base import CountryPack

GENERIC = "generic"


def get_pack(country_code: str) -> CountryPack:
    """The pack for an ISO 3166 alpha-2 code, or the generic pack if there is none."""
    packs: dict[str, str] = settings.COUNTRY_PACKS
    path = packs.get(country_code.strip().lower(), packs[GENERIC])
    return _load(path)


@cache
def _load(path: str) -> CountryPack:
    pack: CountryPack = import_string(path)()
    return pack
