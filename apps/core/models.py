"""Abstract base models. Tenant isolation comes from django-tenants schemas, not a FK."""

from __future__ import annotations

import uuid
from datetime import datetime

from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _


class UUIDPrimaryKey(models.Model):
    # UUIDv7 is time-ordered, so inserts stay at the end of the index.
    id = models.UUIDField(primary_key=True, default=uuid.uuid7, editable=False)

    class Meta:
        abstract = True


class TimeStamped(models.Model):
    created_at = models.DateTimeField(_("created at"), auto_now_add=True)
    updated_at = models.DateTimeField(_("updated at"), auto_now=True)

    class Meta:
        abstract = True


class AliveManager[M: models.Model](models.Manager[M]):
    def get_queryset(self) -> models.QuerySet[M]:
        return super().get_queryset().filter(deleted_at__isnull=True)


class SoftDelete(models.Model):
    """Hidden from `objects`, kept in `all_objects`. `delete()` still deletes for real."""

    deleted_at = models.DateTimeField(
        _("deleted at"), null=True, blank=True, editable=False, db_index=True
    )

    objects = AliveManager()
    all_objects = models.Manager()

    class Meta:
        abstract = True

    @property
    def is_deleted(self) -> bool:
        return self.deleted_at is not None

    def soft_delete(self, *, at: datetime) -> None:
        self.deleted_at = at
        self.save(update_fields=["deleted_at"])

    def restore(self) -> None:
        self.deleted_at = None
        self.save(update_fields=["deleted_at"])


class CreatedBy(models.Model):
    # related_name="+": many models share this field; no reverse accessor clashes.
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name=_("created by"),
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
        editable=False,
    )

    class Meta:
        abstract = True


class Ordered(models.Model):
    position = models.PositiveIntegerField(_("position"), default=0, db_index=True)

    class Meta:
        abstract = True
        ordering = ["position"]
