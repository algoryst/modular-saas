"""Migrations added since the initial schema run forward and backward cleanly."""

import pytest
from django.db import connection
from django.db.migrations.executor import MigrationExecutor

pytestmark = pytest.mark.django_db(transaction=True)


def _migrate(*targets: tuple[str, str]):
    executor = MigrationExecutor(connection)
    executor.loader.build_graph()
    executor.migrate(list(targets))
    executor.loader.build_graph()
    return executor.loader.project_state(list(targets)).apps


def _columns(table: str) -> set[str]:
    with connection.cursor() as cursor:
        return {
            c.name
            for c in connection.introspection.get_table_description(cursor, table)
        }


LANGUAGE = ("accounts", "0002_user_language")
BEFORE_LANGUAGE = ("accounts", "0001_initial")
SITE_DOMAIN = ("sites", "0005_set_site_domain_from_settings")
BEFORE_SITE_DOMAIN = ("sites", "0004_alter_options_ordering_domain")


@pytest.fixture(autouse=True)
def _back_to_latest():
    yield
    executor = MigrationExecutor(connection)
    executor.migrate(executor.loader.graph.leaf_nodes())


def test_user_language_migration_forward_and_backward():
    _migrate(BEFORE_LANGUAGE)
    assert "language" not in _columns("accounts_user")

    _migrate(LANGUAGE)
    assert "language" in _columns("accounts_user")

    _migrate(BEFORE_LANGUAGE)
    assert "language" not in _columns("accounts_user")


def _site_domain(apps, site_id: int) -> str:
    return apps.get_model("sites", "Site").objects.get(id=site_id).domain


def test_site_domain_migration_uses_setting_and_reverts(settings):
    settings.SITE_DOMAIN = "app.example.fr"

    apps = _migrate(BEFORE_SITE_DOMAIN)
    assert _site_domain(apps, settings.SITE_ID) == "example.com"

    apps = _migrate(SITE_DOMAIN)
    assert _site_domain(apps, settings.SITE_ID) == "app.example.fr"

    apps = _migrate(BEFORE_SITE_DOMAIN)
    assert _site_domain(apps, settings.SITE_ID) == "example.com"
