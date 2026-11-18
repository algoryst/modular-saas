"""The abstract TaxIdentity model, through a throwaway concrete model (no table needed)."""

import pytest
from django.core.exceptions import ValidationError
from django.db import models

from apps.countrypacks.models import TaxIdentity


class Business(TaxIdentity):
    class Meta:
        app_label = "countrypacks"
        managed = False


def test_tax_identity_clean_normalizes_valid_identifier():
    business = Business(
        tax_country="FR", tax_id_type="siret", tax_id="732 829 320 00074"
    )

    business.clean()

    assert business.tax_id == "73282932000074"
    assert business.tax_country == "fr"


def test_tax_identity_clean_rejects_invalid_identifier_on_the_field():
    business = Business(tax_country="fr", tax_id_type="siret", tax_id="73282932000075")

    with pytest.raises(ValidationError) as excinfo:
        business.clean()

    assert "tax_id" in excinfo.value.message_dict


def test_tax_identity_unknown_country_uses_generic_rules():
    business = Business(tax_country="zz", tax_id_type="tax_id", tax_id="  AB-12 ")

    business.clean()

    assert business.tax_id == "AB-12"


def test_tax_identity_fields_are_abstract():
    assert TaxIdentity._meta.abstract
    assert {f.name for f in Business._meta.get_fields()} >= {
        "tax_country",
        "tax_id_type",
        "tax_id",
    }
    assert isinstance(Business._meta.get_field("tax_id"), models.CharField)
