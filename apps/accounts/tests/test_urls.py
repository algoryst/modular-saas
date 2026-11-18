from __future__ import annotations

from typing import TYPE_CHECKING

from django.urls import resolve, reverse

if TYPE_CHECKING:
    from apps.accounts.models import User


def test_detail(user: User):
    assert reverse("accounts:detail", kwargs={"pk": user.pk}) == f"/users/{user.pk}/"
    assert resolve(f"/users/{user.pk}/").view_name == "accounts:detail"


def test_update():
    assert reverse("accounts:update") == "/users/~update/"
    assert resolve("/users/~update/").view_name == "accounts:update"


def test_redirect():
    assert reverse("accounts:redirect") == "/users/~redirect/"
    assert resolve("/users/~redirect/").view_name == "accounts:redirect"
