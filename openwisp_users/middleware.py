from django.contrib import messages
from django.contrib.auth import REDIRECT_FIELD_NAME
from django.contrib.auth import SESSION_KEY as AUTH_SESSION_KEY
from django.shortcuts import redirect
from django.urls import resolve, reverse_lazy
from django.urls.exceptions import Resolver404
from django.utils.translation import gettext_lazy as _
from rest_framework.renderers import JSONRenderer
from rest_framework.response import Response
from rest_framework.views import APIView

from .auth import (
    ACCOUNT_CHANGE_PASSWORD_PATH,
    API_PASSWORD_CHANGE_URL_NAME,
    is_password_based_login,
    password_expired_response_payload,
)


class PasswordExpirationMiddleware:
    """
    Blocks requests from authenticated users whose local password has
    expired, redirecting HTML requests to the password-change page and
    returning a JSON 403 for DRF requests instead.

    Only sessions authenticated with a local password are enforced
    (``is_password_based_login``): SSO/SAML/OAuth sessions are exempt even if
    the local password has technically expired.
    """

    exempted_url_names = [
        "account_change_password",
        "admin:logout",
        "account_logout",
        "account_reset_password",
        "account_reset_password_done",
        "account_reset_password_from_key",
        "account_reset_password_from_key_done",
        API_PASSWORD_CHANGE_URL_NAME,
        "users:user_password_reset",
        "users:user_password_reset_confirm",
        "users:user_auth_token",
    ]
    admin_login_path = reverse_lazy("admin:login")
    admin_index_path = reverse_lazy("admin:index")

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        session_authenticated_before = AUTH_SESSION_KEY in request.session
        if session_authenticated_before and self._is_expired_password_session(request):
            blocked = self._blocked_response(request)
            if blocked is not None:
                return blocked
        response = self.get_response(request)
        if (
            not session_authenticated_before
            and AUTH_SESSION_KEY in request.session
            and self._is_expired_password_session(request)
        ):
            blocked = self._blocked_response(request)
            if blocked is not None:
                return blocked
        return response

    def _is_expired_password_session(self, request):
        return (
            request.user.is_authenticated
            and request.user.has_password_expired()
            and is_password_based_login(request)
        )

    def _blocked_response(self, request):
        try:
            resolver_match = resolve(request.path_info)
        except Resolver404:
            return None
        if (
            resolver_match.url_name in self.exempted_url_names
            or resolver_match.view_name in self.exempted_url_names
        ):
            return None
        view_class = getattr(resolver_match.func, "cls", None)
        if view_class is not None and issubclass(view_class, APIView):
            return self._rest_response(request)
        return self._html_response(request)

    def _html_response(self, request):
        messages.warning(
            request,
            _("Your password has expired, please update your password."),
        )
        redirect_path = ACCOUNT_CHANGE_PASSWORD_PATH
        if request.user.is_staff:
            next_path = (
                request.path
                if request.path != self.admin_login_path
                else self.admin_index_path
            )
            redirect_path = f"{redirect_path}?{REDIRECT_FIELD_NAME}={next_path}"
        return redirect(redirect_path)

    def _rest_response(self, request):
        response = Response(password_expired_response_payload(request), status=403)
        response.accepted_renderer = JSONRenderer()
        response.accepted_media_type = "application/json"
        response.renderer_context = {}
        response.render()
        return response
