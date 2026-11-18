from collections.abc import Callable

from django.conf import settings
from django.http import HttpRequest, HttpResponse
from django.utils import translation


class UserLanguageMiddleware:
    """A signed-in user's saved language beats the cookie and the browser.

    Runs after AuthenticationMiddleware; LocaleMiddleware has already picked a
    language for anonymous visitors, which this leaves alone.
    """

    def __init__(self, get_response: Callable[[HttpRequest], HttpResponse]) -> None:
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        user = getattr(request, "user", None)
        language = getattr(user, "language", "")
        if user is not None and user.is_authenticated and language:
            if language in dict(settings.LANGUAGES):
                translation.activate(language)
                request.LANGUAGE_CODE = language
        return self.get_response(request)
