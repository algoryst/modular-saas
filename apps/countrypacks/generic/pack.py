"""Fallback for countries without a pack: manual tax lines, no e-invoicing."""

from collections.abc import Mapping

from django.utils.translation import gettext_lazy as _

from apps.countrypacks.base import (
    AccountingExport,
    CompanyRegistry,
    LocaleDefaults,
    NumberingRules,
    PlatformAdapter,
    SellerProfile,
    TaxIdentityResult,
    TaxIdentityType,
    TaxRate,
)


class GenericPack:
    code = "generic"
    name = _("Other country")

    def locale_defaults(self) -> LocaleDefaults:
        return LocaleDefaults(language="en", timezone="UTC", currency="EUR")

    def tax_rates(self) -> tuple[TaxRate, ...]:
        return ()

    def tax_identity_types(self) -> tuple[TaxIdentityType, ...]:
        return (TaxIdentityType("tax_id", _("Tax identification number")),)

    def validate_tax_identity(self, type_code: str, value: str) -> TaxIdentityResult:
        if type_code != "tax_id":
            return TaxIdentityResult.invalid(_("Unknown identifier type."))
        normalized = value.strip()
        if not normalized:
            return TaxIdentityResult.invalid(_("Enter your tax identification number."))
        return TaxIdentityResult.ok(normalized)

    def invoice_mentions(self, seller: SellerProfile) -> tuple[str, ...]:
        return ()

    def numbering_rules(self) -> NumberingRules:
        return NumberingRules(pattern="{year}-{sequence:05d}", resets_yearly=True)

    def company_registry(self) -> CompanyRegistry | None:
        return None

    def einvoicing_adapter(self) -> PlatformAdapter | None:
        return None

    def accounting_export(self) -> AccountingExport | None:
        return None

    def legal_templates(self) -> Mapping[str, str]:
        return {}
