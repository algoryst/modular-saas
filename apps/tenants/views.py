from __future__ import annotations

from typing import Any

from allauth.account.views import SignupView
from django.conf import settings
from django.contrib.auth import login
from django.contrib.auth.base_user import AbstractBaseUser
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.cache import cache
from django.http import HttpRequest, HttpResponse, HttpResponseRedirect
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.views import View
from django.views.generic import FormView, TemplateView
from django_ratelimit.decorators import ratelimit
from django_tenants.utils import get_public_schema_name

from apps.core.clock import SystemClock
from apps.core.events import bus
from apps.countrypacks.registry import get_pack
from apps.tenants.forms import (
    PENDING_WORKSPACE,
    SIGNUP_COMPANY,
    CompanyForm,
    WorkspaceNameForm,
)
from apps.tenants.models import Tenant
from apps.tenants.repositories import TenantRepository
from apps.tenants.services import (
    CheckCompany,
    CompanyCheck,
    CreateTenant,
    IssueHandoff,
    LookupOutcome,
    NewWorkspace,
    RedeemHandoff,
    TaxIdentityTakenError,
    taken_message,
)


class WorkspaceHomeView(LoginRequiredMixin, TemplateView):
    """Landing page inside a workspace until the W7 dashboard replaces it."""

    template_name = "tenants/home.html"


def _workspace_of(request: HttpRequest) -> Tenant | None:
    """The workspace this host serves; None on the root domain.

    TenantMainMiddleware sets request.tenant, except for hosts without a Domain
    (SHOW_PUBLIC_IF_NO_TENANT_FOUND), which it serves as the root domain.
    """
    tenant: Tenant | None = getattr(request, "tenant", None)
    if tenant is None or tenant.schema_name == get_public_schema_name():
        return None
    return tenant


def _signed_in(request: HttpRequest) -> AbstractBaseUser:
    user = request.user
    # mypy type guard; LoginRequiredMixin already rejects anonymous users.
    assert user.is_authenticated  # nosec B101
    return user


def _root_url(request: HttpRequest, path: str = "/") -> str:
    return f"{request.scheme}://{settings.SITE_DOMAIN}{path}"


class RootDomainOnlyMixin(View):
    """Signup and workspace switching happen on the root domain, never a workspace."""

    def dispatch(self, request: HttpRequest, *args: Any, **kwargs: Any) -> Any:
        if _workspace_of(request) is not None:
            return HttpResponseRedirect(_root_url(request, request.path))
        return super().dispatch(request, *args, **kwargs)


class CompanyInSessionMixin(View):
    """Steps after the company step: send people back if they skipped it."""

    def dispatch(self, request: HttpRequest, *args: Any, **kwargs: Any) -> Any:
        if SIGNUP_COMPANY not in request.session:
            return redirect("tenants:signup")
        return super().dispatch(request, *args, **kwargs)

    def get_initial(self) -> dict[str, Any]:
        return {"company_name": self.request.session[SIGNUP_COMPANY]["name"]}

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        # get_context_data comes from the FormView this mixin is combined with.
        parent: Any = super()
        context: dict[str, Any] = parent.get_context_data(**kwargs)
        context["company"] = self.request.session[SIGNUP_COMPANY]
        return context


def _create_tenant() -> CreateTenant:
    return CreateTenant(
        tenants=TenantRepository(),
        root_domain=settings.SITE_DOMAIN.split(":")[0],
        unique_tax_id=settings.TENANT_UNIQUE_TAX_ID,
        events=bus,
        clock=SystemClock(),
    )


def _handoff(request: HttpRequest, tenant: Tenant) -> HttpResponseRedirect:
    """Sign the current user into `tenant`'s host with a one-minute token."""
    user_id = _signed_in(request).pk
    token = IssueHandoff(cache=cache)(user_id=user_id, tenant_id=tenant.pk)
    host = TenantRepository().primary_domain(tenant)
    _, _, port = settings.SITE_DOMAIN.partition(":")
    origin = f"{request.scheme}://{host}" + (f":{port}" if port else "")
    return HttpResponseRedirect(f"{origin}{reverse('tenants:handoff')}?token={token}")


def _company_session(result: CompanyCheck) -> dict[str, Any]:
    record = result.record if result.lookup is LookupOutcome.FOUND else None
    return {
        "country": result.country,
        "tax_id_type": result.tax_id_type,
        "tax_id": result.tax_id,
        "lookup": str(result.lookup),
        "name": record.legal_name if record else "",
        "address": (
            [*record.address_lines, f"{record.postcode} {record.city}"]
            if record
            else []
        ),
    }


def _lookup_rate(group: str, request: HttpRequest) -> str:
    return str(settings.SIGNUP_LOOKUP_RATE_LIMIT)


@method_decorator(
    ratelimit(key="ip", rate=_lookup_rate, method="POST", block=True), name="post"
)
class CompanySignupView(RootDomainOnlyMixin, FormView):
    """Step 1: the company number, checked and looked up in the official register."""

    template_name = "tenants/signup_company.html"
    form_class = CompanyForm

    def dispatch(self, request: HttpRequest, *args: Any, **kwargs: Any) -> Any:
        if (
            not settings.ACCOUNT_ALLOW_REGISTRATION
            and not request.user.is_authenticated
        ):
            return render(request, "account/signup_closed.html")
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form: CompanyForm) -> HttpResponse:
        country = form.cleaned_data["country"]
        result = CheckCompany(
            tenants=TenantRepository(),
            unique_tax_id=settings.TENANT_UNIQUE_TAX_ID,
            registry_for=lambda code: get_pack(code).company_registry(),
        )(
            country,
            get_pack(country).tax_identity_types()[0].code,
            form.cleaned_data["tax_id"],
        )
        if not result.ok:
            form.add_error("tax_id", result.error)
            return self.form_invalid(form)
        self.request.session[SIGNUP_COMPANY] = _company_session(result)
        if self.request.user.is_authenticated:
            return redirect("tenants:create")
        return redirect("account_signup")


class WorkspaceSignupView(RootDomainOnlyMixin, CompanyInSessionMixin, SignupView):
    """Step 2: confirm the company, then email and password (allauth)."""


class CreateWorkspaceView(
    RootDomainOnlyMixin, LoginRequiredMixin, CompanyInSessionMixin, FormView
):
    """A signed-in user adds a workspace (the company step already ran)."""

    template_name = "tenants/create_workspace.html"
    form_class = WorkspaceNameForm

    def form_valid(self, form: WorkspaceNameForm) -> HttpResponse:
        company = self.request.session[SIGNUP_COMPANY]
        workspace = NewWorkspace(
            name=form.cleaned_data["company_name"],
            country=company["country"],
            tax_id_type=company["tax_id_type"],
            tax_id=company["tax_id"],
        )
        try:
            tenant = _create_tenant()(_signed_in(self.request), workspace)
        except TaxIdentityTakenError:
            form.add_error(None, taken_message())
            return self.form_invalid(form)
        del self.request.session[SIGNUP_COMPANY]
        return _handoff(self.request, tenant)


class GoToWorkspaceView(RootDomainOnlyMixin, LoginRequiredMixin, View):
    """After login or email verification: create the pending workspace, or pick one."""

    def get(self, request: HttpRequest) -> HttpResponse:
        pending = request.session.pop(PENDING_WORKSPACE, None)
        if pending is not None:
            return self._create_pending(request, pending)
        memberships = TenantRepository().memberships_for(_signed_in(request).pk)
        if len(memberships) == 1:
            return _handoff(request, memberships[0].tenant)
        template = "tenants/picker.html" if memberships else "tenants/no_workspace.html"
        return render(request, template, {"memberships": memberships})

    def _create_pending(
        self, request: HttpRequest, pending: dict[str, Any]
    ) -> HttpResponse:
        workspace = NewWorkspace(
            pending["name"],
            pending["country"],
            pending["tax_id_type"],
            pending["tax_id"],
        )
        try:
            tenant = _create_tenant()(_signed_in(request), workspace)
        except TaxIdentityTakenError:
            # Someone registered the same company between the two steps.
            return render(request, "tenants/no_workspace.html", {"taken": True})
        request.session.pop(SIGNUP_COMPANY, None)
        return _handoff(request, tenant)


class OpenWorkspaceView(RootDomainOnlyMixin, LoginRequiredMixin, View):
    def get(self, request: HttpRequest, pk: int) -> HttpResponse:
        membership = TenantRepository().membership(_signed_in(request).pk, pk)
        if membership is None:
            return render(request, "tenants/no_workspace.html", status=404)
        return _handoff(request, membership.tenant)


class HandoffView(View):
    """On a workspace host: exchange the one-minute token for a session."""

    def get(self, request: HttpRequest) -> HttpResponse:
        tenant = _workspace_of(request)
        token = request.GET.get("token", "")
        user_id = (
            RedeemHandoff(cache=cache)(token, tenant_id=tenant.pk) if tenant else None
        )
        membership = (
            TenantRepository().membership(user_id, tenant.pk)
            if tenant and user_id
            else None
        )
        if membership is None:
            login_url = _root_url(request, reverse("account_login"))
            return render(
                request,
                "tenants/handoff_expired.html",
                {"login_url": login_url},
                status=400,
            )
        login(
            request,
            membership.user,
            backend="django.contrib.auth.backends.ModelBackend",
        )
        return redirect("home")
