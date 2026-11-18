"""French business identifiers: SIREN, SIRET and intra-EU VAT number."""

import re

from django.utils.translation import gettext as _

from apps.countrypacks.base import TaxIdentityResult

# People type identifiers the way they are printed: "732 829 320 00074".
_SEPARATORS = re.compile(r"[\s.\-]")
_ASCII_DIGITS = re.compile(r"[0-9]+")
# La Poste's establishments use a digit-sum rule instead of Luhn; its head
# office (35600000000048) still passes Luhn, so either rule is accepted.
LA_POSTE_SIREN = "356000000"


def normalize(value: str) -> str:
    return _SEPARATORS.sub("", value).upper()


def luhn_valid(digits: str) -> bool:
    total = 0
    for position, char in enumerate(reversed(digits)):
        digit = int(char)
        if position % 2 == 1:
            digit = digit * 2 - 9 if digit > 4 else digit * 2
        total += digit
    return total % 10 == 0


def _check_digits(value: str, *, name: str, length: int) -> TaxIdentityResult | None:
    """The shape errors shared by SIREN and SIRET, or None when the shape is right."""
    if not value:
        return TaxIdentityResult.invalid(
            _("Enter your %(name)s number.") % {"name": name}
        )
    if not _ASCII_DIGITS.fullmatch(value):
        return TaxIdentityResult.invalid(
            _("A %(name)s contains only digits.") % {"name": name}
        )
    if len(value) != length:
        return TaxIdentityResult.invalid(
            _("A %(name)s has %(length)d digits; you entered %(count)d.")
            % {"name": name, "length": length, "count": len(value)}
        )
    return None


def _checksum_error(name: str) -> TaxIdentityResult:
    return TaxIdentityResult.invalid(
        _("This %(name)s number is not valid. Check for a typo.") % {"name": name}
    )


def validate_siren(value: str) -> TaxIdentityResult:
    siren = normalize(value)
    if error := _check_digits(siren, name="SIREN", length=9):
        return error
    return (
        TaxIdentityResult.ok(siren) if luhn_valid(siren) else _checksum_error("SIREN")
    )


def validate_siret(value: str) -> TaxIdentityResult:
    siret = normalize(value)
    if error := _check_digits(siret, name="SIRET", length=14):
        return error
    la_poste = siret.startswith(LA_POSTE_SIREN) and sum(map(int, siret)) % 5 == 0
    if luhn_valid(siret) or la_poste:
        return TaxIdentityResult.ok(siret)
    return _checksum_error("SIRET")


def vat_key(siren: str) -> str:
    return f"{(12 + 3 * (int(siren) % 97)) % 97:02d}"


def validate_vat(value: str) -> TaxIdentityResult:
    vat = normalize(value)
    shape_ok = (
        len(vat) == 13 and vat.startswith("FR") and _ASCII_DIGITS.fullmatch(vat[2:])
    )
    if not shape_ok:
        return TaxIdentityResult.invalid(
            _("A French VAT number looks like FR 12 345678901 (FR, 2 digits, SIREN).")
        )
    key, siren = vat[2:4], vat[4:]
    if not luhn_valid(siren) or key != vat_key(siren):
        return _checksum_error(_("VAT"))
    return TaxIdentityResult.ok(vat)
