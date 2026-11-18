from __future__ import annotations

import hashlib
import secrets
from collections.abc import Callable
from dataclasses import dataclass
from enum import StrEnum
from typing import TYPE_CHECKING

from django.core import signing
from django.core.cache.backends.base import BaseCache
from django.db import transaction
from django.utils.text import slugify
from django.utils.translation import gettext as _
from django_tenants.utils import get_public_schema_name, schema_context

from apps.core.clock import Clock
from apps.core.events import EventBus, WorkspaceCreated
from apps.countrypacks.base import CompanyRecord, CompanyRegistry, RegistryUnavailable
from apps.countrypacks.registry import get_pack
from apps.tenants.models import Membership, Tenant
from apps.tenants.repositories import TenantRepository

if TYPE_CHECKING:
    from django.contrib.auth.models import AbstractBaseUser

# Subdomains that must never belong to a workspace.
RESERVED_SLUGS = frozenset(
    {"admin", "api", "app", "blog", "docs", "help", "mail", "media", "public"}
    | {"static", "status", "support", "www"}
)
FALLBACK_SLUG = "workspace"
MAX_SLUG_LENGTH = 40


def taken_message() -> str:
    return _(
        "This company already has a workspace. Ask a colleague who uses it to "
        "invite you."
    )


class InvalidTaxIdentityError(ValueError):
    pass


class TaxIdentityTakenError(Exception):
    """Another workspace already uses this identifier (TENANT_UNIQUE_TAX_ID)."""


@dataclass(frozen=True)
class NewWorkspace:
    name: str
    country: str
    tax_id_type: str
    tax_id: str


class CreateTenant:
    """The one place workspaces are created: schema, domain, owner, event.

    Everything runs in one transaction; Postgres DDL is transactional, so a failure
    leaves no schema behind. A tenant migration marked non-atomic would fail here.
    """

    def __init__(
        self,
        *,
        tenants: TenantRepository,
        root_domain: str,
        unique_tax_id: bool,
        events: EventBus,
        clock: Clock,
    ) -> None:
        self._tenants = tenants
        self._root_domain = root_domain
        self._unique_tax_id = unique_tax_id
        self._events = events
        self._clock = clock

    def __call__(self, owner: AbstractBaseUser, workspace: NewWorkspace) -> Tenant:
        country = workspace.country.strip().lower()
        pack = get_pack(country)
        identity = pack.validate_tax_identity(workspace.tax_id_type, workspace.tax_id)
        if not identity.valid:
            raise InvalidTaxIdentityError(str(identity.error))
        defaults = pack.locale_defaults()
        with transaction.atomic():
            if self._unique_tax_id:
                self._ensure_identity_free(
                    country, workspace.tax_id_type, identity.normalized
                )
            slug = self._free_slug(workspace.name)
            tenant = self._tenants.create(
                Tenant(
                    schema_name=_schema_name(slug),
                    name=workspace.name.strip(),
                    tax_country=country,
                    tax_id_type=workspace.tax_id_type,
                    tax_id=identity.normalized,
                    timezone=defaults.timezone,
                    currency=defaults.currency,
                )
            )
            self._tenants.add_domain(tenant, self._domain(slug))
            self._tenants.add_membership(owner.pk, tenant, Membership.Role.OWNER)
            self._events.publish(
                WorkspaceCreated(
                    occurred_at=self._clock.now(),
                    tenant_schema=tenant.schema_name,
                    owner_id=owner.pk,
                )
            )
        return tenant

    def _ensure_identity_free(self, country: str, type_code: str, value: str) -> None:
        self._tenants.lock_tax_identity(country, type_code, value)
        if self._tenants.tax_identity_taken(country, type_code, value):
            raise TaxIdentityTakenError(value)

    def _free_slug(self, name: str) -> str:
        base = slugify(name)[:MAX_SLUG_LENGTH].strip("-") or FALLBACK_SLUG
        if base in RESERVED_SLUGS:
            base = f"{base}-team"
        slug, suffix = base, 1
        while self._tenants.address_taken(_schema_name(slug), self._domain(slug)):
            suffix += 1
            slug = f"{base}-{suffix}"
        return slug

    def _domain(self, slug: str) -> str:
        return f"{slug}.{self._root_domain}"


def _schema_name(slug: str) -> str:
    # The prefix keeps workspace schemas apart from Postgres' own (public, pg_*).
    return "ws_" + slug.replace("-", "_")


class CompanyStatus(StrEnum):
    OK = "ok"
    INVALID = "invalid"
    TAKEN = "taken"
    CLOSED = "closed"


class LookupOutcome(StrEnum):
    FOUND = "found"  # name and address prefilled for the user to confirm
    NOT_PUBLIC = "not_public"  # listed but withheld: the user types them
    NOT_FOUND = "not_found"
    UNAVAILABLE = "unavailable"  # register down or rate-limited: manual entry
    OFF = "off"  # no register for this country, or no API key


@dataclass(frozen=True)
class CompanyCheck:
    status: CompanyStatus
    country: str
    tax_id_type: str
    tax_id: str
    lookup: LookupOutcome = LookupOutcome.OFF
    record: CompanyRecord | None = None
    error: str = ""

    @property
    def ok(self) -> bool:
        return self.status is CompanyStatus.OK


class CheckCompany:
    """Signup step 1: is this identifier valid, free, open, and what is it called?"""

    def __init__(
        self,
        *,
        tenants: TenantRepository,
        unique_tax_id: bool,
        registry_for: Callable[[str], CompanyRegistry | None],
    ) -> None:
        self._tenants = tenants
        self._unique_tax_id = unique_tax_id
        self._registry_for = registry_for

    def __call__(self, country: str, tax_id_type: str, value: str) -> CompanyCheck:
        country = country.strip().lower()
        identity = get_pack(country).validate_tax_identity(tax_id_type, value)
        if not identity.valid:
            return CompanyCheck(
                CompanyStatus.INVALID,
                country,
                tax_id_type,
                value,
                error=str(identity.error),
            )
        tax_id = identity.normalized
        if self._unique_tax_id and self._tenants.tax_identity_taken(
            country, tax_id_type, tax_id
        ):
            return CompanyCheck(
                CompanyStatus.TAKEN,
                country,
                tax_id_type,
                tax_id,
                error=taken_message(),
            )
        lookup, record = self._look_up(country, tax_id_type, tax_id)
        if record is not None and not record.active:
            return CompanyCheck(
                CompanyStatus.CLOSED,
                country,
                tax_id_type,
                tax_id,
                lookup,
                record,
                error=_(
                    "The official register lists this establishment as closed. "
                    "Check the number, or use your current establishment's."
                ),
            )
        return CompanyCheck(
            CompanyStatus.OK, country, tax_id_type, tax_id, lookup, record
        )

    def _look_up(
        self, country: str, tax_id_type: str, tax_id: str
    ) -> tuple[LookupOutcome, CompanyRecord | None]:
        registry = self._registry_for(country)
        if registry is None:
            return LookupOutcome.OFF, None
        try:
            record = registry.lookup(tax_id_type, tax_id)
        except RegistryUnavailable:
            return LookupOutcome.UNAVAILABLE, None
        if record is None:
            return LookupOutcome.NOT_FOUND, None
        if not record.public:
            return LookupOutcome.NOT_PUBLIC, record
        return LookupOutcome.FOUND, record


# Signs a user into a workspace host after signup or login on the root domain.
# Session cookies do not cross hosts, so the root domain hands over a signed,
# single-use token valid for one minute. Only a hash of its nonce is stored.
HANDOFF_SALT = "apps.tenants.handoff"
HANDOFF_MAX_AGE_SECONDS = 60


def _nonce_key(nonce: str) -> str:
    return "handoff:" + hashlib.sha256(nonce.encode()).hexdigest()


class IssueHandoff:
    def __init__(self, *, cache: BaseCache) -> None:
        self._cache = cache

    def __call__(self, *, user_id: int, tenant_id: int) -> str:
        nonce = secrets.token_urlsafe(16)
        # Cache keys carry the schema: both ends use the public one.
        with schema_context(get_public_schema_name()):
            self._cache.set(_nonce_key(nonce), True, HANDOFF_MAX_AGE_SECONDS)
        return signing.dumps(
            {"u": user_id, "t": tenant_id, "n": nonce}, salt=HANDOFF_SALT
        )


class RedeemHandoff:
    def __init__(self, *, cache: BaseCache) -> None:
        self._cache = cache

    def __call__(self, token: str, *, tenant_id: int) -> int | None:
        """The user id if the token is genuine, fresh, unused and for this workspace."""
        try:
            data = signing.loads(
                token, salt=HANDOFF_SALT, max_age=HANDOFF_MAX_AGE_SECONDS
            )
        except signing.BadSignature:  # also covers SignatureExpired
            return None
        if data.get("t") != tenant_id:
            return None
        with schema_context(get_public_schema_name()):
            if not self._cache.delete(_nonce_key(str(data.get("n")))):
                return None  # already used
        return int(data["u"])
