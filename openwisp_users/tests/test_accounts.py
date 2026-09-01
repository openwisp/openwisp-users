import re
from unittest.mock import patch

from allauth.core.context import request_context
from allauth.socialaccount.helpers import complete_social_login
from allauth.socialaccount.models import SocialAccount, SocialLogin
from django.conf import settings
from django.contrib.auth import authenticate, get_user_model
from django.contrib.auth import login as auth_login
from django.contrib.auth.models import AnonymousUser
from django.contrib.messages.storage.fallback import FallbackStorage
from django.core import mail
from django.test import RequestFactory, TestCase, modify_settings
from django.urls import reverse
from django.utils.timezone import now, timedelta

from .. import settings as app_settings
from ..api.authentication import get_one_time_auth_token_for_user
from ..auth import SESSION_KEY, create_auth_token, is_password_based_user
from .utils import TestOrganizationMixin

User = get_user_model()


class TestAccountView(TestOrganizationMixin, TestCase):
    def _login_user(self, username="tester", password="tester"):
        response = self.client.post(
            reverse("account_login"),
            data={"login": username, "password": password},
            follow=True,
        )
        return response

    def _complete_social_login(self, user):
        # Drives the same post-authentication entry point every allauth
        # provider callback calls once a provider confirms the user's
        # identity, without needing to mock a real OAuth handshake.
        SocialAccount.objects.create(user=user, provider="google", uid="1234567890")
        sociallogin = SocialLogin(
            account=SocialAccount(provider="google", uid="1234567890")
        )
        request = RequestFactory().get("/")
        request.session = self.client.session
        request.user = AnonymousUser()
        request._messages = FallbackStorage(request)
        with request_context(request):
            complete_social_login(request, sociallogin)
        request.session.save()
        self.client.cookies[settings.SESSION_COOKIE_NAME] = request.session.session_key

    def test_password_login_marks_session_as_password_based(self):
        self._create_org_user()
        self._login_user()
        self.assertEqual(self.client.session[SESSION_KEY], True)

    def test_social_login_marks_session_as_not_password_based(self):
        user = self._create_org_user().user
        self._complete_social_login(user)
        self.assertEqual(self.client.session[SESSION_KEY], False)

    def test_social_login_issues_non_password_based_token(self):
        user = self._create_org_user().user
        self._complete_social_login(user)
        request = RequestFactory().get("/")
        request.session = self.client.session
        request.user = user
        create_auth_token(request, user)
        user.refresh_from_db()
        self.assertEqual(is_password_based_user(user), False)
        self.assertEqual(user.password_based_token, False)

    @patch.object(app_settings, "USER_PASSWORD_EXPIRATION", 30)
    def test_external_session_bypasses_expired_password_check(self):
        user = self._create_administrator(organizations=[self._get_org()])
        User.objects.update(password_updated=now() - timedelta(days=60))
        user.refresh_from_db()
        self.assertEqual(user.has_password_expired(), True)
        # Password expiration is enforced only for password-based sessions.
        self._complete_social_login(user)
        self.assertEqual(self.client.session[SESSION_KEY], False)
        response = self.client.get(reverse("admin:index"))
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(
            response, "Your password has expired, please update your password."
        )

    @modify_settings(AUTHENTICATION_BACKENDS={"append": "sesame.backends.ModelBackend"})
    @patch.object(app_settings, "USER_PASSWORD_EXPIRATION", 30)
    def test_sesame_login_marks_session_as_not_password_based(self):
        user = self._create_administrator(organizations=[self._get_org()])
        User.objects.update(password_updated=now() - timedelta(days=60))
        user.refresh_from_db()
        self.assertEqual(user.has_password_expired(), True)
        token = get_one_time_auth_token_for_user(user)
        request = RequestFactory().get("/")
        request.session = self.client.session
        request.user = AnonymousUser()
        request._messages = FallbackStorage(request)
        authenticated_user = authenticate(request, sesame=token)
        self.assertIsNotNone(authenticated_user)
        auth_login(request, authenticated_user)
        request.session.save()
        self.client.cookies[settings.SESSION_COOKIE_NAME] = request.session.session_key
        self.assertEqual(self.client.session[SESSION_KEY], False)
        response = self.client.get(reverse("admin:index"))
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(
            response, "Your password has expired, please update your password."
        )

    @patch.object(app_settings, "USER_PASSWORD_EXPIRATION", 30)
    def test_password_expired_user_logins(self):
        self._create_org_user()
        User.objects.update(password_updated=now() - timedelta(days=60))
        response = self._login_user()
        self.assertContains(
            response,
            (
                '<ul class="messagelist">\n'
                '<li class="success">Successfully signed in as tester.</li>\n\n'
                '<li class="warning">Your password has expired, please update '
                "your password.</li>\n</ul>"
            ),
            html=True,
        )
        self.assertEqual(
            response.request.get("PATH_INFO"), reverse("account_change_password")
        )
        # Password expired users can browse accounts views
        self.assertContains(
            response, '<label for="id_oldpassword">Current Password:</label>'
        )
        self.assertContains(response, '<label for="id_password1">New Password:</label>')

    def _test_expired_user_password_reset(self, user):
        User.objects.update(password_updated=now() - timedelta(days=60))
        user.refresh_from_db()
        self.assertEqual(user.has_password_expired(), True)
        response = self.client.post(
            reverse(
                "account_reset_password",
            ),
            data={"email": user.email},
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.request.get("PATH_INFO"), reverse("account_reset_password_done")
        )
        self.assertContains(response, "We have sent you an email")
        email = mail.outbox.pop()
        password_reset_url = re.search(r"https?://[^\s]+", email.body).group(0)
        response = self.client.get(
            password_reset_url,
        )
        response = self.client.post(
            response.url,
            data={"password1": "newpassword", "password2": "newpassword"},
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.request.get("PATH_INFO"),
            reverse("account_reset_password_from_key_done"),
        )

    @patch.object(app_settings, "USER_PASSWORD_EXPIRATION", 30)
    def test_password_expired_user_reset_password(self):
        user = self._create_org_user().user
        self._test_expired_user_password_reset(user)

    @patch.object(app_settings, "USER_PASSWORD_EXPIRATION", 30)
    def test_password_expired_user_reset_password_after_login(self):
        user = self._create_org_user().user
        self._login_user()
        self._test_expired_user_password_reset(user)

    def _test_login_flow(self):
        self._create_org_user()
        User.objects.update(password_updated=now() - timedelta(days=60))
        response = self._login_user()
        self.assertContains(
            response,
            (
                '<ul class="messagelist">\n'
                '<li class="success">Successfully signed in as tester.</li>\n</ul>'
            ),
            html=True,
        )
        self.assertNotContains(
            response,
            (
                '<li class="warning">Your password has expired, please update '
                "your password at http://testserver/accounts/password/change/</li>"
            ),
        )

    @patch.object(app_settings, "USER_PASSWORD_EXPIRATION", 0)
    def test_user_login_password_expiration_disabled(self):
        self._test_login_flow()

    @patch.object(app_settings, "USER_PASSWORD_EXPIRATION", 90)
    def test_user_login_password_expiration_enabled(self):
        self._test_login_flow()

    def test_redirection_to_success_page_after_password_update(self):
        user = self._create_operator()
        self.client.force_login(user)
        response = self.client.post(
            reverse("account_change_password"),
            data={
                "oldpassword": "tester",
                "password1": "newpassword",
                "password2": "newpassword",
            },
            follow=True,
        )
        self.assertContains(response, "Your password has been changed successfully.")
        self.assertContains(response, "This web page can be closed.")

    def test_inactive_user_login(self):
        self._create_org_user()
        User.objects.update(is_active=False)
        response = self._login_user()
        self.assertContains(
            response, "The username and/or password you specified are not correct."
        )

    def test_social_login_user_change_password(self):
        """
        Tests the scenario where a user registers with social login
        and then accesses the change password view.
        """
        # This test simulates the scenario where a user signs up using
        # social login. Social login users do not set a password, so to
        # verify this behavior, we set an unusable password to the user
        # object.
        user = self._create_org_user().user
        user.set_unusable_password()
        user.save()
        self.client.force_login(user)
        response = self.client.get(reverse("account_change_password"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response,
            (
                "<h1>You cannot change your password from this application because"
                " your account is linked to a third-party authentication provider.</h1>"
                "<h1>Please visit the provider's website to manage your password.</h1>"
                "<h1>This web page can be closed.</h1>"
            ),
            html=True,
        )
