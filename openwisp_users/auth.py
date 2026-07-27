from django.urls import NoReverseMatch, reverse, reverse_lazy
from django.utils.translation import gettext_lazy as _

SESSION_KEY = "openwisp_auth_method"
PASSWORD = "password"
EXTERNAL = "external"

# Shared by PasswordExpirationMiddleware and ObtainAuthTokenView so the two
# enforcement points can't drift apart on where the change-password page lives.
ACCOUNT_CHANGE_PASSWORD_PATH = reverse_lazy("account_change_password")
# OpenWISP Users API can be disabled using the OPENWISP_USERS_AUTH_API setting.
# We avoid using reverse_lazy here because it would raise an exception if the API is
# disabled.
API_PASSWORD_CHANGE_URL_NAME = "users:rest_password_change"


def set_authentication_method(request, method):
    request.session[SESSION_KEY] = method


def get_authentication_method(request):
    """
    Sessions without a marker predate this feature: default to PASSWORD
    so expiration keeps being enforced for them.
    """
    return request.session.get(SESSION_KEY, PASSWORD)


def is_password_authenticated(request):
    return get_authentication_method(request) != EXTERNAL


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
    }
    try:
        api_password_change_url = reverse(API_PASSWORD_CHANGE_URL_NAME)
    except NoReverseMatch:
        pass
    else:
        payload["api_password_change_url"] = request.build_absolute_uri(
            api_password_change_url
        )
    return payload
