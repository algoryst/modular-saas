"""Workspaces. These tables live in the public schema, next to users.

Business data never goes here: it lives in each workspace's own schema.
"""

from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _
from django_tenants.models import DomainMixin, TenantMixin

from apps.core.models import TimeStamped
from apps.countrypacks.models import TaxIdentity


class Tenant(TenantMixin, TaxIdentity, TimeStamped):
    name = models.CharField(_("name"), max_length=200)
    # Defaults come from the country pack at creation; editable per workspace.
    timezone = models.CharField(_("time zone"), max_length=64)
    currency = models.CharField(_("currency"), max_length=3)

    # Schemas are created by CreateTenant; they are never dropped implicitly.
    auto_create_schema = True
    auto_drop_schema = False

    class Meta:
        verbose_name = _("workspace")
        verbose_name_plural = _("workspaces")
        indexes = [models.Index(fields=["tax_country", "tax_id_type", "tax_id"])]

    def __str__(self) -> str:
        return self.name


# models.Model listed explicitly: DomainMixin is untyped (Any to mypy), so without
# it the django-stubs plugin does not treat Domain as a model.
class Domain(DomainMixin, models.Model):
    # Redeclared from DomainMixin so type checkers see the Tenant relation.
    tenant = models.ForeignKey(
        Tenant,
        verbose_name=_("workspace"),
        db_index=True,
        related_name="domains",
        on_delete=models.CASCADE,
    )

    class Meta:
        verbose_name = _("domain")
        verbose_name_plural = _("domains")


class Membership(TimeStamped):
    """A user's place in a workspace. W3 adds invitations and permissions."""

    class Role(models.TextChoices):
        OWNER = "owner", _("Owner")
        ADMIN = "admin", _("Admin")
        MEMBER = "member", _("Member")

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name=_("user"),
        on_delete=models.CASCADE,
        related_name="memberships",
    )
    tenant = models.ForeignKey(
        Tenant,
        verbose_name=_("workspace"),
        on_delete=models.CASCADE,
        related_name="memberships",
    )
    role = models.CharField(_("role"), max_length=10, choices=Role.choices)

    class Meta:
        verbose_name = _("membership")
        verbose_name_plural = _("memberships")
        constraints = [
            models.UniqueConstraint(
                fields=["user", "tenant"], name="unique_membership_per_workspace"
            )
        ]

    def __str__(self) -> str:
        return f"{self.user} @ {self.tenant} ({self.role})"
