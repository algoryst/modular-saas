"""TaxIdentity is abstract: Tenant (public schema) and Company (tenant schemas)
inherit it, so the public schema keeps holding only Tenant and Domain.
"""

from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.countrypacks.registry import get_pack


class TaxIdentity(models.Model):
    tax_country = models.CharField(_("country"), max_length=10)
    tax_id_type = models.CharField(_("identifier type"), max_length=20)
    # Stored normalised (no spaces), as the country pack returns it.
    tax_id = models.CharField(_("identifier"), max_length=32)

    class Meta:
        abstract = True

    def clean(self) -> None:
        super().clean()
        self.tax_country = self.tax_country.strip().lower()
        result = get_pack(self.tax_country).validate_tax_identity(
            self.tax_id_type, self.tax_id
        )
        if not result.valid:
            raise ValidationError({"tax_id": result.error})
        self.tax_id = result.normalized
