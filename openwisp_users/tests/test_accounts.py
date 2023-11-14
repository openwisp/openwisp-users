from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils.timezone import now, timedelta

from .. import settings as app_settings
from .utils import TestOrganizationMixin

User = get_user_model()


class TestAccountView(TestOrganizationMixin, TestCase):
    def _login_user(self, username='tester', password='tester'):
        response = self.client.post(
            reverse('account_login'),
            data={'login': username, 'password': password},
            follow=True,
        )
        return response

    @patch.object(app_settings, 'USER_PASSWORD_EXPIRATION', 30)
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
                'your password.</li>\n</ul>'
            ),
            html=True,
        )
        self.assertEqual(
            response.request.get('PATH_INFO'), reverse('account_change_password')
        )
        # Password expired users can browse accounts views
        self.assertContains(
            response, '<label for="id_oldpassword">Current Password:</label>'
        )
        self.assertContains(response, '<label for="id_password1">New Password:</label>')

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
                'your password at http://testserver/accounts/password/change/</li>'
            ),
        )

    @patch.object(app_settings, 'USER_PASSWORD_EXPIRATION', 0)
    def test_user_login_password_expiration_disabled(self):
        self._test_login_flow()

    @patch.object(app_settings, 'USER_PASSWORD_EXPIRATION', 90)
    def test_user_login_password_expiration_enabled(self):
        self._test_login_flow()

    def test_redirection_to_success_page_after_password_update(self):
        user = self._create_operator()
        self.client.force_login(user)
        response = self.client.post(
            reverse('account_change_password'),
            data={
                'oldpassword': 'tester',
                'password1': 'newpassword',
                'password2': 'newpassword',
            },
            follow=True,
        )
        self.assertContains(response, 'Your password has been changed successfully.')
        self.assertContains(response, 'This web page can be closed.')

    def test_inactive_user_login(self):
        self._create_org_user()
        User.objects.update(is_active=False)
        response = self._login_user()
        self.assertContains(
            response, 'The username and/or password you specified are not correct.'
        )
