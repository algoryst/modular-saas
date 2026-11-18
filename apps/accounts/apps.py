from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class AccountsConfig(AppConfig):
    name = "apps.accounts"
    verbose_name = _("Accounts")

    def ready(self):
        """
        Override this method in subclasses to run code when Django starts.
        """
