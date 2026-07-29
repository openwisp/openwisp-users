from django.contrib.sessions.backends.db import SessionStore
from django.test import RequestFactory, TestCase

from ..auth import (
    EXTERNAL,
    PASSWORD,
    SESSION_KEY,
    get_authentication_method,
    is_password_authenticated,
    set_authentication_method,
)
from .utils import TestOrganizationMixin


class TestAuthenticationMethodTracking(TestOrganizationMixin, TestCase):
    def test_missing_session_marker_defaults_to_password(self):
        # Sessions established before this feature existed have no marker
        # at all; they must keep being treated as password-authenticated
        # so expiration enforcement does not silently change for them.
        request = RequestFactory().get("/")
        request.session = SessionStore()
        self.assertEqual(get_authentication_method(request), PASSWORD)
        self.assertEqual(is_password_authenticated(request), True)
        # Same fallback applies when reading straight off a user with no
        # recorded method (eg: a stateless token endpoint with no session).
        user = self._get_user()
        self.assertEqual(user.last_login_method, "")
        self.assertEqual(get_authentication_method(user=user), PASSWORD)
        self.assertEqual(is_password_authenticated(user=user), True)

    def test_set_authentication_method_with_external_login(self):
        """
        The public helper set_authentication_method should work for any
        external login method (e.g. SAML).
        """
        request = RequestFactory().get("/")
        request.session = SessionStore()
        request.user = self._get_user()
        set_authentication_method(request, EXTERNAL)
        self.assertEqual(request.session[SESSION_KEY], EXTERNAL)
        self.assertEqual(get_authentication_method(request), EXTERNAL)
        self.assertEqual(is_password_authenticated(request), False)
        request.user.refresh_from_db()
        self.assertEqual(request.user.last_login_method, EXTERNAL)
        self.assertEqual(is_password_authenticated(user=request.user), False)
