from uuid import UUID

from django.test import TestCase
from django.test.utils import override_settings

from .utils import TestOrganizationMixin


class TestBackends(TestOrganizationMixin, TestCase):
    def _test_user_auth_backend_helper(self, username, password, pk):
        self.client.login(username=username, password=password)
        self.assertIn('_auth_user_id', self.client.session)
        self.assertEqual(
            UUID(self.client.session['_auth_user_id'], version=4), pk,
        )
        self.client.logout()
        self.assertNotIn('_auth_user_id', self.client.session)

    @override_settings(
        AUTHENTICATION_BACKENDS=('openwisp_users.backends.UserAuthenticationBackend',)
    )
    def test_user_auth_backend(self):
        user = self._create_user(
            username='tester',
            email='tester@gmail.com',
            phone_number='+237675579231',
            password='tester',
        )
        with self.subTest('Test login with username'):
            self._test_user_auth_backend_helper('tester', 'tester', user.pk)

        with self.subTest('Test login with email'):
            self._test_user_auth_backend_helper('tester@gmail.com', 'tester', user.pk)

        with self.subTest('Test login with phone_number'):
            self._test_user_auth_backend_helper('+237675579231', 'tester', user.pk)

    @override_settings(
        AUTHENTICATION_BACKENDS=('openwisp_users.backends.UserAuthenticationBackend',)
    )
    def test_user_with_email_as_username_auth_backend(self):
        user1 = self._create_user(
            username='tester',
            email='tester@gmail.com',
            phone_number='+237675579231',
            password='tester',
        )
        user = self._create_user(
            username='tester@gmail.com',
            email='tester1@gmail.com',
            phone_number='+237675579232',
            password='tester1',
        )
        self._test_user_auth_backend_helper(user.username, 'tester1', user.pk)
        self._test_user_auth_backend_helper(user1.email, 'tester', user1.pk)

    @override_settings(
        AUTHENTICATION_BACKENDS=('openwisp_users.backends.UserAuthenticationBackend',)
    )
    def test_user_with_phone_number_as_username_auth_backend(self):
        user1 = self._create_user(
            username='tester',
            email='tester@gmail.com',
            phone_number='+237675579231',
            password='tester',
        )
        user = self._create_user(
            username='+237675579231',
            email='tester1@gmail.com',
            phone_number='+237675579232',
            password='tester1',
        )

        self._test_user_auth_backend_helper(user.username, 'tester1', user.pk)
        self._test_user_auth_backend_helper(user1.phone_number, 'tester', user1.pk)
