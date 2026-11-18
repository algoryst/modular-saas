from django.test import RequestFactory
from django_ratelimit.exceptions import Ratelimited

from apps.core.views import ratelimited


def test_ratelimited_renders_wait_page_with_429(rf: RequestFactory):
    request = rf.post("/somewhere/")

    response = ratelimited(request, Ratelimited())

    assert response.status_code == 429
    assert 'href="/somewhere/"' in response.content.decode()
