"""Replace the cookiecutter's hard-coded example.com with SITE_DOMAIN.

0003 is committed and must not be edited, so this fixes forward. allauth prints the
site domain in its emails ("...on example.com").
"""

from django.conf import settings
from django.db import migrations

PREVIOUS_DOMAIN = "example.com"
SITE_NAME = "Modular SaaS"


def set_domain_from_settings(apps, schema_editor):
    Site = apps.get_model("sites", "Site")
    Site.objects.filter(id=settings.SITE_ID).update(
        domain=settings.SITE_DOMAIN, name=SITE_NAME
    )


def restore_previous_domain(apps, schema_editor):
    Site = apps.get_model("sites", "Site")
    Site.objects.filter(id=settings.SITE_ID).update(
        domain=PREVIOUS_DOMAIN, name=SITE_NAME
    )


class Migration(migrations.Migration):
    dependencies = [("sites", "0004_alter_options_ordering_domain")]

    operations = [
        migrations.RunPython(set_domain_from_settings, restore_previous_domain)
    ]
