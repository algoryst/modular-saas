from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from django.db import transaction
from django.utils.text import slugify

from apps.core.clock import Clock
from apps.core.events import EventBus, WorkspaceCreated
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
