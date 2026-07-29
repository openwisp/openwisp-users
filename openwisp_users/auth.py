from django.contrib.auth import get_user_model
from django.urls import NoReverseMatch, reverse, reverse_lazy
from django.utils.translation import gettext_lazy as _

SESSION_KEY = "openwisp_auth_method"
PASSWORD = "password"
EXTERNAL = "external"

# Used by PasswordExpirationMiddleware to know where to redirect
# when a user's password has expired.
ACCOUNT_CHANGE_PASSWORD_PATH = reverse_lazy("account_change_password")
# OpenWISP Users API can be disabled using the OPENWISP_USERS_AUTH_API setting.
# We avoid using reverse_lazy here because it would raise an exception if the API is
# disabled.
API_PASSWORD_CHANGE_URL_NAME = "users:rest_password_change"


def record_authentication_method(user, method):
    """
    Persist the method on the user, so stateless endpoints (eg: token-based
    APIs) can recover it later without a session.
    """
    if user is None or not user.is_authenticated:
        return
    user.last_login_method = method
    get_user_model().objects.filter(pk=user.pk).update(last_login_method=method)


def set_authentication_method(request, method, user=None):
    request.session[SESSION_KEY] = method
    record_authentication_method(user or getattr(request, "user", None), method)


def get_authentication_method(request=None, user=None):
    """
    Sessions without a marker predate this feature, or never had one to
    begin with (eg: token-based APIs with no session). Fall back to the
    user's persisted ``last_login_method``, and finally to PASSWORD, so
    expiration keeps being enforced when the method is unknown.
    """
    method = request.session.get(SESSION_KEY) if request is not None else None
    if method is not None:
        return method
    user = user if user is not None else getattr(request, "user", None)
    return getattr(user, "last_login_method", "") or PASSWORD


def is_password_authenticated(request=None, user=None):
    return get_authentication_method(request, user=user) != EXTERNAL


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
    try:
        api_password_change_url = reverse(API_PASSWORD_CHANGE_URL_NAME)
    except NoReverseMatch:
        pass
    else:
        payload["api_password_change_url"] = request.build_absolute_uri(
            api_password_change_url
        )
    try:
        api_password_reset_url = reverse("users:rest_password_reset")
    except NoReverseMatch:
        pass
    else:
        payload["api_password_reset_url"] = request.build_absolute_uri(
            api_password_reset_url
        )
    return payload
