from apps.accounts.models import User


class UserRepository:
    def set_language(self, user: User, code: str) -> None:
        User.objects.filter(pk=user.pk).update(language=code)
        user.language = code
