from django.contrib import messages
from django.contrib.auth import REDIRECT_FIELD_NAME
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _
from rest_framework.views import APIView


class PasswordExpirationMiddleware:
    exempted_url_names = [
        "account_change_password",
        "admin:logout",
        "account_logout",
        "account_reset_password",
        "account_reset_password_done",
        "account_reset_password_from_key",
        "account_reset_password_from_key_done",
    ]
    admin_login_path = reverse_lazy("admin:login")
    admin_index_path = reverse_lazy("admin:index")
    account_change_password_path = reverse_lazy("account_change_password")

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        # Check if the user is authenticated and their password has expired
        if not (request.user.is_authenticated and request.user.has_password_expired()):
            return response
        # `request.resolver_match` is already populated by Django while handling
        # the request, no need to call `resolve()` again (which would raise
        # `Resolver404` for genuinely unmatched paths).
        url_match = request.resolver_match
        if url_match is None:
            return response
        # DRF sets `cls` on the view function returned by `APIView.as_view()`,
        # regular Django views don't have this attribute, so this reliably
        # tells apart API requests, which must not be redirected to an HTML
        # page since API clients expect a proper API response.
        is_api_request = issubclass(getattr(url_match.func, "cls", object), APIView)
        if not is_api_request and url_match.url_name not in self.exempted_url_names:
            messages.warning(
                request,
                _("Your password has expired, please update your password."),
            )
            redirect_path = self.account_change_password_path
            if request.user.is_staff:
                next_path = (
                    request.path
                    if request.path != self.admin_login_path
                    else self.admin_index_path
                )
                redirect_path = f"{redirect_path}?{REDIRECT_FIELD_NAME}={next_path}"
            return redirect(redirect_path)
        return response
