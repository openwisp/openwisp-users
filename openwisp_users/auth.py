from django.contrib.auth import SESSION_KEY as AUTH_SESSION_KEY
from django.contrib.auth import get_user_model
from django.urls import reverse, reverse_lazy
from django.utils.translation import gettext_lazy as _

from . import settings as app_settings

SESSION_KEY = "openwisp_password_based_login"
SESAME_BACKEND = "sesame.backends.ModelBackend"

# Used by PasswordExpirationMiddleware to know where to redirect
# when a user's password has expired.
ACCOUNT_CHANGE_PASSWORD_PATH = reverse_lazy("account_change_password")
# OpenWISP Users API can be disabled using the OPENWISP_USERS_AUTH_API setting.
# We avoid using reverse_lazy here because it would raise an exception if the API is
# disabled.
API_PASSWORD_CHANGE_URL_NAME = "users:user_password_change"


def _session_provenance(request):
    """
    Return the session's password marker, or ``None`` when unavailable.

    Unmarked sessions remain password-based for backward compatibility.
    """
    session = getattr(request, "session", None)
    if session is None or AUTH_SESSION_KEY not in session:
        return None
    return session.get(SESSION_KEY) is not False


def _is_sesame_request(request, user):
    from .api.authentication import SesameAuthentication

    return isinstance(
        getattr(request, "successful_authenticator", None), SesameAuthentication
    ) or (getattr(user, "backend", "") == SESAME_BACKEND)


def _is_password_based_request(request, user):
    """Return whether the request used the local password."""
    request_user = getattr(request, "user", None)
    if request_user is None or request_user.is_anonymous or request_user != user:
        # No matching request user means the caller supplied local credentials.
        return True
    if _is_sesame_request(request, request_user):
        return False
    return _session_provenance(request) is not False


def create_auth_token(request, user=None, renew=False):
    """
    Create or renew a DRF token and record whether it used the local password.

    ``renew=True`` replaces the existing token. Persisting provenance on the
    user lets stateless requests classify the token after the session is gone.
    """
    from rest_framework.authtoken.models import Token

    user = user if user is not None else getattr(request, "user", None)
    if user is None or not user.is_authenticated:
        return None
    if renew:
        Token.objects.filter(user=user).delete()
    token, _created = Token.objects.get_or_create(user=user)
    password_based = _is_password_based_request(request, user)
    user.password_based_token = password_based
    get_user_model().objects.filter(pk=user.pk).update(
        password_based_token=password_based
    )
    return token


def is_password_based_user(user):
    """
    Return whether the user's last token used the local password.

    Unset provenance is treated as password-based for backward compatibility.
    """
    return getattr(user, "password_based_token", None) is not False


def record_password_based_login(request, password_based):
    """
    Record on the session whether the user logged in with the local password.
    """
    request.session[SESSION_KEY] = password_based


def is_password_based_login(request=None, user=None):
    """
    Return whether the local password was used to authenticate.

    Check DRF token provenance first, then the session marker, and finally the
    user's stored value. Missing provenance remains password-based for backward
    compatibility.
    """
    from rest_framework.authtoken.models import Token

    token = getattr(request, "auth", None)
    if isinstance(token, Token):
        return is_password_based_user(token.user)
    provenance = _session_provenance(request)
    if provenance is not None:
        return provenance
    return is_password_based_user(
        user if user is not None else getattr(request, "user", None)
    )


def password_expired_response_payload(request):
    """
    Return the standard payload for password-expired authentication errors.

    The payload is shared by all authentication entry points so password
    expiration is reported consistently. Callers are responsible for wrapping
    it in a JsonResponse or DRF Response and setting the HTTP status code.
    """
    payload = {
        "detail": _("Your password has expired. Update it to continue."),
        "code": "password_expired",
        "web_password_change_url": request.build_absolute_uri(
            str(ACCOUNT_CHANGE_PASSWORD_PATH)
        ),
    }
    if app_settings.USERS_AUTH_API:
        api_password_change_url = reverse(API_PASSWORD_CHANGE_URL_NAME)
        payload["api_password_change_url"] = request.build_absolute_uri(
            api_password_change_url
        )
        api_password_reset_url = reverse("users:user_password_reset")
        payload["api_password_reset_url"] = request.build_absolute_uri(
            api_password_reset_url
        )
    return payload
