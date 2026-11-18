from django.conf import settings

from apps.accounts.models import User
from apps.accounts.repositories import UserRepository


class SetPreferredLanguage:
    def __init__(self, *, users: UserRepository) -> None:
        self._users = users

    def __call__(self, user: User, code: str) -> None:
        if code not in dict(settings.LANGUAGES):
            return
        self._users.set_language(user, code)
