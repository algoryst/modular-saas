from celery import shared_task
from django.conf import settings

from .adapters import (
    BrevoWaitlistProvider,
    WaitlistProvider,
    WaitlistProviderUnavailable,
)
from .services import SubscribeToWaitlist, WaitlistProduct


def _provider() -> WaitlistProvider:
    return BrevoWaitlistProvider(
        api_key=settings.BREVO_API_KEY,
        api_url=settings.BREVO_API_URL,
        template_id=settings.BREVO_DOI_TEMPLATE_ID,
        redirect_url=settings.WAITLIST_CONFIRMED_URL,
    )


# The waitlist belongs to the public marketing site, not to any tenant, so this task
# takes no tenant identifier and sets no tenant context.
@shared_task(
    autoretry_for=(WaitlistProviderUnavailable,),
    retry_backoff=True,
    max_retries=5,
)
def subscribe_to_waitlist(email: str, product: str) -> None:
    subscribe = SubscribeToWaitlist(
        provider=_provider(),
        list_ids={
            WaitlistProduct.SAAS: settings.BREVO_WAITLIST_LIST_SAAS,
            WaitlistProduct.BOILERPLATE: settings.BREVO_WAITLIST_LIST_BOILERPLATE,
        },
    )
    subscribe(email, WaitlistProduct(product))
