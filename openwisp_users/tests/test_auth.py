from django.contrib.auth import SESSION_KEY as AUTH_SESSION_KEY
from django.contrib.auth import get_user_model
from django.contrib.sessions.backends.db import SessionStore
from django.test import RequestFactory, TestCase
from rest_framework.authtoken.models import Token

from ..api.authentication import SesameAuthentication
from ..auth import (
    SESSION_KEY,
    create_auth_token,
    is_password_based_login,
    is_password_based_user,
    record_password_based_login,
)
from .utils import TestOrganizationMixin

User = get_user_model()


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


class TestPasswordBasedLoginTracking(TestOrganizationMixin, TestCase):
    def test_missing_session_marker_defaults_to_password(self):
        # A session established before this feature existed (or that never
        # marked itself) has no marker; it must keep being treated as
        # password-based so expiration enforcement does not silently change
        # for it.
        user = self._get_user()
        request = RequestFactory().get("/")
        request.session = _authenticated_session(user)
        self.assertEqual(is_password_based_login(request), True)

    def test_stateless_caller_falls_back_to_persisted_token(self):
        # No request/session at all (eg: a Bearer-token endpoint): the
        # only signal available is the persisted password_based_token.
        user = self._get_user()
        self.assertEqual(user.password_based_token, None)
        self.assertEqual(is_password_based_login(user=user), True)

        User.objects.filter(pk=user.pk).update(password_based_token=False)
        user.refresh_from_db()
        self.assertEqual(is_password_based_login(user=user), False)

    def test_request_with_no_session_falls_back_to_persisted_token(self):
        user = self._get_user()
        User.objects.filter(pk=user.pk).update(password_based_token=False)
        user.refresh_from_db()
        request = RequestFactory().get("/")
        request.user = user
        self.assertEqual(is_password_based_login(request), False)

    def test_token_overrides_session(self):
        """
        A Bearer request may carry an unrelated browser session.

        Its provenance must come from the DRF token that authenticated it.
        """
        cases = (
            ("external session and password token", False, True),
            ("password session and external token", True, False),
        )
        for label, session_password_based, token_password_based in cases:
            with self.subTest(label=label):
                username = label.replace(" ", "_")
                user = self._create_user(
                    username=username, email=f"{username}@example.com"
                )
                token_request = RequestFactory().post("/")
                if not token_password_based:
                    token_request.user = user
                    token_request.successful_authenticator = SesameAuthentication()
                token = create_auth_token(token_request, user)
                request = RequestFactory().get("/")
                request.user = user
                request.auth = token
                request.session = _authenticated_session(user)
                record_password_based_login(request, session_password_based)
                self.assertEqual(
                    is_password_based_login(request),
                    token_password_based,
                    "The DRF token used to authenticate the request "
                    "must take precedence.",
                )

    def test_unmarked_session_ignores_other_sessions_persisted_token(self):
        # Two independent sessions for the same user: session A is
        # session-authenticated but never set a marker of its own. A later
        # non-password login in session B persists False on the user, but
        # that must not change how session A is classified, or an SSO login
        # elsewhere would silently unblock an unrelated expired-password
        # session.
        user = self._get_user()
        session_a = RequestFactory().get("/")
        session_a.session = _authenticated_session(user)
        session_b = RequestFactory().get("/")
        session_b.session = _authenticated_session(user)
        record_password_based_login(session_b, False)
        User.objects.filter(pk=user.pk).update(password_based_token=False)
        user.refresh_from_db()
        self.assertEqual(user.password_based_token, False)
        self.assertEqual(is_password_based_login(session_a), True)

    def test_unmarked_session_ignores_other_sessions_password_login(self):
        # The converse: a later password login in session B must not
        # misclassify an external session A that marked itself.
        user = self._get_user()
        session_a = RequestFactory().get("/")
        session_a.session = _authenticated_session(user)
        session_a.session[SESSION_KEY] = False
        session_b = RequestFactory().get("/")
        session_b.session = _authenticated_session(user)
        session_b.user = user
        record_password_based_login(session_b, True)
        User.objects.filter(pk=user.pk).update(password_based_token=True)
        user.refresh_from_db()
        self.assertEqual(user.password_based_token, True)
        self.assertEqual(is_password_based_login(session_a), False)

    def test_record_password_based_login_with_external_login(self):
        """
        The public helper record_password_based_login should work for any
        non-password login (e.g. SAML).
        """
        user = self._get_user()
        request = RequestFactory().get("/")
        request.session = _authenticated_session(user)
        request.user = user
        record_password_based_login(request, False)
        self.assertEqual(request.session[SESSION_KEY], False)
        self.assertEqual(is_password_based_login(request), False)
        request.user.refresh_from_db()
        self.assertEqual(request.user.password_based_token, None)


class TestCreateAuthToken(TestOrganizationMixin, TestCase):
    def test_anonymous_request_with_explicit_user_is_password_based(self):
        # The caller supplied local credentials, so this token is password-based.
        user = self._get_user()
        request = RequestFactory().post("/")
        create_auth_token(request, user)
        user.refresh_from_db()
        self.assertEqual(user.password_based_token, True)
        self.assertEqual(is_password_based_user(user), True)

    def test_sesame_authenticated_request_is_not_password_based(self):
        user = self._get_user()
        request = RequestFactory().get("/")
        request.user = user
        request.successful_authenticator = SesameAuthentication()
        create_auth_token(request, user)
        user.refresh_from_db()
        self.assertEqual(user.password_based_token, False)
        self.assertEqual(is_password_based_user(user), False)

    def test_session_with_passwordless_marker_is_not_password_based(self):
        user = self._get_user()
        request = RequestFactory().get("/")
        request.session = _authenticated_session(user)
        request.user = user
        record_password_based_login(request, False)
        create_auth_token(request, user)
        user.refresh_from_db()
        self.assertEqual(user.password_based_token, False)
        self.assertEqual(is_password_based_user(user), False)

    def test_session_with_no_marker_is_password_based(self):
        user = self._get_user()
        request = RequestFactory().get("/")
        request.session = _authenticated_session(user)
        request.user = user
        create_auth_token(request, user)
        user.refresh_from_db()
        self.assertEqual(user.password_based_token, True)
        self.assertEqual(is_password_based_user(user), True)

    def test_renew_replaces_token_and_keeps_provenance(self):
        user = self._get_user()
        request = RequestFactory().post("/")
        first_token = create_auth_token(request, user)
        request.user = user
        request.successful_authenticator = SesameAuthentication()
        second_token = create_auth_token(request, user, renew=True)
        self.assertNotEqual(first_token.key, second_token.key)
        self.assertEqual(Token.objects.filter(user=user).count(), 1)
        user.refresh_from_db()
        self.assertEqual(is_password_based_user(user), False)

    def test_is_password_based_user_none_is_password_based(self):
        user = self._get_user()
        Token.objects.create(user=user)
        self.assertEqual(user.password_based_token, None)
        self.assertEqual(is_password_based_user(user), True)
