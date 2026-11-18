from django.http import HttpRequest, HttpResponse
from django.shortcuts import render
from django_ratelimit.exceptions import Ratelimited


def ratelimited(request: HttpRequest, exception: Ratelimited) -> HttpResponse:
    """RATELIMIT_VIEW: django-ratelimit blocks get the same page as allauth's limits."""
    return render(request, "429.html", status=429)
