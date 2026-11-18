"""Abstract base models, exercised through throwaway concrete models.

The models below are unmanaged and never imported by Django itself, so they get no
migrations; the fixture creates their tables inside the test transaction, and
Postgres rolls the DDL back with it.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import ClassVar

import pytest
from django.contrib.auth import get_user_model
from django.db import connection, models
from freezegun import freeze_time

from apps.core.models import (
    AliveManager,
    CreatedBy,
    Ordered,
    SoftDelete,
    TimeStamped,
    UUIDPrimaryKey,
)

NOON = datetime(2026, 11, 18, 12, 0, tzinfo=UTC)

pytestmark = pytest.mark.django_db


# Explicit managers: the django-stubs plugin only knows models from INSTALLED_APPS.
class Note(UUIDPrimaryKey, TimeStamped, SoftDelete, CreatedBy):
    text = models.CharField(max_length=50)

    # The plugin types the inherited manager as AliveManager[Self] for unknown models.
    objects: AliveManager[Note] = AliveManager()  # type: ignore[assignment]
    all_objects: models.Manager[Note] = models.Manager()

    class Meta:
        app_label = "core"
        managed = False


class Step(Ordered):
    name = models.CharField(max_length=50)

    objects: ClassVar[models.Manager[Step]] = models.Manager()

    class Meta(Ordered.Meta):
        app_label = "core"
        managed = False


@pytest.fixture(autouse=True)
def _tables():
    with connection.schema_editor() as editor:
        editor.create_model(Note)
        editor.create_model(Step)


class TestUUIDPrimaryKey:
    def test_uuid_primary_key_is_version_7(self):
        note = Note.objects.create(text="a")

        assert note.pk.version == 7

    def test_uuid_primary_keys_sort_by_creation(self):
        first = Note.objects.create(text="a")
        second = Note.objects.create(text="b")

        assert first.pk < second.pk


class TestTimeStamped:
    def test_timestamps_set_on_create_and_update(self):
        with freeze_time(NOON) as clock:
            note = Note.objects.create(text="a")
            clock.tick(timedelta(hours=1))
            note.text = "b"
            note.save()

        note.refresh_from_db()
        assert note.created_at == NOON
        assert note.updated_at == NOON + timedelta(hours=1)


class TestSoftDelete:
    def test_soft_deleted_rows_hidden_from_default_manager(self):
        kept = Note.objects.create(text="kept")
        gone = Note.objects.create(text="gone")

        gone.soft_delete(at=NOON)

        assert list(Note.objects.all()) == [kept]
        assert set(Note.all_objects.all()) == {kept, gone}
        assert Note.all_objects.get(pk=gone.pk).deleted_at == NOON

    def test_restore_brings_row_back(self):
        note = Note.objects.create(text="a")
        note.soft_delete(at=NOON)

        note.restore()

        assert Note.objects.filter(pk=note.pk).exists()
        assert not note.is_deleted


class TestCreatedBy:
    def test_created_by_is_cleared_when_user_is_deleted(self):
        # get_user_model, not the accounts factory: core imports no feature app.
        user = get_user_model().objects.create_user(email="author@example.fr")
        note = Note.objects.create(text="a", created_by=user)

        user.delete()

        note.refresh_from_db()
        assert note.created_by is None


class TestOrdered:
    def test_ordered_models_come_back_by_position(self):
        Step.objects.create(name="third", position=3)
        Step.objects.create(name="first", position=1)
        Step.objects.create(name="second", position=2)

        assert [s.name for s in Step.objects.all()] == ["first", "second", "third"]
