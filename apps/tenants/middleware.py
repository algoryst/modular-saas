from collections.abc import Callable

from django.conf import settings
from django.http import HttpRequest, HttpResponse
from django.shortcuts import render
from django_tenants.utils import get_public_schema_name

from apps.tenants.repositories import TenantRepository


class WorkspaceMembershipMiddleware:
    """On a workspace host, a signed-in user must be a member of that workspace.

    Users are shared across workspaces, so being signed in proves nothing about this
    one. Anonymous visitors pass through to the usual sign-in redirect.
    """

    def __init__(self, get_response: Callable[[HttpRequest], HttpResponse]) -> None:
        self.get_response = get_response
        self.tenants = TenantRepository()

    def __call__(self, request: HttpRequest) -> HttpResponse:
        tenant = getattr(request, "tenant", None)
        user = getattr(request, "user", None)
        if (
            tenant is not None
            and tenant.schema_name != get_public_schema_name()
            and user is not None
            and user.is_authenticated
            and not self.tenants.is_member(user.pk, tenant.pk)
        ):
            root_url = f"{request.scheme}://{settings.SITE_DOMAIN}/"
            return render(
                request, "tenants/no_access.html", {"root_url": root_url}, status=403
            )
        return self.get_response(request)
