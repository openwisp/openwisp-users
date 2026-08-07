from django.contrib.auth import SESSION_KEY as AUTH_SESSION_KEY
from django.contrib.auth import get_user_model
from django.urls import NoReverseMatch, reverse, reverse_lazy
from django.utils.translation import gettext_lazy as _

SESSION_KEY = "openwisp_password_based_login"

# Used by PasswordExpirationMiddleware to know where to redirect
# when a user's password has expired.
ACCOUNT_CHANGE_PASSWORD_PATH = reverse_lazy("account_change_password")
# OpenWISP Users API can be disabled using the OPENWISP_USERS_AUTH_API setting.
# We avoid using reverse_lazy here because it would raise an exception if the API is
# disabled.
API_PASSWORD_CHANGE_URL_NAME = "users:user_password_change"


def record_password_based_token(user, password_based):
    """
    Persist on the user whether the token just issued was obtained with the
    local password, so stateless endpoints (eg: token-based APIs) can
    recover how the *current token* was obtained, independently of whatever
    session the same user may separately hold in a browser.
    """
    if user is None or not user.is_authenticated:
        return
    user.password_based_token = password_based
    get_user_model().objects.filter(pk=user.pk).update(
        password_based_token=password_based
    )


def record_password_based_login(request, password_based):
    """
    Record on the session whether the user logged in with the local password.
    """
    request.session[SESSION_KEY] = password_based


def is_password_based_login(request=None, user=None):
    """
    Return whether the local password was used to authenticate.

    Session-authenticated requests are answered from the session marker; a
    missing marker means password-based, so expiration enforcement does not
    silently change for sessions established before this feature existed.

    Requests without a session (for example, Bearer token authentication)
    fall back to the persisted ``user.password_based_token``, where ``None``
    (no token issued since this feature was introduced) also means
    password-based.
    """
    session = getattr(request, "session", None)
    if session is not None and AUTH_SESSION_KEY in session:
        return session.get(SESSION_KEY) is not False
    user = user if user is not None else getattr(request, "user", None)
    return getattr(user, "password_based_token", None) is not False


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
        api_password_reset_url = reverse("users:user_password_reset")
    except NoReverseMatch:
        pass
    else:
        payload["api_password_reset_url"] = request.build_absolute_uri(
            api_password_reset_url
        )
    return payload
