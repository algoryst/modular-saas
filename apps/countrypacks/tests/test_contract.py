"""Contract suite: every registered country pack must pass all of these.

A new pack is covered as soon as it is added to settings.COUNTRY_PACKS.
"""

import re
import zoneinfo
from dataclasses import dataclass
from decimal import Decimal

import pytest
from django.conf import settings
from django.template.loader import get_template

from apps.core.money import MINOR_UNITS
from apps.countrypacks.base import CountryPack, TaxIdentityResult
from apps.countrypacks.registry import get_pack


@dataclass(frozen=True)
class Seller:
    vat_franchise_mention: str = ""


@pytest.fixture(params=sorted(settings.COUNTRY_PACKS))
def pack(request) -> CountryPack:
    return get_pack(request.param)


def test_pack_code_is_iso_alpha2_or_generic(pack):
    assert pack.code == "generic" or re.fullmatch(r"[a-z]{2}", pack.code)


def test_pack_is_registered_under_its_own_code(pack):
    assert get_pack(pack.code).code == pack.code


def test_pack_has_a_name(pack):
    assert str(pack.name).strip()


def test_locale_defaults_are_supported(pack):
    defaults = pack.locale_defaults()

    assert defaults.language in dict(settings.LANGUAGES)
    assert defaults.currency in MINOR_UNITS
    zoneinfo.ZoneInfo(defaults.timezone)  # raises for an unknown zone


def test_tax_rates_are_decimal_fractions_with_unique_codes(pack):
    rates = pack.tax_rates()

    assert all(isinstance(r.rate, Decimal) for r in rates)
    assert all(Decimal(0) <= r.rate < Decimal(1) for r in rates)
    assert len({r.code for r in rates}) == len(rates)
    assert sum(r.code == "standard" for r in rates) <= 1
    assert all(str(r.label).strip() for r in rates)


def test_numbering_pattern_renders_year_and_sequence(pack):
    rules = pack.numbering_rules()

    first = rules.render(year=2027, sequence=1)
    second = rules.render(year=2027, sequence=2)

    assert first != second
    if rules.resets_yearly:
        assert "2027" in first


def test_tax_identity_types_have_unique_codes_and_labels(pack):
    types = pack.tax_identity_types()

    assert len({t.code for t in types}) == len(types)
    assert all(str(t.label).strip() for t in types)


@pytest.mark.parametrize("value", ["", "   ", "x" * 500, "12 34", "<script>", "é∑"])
def test_validate_tax_identity_never_raises_on_junk(pack, value):
    for type_code in [t.code for t in pack.tax_identity_types()] + ["unknown"]:
        result = pack.validate_tax_identity(type_code, value)

        assert isinstance(result, TaxIdentityResult)
        assert result.valid or str(result.error).strip()


def test_validate_tax_identity_unknown_type_is_invalid(pack):
    assert not pack.validate_tax_identity("no-such-type", "123").valid


@pytest.mark.parametrize("mention", ["", "Some configured mention"])
def test_invoice_mentions_are_non_empty_strings(pack, mention):
    mentions = pack.invoice_mentions(Seller(vat_franchise_mention=mention))

    assert isinstance(mentions, tuple)
    assert all(isinstance(m, str) and m.strip() for m in mentions)


def test_company_registry_is_none_or_can_look_up(pack, settings):
    settings.SIRENE_API_KEY = "contract-test-key"

    registry = pack.company_registry()

    assert registry is None or callable(registry.lookup)


def test_optional_adapters_are_none_until_implemented(pack):
    # Phase 3b replaces this with the PlatformAdapter / export contract suites.
    assert pack.einvoicing_adapter() is None
    assert pack.accounting_export() is None


def test_legal_templates_exist(pack):
    for template_name in pack.legal_templates().values():
        get_template(template_name)
