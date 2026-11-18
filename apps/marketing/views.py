from typing import Any

from django.conf import settings
from django.http import HttpRequest, HttpResponse
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.views.generic import FormView
from django_ratelimit.decorators import ratelimit

from .forms import WaitlistForm
from .services import JoinWaitlist, WaitlistClosedError, WaitlistProduct
from .tasks import subscribe_to_waitlist


def _waitlist_rate(group: str, request: HttpRequest) -> str:
    return settings.WAITLIST_RATE_LIMIT


@method_decorator(
    ratelimit(key="ip", rate=_waitlist_rate, method="POST", block=True), name="post"
)
class LandingView(FormView):
    template_name = "marketing/landing.html"
    form_class = WaitlistForm

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        return super().get_context_data(
            waitlist_open=settings.WAITLIST_ENABLED,
            joined="joined" in self.request.GET,
            **kwargs,
        )

    def form_valid(self, form: WaitlistForm) -> HttpResponse:
        if not form.is_spam:
            join = JoinWaitlist(
                enabled=settings.WAITLIST_ENABLED,
                enqueue=subscribe_to_waitlist.delay,
            )
            try:
                join(
                    form.cleaned_data["email"],
                    WaitlistProduct(form.cleaned_data["product"]),
                )
            except WaitlistClosedError:
                return self.render_to_response(self.get_context_data(form=form))
        return super().form_valid(form)

    def get_success_url(self) -> str:
        return reverse("home") + "?joined=1"
