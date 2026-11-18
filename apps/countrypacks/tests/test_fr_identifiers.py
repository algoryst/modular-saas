import pytest

from apps.countrypacks.fr.identifiers import (
    validate_siren,
    validate_siret,
    validate_vat,
)
from apps.countrypacks.fr.pack import FrancePack


class TestSiret:
    @pytest.mark.parametrize(
        ("value", "normalized"),
        [
            ("73282932000074", "73282932000074"),
            ("732 829 320 00074", "73282932000074"),  # as printed on documents
            ("732.829.320.00074", "73282932000074"),
            (" 732-829-320-00074 ", "73282932000074"),
        ],
    )
    def test_siret_valid_and_normalized(self, value, normalized):
        result = validate_siret(value)

        assert result.valid
        assert result.normalized == normalized

    @pytest.mark.parametrize(
        "value",
        [
            "35600000049837",  # La Poste establishment: digit sum, not Luhn
            "35600000000048",  # La Poste head office: Luhn
        ],
    )
    def test_siret_la_poste_exception(self, value):
        assert validate_siret(value).valid

    @pytest.mark.parametrize(
        ("value", "message_part"),
        [
            ("", "Enter"),
            ("7328293200007", "13"),  # says how many digits were typed
            ("7328293200007A", "digits"),
            ("73282932000075", "typo"),  # checksum
            ("７３２８２９３２０００７４", "digits"),  # full-width digits are not ASCII
        ],
    )
    def test_siret_invalid_explains_why(self, value, message_part):
        result = validate_siret(value)

        assert not result.valid
        assert message_part in str(result.error)


class TestSiren:
    def test_siren_valid(self):
        assert validate_siren("552 032 534").normalized == "552032534"

    @pytest.mark.parametrize("value", ["732829321", "12345678", "ABCDEFGHI"])
    def test_siren_invalid(self, value):
        assert not validate_siren(value).valid


class TestVat:
    @pytest.mark.parametrize(
        ("value", "normalized"),
        [
            ("FR83404833048", "FR83404833048"),
            ("fr 27 552032534", "FR27552032534"),
        ],
    )
    def test_vat_valid_and_normalized(self, value, normalized):
        result = validate_vat(value)

        assert result.valid
        assert result.normalized == normalized

    @pytest.mark.parametrize(
        "value",
        [
            "FR84404833048",  # wrong key
            "FR83404833049",  # SIREN checksum
            "DE83404833048",  # not French
            "FR8340483304",  # too short
            "FRXX404833048",
        ],
    )
    def test_vat_invalid(self, value):
        assert not validate_vat(value).valid


class TestFrancePackUsesValidators:
    @pytest.mark.parametrize(
        ("type_code", "value"),
        [("siret", "73282932000074"), ("siren", "732829320"), ("vat", "FR83404833048")],
    )
    def test_france_pack_validates_each_type(self, type_code, value):
        assert FrancePack().validate_tax_identity(type_code, value).valid
