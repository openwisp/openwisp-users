from unittest.mock import patch

from django.contrib.sessions.backends.db import SessionStore
from django.test import RequestFactory, TestCase
from django.urls import NoReverseMatch

from ..auth import (
    PASSWORD,
    get_authentication_method,
    is_password_authenticated,
    password_expired_response_payload,
)


class TestAuthenticationMethodTracking(TestCase):
    def test_missing_session_marker_defaults_to_password(self):
        # Sessions established before this feature existed have no marker
        # at all; they must keep being treated as password-authenticated
        # so expiration enforcement does not silently change for them.
        request = RequestFactory().get("/")
        request.session = SessionStore()
        self.assertEqual(get_authentication_method(request), PASSWORD)
        self.assertEqual(is_password_authenticated(request), True)

    def test_payload_omits_url_when_reverse_fails(self):
        # When OPENWISP_USERS_AUTH_API is disabled, "users:rest_password_change"
        # is not part of the urlconf and reverse() raises NoReverseMatch.
        # Blocking still has to work in that case, so the payload builder
        # must degrade to omitting the key instead of propagating the error.
        request = RequestFactory().get("/")
        with patch("openwisp_users.auth.reverse", side_effect=NoReverseMatch):
            payload = password_expired_response_payload(request)
        self.assertNotIn("api_password_change_url", payload)
        self.assertEqual(payload["code"], "password_expired")
