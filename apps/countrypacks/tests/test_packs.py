"""Pack-specific data, and the registry's lookup and fallback."""

from dataclasses import dataclass
from decimal import Decimal

import pytest

from apps.countrypacks.base import CountryPack
from apps.countrypacks.fr.pack import FrancePack
from apps.countrypacks.generic.pack import GenericPack
from apps.countrypacks.registry import get_pack


@dataclass(frozen=True)
class Seller:
    vat_franchise_mention: str = ""


def test_packs_satisfy_the_protocol():
    # The registry loads packs by dotted path, so mypy only sees them here: this
    # assignment fails `make types` if a pack drifts from CountryPack.
    packs: list[CountryPack] = [FrancePack(), GenericPack()]

    assert {p.code for p in packs} == {"fr", "generic"}


class TestRegistry:
    @pytest.mark.parametrize("code", ["fr", "FR", " fr "])
    def test_get_pack_finds_france_case_insensitively(self, code):
        assert isinstance(get_pack(code), FrancePack)

    @pytest.mark.parametrize("code", ["zz", "", "gb"])
    def test_get_pack_unknown_country_falls_back_to_generic(self, code):
        assert isinstance(get_pack(code), GenericPack)

    def test_get_pack_returns_the_same_instance(self):
        assert get_pack("fr") is get_pack("fr")


class TestFrancePack:
    def test_france_locale_defaults(self):
        defaults = FrancePack().locale_defaults()

        assert (defaults.language, defaults.timezone, defaults.currency) == (
            "fr",
            "Europe/Paris",
            "EUR",
        )

    def test_france_mainland_vat_rates(self):
        rates = {r.code: r.rate for r in FrancePack().tax_rates()}

        assert rates == {
            "standard": Decimal("0.20"),
            "intermediate": Decimal("0.10"),
            "reduced": Decimal("0.055"),
            "super_reduced": Decimal("0.021"),
        }

    def test_france_tax_identity_types(self):
        codes = [t.code for t in FrancePack().tax_identity_types()]

        assert codes == ["siret", "siren", "vat"]

    def test_france_unknown_identifier_type_is_invalid(self):
        assert not FrancePack().validate_tax_identity("ssn", "123").valid

    def test_france_vat_franchise_mention_is_the_configured_text(self):
        mention = "TVA non applicable, art. 293 B du CGI"

        assert FrancePack().invoice_mentions(Seller(mention)) == (mention,)

    def test_france_no_vat_franchise_no_mention(self):
        assert FrancePack().invoice_mentions(Seller("  ")) == ()


class TestGenericPack:
    def test_generic_has_no_preset_tax_rates(self):
        assert GenericPack().tax_rates() == ()

    def test_generic_accepts_any_non_empty_tax_identity(self):
        result = GenericPack().validate_tax_identity("tax_id", "  AB-123  ")

        assert result.valid
        assert result.normalized == "AB-123"

    def test_generic_rejects_empty_tax_identity(self):
        assert not GenericPack().validate_tax_identity("tax_id", "   ").valid
