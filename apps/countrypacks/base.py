"""The CountryPack interface (docs/ARCHITECTURE.md section 2b) and its value types.

Everything that differs by country is answered by the tenant's pack, never
hard-coded. Mandatory legal mentions are legal text: they are returned exactly as
the law words them, never passed through gettext.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from decimal import Decimal
from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    # Dev-only package; annotations are strings at runtime (future import).
    from django_stubs_ext import StrOrPromise


@dataclass(frozen=True, slots=True)
class TaxRate:
    code: str  # "standard", "intermediate", "reduced", ...
    rate: Decimal  # a fraction: Decimal("0.20") is 20 %
    label: StrOrPromise


@dataclass(frozen=True, slots=True)
class LocaleDefaults:
    language: str
    timezone: str
    currency: str


@dataclass(frozen=True, slots=True)
class NumberingRules:
    """How document numbers look. Gap-free numbering is never optional."""

    pattern: str  # str.format with {year} and {sequence}
    resets_yearly: bool

    def render(self, *, year: int, sequence: int) -> str:
        return self.pattern.format(year=year, sequence=sequence)


@dataclass(frozen=True, slots=True)
class TaxIdentityType:
    code: str
    label: StrOrPromise


@dataclass(frozen=True, slots=True)
class TaxIdentityResult:
    valid: bool
    normalized: str = ""
    error: StrOrPromise = ""

    @classmethod
    def ok(cls, normalized: str) -> TaxIdentityResult:
        return cls(valid=True, normalized=normalized)

    @classmethod
    def invalid(cls, error: StrOrPromise) -> TaxIdentityResult:
        return cls(valid=False, error=error)


class SellerProfile(Protocol):
    """What a pack needs to know about the issuing business (the tenant, from W2)."""

    @property
    def vat_franchise_mention(self) -> str: ...


@dataclass(frozen=True, slots=True)
class CompanyRecord:
    """A business as an official register describes it, for the user to confirm."""

    identifier: str
    legal_name: str  # "" when the register does not disclose it
    address_lines: tuple[str, ...]
    postcode: str
    city: str
    active: bool  # False: the register lists it as closed
    public: bool  # False: the business opted out of public listing


class RegistryUnavailable(Exception):
    """The register could not answer (timeout, rate limit, outage, bad key)."""


class CompanyRegistry(Protocol):
    def lookup(self, type_code: str, value: str) -> CompanyRecord | None:
        """None when not found or the type is not supported.

        Raises RegistryUnavailable when the register cannot answer; callers fall
        back to manual entry, never block on it.
        """
        ...


class PlatformAdapter(Protocol):
    """E-invoicing platform (PA) connection. Methods arrive in Phase 3b."""


class AccountingExport(Protocol):
    """Accounting export such as the French FEC. Methods arrive in Phase 3b."""


class CountryPack(Protocol):
    # Read-only: a plain class attribute in a pack satisfies these.
    @property
    def code(self) -> str:
        """ISO 3166-1 alpha-2, lowercase, or "generic"."""
        ...

    @property
    def name(self) -> StrOrPromise: ...

    def locale_defaults(self) -> LocaleDefaults: ...

    def tax_rates(self) -> tuple[TaxRate, ...]: ...

    def tax_identity_types(self) -> tuple[TaxIdentityType, ...]: ...

    def validate_tax_identity(self, type_code: str, value: str) -> TaxIdentityResult:
        """Never raises: junk input gives an invalid result with an error message."""
        ...

    def invoice_mentions(self, seller: SellerProfile) -> tuple[str, ...]: ...

    def numbering_rules(self) -> NumberingRules: ...

    def company_registry(self) -> CompanyRegistry | None:
        """Official business register lookup, or None if unavailable for the country."""
        ...

    def einvoicing_adapter(self) -> PlatformAdapter | None: ...

    def accounting_export(self) -> AccountingExport | None: ...

    def legal_templates(self) -> Mapping[str, str]:
        """Document kind ("terms", "dpa", "privacy") to template name."""
        ...
