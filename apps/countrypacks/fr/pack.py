"""France. Invoicing detail (mentions, series, Factur-X, FEC, PA) lands in Phase 3b."""

from collections.abc import Mapping
from decimal import Decimal

from django.conf import settings
from django.core.cache import caches
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
from apps.countrypacks.fr.identifiers import (
    validate_siren,
    validate_siret,
    validate_vat,
)
from apps.countrypacks.fr.sirene import SireneRegistry

# Mainland France VAT rates (CGI art. 278 to 281 nonies). Overseas rates differ.
VAT_RATES = (
    TaxRate("standard", Decimal("0.20"), _("Standard rate (20%)")),
    TaxRate("intermediate", Decimal("0.10"), _("Intermediate rate (10%)")),
    TaxRate("reduced", Decimal("0.055"), _("Reduced rate (5.5%)")),
    TaxRate("super_reduced", Decimal("0.021"), _("Super-reduced rate (2.1%)")),
)

VALIDATORS = {"siret": validate_siret, "siren": validate_siren, "vat": validate_vat}

TAX_IDENTITY_TYPES = (
    TaxIdentityType("siret", _("SIRET")),
    TaxIdentityType("siren", _("SIREN")),
    TaxIdentityType("vat", _("VAT number")),
)


class FrancePack:
    code = "fr"
    name = _("France")

    def locale_defaults(self) -> LocaleDefaults:
        return LocaleDefaults(language="fr", timezone="Europe/Paris", currency="EUR")

    def tax_rates(self) -> tuple[TaxRate, ...]:
        return VAT_RATES

    def tax_identity_types(self) -> tuple[TaxIdentityType, ...]:
        return TAX_IDENTITY_TYPES

    def validate_tax_identity(self, type_code: str, value: str) -> TaxIdentityResult:
        validator = VALIDATORS.get(type_code)
        if validator is None:
            return TaxIdentityResult.invalid(_("Unknown identifier type."))
        return validator(value)

    def company_registry(self) -> CompanyRegistry | None:
        # No key (local dev, tests): no lookup, signup falls back to manual entry.
        if not settings.SIRENE_API_KEY:
            return None
        return SireneRegistry(
            api_key=settings.SIRENE_API_KEY,
            api_url=settings.SIRENE_API_URL,
            cache=caches["default"],
        )

    def invoice_mentions(self, seller: SellerProfile) -> tuple[str, ...]:
        # The VAT-franchise wording is configured per seller, never a literal here.
        # Phase 3b adds the other mandatory mentions after the accountant review.
        mention = seller.vat_franchise_mention.strip()
        return (mention,) if mention else ()

    def numbering_rules(self) -> NumberingRules:
        # Placeholder series until Phase 3b defines invoice/credit-note series.
        return NumberingRules(pattern="{year}-{sequence:05d}", resets_yearly=True)

    def einvoicing_adapter(self) -> PlatformAdapter | None:
        return None  # Phase 3b: partner PA adapter

    def accounting_export(self) -> AccountingExport | None:
        return None  # Phase 3b: FEC export

    def legal_templates(self) -> Mapping[str, str]:
        return {}
