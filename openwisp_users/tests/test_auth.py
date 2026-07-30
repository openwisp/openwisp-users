from django.contrib.auth import SESSION_KEY as AUTH_SESSION_KEY
from django.contrib.sessions.backends.db import SessionStore
from django.test import RequestFactory, TestCase

from ..auth import (
    EXTERNAL,
    PASSWORD,
    SESSION_KEY,
    get_authentication_method,
    is_password_authenticated,
    record_authentication_method,
    set_authentication_method,
)
from .utils import TestOrganizationMixin


def _authenticated_session(user):
    """
    A bare ``SessionStore`` has no ``AUTH_SESSION_KEY``, so it reads as a
    stateless caller (eg: a Bearer-token request). Set the same key Django
    itself sets on login, so the returned session models a real
    session-authenticated (browser) request.
    """
    session = SessionStore()
    session[AUTH_SESSION_KEY] = str(user.pk)
    session.user = user
    return session


class TestAuthenticationMethodTracking(TestOrganizationMixin, TestCase):
    def test_missing_session_marker_defaults_to_password(self):
        # A session established before this feature existed (or that never
        # marked itself) has no marker; it must keep being treated as
        # password-authenticated so expiration enforcement does not
        # silently change for it.
        user = self._get_user()
        request = RequestFactory().get("/")
        request.session = _authenticated_session(user)
        self.assertEqual(get_authentication_method(request), PASSWORD)
        self.assertEqual(is_password_authenticated(request), True)

    def test_stateless_caller_falls_back_to_persisted_method(self):
        # No request/session at all (eg: a Bearer-token endpoint): the
        # only signal available is the persisted last_login_method.
        user = self._get_user()
        self.assertEqual(user.last_login_method, "")
        self.assertEqual(get_authentication_method(user=user), PASSWORD)
        self.assertEqual(is_password_authenticated(user=user), True)

        record_authentication_method(user, EXTERNAL)
        user.refresh_from_db()
        self.assertEqual(get_authentication_method(user=user), EXTERNAL)
        self.assertEqual(is_password_authenticated(user=user), False)

    def test_request_with_no_session_falls_back_to_persisted_method(self):
        user = self._get_user()
        record_authentication_method(user, EXTERNAL)
        user.refresh_from_db()
        request = RequestFactory().get("/")
        request.user = user
        self.assertEqual(get_authentication_method(request), EXTERNAL)
        self.assertEqual(is_password_authenticated(request), False)

    def test_unmarked_session_ignores_other_sessions_persisted_method(self):
        # Two independent sessions for the same user: session A is
        # session-authenticated but never set a marker of its own. A later
        # external login in session B persists EXTERNAL on the user, but
        # that must not change how session A is classified, or an SSO
        # login elsewhere would silently unblock an unrelated
        # expired-password session.
        user = self._get_user()
        session_a = RequestFactory().get("/")
        session_a.session = _authenticated_session(user)
        session_b = RequestFactory().get("/")
        session_b.session = _authenticated_session(user)
        set_authentication_method(session_b, EXTERNAL)
        record_authentication_method(user, EXTERNAL)
        user.refresh_from_db()
        self.assertEqual(user.last_login_method, EXTERNAL)
        self.assertEqual(get_authentication_method(session_a), PASSWORD)
        self.assertEqual(is_password_authenticated(session_a), True)

    def test_unmarked_session_ignores_other_sessions_password_login(self):
        # The converse: a later password login in session B must not
        # misclassify an external session A that marked itself.
        user = self._get_user()
        session_a = RequestFactory().get("/")
        session_a.session = _authenticated_session(user)
        session_a.session[SESSION_KEY] = EXTERNAL
        session_b = RequestFactory().get("/")
        session_b.session = _authenticated_session(user)
        session_b.user = user
        set_authentication_method(session_b, PASSWORD)
        record_authentication_method(user, PASSWORD)
        user.refresh_from_db()
        self.assertEqual(user.last_login_method, PASSWORD)
        self.assertEqual(get_authentication_method(session_a), EXTERNAL)
        self.assertEqual(is_password_authenticated(session_a), False)

    def test_set_authentication_method_with_external_login(self):
        """
        The public helper set_authentication_method should work for any
        external login method (e.g. SAML).
        """
        user = self._get_user()
        request = RequestFactory().get("/")
        request.session = _authenticated_session(user)
        request.user = user
        set_authentication_method(request, EXTERNAL)
        self.assertEqual(request.session[SESSION_KEY], EXTERNAL)
        self.assertEqual(get_authentication_method(request), EXTERNAL)
        self.assertEqual(is_password_authenticated(request), False)
        request.user.refresh_from_db()
        self.assertEqual(request.user.last_login_method, "")
